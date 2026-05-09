"""
Genera il Foglio di Servizio .odt per una data specifica.
- Carica il template del gruppo in RC quel giorno (B1-B8.odt)
- Trova i nomi dei ferianti nelle colonne mezzi (sopra PERSONALE ASSENTE)
- Li rimuove dal mezzo e li inserisce nella sezione FERIE
"""

import io
import re
import zipfile
import logging
from datetime import date
from pathlib import Path

from lxml import etree

import calendar_turni as cal
import database as db
from config import ODT_TEMPLATES_DIR

logger = logging.getLogger(__name__)

# Namespace ODT
TBL  = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
TXT  = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
CELL = f"{{{TBL}}}table-cell"
COV  = f"{{{TBL}}}covered-table-cell"
ROW  = f"{{{TBL}}}table-row"
P    = f"{{{TXT}}}p"

GRADI = r"(?:Cs|Vp|Cr|Cf|Asp|Dc|Isp)"


# ── helpers XML ───────────────────────────────────────────────────────────────

def _row_text(row) -> str:
    return " ".join(
        (p.text or "").strip()
        for p in row.iter(P)
        if (p.text or "").strip()
    )


def _cell_text(cell) -> str:
    return " ".join(
        (p.text or "").strip()
        for p in cell.iter(P)
        if (p.text or "").strip()
    )


def _clear_cell(cell):
    for p in cell.iter(P):
        p.text = None
        for child in list(p):
            p.remove(child)


def _set_cell_text(cell, text: str):
    p = cell.find(P)
    if p is not None:
        _clear_cell(cell)
        p.text = text


def _direct_cells(row) -> list:
    """Restituisce solo i table-cell diretti (non covered) di una riga."""
    return [c for c in row if c.tag == CELL]


# ── logica principale ─────────────────────────────────────────────────────────

def _trova_indici_sezioni(rows: list) -> tuple[int, int, int]:
    """
    Restituisce (pa_idx, ferie_col_header_idx, missione_idx).
    pa_idx               = riga "PERSONALE ASSENTE"
    ferie_col_header_idx = riga "Cognome | Turni | Da | A"
    missione_idx         = riga "MISSIONE o PERMESSO"
    """
    pa_idx = ferie_col_header_idx = missione_idx = -1
    for i, row in enumerate(rows):
        t = _row_text(row)
        if "PERSONALE ASSENTE" in t and pa_idx == -1:
            pa_idx = i
        if "FERIE" in t and "RIPOSO COMPENSATIVO" in t and pa_idx != -1:
            pass  # riga header sezioni — il col header è la successiva
        if "Cognome" in t and "Turni" in t and "Da" in t and pa_idx != -1:
            ferie_col_header_idx = i
        if "MISSIONE" in t and pa_idx != -1:
            missione_idx = i
            break
    return pa_idx, ferie_col_header_idx, missione_idx


def _rimuovi_nome_da_mezzi(rows: list, pa_idx: int, cognome: str, num: int | None) -> str:
    """
    Cerca 'Grado Cognome [num]' nelle righe SOPRA pa_idx.
    Svuota la cella e restituisce l'etichetta completa trovata (es. 'Vp Genovesi').
    """
    pattern = re.compile(
        rf"({GRADI})\s+{re.escape(cognome)}(?:\s+{num})?" if num
        else rf"({GRADI})\s+{re.escape(cognome)}(?:\s+\d+)?",
        re.IGNORECASE,
    )
    for row in rows[:pa_idx]:
        for cell in row.iter(CELL):
            txt = _cell_text(cell)
            m = pattern.search(txt)
            if m:
                _clear_cell(cell)
                # Ricostruisci etichetta: grado + cognome (+ num se c'è)
                grado = m.group(1)
                label = f"{grado} {cognome}"
                if num:
                    label += f" {num}"
                logger.info("Rimosso '%s' dalla cella mezzo", label)
                return label
    logger.warning("Nome non trovato nei mezzi: %s", cognome)
    return cognome


def _inserisci_in_ferie(rows: list, ferie_start: int, missione_idx: int,
                        label: str, tipo: str, data_str: str):
    """
    Trova la prima riga FERIE con la cella Cognome vuota e la riempie.
    Colonne (celle dirette per riga): 0=Cognome, 1=?, 2=Turni, 3=Da, 4=A
    """
    for row in rows[ferie_start:missione_idx]:
        cells = _direct_cells(row)
        if len(cells) < 5:
            continue
        cognome_cell = cells[0]
        if _cell_text(cognome_cell).strip():
            continue  # riga già occupata
        # Riga libera — inserisci
        _set_cell_text(cells[0], label)       # Cognome
        _set_cell_text(cells[2], "1")         # Turni
        _set_cell_text(cells[3], data_str)    # Da
        _set_cell_text(cells[4], data_str)    # A
        return
    logger.warning("Nessuna riga FERIE libera per %s", label)


# ── entry point pubblico ──────────────────────────────────────────────────────

def genera_foglio(data_iso: str) -> bytes | None:
    """
    Genera il .odt modificato per la data indicata.
    Restituisce i bytes del file o None in caso di errore.
    """
    d = date.fromisoformat(data_iso)
    turno = cal.get_turno(d)
    if not turno:
        logger.warning("Nessun gruppo in calendario per %s", data_iso)
        return None

    gruppo_rc = turno["gruppo"]          # es. "B4" — il gruppo in RC quel giorno
    odt_path  = Path(ODT_TEMPLATES_DIR) / f"{gruppo_rc}.odt"
    if not odt_path.exists():
        logger.error("Template non trovato: %s", odt_path)
        return None

    ferie = db.get_requests_by_date(data_iso)
    if not ferie:
        return odt_path.read_bytes()     # nessuna feria, template invariato

    # Leggi il .odt (zip)
    with zipfile.ZipFile(odt_path, "r") as zin:
        xml_bytes   = zin.read("content.xml")
        altri_files = {n: zin.read(n) for n in zin.namelist() if n != "content.xml"}

    root = etree.fromstring(xml_bytes)
    rows = root.findall(f".//{ROW}")

    pa_idx, col_header_idx, missione_idx = _trova_indici_sezioni(rows)
    if pa_idx == -1 or col_header_idx == -1 or missione_idx == -1:
        logger.error("Struttura .odt non riconosciuta per %s", gruppo_rc)
        return None

    ferie_data_start = col_header_idx + 1
    data_fmt = d.strftime("%d/%m/%Y")

    for r in ferie:
        label = _rimuovi_nome_da_mezzi(rows, pa_idx, r["cognome"], r["numero_vvf"])
        _inserisci_in_ferie(rows, ferie_data_start, missione_idx, label, r["tipo_turno"], data_fmt)

    # Serializza e reimpacchetta
    xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=False)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in altri_files.items():
            zout.writestr(name, data)
        zout.writestr("content.xml", xml_out)
    buf.seek(0)
    return buf.read()
