import datetime
import logging
from contextlib import contextmanager
from typing import Optional

import pymysql
import pymysql.cursors

from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

logger = logging.getLogger(__name__)


# ── connessione ───────────────────────────────────────────────────────────────

def _connect():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ssl_verify_cert": True} if MYSQL_HOST != "127.0.0.1" else None,
    )


@contextmanager
def get_conn():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── normalizzazione date (MySQL restituisce oggetti datetime.date) ─────────────

def _fix(row: Optional[dict]) -> Optional[dict]:
    if row is None:
        return None
    out = {}
    for k, v in row.items():
        if isinstance(v, datetime.datetime):
            out[k] = v.isoformat(timespec="seconds")
        elif isinstance(v, datetime.date):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def _fixall(rows: list) -> list:
    return [_fix(r) for r in rows]


# ── query base vigili ─────────────────────────────────────────────────────────

_VIGILE = """
    SELECT v.id, v.nome, v.cognome, v.telegram_id, v.email, v.telefono,
           v.email_password_enc, v.odt_label,
           v.disambiguatore AS numero_vvf,
           v.ruolo,
           se.nome  AS distaccamento,
           st.codice AS gruppo_turno
    FROM vigili v
    JOIN sedi se       ON v.sede_id  = se.id
    JOIN salti_turno st ON v.salto_id = st.id
"""


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_requests (
                    id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
                    vigile_id      INT UNSIGNED NOT NULL,
                    data_richiesta DATE NOT NULL,
                    tipo_turno     ENUM('D','N','DN') NOT NULL,
                    stato          ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
                    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    processed_at   DATETIME DEFAULT NULL,
                    note_rifiuto   VARCHAR(200) DEFAULT NULL,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_req (vigile_id, data_richiesta, tipo_turno),
                    KEY fk_br_vigile (vigile_id),
                    CONSTRAINT bot_requests_ibfk_1 FOREIGN KEY (vigile_id) REFERENCES vigili (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_salto (
                    id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
                    vigile_id INT UNSIGNED NOT NULL,
                    data      DATE NOT NULL,
                    tipo      ENUM('D','N') NOT NULL,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_salto (vigile_id, data, tipo),
                    CONSTRAINT bot_salto_ibfk_1 FOREIGN KEY (vigile_id) REFERENCES vigili (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)


# ── users / vigili ────────────────────────────────────────────────────────────

def find_user_by_email(email: str) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_VIGILE + " WHERE LOWER(v.email) = LOWER(%s)", (email,))
            return _fix(cur.fetchone())


def set_email_password(user_id: int, encrypted_password: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE vigili SET email_password_enc = %s WHERE id = %s",
                (encrypted_password, user_id),
            )


def find_user_by_name(nome: str, cognome: str) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _VIGILE + " WHERE LOWER(v.nome) = LOWER(%s) AND LOWER(v.cognome) = LOWER(%s)",
                (nome, cognome),
            )
            return _fix(cur.fetchone())


def find_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_VIGILE + " WHERE v.telegram_id = %s", (telegram_id,))
            return _fix(cur.fetchone())


def set_telegram_id(user_id: int, telegram_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE vigili SET telegram_id = %s WHERE id = %s",
                (telegram_id, user_id),
            )


def insert_user(nome, cognome, distaccamento, email, telefono, gruppo_turno, ruolo,
                numero_vvf=None) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sedi WHERE nome = %s", (distaccamento,))
            sede_row = cur.fetchone()
            sede_id = sede_row["id"] if sede_row else 1

            cur.execute("SELECT id FROM salti_turno WHERE codice = %s", (gruppo_turno,))
            salto_row = cur.fetchone()
            salto_id = salto_row["id"] if salto_row else 1

            cur.execute("""
                INSERT INTO vigili
                    (nome, cognome, sede_id, salto_id, qualifica_id,
                     email, telefono, ruolo, disambiguatore)
                VALUES (%s, %s, %s, %s, 1, %s, %s, %s, %s)
            """, (nome, cognome, sede_id, salto_id, email, telefono, ruolo, numero_vvf))
            return cur.lastrowid


def find_user_by_cognome(cognome: str, numero_vvf: int | None = None,
                         distaccamento: str | None = None) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if numero_vvf is not None:
                cur.execute(
                    _VIGILE + " WHERE LOWER(v.cognome) = LOWER(%s) AND v.disambiguatore = %s",
                    (cognome, numero_vvf),
                )
                return _fix(cur.fetchone())
            if distaccamento:
                cur.execute(
                    _VIGILE + " WHERE LOWER(v.cognome) = LOWER(%s) AND LOWER(se.nome) = LOWER(%s)",
                    (cognome, distaccamento),
                )
                row = cur.fetchone()
                if row:
                    return _fix(row)
            cur.execute(_VIGILE + " WHERE LOWER(v.cognome) = LOWER(%s)", (cognome,))
            return _fix(cur.fetchone())


def set_odt_label(user_id: int, odt_label: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE vigili SET odt_label = %s WHERE id = %s",
                (odt_label, user_id),
            )


# ── helpers fogli / assenze ───────────────────────────────────────────────────

def _get_or_create_foglio(cur, data_iso: str, tipo_turno: str) -> int:
    cur.execute(
        "SELECT id FROM fogli_servizio WHERE data_servizio=%s AND tipo_turno=%s",
        (data_iso, tipo_turno),
    )
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute("SELECT MAX(id) AS max_id FROM fogli_servizio")
    next_id = (cur.fetchone()["max_id"] or 0) + 1
    cur.execute(
        "INSERT INTO fogli_servizio (id, data_servizio, tipo_turno, salto_riposo_id, creato_da)"
        " VALUES (%s, %s, %s, 1, 'bot')",
        (next_id, data_iso, tipo_turno),
    )
    return next_id


def _insert_assenza(cur, vigile_id: int, foglio_id: int):
    cur.execute(
        "SELECT id FROM assenze WHERE foglio_id=%s AND vigile_id=%s AND tipo_assenza_id=1",
        (foglio_id, vigile_id),
    )
    if cur.fetchone():
        return
    cur.execute("SELECT MAX(id) AS max_id FROM assenze")
    next_id = (cur.fetchone()["max_id"] or 0) + 1
    cur.execute(
        "INSERT INTO assenze (id, foglio_id, vigile_id, tipo_assenza_id) VALUES (%s, %s, %s, 1)",
        (next_id, foglio_id, vigile_id),
    )


def _delete_assenza(cur, vigile_id: int, data_iso: str, tipo_turno: str):
    if tipo_turno == "DN":
        tipi = ["D", "N"]
    else:
        tipi = [tipo_turno]
    for t in tipi:
        cur.execute(
            "DELETE a FROM assenze a"
            " JOIN fogli_servizio f ON a.foglio_id = f.id"
            " WHERE a.vigile_id=%s AND f.data_servizio=%s AND f.tipo_turno=%s"
            " AND a.tipo_assenza_id=1",
            (vigile_id, data_iso, t),
        )


# ── requests ─────────────────────────────────────────────────────────────────

def insert_request(user_id: int, data_richiesta: str, tipo_turno: str) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO bot_requests (vigile_id, data_richiesta, tipo_turno)
                VALUES (%s, %s, %s)
            """, (user_id, data_richiesta, tipo_turno))
            request_id = cur.lastrowid
            tipi = ["D", "N"] if tipo_turno == "DN" else [tipo_turno]
            for t in tipi:
                foglio_id = _get_or_create_foglio(cur, data_richiesta, t)
                _insert_assenza(cur, user_id, foglio_id)
            return request_id


def get_request(request_id: int) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM bot_requests WHERE id = %s", (request_id,))
            return _fix(cur.fetchone())


def get_requests_by_user(user_id: int) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM bot_requests WHERE vigile_id = %s ORDER BY data_richiesta DESC",
                (user_id,),
            )
            return _fixall(cur.fetchall())


def get_ferie_utente(user_id: int) -> set[tuple[str, str]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT f.data_servizio, f.tipo_turno"
                " FROM assenze a JOIN fogli_servizio f ON a.foglio_id = f.id"
                " WHERE a.vigile_id = %s AND a.tipo_assenza_id = 1",
                (user_id,),
            )
            rows = cur.fetchall()
    return {(str(r["data_servizio"]), r["tipo_turno"]) for r in rows}


def get_pending_requests() -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.*, v.nome, v.cognome,
                       se.nome   AS distaccamento,
                       st.codice AS gruppo_turno
                FROM bot_requests r
                JOIN vigili v       ON r.vigile_id  = v.id
                JOIN sedi se        ON v.sede_id     = se.id
                JOIN salti_turno st ON v.salto_id    = st.id
                WHERE r.stato = 'pending'
                ORDER BY r.data_richiesta
            """)
            return _fixall(cur.fetchall())


def get_pending_requests_by_month(anno_mese: str) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.*, v.nome, v.cognome,
                       se.nome   AS distaccamento,
                       st.codice AS gruppo_turno
                FROM bot_requests r
                JOIN vigili v       ON r.vigile_id  = v.id
                JOIN sedi se        ON v.sede_id     = se.id
                JOIN salti_turno st ON v.salto_id    = st.id
                WHERE r.stato = 'pending'
                  AND DATE_FORMAT(r.data_richiesta, '%%Y-%%m') = %s
                ORDER BY r.data_richiesta
            """, (anno_mese,))
            return _fixall(cur.fetchall())


def get_requests_by_date(data_iso: str) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.*, v.nome, v.cognome,
                       se.nome            AS distaccamento,
                       st.codice          AS gruppo_turno,
                       v.disambiguatore   AS numero_vvf,
                       v.odt_label
                FROM bot_requests r
                JOIN vigili v       ON r.vigile_id  = v.id
                JOIN sedi se        ON v.sede_id     = se.id
                JOIN salti_turno st ON v.salto_id    = st.id
                WHERE r.data_richiesta = %s
                ORDER BY v.cognome
            """, (data_iso,))
            return _fixall(cur.fetchall())


def get_ferianti_per_giorno(data_iso: str) -> list[dict]:
    """
    Ritorna una riga per ogni blocco contiguo di ferie nel mese,
    per i vigili che risultano assenti in data_iso.
    Un blocco = sequenza di date senza buchi > 1 giorno.
    """
    anno_mese = data_iso[:7]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.vigile_id, v.odt_label, v.cognome, v.nome,
                       q.codice AS qcodice,
                       se.nome AS distaccamento,
                       f.data_servizio
                FROM assenze a
                JOIN fogli_servizio f  ON a.foglio_id    = f.id
                JOIN vigili v          ON a.vigile_id    = v.id
                JOIN sedi se           ON v.sede_id      = se.id
                JOIN qualifiche q      ON v.qualifica_id = q.id
                WHERE a.tipo_assenza_id = 1
                  AND a.vigile_id IN (
                    SELECT a2.vigile_id FROM assenze a2
                    JOIN fogli_servizio f2 ON a2.foglio_id = f2.id
                    WHERE f2.data_servizio = %s AND a2.tipo_assenza_id = 1
                  )
                  AND DATE_FORMAT(f.data_servizio, '%%Y-%%m') = %s
                ORDER BY a.vigile_id, f.data_servizio
            """, (data_iso, anno_mese))
            raw = _fixall(cur.fetchall())

    if not raw:
        return []

    # Raggruppa per vigile
    by_vigile: dict[int, dict] = {}
    for r in raw:
        vid = r["vigile_id"]
        if vid not in by_vigile:
            by_vigile[vid] = {"meta": r, "dates": []}
        by_vigile[vid]["dates"].append(r["data_servizio"])

    result = []
    for data in by_vigile.values():
        meta  = data["meta"]
        dates = data["dates"]                     # già ordinate

        # Date uniche per rilevare buchi; le duplicates (DN=2 record/giorno) le teniamo
        unique_dates = sorted(set(dates))

        # Spezza in blocchi contigui (gap > 1 giorno = nuovo blocco)
        blocks: list[list[str]] = []
        current = [unique_dates[0]]
        for d in unique_dates[1:]:
            if (datetime.date.fromisoformat(d) - datetime.date.fromisoformat(current[-1])).days <= 3:
                current.append(d)
            else:
                blocks.append(current)
                current = [d]
        blocks.append(current)

        for block in blocks:
            # Solo il blocco che contiene la data del foglio
            if not (block[0] <= data_iso <= block[-1]):
                continue
            block_set = set(block)
            turni = sum(1 for d in dates if d in block_set)
            result.append({
                "odt_label":    meta["odt_label"],
                "cognome":      meta["cognome"],
                "nome":         meta["nome"],
                "qcodice":      meta["qcodice"],
                "distaccamento": meta["distaccamento"],
                "turni":        turni,
                "da":           block[0],
                "a":            block[-1],
            })

    return result


def get_requests_by_period(da_iso: str, a_iso: str) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.*, v.nome, v.cognome,
                       se.nome   AS distaccamento,
                       st.codice AS gruppo_turno
                FROM bot_requests r
                JOIN vigili v       ON r.vigile_id  = v.id
                JOIN sedi se        ON v.sede_id     = se.id
                JOIN salti_turno st ON v.salto_id    = st.id
                WHERE r.data_richiesta BETWEEN %s AND %s
                ORDER BY r.data_richiesta, v.cognome, v.nome
            """, (da_iso, a_iso))
            return _fixall(cur.fetchall())


def count_requests() -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM bot_requests")
            return cur.fetchone()["cnt"]


def reset_all_requests() -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bot_requests")
            return cur.rowcount


def delete_request(request_id: int, user_id: int) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT data_richiesta, tipo_turno FROM bot_requests"
                " WHERE id=%s AND vigile_id=%s AND stato='pending'",
                (request_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                return False
            cur.execute(
                "DELETE FROM bot_requests WHERE id=%s AND vigile_id=%s AND stato='pending'",
                (request_id, user_id),
            )
            if cur.rowcount > 0:
                _delete_assenza(cur, user_id, str(row["data_richiesta"]), row["tipo_turno"])
                return True
            return False


def approve_request(request_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE bot_requests SET stato = 'approved', processed_at = NOW() WHERE id = %s",
                (request_id,),
            )


def reject_request(request_id: int, note: str = ""):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE bot_requests SET stato = 'rejected', processed_at = NOW(),"
                " note_rifiuto = %s WHERE id = %s",
                (note, request_id),
            )


# ── salto ─────────────────────────────────────────────────────────────────────

def insert_salto(user_id: int, data: str, tipo: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT IGNORE INTO bot_salto (vigile_id, data, tipo) VALUES (%s, %s, %s)",
                (user_id, data, tipo),
            )


def get_salti_utente(user_id: int) -> set[tuple[str, str]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT data, tipo FROM bot_salto WHERE vigile_id = %s", (user_id,)
            )
            rows = cur.fetchall()
    return {(str(r["data"]), r["tipo"]) for r in rows}


def is_salto(user_id: int, data: str, tipo: str) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM bot_salto WHERE vigile_id = %s AND data = %s AND tipo = %s",
                (user_id, data, tipo),
            )
            return cur.fetchone() is not None
