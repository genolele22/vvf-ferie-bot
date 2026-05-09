"""
Legge 'Turno B nuovo.csv' e aggiorna la colonna odt_label nel DB.
Il CSV ha formato: LABEL_ODT,email,gruppo,grado,distaccamento
La label viene salvata in title case (es. "CS API" → "Cs Api").

Uso:
    python scripts/update_odt_labels.py
    python scripts/update_odt_labels.py --csv /path/to/file.csv
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database as db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/turno_b_labels.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db.init_db()

    # Aggiungi colonna se mancante (migrazione sicura)
    with db.get_conn() as conn:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN odt_label TEXT")
            print("Colonna odt_label aggiunta al DB.")
        except Exception:
            pass  # già esiste

    aggiornati = 0
    non_trovati = []

    with open(args.csv, encoding="cp1252") as f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            raw_label, email = row[0].strip(), row[1].strip().lower()
            odt_label = raw_label.title()

            user = db.find_user_by_email(email)
            if user is None:
                non_trovati.append(f"  ✗ {odt_label!r:30} email={email}")
                continue

            if not args.dry_run:
                db.set_odt_label(user["id"], odt_label)
            tag = "[DRY] " if args.dry_run else ""
            print(f"{tag}✓ {odt_label!r:30} → {user['nome']} {user['cognome']} ({email})")
            aggiornati += 1

    print(f"\nAggiornati: {aggiornati}")
    if non_trovati:
        print(f"Non trovati ({len(non_trovati)}):")
        for m in non_trovati:
            print(m)


if __name__ == "__main__":
    main()
