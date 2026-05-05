"""
Interfaccia di lettura del calendario turni B.
Carica calendario.json una sola volta e risponde a query sui turni.
I giorni Salto sono gestiti a livello DB (tabella salto), non qui.
"""

import json
from datetime import date, timedelta
from config import CALENDARIO_PATH

_cal: dict | None = None


def _get_cal() -> dict:
    global _cal
    if _cal is None:
        with open(CALENDARIO_PATH) as f:
            _cal = json.load(f)
    return _cal


def get_turno(d: date) -> dict | None:
    """
    Restituisce {"tipo": "D"|"N", "gruppo": "B#"} o None se nessun gruppo B è in servizio.
    Non tiene conto dei Salto individuali (responsabilità del chiamante).
    """
    return _get_cal().get(d.isoformat())


def date_in_servizio(gruppo: str, mesi: int = 6) -> list[tuple[date, str]]:
    """
    Restituisce lista (data, tipo) per cui il gruppo è in servizio nei prossimi mesi.
    NON filtra i Salto — il chiamante deve escluderli consultando il DB.
    """
    oggi  = date.today()
    fine  = oggi + timedelta(days=mesi * 31)
    cal   = _get_cal()
    result = []
    for date_str, entry in cal.items():
        d = date.fromisoformat(date_str)
        if oggi <= d <= fine and entry["gruppo"] == gruppo:
            result.append((d, entry["tipo"]))
    return sorted(result)


def date_per_mese(gruppo: str, anno: int, mese: int) -> list[tuple[date, str]]:
    """
    Restituisce i giorni di servizio (D/N) per un gruppo in un mese specifico.
    NON filtra i Salto — il chiamante deve escluderli consultando il DB.
    """
    prefisso = f"{anno:04d}-{mese:02d}-"
    cal = _get_cal()
    result = []
    for date_str, entry in cal.items():
        if date_str.startswith(prefisso) and entry["gruppo"] == gruppo:
            result.append((date.fromisoformat(date_str), entry["tipo"]))
    return sorted(result)


def gruppo_in_servizio(d: date) -> dict | None:
    """Restituisce {"tipo", "gruppo"} per la data, o None se nessun gruppo B è in turno."""
    return _get_cal().get(d.isoformat())
