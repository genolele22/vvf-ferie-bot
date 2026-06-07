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
TBL    = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
TXT    = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
STY    = "urn:oasis:names:tc:opendocument:xmlns:style:1.0"
FO     = "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
CELL = f"{{{TBL}}}table-cell"
COV  = f"{{{TBL}}}covered-table-cell"
ROW  = f"{{{TBL}}}table-row"
P    = f"{{{TXT}}}p"

# ── layout pagina (A4 portrait, margini 1cm → area utile 27.7cm) ────────────────
PAGE_USABLE_CM    = 27.7     # 29.7 - 1 - 1
SAFETY_CM         = 0.7      # margine di sicurezza sotto il limite pagina
TARGET_CM         = PAGE_USABLE_CM - SAFETY_CM   # 27.0 → tetto per ciascun blocco
DEFAULT_ROW_CM    = 0.621    # altezza riga di riferimento del template
VIGILE_ROW_CM     = 0.5      # altezza imposta alle righe dati (vigili)
STRUCT_THRESH_CM  = 0.7      # righe più alte di così = strutturali (altezza preservata)

GRADI = r"(?:Cs|Vp|Cr|Cf|Asp|Dc|Isp)"

DIST_SIGLA: dict[str, str] = {
    "AEROPORTO": "AP",
    "BOLZANETO": "BL",
    "BUSALLA":   "BS",
    "CHIAVARI":  "CH",
    "GADDA":     "GA",
    "GEEST":     "GE",
    "MLNAU":     "MN",
    "MULTEDO":   "ML",
    "RAPALLO":   "RP",
    # CENTRALE e SMZT: nessuna sigla
}


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


def _normalizza_label(label: str) -> str:
    """'CS MOLINARI 2' → 'Cs Molinari 2'"""
    return " ".join(p.capitalize() if not p.isdigit() else p for p in label.split())


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


def _trova_furieri_names_idx(rows: list) -> int:
    """Restituisce l'indice della riga con i nomi furieri (quella SOTTO 'Furieri'), o -1."""
    for i, row in enumerate(rows):
        if "Furieri" in _row_text(row):
            return i + 1
    return -1


def _rimuovi_nome_da_mezzi(rows: list, pa_idx: int, odt_label: str, furieri_idx: int) -> str:
    """
    Cerca la label esatta (es. 'Vp Genovesi') nelle righe SOPRA pa_idx,
    saltando la riga dei furieri (non va toccata).
    """
    for i, row in enumerate(rows[:pa_idx]):
        if i == furieri_idx:
            continue
        for cell in row.iter(CELL):
            txt = _cell_text(cell)
            if odt_label in txt:
                _clear_cell(cell)
                logger.info("Rimosso '%s' dalla cella mezzo", odt_label)
                return odt_label

    # Fallback: regex su cognome
    parts = odt_label.split()
    cognome = parts[1] if len(parts) >= 2 else odt_label
    num = parts[2] if len(parts) >= 3 and parts[2].isdigit() else None
    pattern = re.compile(
        rf"({GRADI})\s+{re.escape(cognome)}(?:\s+{num})?" if num
        else rf"({GRADI})\s+{re.escape(cognome)}(?:\s+\d+)?",
        re.IGNORECASE,
    )
    for i, row in enumerate(rows[:pa_idx]):
        if i == furieri_idx:
            continue
        for cell in row.iter(CELL):
            txt = _cell_text(cell)
            if pattern.search(txt):
                _clear_cell(cell)
                logger.info("Rimosso '%s' (fallback regex) dalla cella mezzo", odt_label)
                return odt_label

    logger.warning("Nome non trovato nei mezzi: %s", odt_label)
    return odt_label


def _inserisci_in_ferie(rows: list, ferie_start: int, missione_idx: int,
                        label: str, sigla: str, turni: int, da_giorno: str, a_giorno: str):
    """
    Trova la prima riga FERIE con la cella Cognome vuota e la riempie.
    Colonne (celle dirette per riga): 0=Cognome, 1=Sigla dist., 2=Turni, 3=Da, 4=A
    """
    for row in rows[ferie_start:missione_idx]:
        cells = _direct_cells(row)
        if len(cells) < 5:
            continue
        if _cell_text(cells[0]).strip():
            continue  # riga già occupata
        _set_cell_text(cells[0], label)
        if sigla and len(cells) > 1:
            _set_cell_text(cells[1], sigla)
        _set_cell_text(cells[2], str(turni))
        _set_cell_text(cells[3], da_giorno)
        _set_cell_text(cells[4], a_giorno)
        return
    logger.warning("Nessuna riga FERIE libera per %s", label)


# ── layout: imponi altezze e taglio a due pagine ────────────────────────────────

def _parse_cm(val: str | None) -> float | None:
    if val and val.endswith("cm"):
        try:
            return float(val[:-2])
        except ValueError:
            return None
    return None


def _altezze_dichiarate(root) -> dict[str, float]:
    """Mappa style-name (table-row) → altezza in cm dichiarata nel template."""
    out: dict[str, float] = {}
    for st in root.iter(f"{{{STY}}}style"):
        if st.get(f"{{{STY}}}family") != "table-row":
            continue
        rp = st.find(f"{{{STY}}}table-row-properties")
        if rp is None:
            continue
        h = _parse_cm(rp.get(f"{{{STY}}}row-height"))
        if h is not None:
            out[st.get(f"{{{STY}}}name")] = h
    return out


def _imposta_due_pagine(root, rows: list, pa_idx: int):
    """
    Forza il foglio su due pagine esatte:
    - blocco 1 (righe 0..pa_idx-1)  → pagina 1
    - blocco 2 (righe pa_idx..fine) → pagina 2 (page-break su PERSONALE ASSENTE)
    Impone a ogni riga un'altezza esplicita (use-optimal-row-height=false) ricalcolata
    così che ciascun blocco rientri in TARGET_CM. Senza questo LibreOffice gonfia le
    righe al contenuto e il foglio sfora su 3+ pagine.
    """
    autostyles = root.find(f"{{{OFFICE}}}automatic-styles")
    if autostyles is None:
        logger.error("automatic-styles non trovato: impossibile imporre le altezze")
        return

    dichiarate = _altezze_dichiarate(root)
    # righe dati (vigili) → altezza fissa bassa; righe strutturali (intestazione) → invariate
    base = []
    for r in rows:
        h = dichiarate.get(r.get(f"{{{TBL}}}style-name"), DEFAULT_ROW_CM)
        base.append(h if h > STRUCT_THRESH_CM else VIGILE_ROW_CM)

    # fattore di compressione per blocco: comprime ancora solo se un blocco sfora TARGET_CM
    sum1 = sum(base[:pa_idx]) or 1.0
    sum2 = sum(base[pa_idx:]) or 1.0
    factor1 = min(1.0, TARGET_CM / sum1)
    factor2 = min(1.0, TARGET_CM / sum2)
    logger.info(
        "Altezze ODT: blocco1=%.2fcm (x%.3f), blocco2=%.2fcm (x%.3f)",
        sum1, factor1, sum2, factor2,
    )

    for i, row in enumerate(rows):
        factor = factor1 if i < pa_idx else factor2
        new_h = round(base[i] * factor, 3)
        style = etree.SubElement(autostyles, f"{{{STY}}}style")
        style.set(f"{{{STY}}}name", f"GenRow{i}")
        style.set(f"{{{STY}}}family", "table-row")
        props = etree.SubElement(style, f"{{{STY}}}table-row-properties")
        props.set(f"{{{STY}}}row-height", f"{new_h}cm")
        props.set(f"{{{STY}}}use-optimal-row-height", "false")
        props.set(f"{{{FO}}}keep-together", "always")
        if i == pa_idx:
            props.set(f"{{{FO}}}break-before", "page")
        row.set(f"{{{TBL}}}style-name", f"GenRow{i}")


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

    ferie = db.get_ferianti_per_giorno(data_iso)

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

    furieri_idx = _trova_furieri_names_idx(rows)
    ferie_data_start = col_header_idx + 1

    for r in (ferie or []):
        if r["odt_label"]:
            odt_label = r["odt_label"]
        else:
            qc = (r.get("qcodice") or "").capitalize()   # "VP" → "Vp"
            cg = (r["cognome"] or "").title()             # "GENOVESI" → "Genovesi"
            odt_label = f"{qc} {cg}".strip()
        sigla        = DIST_SIGLA.get(r["distaccamento"], "")
        ferie_label  = _normalizza_label(odt_label)
        _rimuovi_nome_da_mezzi(rows, pa_idx, odt_label, furieri_idx)
        da_giorno = str(date.fromisoformat(r["da"]).day)
        a_giorno  = str(date.fromisoformat(r["a"]).day)
        _inserisci_in_ferie(rows, ferie_data_start, missione_idx, ferie_label, sigla, r["turni"], da_giorno, a_giorno)

    # Sempre: imponi le altezze e taglia su due pagine (anche senza ferie)
    _imposta_due_pagine(root, rows, pa_idx)

    xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=False)

    # Reimpacchetta: mimetype DEVE essere primo e STORED (standard ODF)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zout:
        for info, data in entries:
            if info.filename == "content.xml":
                data = xml_out
            zout.writestr(info, data)  # info preserva compress_type originale
    return buf.getvalue()
