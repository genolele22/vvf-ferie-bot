import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional
from config import DATABASE_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id         INTEGER UNIQUE,
                nome                TEXT NOT NULL,
                cognome             TEXT NOT NULL,
                distaccamento       TEXT NOT NULL,
                email               TEXT NOT NULL,
                telefono            TEXT,
                gruppo_turno        TEXT NOT NULL CHECK(gruppo_turno IN ('B1','B2','B3','B4','B5','B6','B7','B8')),
                ruolo               TEXT NOT NULL CHECK(ruolo IN ('pompiere','capoturno')),
                numero_vvf          INTEGER,
                email_password_enc  TEXT
            );

            CREATE TABLE IF NOT EXISTS salto (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                data        TEXT NOT NULL,
                tipo        TEXT NOT NULL CHECK(tipo IN ('D','N')),
                UNIQUE(user_id, data, tipo)
            );

            CREATE TABLE IF NOT EXISTS requests (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL REFERENCES users(id),
                data_richiesta  TEXT NOT NULL,
                tipo_turno      TEXT NOT NULL CHECK(tipo_turno IN ('D','N','DN')),
                stato           TEXT NOT NULL DEFAULT 'pending'
                                    CHECK(stato IN ('pending','approved','rejected')),
                created_at      TEXT NOT NULL,
                processed_at    TEXT,
                note_rifiuto    TEXT
            );
        """)


# ── users ────────────────────────────────────────────────────────────────────

def find_user_by_email(email: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE lower(email)=lower(?)", (email,)
        ).fetchone()


def set_email_password(user_id: int, encrypted_password: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET email_password_enc=? WHERE id=?",
            (encrypted_password, user_id),
        )


def find_user_by_name(nome: str, cognome: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE lower(nome)=lower(?) AND lower(cognome)=lower(?)",
            (nome, cognome),
        ).fetchone()


def find_user_by_telegram_id(telegram_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE telegram_id=?", (telegram_id,)
        ).fetchone()


def set_telegram_id(user_id: int, telegram_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET telegram_id=? WHERE id=?", (telegram_id, user_id)
        )


def insert_user(nome, cognome, distaccamento, email, telefono, gruppo_turno, ruolo,
                numero_vvf=None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO users
               (nome, cognome, distaccamento, email, telefono, gruppo_turno, ruolo, numero_vvf)
               VALUES (?,?,?,?,?,?,?,?)""",
            (nome, cognome, distaccamento, email, telefono, gruppo_turno, ruolo, numero_vvf),
        )
        return cur.lastrowid


def find_user_by_cognome(cognome: str, numero_vvf: int | None = None,
                         distaccamento: str | None = None) -> Optional[sqlite3.Row]:
    """
    Match per il parsing dei fogli ODT.
    Se numero_vvf è presente lo usa come discriminatore primario.
    """
    with get_conn() as conn:
        if numero_vvf is not None:
            return conn.execute(
                "SELECT * FROM users WHERE lower(cognome)=lower(?) AND numero_vvf=?",
                (cognome, numero_vvf),
            ).fetchone()
        if distaccamento:
            row = conn.execute(
                "SELECT * FROM users WHERE lower(cognome)=lower(?) AND lower(distaccamento)=lower(?)",
                (cognome, distaccamento),
            ).fetchone()
            if row:
                return row
        # fallback: solo cognome (ambiguo se duplicati — il chiamante gestisce)
        return conn.execute(
            "SELECT * FROM users WHERE lower(cognome)=lower(?)", (cognome,)
        ).fetchone()


# ── requests ─────────────────────────────────────────────────────────────────

def insert_request(user_id: int, data_richiesta: str, tipo_turno: str) -> int:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO requests (user_id, data_richiesta, tipo_turno, stato, created_at)
               VALUES (?,?,?,'pending',?)""",
            (user_id, data_richiesta, tipo_turno, now),
        )
        return cur.lastrowid


def get_request(request_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM requests WHERE id=?", (request_id,)
        ).fetchone()


def get_requests_by_user(user_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM requests WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()


def get_pending_requests() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """SELECT r.*, u.nome, u.cognome, u.distaccamento, u.gruppo_turno
               FROM requests r JOIN users u ON r.user_id = u.id
               WHERE r.stato='pending'
               ORDER BY r.data_richiesta""",
        ).fetchall()


def get_pending_requests_by_month(anno_mese: str) -> list[sqlite3.Row]:
    """anno_mese = 'YYYY-MM'"""
    with get_conn() as conn:
        return conn.execute(
            """SELECT r.*, u.nome, u.cognome, u.distaccamento, u.gruppo_turno
               FROM requests r JOIN users u ON r.user_id = u.id
               WHERE r.stato='pending' AND r.data_richiesta LIKE ?
               ORDER BY r.data_richiesta""",
            (f"{anno_mese}-%",),
        ).fetchall()


def approve_request(request_id: int):
    now = datetime.utcnow().isoformat(timespec="seconds")
    with get_conn() as conn:
        conn.execute(
            "UPDATE requests SET stato='approved', processed_at=? WHERE id=?",
            (now, request_id),
        )


def reject_request(request_id: int, note: str = ""):
    now = datetime.utcnow().isoformat(timespec="seconds")
    with get_conn() as conn:
        conn.execute(
            "UPDATE requests SET stato='rejected', processed_at=?, note_rifiuto=? WHERE id=?",
            (now, note, request_id),
        )


# ── salto ─────────────────────────────────────────────────────────────────────

def insert_salto(user_id: int, data: str, tipo: str):
    """Inserisce un giorno Salto per un utente. Ignora duplicati."""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO salto (user_id, data, tipo) VALUES (?,?,?)",
            (user_id, data, tipo),
        )


def get_salti_utente(user_id: int) -> set[tuple[str, str]]:
    """Restituisce set di (data_iso, tipo) per i Salto di un utente."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT data, tipo FROM salto WHERE user_id=?", (user_id,)
        ).fetchall()
    return {(r["data"], r["tipo"]) for r in rows}


def is_salto(user_id: int, data: str, tipo: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM salto WHERE user_id=? AND data=? AND tipo=?",
            (user_id, data, tipo),
        ).fetchone()
    return row is not None
