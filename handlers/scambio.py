"""
Scambio salto turno tra vigili.

Flusso (tutto via inline button, perché i tre attori sono chat diverse):
  A propone (sceglie la controparte)  → stato 'proposto'   → notifica B
  B conferma                          → stato 'confermato' → notifica fureria
  fureria approva                     → stato 'approvato'  → scrive override,
                                        patcha i fogli esistenti, manda la mail
                                        di conferma a entrambi i vigili.

Regola scambio: dentro lo stesso blocco B1→B8, con qualsiasi altro slot,
purché il giorno di riposo della controparte non sia già passato.
"""

import logging
from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

import calendar_turni as cal
import database as db
import email_service
from config import TELEGRAM_FURERIA_IDS
from crypto import decrypt

logger = logging.getLogger(__name__)


# ── helpers ─────────────────────────────────────────────────────────────────────

def _fmt(par: tuple[date, date]) -> str:
    d, n = par
    return f"{d.strftime('%d/%m')} ☀️ + {n.strftime('%d/%m')} 🌙"


def _blocco_di(slot: int) -> tuple[tuple[date, date], tuple[date, date]] | None:
    """(blocco, occorrenza_dello_slot) per il prossimo riposo futuro dello slot."""
    occ = cal.prossimo_salto(slot, date.today())
    if occ is None:
        return None
    blocco = cal.blocco_corrente(occ[0])
    return blocco, occ


def _controparti(a_user: dict) -> tuple[tuple[date, date], tuple[date, date], list[dict]] | None:
    """
    Ritorna (blocco, occorrenza_di_A, lista_controparti).
    Controparti = vigili registrati, slot diverso da A, riposo nel blocco di A
    con data ancora futura. Ogni voce: {id, cognome, nome, slot, occ}.
    """
    bo = _blocco_di(a_user["salto_id"])
    if bo is None:
        return None
    blocco, a_occ = bo
    oggi = date.today()
    out = []
    for v in db.vigili_turno_b_registrati():
        if v["id"] == a_user["id"] or v["salto_id"] == a_user["salto_id"]:
            continue
        occ = cal.slot_dates_in_blocco(v["salto_id"], blocco)
        if occ is None or occ[0] <= oggi:
            continue
        out.append({"id": v["id"], "cognome": v["cognome"], "nome": v["nome"],
                    "slot": v["salto_id"], "occ": occ})
    out.sort(key=lambda x: x["occ"][0])
    return blocco, a_occ, out


def _override_rows(s: dict) -> tuple[list[tuple[str, str, int, int]], tuple[date, date], tuple[date, date]]:
    """Calcola le 4 righe override + le occorrenze (a_occ, b_occ) dallo scambio salvato."""
    blocco = (date.fromisoformat(s["blocco_inizio"]), date.fromisoformat(s["blocco_fine"]))
    a_occ = cal.slot_dates_in_blocco(s["slot_a"], blocco)
    b_occ = cal.slot_dates_in_blocco(s["slot_b"], blocco)
    a_id, b_id = s["vigile_a_id"], s["vigile_b_id"]
    rows = [
        (a_occ[0].isoformat(), "D", a_id, b_id),
        (a_occ[1].isoformat(), "N", a_id, b_id),
        (b_occ[0].isoformat(), "D", b_id, a_id),
        (b_occ[1].isoformat(), "N", b_id, a_id),
    ]
    return rows, a_occ, b_occ


async def _notifica(context, chat_id: int, testo: str, markup=None):
    try:
        await context.bot.send_message(chat_id=chat_id, text=testo,
                                       reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logger.warning("Notifica a %s fallita: %s", chat_id, e)


# ── A: proposta ─────────────────────────────────────────────────────────────────

def _salti_kbd(lista: list[dict]) -> InlineKeyboardMarkup:
    """Step 1: i salti (slot) disponibili nel blocco — uno per riga + Annulla."""
    visti: dict[int, tuple] = {}
    for c in lista:
        visti.setdefault(c["slot"], c["occ"])
    righe = [
        [InlineKeyboardButton(
            f"B{slot} — riposo {occ[0].strftime('%d/%m')}",
            callback_data=f"scs:slot:{slot}",
        )]
        for slot, occ in sorted(visti.items())
    ]
    righe.append([InlineKeyboardButton("✖️ Annulla", callback_data="scs:x")])
    return InlineKeyboardMarkup(righe)


def _vigili_kbd(lista: list[dict], slot: int) -> InlineKeyboardMarkup:
    """Step 2: i vigili del salto scelto + Indietro + Annulla."""
    righe = [
        [InlineKeyboardButton(f"{c['cognome']} {c['nome']}", callback_data=f"scs:sel:{c['id']}")]
        for c in lista if c["slot"] == slot
    ]
    righe.append([InlineKeyboardButton("⬅️ Altri salti", callback_data="scs:slts")])
    righe.append([InlineKeyboardButton("✖️ Annulla", callback_data="scs:x")])
    return InlineKeyboardMarkup(righe)


async def scambia_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    a = db.find_user_by_telegram_id(update.effective_user.id)
    if not a:
        await update.message.reply_text("Non sei registrato. Usa /start.")
        return

    res = _controparti(a)
    if res is None:
        await update.message.reply_text("Nessun salto futuro trovato per il tuo slot.")
        return
    blocco, a_occ, lista = res
    if not lista:
        await update.message.reply_text(
            f"Il tuo prossimo riposo: <b>{_fmt(a_occ)}</b>\n"
            "Nessuna controparte disponibile in questo blocco "
            "(riposi già passati o nessun collega registrato).",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        f"Scambio salto turno.\nIl tuo prossimo riposo: <b>{_fmt(a_occ)}</b>\n\n"
        "Scegli il <b>salto</b> con cui scambiare:",
        reply_markup=_salti_kbd(lista),
        parse_mode="HTML",
    )


async def _step_mostra_salti(update, context, a):
    """Torna alla scelta del salto (Altri salti)."""
    res = _controparti(a)
    if res is None or not res[2]:
        await update.callback_query.edit_message_text("Scambio non più disponibile.")
        return
    blocco, a_occ, lista = res
    await update.callback_query.edit_message_text(
        f"Scambio salto turno.\nIl tuo prossimo riposo: <b>{_fmt(a_occ)}</b>\n\n"
        "Scegli il <b>salto</b> con cui scambiare:",
        reply_markup=_salti_kbd(lista), parse_mode="HTML",
    )


async def _step_scegli_slot(update, context, a, slot):
    """Mostra i vigili del salto scelto (cascata salto → vigili)."""
    res = _controparti(a)
    if res is None:
        await update.callback_query.edit_message_text("Scambio non più disponibile.")
        return
    blocco, a_occ, lista = res
    vigili = [c for c in lista if c["slot"] == slot]
    if not vigili:
        await update.callback_query.edit_message_text(
            "Nessun vigile disponibile in quel salto. Riprova con 🔄 Scambia salto."
        )
        return
    await update.callback_query.edit_message_text(
        f"Salto <b>B{slot}</b> — riposo {_fmt(vigili[0]['occ'])}\n\n"
        "Scegli il vigile con cui scambiare:",
        reply_markup=_vigili_kbd(lista, slot), parse_mode="HTML",
    )


async def _step_seleziona(update, context, a, b_id):
    res = _controparti(a)
    if res is None:
        await update.callback_query.edit_message_text("Scambio non più disponibile.")
        return
    blocco, a_occ, lista = res
    b = next((c for c in lista if c["id"] == b_id), None)
    if b is None:
        await update.callback_query.edit_message_text("Controparte non più valida.")
        return
    testo = (
        f"Confermi la proposta di scambio?\n\n"
        f"• Tu (B{a['salto_id']}) cedi il riposo <b>{_fmt(a_occ)}</b>\n"
        f"• {b['cognome']} (B{b['slot']}) cede <b>{_fmt(b['occ'])}</b>\n\n"
        f"Dopo lo scambio riposerai nei giorni di {b['cognome']}."
    )
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Proponi", callback_data=f"scs:go:{b_id}"),
        InlineKeyboardButton("✖️ Annulla", callback_data="scs:x"),
    ]])
    await update.callback_query.edit_message_text(testo, reply_markup=markup, parse_mode="HTML")


async def _step_proponi(update, context, a, b_id):
    res = _controparti(a)
    if res is None:
        await update.callback_query.edit_message_text("Scambio non più disponibile.")
        return
    blocco, a_occ, lista = res
    b = next((c for c in lista if c["id"] == b_id), None)
    if b is None:
        await update.callback_query.edit_message_text("Controparte non più valida.")
        return

    sid = db.crea_scambio(
        a["id"], b["id"], a["salto_id"], b["slot"],
        blocco[0].isoformat(), blocco[1].isoformat(), creato_da=a["id"],
    )
    await update.callback_query.edit_message_text(
        f"Proposta inviata a {b['cognome']}. In attesa della sua conferma.",
    )

    # notifica B
    s = db.get_scambio(sid)
    rows, a_occ2, b_occ2 = _override_rows(s)
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confermo", callback_data=f"scs:bok:{sid}"),
        InlineKeyboardButton("✖️ Rifiuto", callback_data=f"scs:bno:{sid}"),
    ]])
    await _notifica(
        context, s["b_tg"],
        f"🔄 <b>{s['a_cognome']}</b> (B{s['slot_a']}) ti propone uno scambio salto:\n\n"
        f"• lui cede <b>{_fmt(a_occ2)}</b>\n"
        f"• tu cedi <b>{_fmt(b_occ2)}</b>\n\n"
        f"Confermi?",
        markup,
    )


# ── B: conferma / rifiuto ────────────────────────────────────────────────────────

async def _step_b_risponde(update, context, sid, ok: bool):
    s = db.get_scambio(sid)
    if not s or s["stato"] != "proposto":
        await update.callback_query.edit_message_text("Proposta non più valida.")
        return
    if update.effective_user.id != s["b_tg"]:
        await update.callback_query.answer("Non sei il destinatario.", show_alert=True)
        return

    if not ok:
        db.rifiuta_scambio(sid)
        await update.callback_query.edit_message_text("Hai rifiutato lo scambio.")
        await _notifica(context, s["a_tg"], f"❌ {s['b_cognome']} ha rifiutato lo scambio salto.")
        return

    db.conferma_scambio(sid)
    await update.callback_query.edit_message_text("Confermato. In attesa dell'approvazione della fureria.")
    await _notifica(context, s["a_tg"], f"✅ {s['b_cognome']} ha confermato. In attesa della fureria.")

    rows, a_occ, b_occ = _override_rows(s)
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approva", callback_data=f"scs:ok:{sid}"),
        InlineKeyboardButton("✖️ Rifiuta", callback_data=f"scs:no:{sid}"),
    ]])
    for fid in TELEGRAM_FURERIA_IDS:
        await _notifica(
            context, fid,
            f"🔄 <b>Scambio salto da approvare</b>\n\n"
            f"• {s['a_cognome']} (B{s['slot_a']}) → riposava {_fmt(a_occ)}\n"
            f"• {s['b_cognome']} (B{s['slot_b']}) → riposava {_fmt(b_occ)}\n\n"
            f"Approvando, i due riposi vengono scambiati su fogli/ODT e parte la mail.",
            markup,
        )


# ── Fureria: approva / rifiuta ───────────────────────────────────────────────────

async def _step_fureria(update, context, sid, ok: bool):
    if update.effective_user.id not in TELEGRAM_FURERIA_IDS:
        await update.callback_query.answer("Riservato alla fureria.", show_alert=True)
        return
    s = db.get_scambio(sid)
    if not s or s["stato"] != "confermato":
        await update.callback_query.edit_message_text("Scambio non più in attesa.")
        return

    if not ok:
        db.rifiuta_scambio(sid)
        await update.callback_query.edit_message_text("Scambio rifiutato.")
        await _notifica(context, s["a_tg"], "❌ La fureria ha rifiutato lo scambio salto.")
        await _notifica(context, s["b_tg"], "❌ La fureria ha rifiutato lo scambio salto.")
        return

    fureria = db.find_user_by_telegram_id(update.effective_user.id)
    rows, a_occ, b_occ = _override_rows(s)
    try:
        db.approva_scambio(sid, approvato_da=fureria["id"] if fureria else s["vigile_a_id"],
                           override_rows=rows)
    except db.ScambioConflitto as e:
        await update.callback_query.edit_message_text(
            f"⚠️ Impossibile approvare: {e}\n"
            "Annulla prima lo scambio in conflitto, poi riprova."
        )
        return

    # mail di conferma dall'account della fureria a entrambi i vigili
    mail_ok = False
    if fureria and fureria.get("email") and fureria.get("email_password_enc"):
        try:
            mail_ok = email_service.send_scambio_conferma(
                fureria["email"], decrypt(fureria["email_password_enc"]),
                s["a_nome"], s["a_cognome"], s["a_email"],
                s["b_nome"], s["b_cognome"], s["b_email"],
                a_riposa=(b_occ[0].isoformat(), b_occ[1].isoformat()),  # A ora riposa nei giorni di B
                b_riposa=(a_occ[0].isoformat(), a_occ[1].isoformat()),
            )
        except Exception as e:
            logger.error("Mail scambio fallita: %s", e)

    nota_mail = "📧 Mail di conferma inviata a entrambi." if mail_ok else \
        "⚠️ Mail non inviata (manca l'email/password fureria): avvisa i vigili a voce."
    undo_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("↩️ Annulla scambio", callback_data=f"scs:undo:{sid}"),
    ]])
    await update.callback_query.edit_message_text(
        f"✅ Scambio approvato.\n{nota_mail}", reply_markup=undo_markup
    )

    msg = (f"✅ Scambio salto <b>approvato</b> dalla fureria.\n\n"
           f"• {s['a_cognome']} ora riposa {_fmt(b_occ)}\n"
           f"• {s['b_cognome']} ora riposa {_fmt(a_occ)}")
    await _notifica(context, s["a_tg"], msg)
    await _notifica(context, s["b_tg"], msg)


# ── Fureria: annulla uno scambio approvato (doppia conferma) ─────────────────────

async def _step_annulla_chiedi(update, context, sid):
    if update.effective_user.id not in TELEGRAM_FURERIA_IDS:
        await update.callback_query.answer("Riservato alla fureria.", show_alert=True)
        return
    s = db.get_scambio(sid)
    if not s or s["stato"] != "approvato":
        await update.callback_query.edit_message_text(
            "Scambio non annullabile (non approvato o già annullato)."
        )
        return
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Sì, annulla", callback_data=f"scs:undook:{sid}"),
        InlineKeyboardButton("✖️ No", callback_data=f"scs:undono:{sid}"),
    ]])
    await update.callback_query.edit_message_text(
        f"Confermi l'annullamento dello scambio salto tra "
        f"<b>{s['a_cognome']}</b> (B{s['slot_a']}) e <b>{s['b_cognome']}</b> (B{s['slot_b']})?\n"
        "I due vigili tornano alla situazione di partenza su tutte le date.",
        reply_markup=markup, parse_mode="HTML",
    )


async def _step_annulla(update, context, sid):
    if update.effective_user.id not in TELEGRAM_FURERIA_IDS:
        await update.callback_query.answer("Riservato alla fureria.", show_alert=True)
        return
    s = db.get_scambio(sid)
    if not s or s["stato"] != "approvato":
        await update.callback_query.edit_message_text("Scambio non annullabile o già annullato.")
        return
    db.annulla_scambio_approvato(sid)
    await update.callback_query.edit_message_text(
        "↩️ Scambio salto <b>annullato</b>. I due vigili tornano alla situazione di partenza.",
        parse_mode="HTML",
    )
    msg = "↩️ Lo scambio salto è stato <b>annullato</b> dalla fureria. Torni al tuo riposo originale."
    await _notifica(context, s["a_tg"], msg)
    await _notifica(context, s["b_tg"], msg)


# ── dispatcher callback ──────────────────────────────────────────────────────────

async def scambio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split(":")
    azione = parts[1]

    if azione == "x":
        await q.edit_message_text("Annullato.")
        return

    a = db.find_user_by_telegram_id(update.effective_user.id)
    if a is None:
        await q.edit_message_text("Non risulti più registrato. Usa /start.")
        return

    if azione == "slot":
        await _step_scegli_slot(update, context, a, int(parts[2]))
    elif azione == "slts":
        await _step_mostra_salti(update, context, a)
    elif azione == "sel":
        await _step_seleziona(update, context, a, int(parts[2]))
    elif azione == "go":
        await _step_proponi(update, context, a, int(parts[2]))
    elif azione == "bok":
        await _step_b_risponde(update, context, int(parts[2]), ok=True)
    elif azione == "bno":
        await _step_b_risponde(update, context, int(parts[2]), ok=False)
    elif azione == "ok":
        await _step_fureria(update, context, int(parts[2]), ok=True)
    elif azione == "no":
        await _step_fureria(update, context, int(parts[2]), ok=False)
    elif azione == "undo":
        await _step_annulla_chiedi(update, context, int(parts[2]))
    elif azione == "undook":
        await _step_annulla(update, context, int(parts[2]))
    elif azione == "undono":
        await q.edit_message_text("Annullamento non eseguito. Lo scambio resta valido.")


def build_scambio_handlers() -> list:
    return [
        CommandHandler("scambia", scambia_start),
        MessageHandler(filters.Regex("^🔄 Scambia salto$"), scambia_start),
        CallbackQueryHandler(scambio_callback, pattern=r"^scs:"),
    ]
