"""
Drain della coda bot_outbox: il gestionale enfila eventi (es. ferie approvata alla
generazione ODT), qui li inviamo via Telegram (API diretta) + mail (account fureria).
Gira in un thread daemon, indipendente dal loop di python-telegram-bot.
"""
import json
import logging
import threading
import time
import urllib.request
from datetime import date

import database as db
import email_service
from config import TELEGRAM_BOT_TOKEN
from email_service import TIPO_LABEL

logger = logging.getLogger(__name__)


def _tg_send(chat_id: int, text: str) -> None:
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data=payload, headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()


def _compose(row: dict) -> str | None:
    if row["tipo"] == "ferie_approvata":
        d = date.fromisoformat(str(row["data"])).strftime("%d/%m/%Y")
        t = TIPO_LABEL.get(row["tipo_turno"], row["tipo_turno"])
        return f"✅ Ferie approvate: {d} {t}.\nIl foglio di servizio è stato generato."
    return None


def _drain_once() -> None:
    rows = db.outbox_fetch_pending()
    if not rows:
        return
    fureria = db.get_fureria_credentials()
    for row in rows:
        try:
            v = db.get_vigile_contacts(row["vigile_id"])
            if not v:
                db.outbox_mark_error(row["id"], "vigile inesistente")
                continue
            text = _compose(row)
            if text and v.get("telegram_id"):
                _tg_send(int(v["telegram_id"]), text)
            if row["tipo"] == "ferie_approvata" and v.get("email") and fureria:
                email_service.send_ferie_conferma(
                    fureria[0], fureria[1], v["email"],
                    v.get("nome") or "", v.get("cognome") or "",
                    str(row["data"]), row["tipo_turno"],
                )
            db.outbox_mark_sent(row["id"])
            logger.info("outbox #%s inviato (vigile %s)", row["id"], row["vigile_id"])
        except Exception as e:
            logger.error("outbox #%s errore: %s", row["id"], e)
            db.outbox_mark_error(row["id"], str(e))


def _run_loop(interval: int) -> None:
    logger.info("Outbox drain avviato (ogni %ss)", interval)
    while True:
        try:
            _drain_once()
        except Exception as e:
            logger.error("drain loop: %s", e)
        time.sleep(interval)


def start(interval: int = 30) -> None:
    threading.Thread(target=_run_loop, args=(interval,), daemon=True).start()
