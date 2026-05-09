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
        elif pa_idx != -1:
            if "Cognome" in t and "Turni" in t and "Da" in t:
                ferie_col_header_idx = i
            elif "MISSIONE" in t:
                missione_idx = i
                break
    return pa_idx, ferie_col_header_idx, missione_idx


def _rimuovi_nome_da_mezzi(rows: list, pa_idx: int, odt_label: str) -> str:
    """
    Cerca la label esatta (es. 'Vp Genovesi') nelle righe SOPRA pa_idx.
    Svuota la cella e restituisce la label.
    Come fallback usa il regex su cognome.
    """
    # Ricerca esatta della label (es. "Vp Genovesi")
    for row in rows[:pa_idx]:
        for cell in row.iter(CELL):
            txt = _cell_text(cell)
            if odt_label in txt:
                _clear_cell(cell)
                logger.info("Rimosso '%s' dalla cella mezzo", odt_label)
                return odt_label

    # Fallback: regex su cognome (per utenti senza odt_label nel DB)
    parts = odt_label.split()
    cognome = parts[1] if len(parts) >= 2 else odt_label
    num = parts[2] if len(parts) >= 3 and parts[2].isdigit() else None
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
                logger.info("Rimosso '%s' (fallback regex) dalla cella mezzo", odt_label)
                return odt_label

    logger.warning("Nome non trovato nei mezzi: %s", odt_label)
    return odt_label


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

    # Leggi il .odt (zip) preservando ordine e tipo compressione di ogni entry
    with zipfile.ZipFile(odt_path, "r") as zin:
        entries = [
            (info, zin.read(info.filename))
            for info in zin.infolist()
        ]

    xml_bytes = next(data for info, data in entries if info.filename == "content.xml")
    root = etree.fromstring(xml_bytes)
    rows = root.findall(f".//{ROW}")

    pa_idx, col_header_idx, missione_idx = _trova_indici_sezioni(rows)
    if pa_idx == -1 or col_header_idx == -1 or missione_idx == -1:
        logger.error("Struttura .odt non riconosciuta per %s", gruppo_rc)
        return None

    ferie_data_start = col_header_idx + 1
    data_fmt = d.strftime("%d/%m/%Y")

    for r in ferie:
        odt_label = r["odt_label"] if r["odt_label"] else r["cognome"]
        label = _rimuovi_nome_da_mezzi(rows, pa_idx, odt_label)
        _inserisci_in_ferie(rows, ferie_data_start, missione_idx, label, r["tipo_turno"], data_fmt)

    xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=False)

    # Reimpacchetta: mimetype DEVE essere primo e STORED (standard ODF)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zout:
        for info, data in entries:
            if info.filename == "content.xml":
                data = xml_out
            zout.writestr(info, data)  # info preserva compress_type originale
    return buf.getvalue()
