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
    Restituisce i giorni di riposo (D/N) per un gruppo in un mese specifico,
    cioè i giorni in cui gli ALTRI gruppi sono in turno (e il gruppo indicato è a casa).
    NON filtra i Salto — il chiamante deve escluderli consultando il DB.
    """
    prefisso = f"{anno:04d}-{mese:02d}-"
    cal = _get_cal()
    result = []
    for date_str, entry in cal.items():
        if date_str.startswith(prefisso) and entry["gruppo"] != gruppo:
            result.append((date.fromisoformat(date_str), entry["tipo"]))
    return sorted(result)


def gruppo_in_servizio(d: date) -> dict | None:
    """Restituisce {"tipo", "gruppo"} per la data, o None se nessun gruppo B è in turno."""
    return _get_cal().get(d.isoformat())


# ── blocchi ciclici B1→B8 (scambio salto turno) ─────────────────────────────────
#
# Ogni slot di riposo (B1..B8) compare nel calendario come un giorno D + il giorno N
# successivo. In ordine di data gli slot scorrono ...B8,B1,B2,...,B8,B1... : un "blocco"
# è il giro completo B1→B8 (B8 = fine giro). Lo scambio è ammesso solo in avanti, dentro
# lo stesso blocco, fino a B8.

def _slot_num(gruppo: str) -> int:
    return int(gruppo[1:])


def _occorrenze() -> list[tuple[int, date, date]]:
    """Lista (slot, data_D, data_N) ordinata per data_D. data_N = data_D + 1 giorno."""
    cal = _get_cal()
    occ = [
        (_slot_num(v["gruppo"]), date.fromisoformat(k), date.fromisoformat(k) + timedelta(days=1))
        for k, v in cal.items()
        if v["tipo"] == "D"
    ]
    return sorted(occ, key=lambda x: x[1])


def blocco_corrente(d: date) -> tuple[date, date]:
    """
    Confini del blocco B1→B8 che contiene la data d:
    (data_D di B1, data_N di B8). Il blocco "possiede" tutte le date dal suo B1
    fino al B1 successivo (escluso).
    """
    occ = _occorrenze()
    starts = [o for o in occ if o[0] == 1]
    inizio = starts[0]
    for o in starts:
        if o[1] <= d:
            inizio = o
        else:
            break
    fine = next((o for o in occ if o[0] == 8 and o[1] >= inizio[1]), inizio)
    return inizio[1], fine[2]


def blocco_successivo(blocco: tuple[date, date]) -> tuple[date, date] | None:
    """Il blocco B1→B8 immediatamente dopo quello dato, o None se il calendario
    non arriva fin là."""
    inizio, _ = blocco
    occ = _occorrenze()
    nb_starts = [o for o in occ if o[0] == 1 and o[1] > inizio]
    if not nb_starts:
        return None
    return blocco_corrente(nb_starts[0][1])


def slot_dates_in_blocco(slot: int, blocco: tuple[date, date]) -> tuple[date, date] | None:
    """(data_D, data_N) dello slot dentro il blocco, o None se non presente."""
    inizio, fine = blocco
    for s, dd, nn in _occorrenze():
        if s == slot and inizio <= dd <= fine:
            return dd, nn
    return None


def prossimo_salto(slot: int, da: date | None = None) -> tuple[date, date] | None:
    """Prima occorrenza (data_D, data_N) dello slot strettamente dopo `da` (default oggi)."""
    da = da or date.today()
    for s, dd, nn in _occorrenze():
        if s == slot and dd > da:
            return dd, nn
    return None
