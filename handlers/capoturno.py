"""
Handlers per il capoturno: /pending, /pending_data.
La risposta alle richieste avviene via email (Rispondi direttamente al messaggio ricevuto).
"""

import logging
from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

import database as db
from config import TELEGRAM_CAPOTURNO_ID

logger = logging.getLogger(__name__)

TIPO_LABEL = {
    "D":  "Diurno 🌅",
    "N":  "Notturno 🌙",
    "DN": "Diurno + Notturno 🌅🌙",
}


async def _check_capoturno(update: Update) -> bool:
    if update.effective_user.id != TELEGRAM_CAPOTURNO_ID:
        await update.message.reply_text("Comando riservato al capoturno.")
        return False
    return True


def _format_request(r) -> str:
    d = date.fromisoformat(r["data_richiesta"])
    return (
        f"*#{r['id']}* — {r['nome']} {r['cognome']} "
        f"({r['distaccamento']}, {r['gruppo_turno']})\n"
        f"Data: {d.strftime('%d/%m/%Y')} | {TIPO_LABEL.get(r['tipo_turno'], r['tipo_turno'])}\n"
        f"_Rispondi via email_"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# /pending — tutte le richieste in attesa
# ═══════════════════════════════════════════════════════════════════════════════

async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_capoturno(update):
        return

    richieste = db.get_pending_requests()
    if not richieste:
        await update.message.reply_text("Nessuna richiesta in attesa.")
        return

    for r in richieste:
        await update.message.reply_text(_format_request(r), parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════════════════════
# /pending_data [YYYY-MM] — richieste in attesa per mese
# ═══════════════════════════════════════════════════════════════════════════════

async def pending_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_capoturno(update):
        return

    if context.args:
        anno_mese = context.args[0]
    else:
        oggi = date.today()
        anno_mese = f"{oggi.year:04d}-{oggi.month:02d}"

    richieste = db.get_pending_requests_by_month(anno_mese)
    if not richieste:
        await update.message.reply_text(f"Nessuna richiesta in attesa per {anno_mese}.")
        return

    for r in richieste:
        await update.message.reply_text(_format_request(r), parse_mode="Markdown")
