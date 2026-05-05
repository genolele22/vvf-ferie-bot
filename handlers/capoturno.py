"""
Handlers per il capoturno: /pending, /pending_data, approve/reject callbacks.
"""

import logging
from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import database as db
from config import TELEGRAM_CAPOTURNO_ID

logger = logging.getLogger(__name__)

# ── STATI ─────────────────────────────────────────────────────────────────────

R_NOTE = 0

TIPO_LABEL = {
    "D":  "Diurno 🌅",
    "N":  "Notturno 🌙",
    "DN": "Diurno + Notturno 🌅🌙",
}


def _stato_emoji(stato: str) -> str:
    return {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(stato, "?")


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
        f"Data: {d.strftime('%d/%m/%Y')} | {TIPO_LABEL.get(r['tipo_turno'], r['tipo_turno'])}"
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
        kbd = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approva", callback_data=f"approve:{r['id']}"),
            InlineKeyboardButton("❌ Rifiuta", callback_data=f"reject:{r['id']}"),
        ]])
        await update.message.reply_text(
            _format_request(r), parse_mode="Markdown", reply_markup=kbd
        )


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
        kbd = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approva", callback_data=f"approve:{r['id']}"),
            InlineKeyboardButton("❌ Rifiuta", callback_data=f"reject:{r['id']}"),
        ]])
        await update.message.reply_text(
            _format_request(r), parse_mode="Markdown", reply_markup=kbd
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACK approve / reject
# ═══════════════════════════════════════════════════════════════════════════════

async def capoturno_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != TELEGRAM_CAPOTURNO_ID:
        await query.edit_message_text("Azione non autorizzata.")
        return ConversationHandler.END

    action, request_id_s = query.data.split(":", 1)
    request_id = int(request_id_s)

    req = db.get_request(request_id)
    if not req:
        await query.edit_message_text(f"Richiesta #{request_id} non trovata.")
        return ConversationHandler.END

    if req["stato"] != "pending":
        emoji = _stato_emoji(req["stato"])
        await query.edit_message_text(
            f"Richiesta #{request_id} già processata ({emoji} {req['stato']})."
        )
        return ConversationHandler.END

    if action == "approve":
        db.approve_request(request_id)
        await query.edit_message_text(
            f"✅ Richiesta *#{request_id}* approvata.", parse_mode="Markdown"
        )
        await _notifica_pompiere(context, req, "approved", "")
        return ConversationHandler.END

    # action == "reject" → chiedi nota
    context.user_data["reject_id"] = request_id
    await query.edit_message_text(
        f"Richiesta *#{request_id}* — inserisci il motivo del rifiuto\n"
        "(o scrivi `-` per nessuna nota):",
        parse_mode="Markdown",
    )
    return R_NOTE


async def capoturno_reject_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != TELEGRAM_CAPOTURNO_ID:
        return ConversationHandler.END

    nota = update.message.text.strip()
    if nota == "-":
        nota = ""

    request_id = context.user_data.pop("reject_id", None)
    if not request_id:
        await update.message.reply_text("Errore: nessuna richiesta in attesa di rifiuto.")
        return ConversationHandler.END

    req = db.get_request(request_id)
    db.reject_request(request_id, nota)
    await update.message.reply_text(
        f"❌ Richiesta *#{request_id}* rifiutata.", parse_mode="Markdown"
    )
    if req:
        await _notifica_pompiere(context, req, "rejected", nota)
    return ConversationHandler.END


async def capoturno_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("reject_id", None)
    await update.message.reply_text("Operazione annullata.")
    return ConversationHandler.END


def build_capoturno_callback_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(capoturno_callback, pattern=r"^(approve|reject):\d+$"),
        ],
        states={
            R_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, capoturno_reject_note)],
        },
        fallbacks=[CommandHandler("cancel", capoturno_cancel)],
        name="capoturno_conv",
        persistent=False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICA POMPIERE
# ═══════════════════════════════════════════════════════════════════════════════

async def _notifica_pompiere(
    context: ContextTypes.DEFAULT_TYPE,
    req,
    stato: str,
    nota: str,
) -> None:
    with db.get_conn() as conn:
        vigile = conn.execute(
            "SELECT * FROM users WHERE id=?", (req["user_id"],)
        ).fetchone()
    if not vigile or not vigile["telegram_id"]:
        return

    d = date.fromisoformat(req["data_richiesta"])
    tipo_str = TIPO_LABEL.get(req["tipo_turno"], req["tipo_turno"])

    if stato == "approved":
        testo = (
            f"✅ La tua richiesta *#{req['id']}* è stata *approvata*.\n\n"
            f"Data: {d.strftime('%d/%m/%Y')} — {tipo_str}"
        )
    else:
        testo = (
            f"❌ La tua richiesta *#{req['id']}* è stata *rifiutata*.\n\n"
            f"Data: {d.strftime('%d/%m/%Y')} — {tipo_str}"
        )
        if nota:
            testo += f"\n\nMotivo: _{nota}_"

    try:
        await context.bot.send_message(
            chat_id=vigile["telegram_id"],
            text=testo,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error("Errore notifica pompiere per richiesta #%d: %s", req["id"], e)
