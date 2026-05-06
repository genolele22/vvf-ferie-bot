"""
Handlers per il pompiere: /start, /aggiorna_password, /ferie, /mie_richieste.
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
import email_service
from config import TELEGRAM_CAPOTURNO_ID
from crypto import decrypt, encrypt

logger = logging.getLogger(__name__)

# ── STATI ─────────────────────────────────────────────────────────────────────

# /start e /aggiorna_password
S_EMAIL, S_PASSWORD = range(2)

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
            "Usa /ferie per richiedere ferie o /mie_richieste per vedere lo storico.\n"
            "Per aggiornare la password email usa /aggiorna_password."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Benvenuto nel sistema ferie — Comando VVF Genova.\n\n"
        "Inserisci la tua *email istituzionale* vigilfuoco.it:",
        parse_mode="Markdown",
    )
    return S_EMAIL


async def start_ricevi_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip().lower()

    if not email.endswith("@vigilfuoco.it"):
        await update.message.reply_text(
            "Inserisci un indirizzo @vigilfuoco.it valido:"
        )
        return S_EMAIL

    user = db.find_user_by_email(email)
    if not user:
        await update.message.reply_text(
            "Email non trovata in anagrafica.\n"
            "Controlla l'indirizzo o contatta il responsabile."
        )
        return ConversationHandler.END

    if user["telegram_id"] and user["telegram_id"] != update.effective_user.id:
        await update.message.reply_text(
            "Questa email è già associata a un altro account Telegram.\n"
            "Contatta il responsabile."
        )
        return ConversationHandler.END

    context.user_data["reg_user_id"] = user["id"]
    context.user_data["reg_nome"] = user["nome"]
    context.user_data["reg_email"] = email

    await update.message.reply_text(
        f"Trovato: *{user['nome']} {user['cognome']}*, gruppo *{user['gruppo_turno']}*.\n\n"
        "Inserisci la tua *password email* vigilfuoco.it\n"
        "_(il messaggio verrà eliminato automaticamente)_",
        parse_mode="Markdown",
    )
    return S_PASSWORD


async def start_ricevi_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text
    email = context.user_data.get("reg_email", "")
    user_id = context.user_data.get("reg_user_id")
    nome = context.user_data.get("reg_nome", "")

    # Cancella subito il messaggio con la password dalla chat
    try:
        await update.message.delete()
    except Exception:
        pass

    await update.message.reply_text("Verifico le credenziali...")

    if not email_service.test_smtp(email, password):
        await update.message.reply_text(
            "Password non corretta o server non raggiungibile.\n"
            "Riprova con /start."
        )
        context.user_data.clear()
        return ConversationHandler.END

    db.set_telegram_id(user_id, update.effective_user.id)
    db.set_email_password(user_id, encrypt(password))
    context.user_data.clear()

    await update.message.reply_text(
        f"Registrazione completata, *{nome}*.\n\n"
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
            S_EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, start_ricevi_email)],
            S_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_ricevi_password)],
        },
        fallbacks=[CommandHandler("cancel", start_cancel)],
        name="start_conv",
        persistent=False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# /aggiorna_password
# ═══════════════════════════════════════════════════════════════════════════════

async def aggiorna_password_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = await _get_registered_user(update)
    if not user:
        return ConversationHandler.END

    context.user_data["upd_user_id"] = user["id"]
    context.user_data["upd_email"] = user["email"]

    await update.message.reply_text(
        "Inserisci la nuova *password email* vigilfuoco.it\n"
        "_(il messaggio verrà eliminato automaticamente)_",
        parse_mode="Markdown",
    )
    return S_PASSWORD


async def aggiorna_password_ricevi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text
    user_id = context.user_data.get("upd_user_id")
    email = context.user_data.get("upd_email", "")

    try:
        await update.message.delete()
    except Exception:
        pass

    await update.message.reply_text("Verifico le credenziali...")

    if not email_service.test_smtp(email, password):
        await update.message.reply_text(
            "Password non corretta o server non raggiungibile. Riprova."
        )
        context.user_data.clear()
        return ConversationHandler.END

    db.set_email_password(user_id, encrypt(password))
    context.user_data.clear()

    await update.message.reply_text("Password aggiornata.")
    return ConversationHandler.END


async def aggiorna_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Operazione annullata.")
    return ConversationHandler.END


def build_aggiorna_password_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("aggiorna_password", aggiorna_password_start)],
        states={
            S_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, aggiorna_password_ricevi)],
        },
        fallbacks=[CommandHandler("cancel", aggiorna_cancel)],
        name="aggiorna_password_conv",
        persistent=False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# /ferie — wizard a step
# ═══════════════════════════════════════════════════════════════════════════════

async def ferie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = await _get_registered_user(update)
    if not user:
        return ConversationHandler.END

    if not user["email_password_enc"]:
        await update.message.reply_text(
            "Password email non configurata. Usa /aggiorna_password."
        )
        return ConversationHandler.END

    context.user_data["ferie"] = {
        "user_id":  user["id"],
        "gruppo":   user["gruppo_turno"],
        "email":    user["email"],
        "password": decrypt(user["email_password_enc"]),
        "nome":     user["nome"],
        "cognome":  user["cognome"],
        "distaccamento": user["distaccamento"],
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
    await update.message.reply_text("Seleziona il mese:", reply_markup=kbd)
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
        buttons = [[
            InlineKeyboardButton("🌅 Solo Diurno",      callback_data="t:D"),
            InlineKeyboardButton("🌅🌙 Entrambi (D+N)", callback_data="t:DN"),
        ]]
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
    d_fine = d.replace(day=d.day + 1) if tipo == "DN" else d

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

    w        = context.user_data.pop("ferie", {})
    user_id  = w["user_id"]
    data_iso = w["data"]
    tipo     = w["tipo"]

    request_id = db.insert_request(user_id, data_iso, tipo)

    await query.edit_message_text(
        f"Richiesta *#{request_id}* inviata.\n"
        "Riceverai risposta via email dal capoturno.",
        parse_mode="Markdown",
    )

    ok = email_service.send_ferie_request(
        pompiere_email=w["email"],
        pompiere_password=w["password"],
        pompiere_nome=w["nome"],
        pompiere_cognome=w["cognome"],
        distaccamento=w["distaccamento"],
        gruppo=w["gruppo"],
        request_id=request_id,
        data_iso=data_iso,
        tipo=tipo,
    )

    if not ok:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Richiesta registrata ma l'email non è stata inviata.\n"
                 "Controlla la password con /aggiorna_password.",
        )

    # Notifica informativa al capoturno su Telegram (senza bottoni)
    await _notifica_capoturno_telegram(context, request_id, w)

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
        d        = date.fromisoformat(r["data_richiesta"])
        emoji    = _stato_emoji(r["stato"])
        tipo_str = TIPO_LABEL.get(r["tipo_turno"], r["tipo_turno"])
        riga     = f"{emoji} *#{r['id']}* {d.strftime('%d/%m/%Y')} — {tipo_str}"
        if r["stato"] == "rejected" and r["note_rifiuto"]:
            riga += f"\n   ↳ _{r['note_rifiuto']}_"
        righe.append(riga)

    await update.message.reply_text(
        "Le tue richieste:\n\n" + "\n".join(righe),
        parse_mode="Markdown",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICA TELEGRAM CAPOTURNO (solo informativa, risposta via email)
# ═══════════════════════════════════════════════════════════════════════════════

async def _notifica_capoturno_telegram(
    context: ContextTypes.DEFAULT_TYPE,
    request_id: int,
    w: dict,
) -> None:
    d = date.fromisoformat(w["data"])
    testo = (
        f"📋 Nuova richiesta ferie *#{request_id}*\n\n"
        f"Vigile: {w['nome']} {w['cognome']}\n"
        f"Gruppo: {w['gruppo']} — {w['distaccamento']}\n"
        f"Data: {d.strftime('%d/%m/%Y')} — {TIPO_LABEL[w['tipo']]}\n\n"
        f"_Rispondi via email a {w['email']}_"
    )
    try:
        await context.bot.send_message(
            chat_id=TELEGRAM_CAPOTURNO_ID,
            text=testo,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error("Errore notifica Telegram capoturno per richiesta #%d: %s", request_id, e)
