"""
Importa i giorni Salto (Riposo Compensativo) dagli 8 file ODT del foglio di servizio.

Ogni file B#.odt contiene la lista dei vigili in riposo compensativo per quel gruppo.
Il salto viene inserito per TUTTE le date di servizio (D e N) del gruppo nel calendario.

Prerequisiti:
  1. data/calendario.json generato da scripts/genera_calendario.py
  2. DB inizializzato e popolato con scripts/import_csv.py

Uso:
    python scripts/import_salto.py --dir /path/to/odt/
    python scripts/import_salto.py --dir /path/to/odt/ --dry-run
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from odf.opendocument import load
from odf import teletype

import database as db
import calendar_turni as cal

# ── COSTANTI ──────────────────────────────────────────────────────────────────

# Gradi VVF usati nei fogli di servizio (NO "Di" — è particella di cognome)
GRADI = r'(?:Cs|Vp|Cr|Cf|Asp|Dc|Isp)'

# Codici distaccamento → nome nel DB
DIST_MAP = {
    "ML": "Multedo",
    "AP": "Aeroporto",
    "BS": "Busalla",
    "BL": "Bolzaneto",
    "GE": "Genova Est",
    "CH": "Chiavari",
    "RP": "Rapallo",
    "GA": "Nautica",
}
DIST_PAT = r'(?:' + '|'.join(DIST_MAP) + r')'

# ── PARSING ODT ───────────────────────────────────────────────────────────────

def _parse_token(token: str) -> tuple[str, int | None, str | None] | None:
    """
    Parsa un singolo token "Grado Cognome [num] [dist]".
    Restituisce (cognome, numero_vvf, dist_code) o None se non valido.
    """
    token = token.strip()
    m = re.match(rf'^{GRADI}\s+(.+)$', token)
    if not m:
        return None
    rest = m.group(1).strip()

    # Rimuovi dist dal fondo (può essere attaccato senza spazio)
    dm = re.search(rf'({DIST_PAT})\s*$', rest)
    dist = dm.group(1) if dm else None
    if dm:
        rest = rest[:dm.start()].strip()

    # Rimuovi numero dal fondo
    nm = re.search(r'\s*(\d+)\s*$', rest)
    num = int(nm.group(1)) if nm else None
    if nm:
        rest = rest[:nm.start()].strip()

    if not rest or rest.lower().startswith('riposa'):
        return None
    return rest, num, dist


def estrai_nomi_rc(odt_path: Path) -> list[tuple[str, int | None, str | None]]:
    """
    Estrae la lista (cognome, numero_vvf, dist_code) dalla sezione
    RIPOSO COMPENSATIVO del documento ODT.
    """
    doc  = load(str(odt_path))
    text = teletype.extractText(doc.body)

    start = text.find('RIPOSO COMPENSATIVO')
    stop  = text.find('MISSIONE', start)
    if start == -1:
        return []
    sezione = text[start: stop if stop != -1 else None]

    # Splitta ai boundary di grado (lookahead senza \b)
    tokens = re.split(rf'(?={GRADI}\s)', sezione)
    nomi = []
    for tok in tokens:
        r = _parse_token(tok)
        if r:
            nomi.append(r)
    return nomi


# ── MATCHING E IMPORT ─────────────────────────────────────────────────────────

def importa_gruppo(gruppo: str, odt_path: Path, dry_run: bool) -> tuple[int, int, list[str]]:
    """
    Per ogni nome nel file ODT:
    - trova l'utente nel DB
    - inserisce Salto per TUTTE le date di servizio (D e N) del gruppo nel calendario

    Restituisce (inseriti, saltati, warnings).
    """
    nomi = estrai_nomi_rc(odt_path)
    if not nomi:
        return 0, 0, [f"{odt_path.name}: sezione RIPOSO COMPENSATIVO vuota o non trovata"]

    # Tutte le date di servizio del gruppo (D e N, inclusi i salto già marcati nel cal)
    # Usiamo date_in_servizio senza filtro Salto — qui stiamo costruendo il Salto
    from datetime import date
    import json
    from config import CALENDARIO_PATH
    with open(CALENDARIO_PATH) as f:
        cal_data = json.load(f)

    date_gruppo: list[tuple[str, str]] = [
        (data_iso, entry["tipo"])
        for data_iso, entry in cal_data.items()
        if entry["gruppo"] == gruppo
    ]

    if not date_gruppo:
        return 0, 0, [f"Nessuna data in calendario per il gruppo {gruppo}"]

    inseriti = 0
    saltati  = 0
    warnings = []

    for cognome, num, dist_code in nomi:
        dist_full = DIST_MAP.get(dist_code) if dist_code else None
        user = db.find_user_by_cognome(cognome, num, dist_full)

        if user is None:
            warnings.append(
                f"  ⚠  [{gruppo}] utente non trovato: "
                f"'{cognome}' num={num} dist={dist_code}"
            )
            continue

        for data_iso, tipo in date_gruppo:
            if not dry_run:
                if db.is_salto(user["id"], data_iso, tipo):
                    saltati += 1
                else:
                    db.insert_salto(user["id"], data_iso, tipo)
                    inseriti += 1
            else:
                inseriti += 1

    return inseriti, saltati, warnings


# ── MAIN ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", required=True, help="Cartella con i file B1.odt … B8.odt")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main():
    args  = parse_args()
    cartella = Path(args.dir)
    db.init_db()

    tot_ins  = 0
    tot_sal  = 0
    warnings = []

    for gruppo in ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]:
        odt = cartella / f"{gruppo}.odt"
        if not odt.exists():
            warnings.append(f"File non trovato: {odt}")
            continue

        nomi = estrai_nomi_rc(odt)
        label = "[DRY] " if args.dry_run else ""
        print(f"{label}{gruppo}: {len(nomi)} nomi trovati")

        ins, sal, w = importa_gruppo(gruppo, odt, args.dry_run)
        tot_ins += ins
        tot_sal += sal
        warnings.extend(w)

    print()
    label = "[DRY RUN] " if args.dry_run else ""
    print(f"{label}Salto inseriti: {tot_ins}, già presenti: {tot_sal}")

    if warnings:
        print("\nAvvisi:")
        for w in warnings:
            print(w)
        if any("utente non trovato" in w for w in warnings):
            print(
                "\nSuggerimento: verifica che import_csv.py sia stato eseguito "
                "e che i cognomi nel CSV corrispondano ai fogli ODT."
            )
        sys.exit(1)


if __name__ == "__main__":
    main()
