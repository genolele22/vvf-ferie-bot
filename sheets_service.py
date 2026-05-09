"""
Integrazione Google Sheets: registra ogni richiesta ferie su un foglio condiviso.
Usa OAuth 2.0 con refresh token (nessun service account necessario).
Se le credenziali non sono configurate, le operazioni falliscono silenziosamente.
"""

import logging
from datetime import datetime

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN

logger = logging.getLogger(__name__)

SHEET_NAME  = "VVF Ferie Genova"
SCOPES      = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
HEADERS     = ["ID", "Nome", "Cognome", "Gruppo", "Distaccamento", "Data", "Tipo Turno", "Timestamp"]

_gc: gspread.Client | None = None
_sheet: gspread.Worksheet | None = None


def _get_client() -> gspread.Client | None:
    global _gc
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
        _gc = gspread.authorize(creds)
        return _gc
    except Exception as e:
        logger.warning("Google Sheets auth fallita: %s", e)
        return None


def _get_sheet() -> gspread.Worksheet | None:
    global _sheet
    if _sheet is not None:
        return _sheet
    gc = _get_client()
    if gc is None:
        return None
    try:
        try:
            spreadsheet = gc.open(SHEET_NAME)
        except gspread.SpreadsheetNotFound:
            spreadsheet = gc.create(SHEET_NAME)
            spreadsheet.share(None, perm_type="anyone", role="reader")
            logger.info("Spreadsheet '%s' creato: %s", SHEET_NAME, spreadsheet.url)

        ws = spreadsheet.sheet1
        if ws.row_count == 0 or ws.cell(1, 1).value != "ID":
            ws.insert_row(HEADERS, index=1)
        _sheet = ws
        return _sheet
    except Exception as e:
        logger.warning("Errore accesso Google Sheets: %s", e)
        return None


def registra_richiesta(
    request_id: int,
    nome: str,
    cognome: str,
    gruppo: str,
    distaccamento: str,
    data_iso: str,
    tipo_turno: str,
) -> bool:
    ws = _get_sheet()
    if ws is None:
        return False
    try:
        from datetime import date
        data_fmt = date.fromisoformat(data_iso).strftime("%d/%m/%Y")
        ts = datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        ws.append_row([request_id, nome, cognome, gruppo, distaccamento, data_fmt, tipo_turno, ts])
        return True
    except Exception as e:
        logger.warning("Errore scrittura Google Sheets: %s", e)
        return False
