"""
Handlers per il pompiere: /start, /ferie, /mie_richieste.
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

import calendar_turni as cal
import database as db
from config import TELEGRAM_CAPOTURNO_ID

logger = logging.getLogger(__name__)

# ── STATI ─────────────────────────────────────────────────────────────────────

# /start
S_NOME, S_COGNOME = range(2)

# /ferie
F_MESE, F_DATA, F_TIPO, F_CONFERMA = range(4)

# ── LOOKUP ────────────────────────────────────────────────────────────────────

MESI_IT = {
    1: "Gennaio", 2: "Febbraio", 3: "Marzo",    4: "Aprile",
    5: "Maggio",  6: "Giugno",  7: "Luglio",    8: "Agosto",
    9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre",
}

TIPO_LABEL = {
    "D":  "Diurno 🌅",
    "N":  "Notturno 🌙",
    "DN": "Diurno + Notturno 🌅🌙",
}


def _stato_emoji(stato: str) -> str:
    return {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(stato, "?")


async def _get_registered_user(update: Update) -> db.sqlite3.Row | None:
    user = db.find_user_by_telegram_id(update.effective_user.id)
    if not user:
        await update.message.reply_text(
            "Non sei ancora registrato. Usa /start per registrarti."
        )
    return user


# ═══════════════════════════════════════════════════════════════════════════════
# /start
# ═══════════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.find_user_by_telegram_id(update.effective_user.id)
    if user:
        await update.message.reply_text(
            f"Sei già registrato come {user['nome']} {user['cognome']} "
            f"(gruppo {user['gruppo_turno']}).\n\n"
            "Usa /ferie per richiedere ferie o /mie_richieste per vedere lo storico."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Benvenuto nel sistema ferie — Comando VVF Genova.\n\n"
        "Inserisci il tuo *nome*:",
        parse_mode="Markdown",
    )
    return S_NOME


async def start_ricevi_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nome = update.message.text.strip()
    if not nome:
        await update.message.reply_text("Nome non valido. Riprova:")
        return S_NOME
    context.user_data["reg_nome"] = nome
    await update.message.reply_text("Inserisci il tuo *cognome*:", parse_mode="Markdown")
    return S_COGNOME


async def start_ricevi_cognome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nome    = context.user_data.pop("reg_nome", "")
    cognome = update.message.text.strip()

    user = db.find_user_by_name(nome, cognome)
    if not user:
        await update.message.reply_text(
            "Non ho trovato nessun vigile con questo nome.\n"
            "Controlla l'ortografia o contatta il responsabile per la registrazione."
        )
        return ConversationHandler.END

    if user["telegram_id"] and user["telegram_id"] != update.effective_user.id:
        await update.message.reply_text(
            "Questo nominativo è già associato a un altro account Telegram.\n"
            "Contatta il responsabile."
        )
        return ConversationHandler.END

    db.set_telegram_id(user["id"], update.effective_user.id)
    await update.message.reply_text(
        f"Registrazione completata.\n\n"
        f"Ciao *{user['nome']} {user['cognome']}*, gruppo *{user['gruppo_turno']}*.\n\n"
        "Usa /ferie per richiedere ferie.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def start_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Registrazione annullata.")
    return ConversationHandler.END


def build_start_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            S_NOME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, start_ricevi_nome)],
            S_COGNOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_ricevi_cognome)],
        },
        fallbacks=[CommandHandler("cancel", start_cancel)],
        name="start_conv",
        persistent=False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# /ferie — wizard a step
# ═══════════════════════════════════════════════════════════════════════════════

async def ferie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = await _get_registered_user(update)
    if not user:
        return ConversationHandler.END

    context.user_data["ferie"] = {
        "user_id": user["id"],
        "gruppo":  user["gruppo_turno"],
    }

    oggi = date.today()
    buttons = []
    for i in range(6):
        mese_offset = oggi.month - 1 + i
        anno = oggi.year + mese_offset // 12
        mese = mese_offset % 12 + 1
        buttons.append(InlineKeyboardButton(
            f"{MESI_IT[mese]} {anno}",
            callback_data=f"m:{anno}:{mese:02d}",
        ))

    kbd = InlineKeyboardMarkup([buttons[i:i+2] for i in range(0, len(buttons), 2)])
    await update.message.reply_text(
        "Seleziona il mese:", reply_markup=kbd
    )
    return F_MESE


async def ferie_scegli_mese(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    _, anno_s, mese_s = query.data.split(":")
    anno, mese = int(anno_s), int(mese_s)

    w       = context.user_data["ferie"]
    gruppo  = w["gruppo"]
    user_id = w["user_id"]

    tutte       = cal.date_per_mese(gruppo, anno, mese)
    salti       = db.get_salti_utente(user_id)
    disponibili = [(d, t) for d, t in tutte if (d.isoformat(), t) not in salti]

    if not disponibili:
        await query.edit_message_text(
            f"Nessun turno disponibile in {MESI_IT[mese]} {anno}.\n"
            "Usa /ferie per scegliere un altro mese."
        )
        return ConversationHandler.END

    w["anno"] = anno
    w["mese"] = mese

    buttons = [
        InlineKeyboardButton(
            f"{'🌅' if t == 'D' else '🌙'} {d.strftime('%d/%m')}",
            callback_data=f"d:{d.isoformat()}:{t}",
        )
        for d, t in disponibili
    ]
    rows = [buttons[i:i+3] for i in range(0, len(buttons), 3)]

    await query.edit_message_text(
        f"Turni disponibili — {MESI_IT[mese]} {anno}\n"
        "🌅 Diurno   🌙 Notturno\n\n"
        "Seleziona una data:",
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return F_DATA


async def ferie_scegli_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    _, data_iso, tipo_cal = query.data.split(":")
    w = context.user_data["ferie"]
    w["data"]     = data_iso
    w["tipo_cal"] = tipo_cal

    d = date.fromisoformat(data_iso)

    if tipo_cal == "D":
        buttons = [
            [
                InlineKeyboardButton("🌅 Solo Diurno",      callback_data="t:D"),
                InlineKeyboardButton("🌅🌙 Entrambi (D+N)", callback_data="t:DN"),
            ]
        ]
    else:
        buttons = [[InlineKeyboardButton("🌙 Solo Notturno", callback_data="t:N")]]

    await query.edit_message_text(
        f"Data: *{d.strftime('%d/%m/%Y')}*\n\nChe turno vuoi richiedere?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return F_TIPO


async def ferie_scegli_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    tipo = query.data.split(":")[1]
    w    = context.user_data["ferie"]
    w["tipo"] = tipo

    d      = date.fromisoformat(w["data"])
    turni  = 2 if tipo == "DN" else 1
    d_fine = d.replace(day=d.day + 1) if tipo == "DN" else d  # N è sempre il giorno dopo

    testo = (
        f"*Riepilogo richiesta*\n\n"
        f"Data: {d.strftime('%d/%m/%Y')}"
        + (f" → {d_fine.strftime('%d/%m/%Y')}" if tipo == "DN" else "")
        + f"\nTurno: {TIPO_LABEL[tipo]}\n"
        f"N° turni: {turni}\n\n"
        "Confermi?"
    )

    kbd = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Conferma", callback_data="fc"),
        InlineKeyboardButton("❌ Annulla",  callback_data="fa"),
    ]])
    await query.edit_message_text(testo, parse_mode="Markdown", reply_markup=kbd)
    return F_CONFERMA


async def ferie_conferma(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "fa":
        context.user_data.pop("ferie", None)
        await query.edit_message_text("Richiesta annullata.")
        return ConversationHandler.END

    w         = context.user_data.pop("ferie", {})
    user_id   = w["user_id"]
    data_iso  = w["data"]
    tipo      = w["tipo"]

    request_id = db.insert_request(user_id, data_iso, tipo)

    await query.edit_message_text(
        f"Richiesta *#{request_id}* ricevuta.\n"
        "Riceverai risposta entro ridosso della data.",
        parse_mode="Markdown",
    )

    # Notifica al capoturno
    await _notifica_capoturno(context, request_id, user_id, data_iso, tipo)

    return ConversationHandler.END


async def ferie_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("ferie", None)
    await update.message.reply_text("Richiesta annullata.")
    return ConversationHandler.END


def build_ferie_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("ferie", ferie)],
        states={
            F_MESE:     [CallbackQueryHandler(ferie_scegli_mese, pattern=r"^m:")],
            F_DATA:     [CallbackQueryHandler(ferie_scegli_data, pattern=r"^d:")],
            F_TIPO:     [CallbackQueryHandler(ferie_scegli_tipo, pattern=r"^t:")],
            F_CONFERMA: [CallbackQueryHandler(ferie_conferma,    pattern=r"^f[ca]$")],
        },
        fallbacks=[CommandHandler("cancel", ferie_cancel)],
        name="ferie_conv",
        persistent=False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# /mie_richieste
# ═══════════════════════════════════════════════════════════════════════════════

async def mie_richieste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await _get_registered_user(update)
    if not user:
        return

    richieste = db.get_requests_by_user(user["id"])
    if not richieste:
        await update.message.reply_text("Non hai ancora fatto nessuna richiesta di ferie.")
        return

    righe = []
    for r in richieste:
        d         = date.fromisoformat(r["data_richiesta"])
        emoji     = _stato_emoji(r["stato"])
        tipo_str  = TIPO_LABEL.get(r["tipo_turno"], r["tipo_turno"])
        riga      = f"{emoji} *#{r['id']}* {d.strftime('%d/%m/%Y')} — {tipo_str}"
        if r["stato"] == "rejected" and r["note_rifiuto"]:
            riga += f"\n   ↳ _{r['note_rifiuto']}_"
        righe.append(riga)

    await update.message.reply_text(
        "Le tue richieste:\n\n" + "\n".join(righe),
        parse_mode="Markdown",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICA CAPOTURNO
# ═══════════════════════════════════════════════════════════════════════════════

async def _notifica_capoturno(
    context: ContextTypes.DEFAULT_TYPE,
    request_id: int,
    user_id: int,
    data_iso: str,
    tipo: str,
) -> None:
    user   = db.find_user_by_telegram_id  # evita seconda query: usiamo user_id diretto
    # Recuperiamo i dati utente tramite id (query separata)
    with db.get_conn() as conn:
        vigile = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not vigile:
        return

    d = date.fromisoformat(data_iso)
    testo = (
        f"Nuova richiesta ferie *#{request_id}*\n\n"
        f"Vigile: {vigile['nome']} {vigile['cognome']}\n"
        f"Gruppo: {vigile['gruppo_turno']}\n"
        f"Distaccamento: {vigile['distaccamento']}\n"
        f"Data: {d.strftime('%d/%m/%Y')}\n"
        f"Turno: {TIPO_LABEL[tipo]}"
    )
    kbd = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approva", callback_data=f"approve:{request_id}"),
        InlineKeyboardButton("❌ Rifiuta", callback_data=f"reject:{request_id}"),
    ]])
    try:
        await context.bot.send_message(
            chat_id=TELEGRAM_CAPOTURNO_ID,
            text=testo,
            parse_mode="Markdown",
            reply_markup=kbd,
        )
    except Exception as e:
        logger.error("Errore notifica capoturno per richiesta #%d: %s", request_id, e)
