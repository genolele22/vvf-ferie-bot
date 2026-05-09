"""
Handlers per il capoturno: /pending, /pending_data, genera_foglio.
La risposta alle richieste avviene via email (Rispondi direttamente al messaggio ricevuto).
"""

import logging
from datetime import date

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

import database as db
import odt_service
from config import TELEGRAM_CAPOTURNO_ID

logger = logging.getLogger(__name__)

MENU_CAPOTURNO = ReplyKeyboardMarkup(
    [["📋 Richieste in attesa", "📅 Per mese"], ["📄 Genera foglio"]],
    resize_keyboard=True,
)

TIPO_LABEL = {
    "D":  "Diurno 🌅",
    "N":  "Notturno 🌙",
    "DN": "Diurno + Notturno 🌅🌙",
}

# stato conversazione genera_foglio
GF_DATA = 0


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
        await update.message.reply_text("Nessuna richiesta in attesa.", reply_markup=MENU_CAPOTURNO)
        return

    for i, r in enumerate(richieste):
        kbd = MENU_CAPOTURNO if i == len(richieste) - 1 else None
        await update.message.reply_text(_format_request(r), parse_mode="Markdown", reply_markup=kbd)


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
        await update.message.reply_text(f"Nessuna richiesta in attesa per {anno_mese}.", reply_markup=MENU_CAPOTURNO)
        return

    for i, r in enumerate(richieste):
        kbd = MENU_CAPOTURNO if i == len(richieste) - 1 else None
        await update.message.reply_text(_format_request(r), parse_mode="Markdown", reply_markup=kbd)


# ═══════════════════════════════════════════════════════════════════════════════
# Genera foglio .odt per una data
# ═══════════════════════════════════════════════════════════════════════════════

async def genera_foglio_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _check_capoturno(update):
        return ConversationHandler.END
    await update.message.reply_text(
        "Inserisci la data del turno (formato *GG/MM/AAAA*):",
        parse_mode="Markdown",
    )
    return GF_DATA


async def genera_foglio_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    testo = update.message.text.strip()
    try:
        d = date.fromisoformat(
            "-".join(reversed(testo.split("/")))
        )
    except ValueError:
        await update.message.reply_text("Formato non valido. Usa GG/MM/AAAA:")
        return GF_DATA

    await update.message.reply_text(f"Genero il foglio per il {d.strftime('%d/%m/%Y')}...")

    odt_bytes = odt_service.genera_foglio(d.isoformat())
    if odt_bytes is None:
        await update.message.reply_text(
            "Nessun gruppo in calendario per questa data, o template non trovato.",
            reply_markup=MENU_CAPOTURNO,
        )
        return ConversationHandler.END

    filename = f"servizio_{d.strftime('%Y%m%d')}.odt"
    await update.message.reply_document(
        document=odt_bytes,
        filename=filename,
        caption=f"Foglio di servizio {d.strftime('%d/%m/%Y')}",
        reply_markup=MENU_CAPOTURNO,
    )
    return ConversationHandler.END


async def genera_foglio_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Annullato.", reply_markup=MENU_CAPOTURNO)
    return ConversationHandler.END


def build_genera_foglio_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("genera_foglio", genera_foglio_start),
            MessageHandler(filters.Regex("^📄 Genera foglio$"), genera_foglio_start),
        ],
        states={
            GF_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, genera_foglio_data)],
        },
        fallbacks=[CommandHandler("cancel", genera_foglio_cancel)],
        name="genera_foglio_conv",
        persistent=False,
    )
