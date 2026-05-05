"""
Genera data/calendario.json — turni B (B1-B8), Comando VVF Genova.

Ciclo per ogni gruppo B#:
  DIURNO (08:00-20:00) → 24h off → NOTTURNO (20:00-08:00) → 48h off → [prossimo gruppo]
  Ogni gruppo è sfasato di 4 giorni dal successivo. Ciclo completo: 32 giorni.

Punto di riferimento ricavato dallo screenshot (5 mag 2026, cerchiato = oggi):
  B5 era in TURNO DIURNO il 2026-05-05.

I giorni Salto (riposo compensativo) sono assegnati per-vigile nel database,
NON vengono calcolati qui.

Esegui una sola volta:
    python scripts/genera_calendario.py
"""

import json
from datetime import date, timedelta
from pathlib import Path

# ─── PARAMETRI ───────────────────────────────────────────────────────────────

REF_DATE  = date(2026, 5, 5)   # B5 in DIURNO — ricavato dallo screenshot
REF_GROUP = "B5"

ANNO_INIZIO = 2025             # include passato recente per storico
ANNO_FINE   = 2028             # incluso

# ─── COSTANTI ────────────────────────────────────────────────────────────────

GRUPPI = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]
OFFSET = 4                         # giorni tra DIURNO di un gruppo e il successivo
CICLO  = len(GRUPPI) * OFFSET      # 32 giorni


def entry_for_date(d: date) -> dict | None:
    """
    Restituisce {"tipo": "D"|"N", "gruppo": "B#"} per la data d,
    o None se nessun gruppo B è in servizio quel giorno.

    delta % OFFSET == 0  →  DIURNO
    delta % OFFSET == 1  →  NOTTURNO (stesso gruppo del giorno prima)
    delta % OFFSET == 2,3 → OFF (nessun gruppo B in servizio)
    """
    ref_idx = GRUPPI.index(REF_GROUP)
    delta   = (d - REF_DATE).days % CICLO
    rem     = delta % OFFSET

    if rem == 0:
        idx = (ref_idx + delta // OFFSET) % len(GRUPPI)
        return {"tipo": "D", "gruppo": GRUPPI[idx]}

    if rem == 1:
        idx = (ref_idx + (delta - 1) // OFFSET) % len(GRUPPI)
        return {"tipo": "N", "gruppo": GRUPPI[idx]}

    return None


def main():
    inizio = date(ANNO_INIZIO, 1, 1)
    fine   = date(ANNO_FINE, 12, 31)

    print(f"Genero calendario {ANNO_INIZIO}–{ANNO_FINE} (riferimento: {REF_GROUP} DIURNO {REF_DATE}) …")

    calendario = {}
    current = inizio
    while current <= fine:
        entry = entry_for_date(current)
        if entry:
            calendario[current.isoformat()] = entry
        current += timedelta(days=1)

    out_path = Path(__file__).parent.parent / "data" / "calendario.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(calendario, f, indent=2, ensure_ascii=False)

    totale = (fine - inizio).days + 1
    print(f"✅  Scritto {out_path}")
    print(f"    {len(calendario)} giorni con gruppo B in servizio su {totale} totali")


if __name__ == "__main__":
    main()
