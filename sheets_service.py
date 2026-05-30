"""
Integrazione Google Sheets: un tab per mese, una sezione per gruppo turno.
Una riga per singola richiesta (D/N/DN), con Turni/Da/A aggregati per vigile.
Fail silenzioso se le credenziali non sono configurate.
"""

import logging
from datetime import date, datetime, timezone, timedelta

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

import database as db
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN

logger = logging.getLogger(__name__)

SHEET_NAME = "VVF Ferie Genova"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
GROUPS  = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]
HEADERS = ["Cognome", "Nome", "Distaccamento", "Turni", "Data inizio", "Data fine", "Tipo Turno", "Timestamp"]
MESI_IT = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]

_ROME = timezone(timedelta(hours=2))   # CEST; CEST/CET si aggiusta in estate/inverno


def _now_rome() -> str:
    return datetime.now(_ROME).strftime("%d/%m/%Y %H:%M")


def _fmt(data_iso: str) -> str:
    return date.fromisoformat(data_iso).strftime("%d/%m/%Y")


def _get_spreadsheet() -> gspread.Spreadsheet | None:
    if not GOOGLE_CLIENT_ID or not GOOGLE_REFRESH_TOKEN:
        return None
    try:
        creds = Credentials(
            token=None,
            refresh_token=GOOGLE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=SCOPES,
        )
        creds.refresh(Request())
        gc = gspread.authorize(creds)
        try:
            return gc.open(SHEET_NAME)
        except gspread.SpreadsheetNotFound:
            sp = gc.create(SHEET_NAME)
            logger.info("Spreadsheet '%s' creato: %s", SHEET_NAME, sp.url)
            return sp
    except Exception as e:
        logger.warning("Google Sheets auth fallita: %s", e)
        return None


def _tab_name(year: int, month: int) -> str:
    return f"{MESI_IT[month - 1]} {year}"


def _get_or_create_ws(
    spreadsheet: gspread.Spreadsheet, year: int, month: int
) -> gspread.Worksheet:
    name = _tab_name(year, month)
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=name, rows=300, cols=len(HEADERS))
        _write_sheet(ws, {g: [] for g in GROUPS})
        logger.info("Tab '%s' creato", name)
        return ws


def _richieste_mese(user_id: int, anno: int, mese: int) -> list:
    """Richieste non rifiutate del vigile nel mese, ordinate per data."""
    prefix = f"{anno:04d}-{mese:02d}-"
    reqs = [
        r for r in db.get_requests_by_user(user_id)
        if r["data_richiesta"].startswith(prefix) and r["stato"] != "rejected"
    ]
    return sorted(reqs, key=lambda r: r["data_richiesta"])


def _consecutive_blocks(richieste: list) -> list[list]:
    """
    Raggruppa richieste in blocchi consecutivi.
    Due richieste sono nello stesso blocco se la distanza tra le date è ≤ 1 giorno.
    """
    if not richieste:
        return []
    blocks, current = [], [richieste[0]]
    for r in richieste[1:]:
        prev = date.fromisoformat(current[-1]["data_richiesta"])
        curr = date.fromisoformat(r["data_richiesta"])
        if (curr - prev).days <= 3:
            current.append(r)
        else:
            blocks.append(current)
            current = [r]
    blocks.append(current)
    return blocks


def _build_rows_for_user(nome: str, cognome: str, distaccamento: str, richieste: list) -> list[list]:
    """
    Una riga per richiesta.
    Il conto alla rovescia (Turni) e la data fine (A) si resettano ad ogni blocco consecutivo.
    """
    if not richieste:
        return []
    ts   = _now_rome()
    rows = []
    for block in _consecutive_blocks(richieste):
        a_str = _fmt(block[-1]["data_richiesta"])
        for i, r in enumerate(block):
            rows.append([
                cognome,
                nome,
                distaccamento,
                len(block) - i,
                _fmt(r["data_richiesta"]),
                a_str,
                r["tipo_turno"],
                ts,
            ])
    return rows


def _build_section(user_id: int, nome: str, cognome: str, distaccamento: str, anno: int, mese: int) -> list[list]:
    """Righe aggiornate per un vigile nel mese."""
    richieste = _richieste_mese(user_id, anno, mese)
    return _build_rows_for_user(nome, cognome, distaccamento, richieste)


def _write_sheet(ws: gspread.Worksheet, sections: dict[str, list]) -> None:
    """
    Riscrive il foglio.
    sections = {gruppo: [[cognome, nome, distaccamento, turni, da, a, tipo, ts], ...]}
    Ogni sezione è ordinata per (cognome, nome).
    """
    rows: list[list] = []
    for g in GROUPS:
        sorted_rows = sorted(
            sections.get(g, []),
            key=lambda r: (str(r[0]).lower(), str(r[1]).lower()),  # cognome, nome
        )
        rows.append([f"▶ TURNO {g}"] + [""] * (len(HEADERS) - 1))
        rows.append(HEADERS[:])
        rows.extend(sorted_rows)
        rows.append([""] * len(HEADERS))
    ws.clear()
    if rows:
        ws.update("A1", rows)


def _parse_sheet(ws: gspread.Worksheet) -> dict[str, list]:
    """
    Legge il foglio e restituisce {gruppo: [[riga], ...]}.
    Scarta intestazioni e separatori.
    """
    sections: dict[str, list] = {g: [] for g in GROUPS}
    current: str | None = None
    for row in ws.get_all_values():
        if not row or not row[0]:
            continue
        cell = row[0].strip()
        if cell.startswith("▶ TURNO "):
            current = cell[len("▶ TURNO "):]
        elif cell == "Cognome" or current is None:
            continue
        elif current in sections:
            sections[current].append(row[:len(HEADERS)])
    return sections


def aggiorna_mese(
    user_id: int,
    nome: str,
    cognome: str,
    gruppo: str,
    distaccamento: str,
    anno: int,
    mese: int,
) -> bool:
    """
    Ricalcola e riscrive le righe del vigile nel tab del mese.
    Legge le richieste correnti dal DB — funziona sia per aggiunte che per annullamenti.
    """
    spreadsheet = _get_spreadsheet()
    if spreadsheet is None:
        return False
    try:
        ws       = _get_or_create_ws(spreadsheet, anno, mese)
        sections = _parse_sheet(ws)

        # rimuovi tutte le righe esistenti del vigile in questo gruppo
        sections[gruppo] = [
            r for r in sections.get(gruppo, [])
            if not (r[0] == cognome and r[1] == nome)
        ]

        # aggiungi righe ricalcolate (vuoto se non ha più richieste)
        nuove = _build_section(user_id, nome, cognome, distaccamento, anno, mese)
        sections[gruppo].extend(nuove)

        _write_sheet(ws, sections)
        logger.info("Sheets: aggiornato %s %s — %s/%s (%d righe)", cognome, nome, mese, anno, len(nuove))
        return True
    except Exception as e:
        logger.warning("Errore aggiornamento Google Sheets: %s", e)
        return False
