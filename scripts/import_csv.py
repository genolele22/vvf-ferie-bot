"""
Importa gli utenti da data/utenti.csv nel database.

Colonne CSV (intestazione obbligatoria):
    nome, cognome, numero_vvf, distaccamento, email, telefono, gruppo_turno, ruolo

numero_vvf: intero opzionale (lascia vuoto se non necessario).
            Serve a disambiguare persone con lo stesso cognome (es. "Parodi 20").

Uso:
    python scripts/import_csv.py
    python scripts/import_csv.py --csv /path/alternativo/utenti.csv
    python scripts/import_csv.py --dry-run   # mostra cosa importerebbe senza scrivere
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database as db

CSV_DEFAULT = Path(__file__).parent.parent / "data" / "utenti.csv"

GRUPPI_VALIDI = {"B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"}
RUOLI_VALIDI  = {"pompiere", "capoturno"}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=str(CSV_DEFAULT))
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"❌  File non trovato: {csv_path}")
        sys.exit(1)

    db.init_db()

    inseriti = 0
    saltati  = 0
    errori   = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # riga 1 = intestazione
            try:
                nome         = row["nome"].strip()
                cognome      = row["cognome"].strip()
                numero_vvf   = int(row["numero_vvf"]) if row.get("numero_vvf", "").strip() else None
                distaccamento = row["distaccamento"].strip()
                email        = row["email"].strip()
                telefono     = row.get("telefono", "").strip() or None
                gruppo_turno = row["gruppo_turno"].strip().upper()
                ruolo        = row["ruolo"].strip().lower()

                if not nome or not cognome:
                    raise ValueError("nome/cognome vuoti")
                if gruppo_turno not in GRUPPI_VALIDI:
                    raise ValueError(f"gruppo_turno non valido: {gruppo_turno!r}")
                if ruolo not in RUOLI_VALIDI:
                    raise ValueError(f"ruolo non valido: {ruolo!r}")

                # controlla duplicati
                esistente = db.find_user_by_name(nome, cognome)
                if esistente:
                    saltati += 1
                    print(f"  ⚠  riga {i}: {nome} {cognome} già presente — saltato")
                    continue

                if not args.dry_run:
                    db.insert_user(nome, cognome, distaccamento, email, telefono,
                                   gruppo_turno, ruolo, numero_vvf)
                inseriti += 1
                print(f"  ✅ riga {i}: {nome} {cognome} ({gruppo_turno}, {ruolo})")

            except (KeyError, ValueError) as e:
                errori.append(f"riga {i}: {e}")
                print(f"  ❌ riga {i}: {e}")

    print()
    if args.dry_run:
        print(f"[DRY RUN] Sarebbero inseriti: {inseriti}, saltati: {saltati}, errori: {len(errori)}")
    else:
        print(f"Inseriti: {inseriti}, saltati: {saltati}, errori: {len(errori)}")
    if errori:
        print("\nRighe con errore:")
        for e in errori:
            print(f"  {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
