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


# Quanti blocchi futuri offrire nella scelta (dal blocco del prossimo riposo di A).
# Tenuto a 5 perché un blocco può essere "lockato" (A già impegnato lì) e sparire:
# così ne restano comunque almeno 4 visibili.
N_BLOCCHI_SCAMBIO = 5


def _blocco_di(slot: int) -> tuple[tuple[date, date], tuple[date, date]] | None:
    """(blocco, occorrenza_dello_slot) per il prossimo riposo futuro dello slot."""
    occ = cal.prossimo_salto(slot, date.today())
    if occ is None:
        return None
    blocco = cal.blocco_corrente(occ[0])
    return blocco, occ


def _controparti(a_user: dict) -> list[dict] | None:
    """
    Lista piatta delle controparti disponibili nei due blocchi rilevanti per A:
    il blocco del suo prossimo riposo (bi=0) e il successivo (bi=1).

    Ogni voce: {bi, blocco, a_occ, id, cognome, nome, slot, occ}, dove a_occ è il
    riposo di A in quel blocco e occ il riposo della controparte.

    Esclusioni:
      - sé stesso e i vigili del proprio slot;
      - controparti il cui riposo nel blocco è già passato o assente;
      - chiunque (A compreso) sia già impegnato in uno scambio attivo nel blocco:
        se A è impegnato il blocco salta del tutto, le sue controparti escono.

    Ritorna None solo se A non ha alcun riposo futuro (slot senza occorrenze).
    """
    a_slot = a_user["salto_id"]
    first = _blocco_di(a_slot)
    if first is None:
        return None

    # Fino a N_BLOCCHI_SCAMBIO blocchi futuri, dal blocco del prossimo riposo di A.
    blocchi: list[tuple[tuple[date, date], tuple[date, date]]] = []
    blocco = first[0]
    while blocco is not None and len(blocchi) < N_BLOCCHI_SCAMBIO:
        a_occ_b = cal.slot_dates_in_blocco(a_slot, blocco)
        if a_occ_b is not None:
            blocchi.append((blocco, a_occ_b))
        blocco = cal.blocco_successivo(blocco)

    oggi = date.today()
    vigili = db.vigili_turno_b_registrati()
    out: list[dict] = []
    for bi, (blocco, a_occ) in enumerate(blocchi):
        impegnati = db.vigili_impegnati_nel_blocco(blocco[0].isoformat())
        if a_user["id"] in impegnati:
            continue  # A ha già uno scambio in questo blocco: non può cederne il riposo
        for v in vigili:
            if v["id"] == a_user["id"] or v["salto_id"] == a_slot:
                continue
            if v["id"] in impegnati:
                continue
            occ = cal.slot_dates_in_blocco(v["salto_id"], blocco)
            if occ is None or occ[0] <= oggi:
                continue
            out.append({"bi": bi, "blocco": blocco, "a_occ": a_occ,
                        "id": v["id"], "cognome": v["cognome"], "nome": v["nome"],
                        "slot": v["salto_id"], "occ": occ})
    out.sort(key=lambda x: x["occ"][0])
    return out


def _find(lista: list[dict], b_id: int, bi: int) -> dict | None:
    return next((c for c in lista if c["id"] == b_id and c["bi"] == bi), None)


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

def _blocchi_kbd(lista: list[dict]) -> InlineKeyboardMarkup:
    """Step 1: un tasto per blocco (da → a), dal più vicino + Annulla."""
    visti: dict[int, tuple] = {}  # bi -> (blocco, a_occ)
    for c in lista:
        visti.setdefault(c["bi"], (c["blocco"], c["a_occ"]))
    righe = [
        [InlineKeyboardButton(
            f"📅 {blocco[0].strftime('%d/%m')} → {blocco[1].strftime('%d/%m')}",
            callback_data=f"scs:blk:{bi}",
        )]
        for bi, (blocco, a_occ) in sorted(visti.items())
    ]
    righe.append([InlineKeyboardButton("✖️ Annulla", callback_data="scs:x")])
    return InlineKeyboardMarkup(righe)


def _salti_kbd(lista: list[dict], bi: int) -> InlineKeyboardMarkup:
    """Step 2: i salti disponibili NEL blocco scelto + Indietro (blocchi) + Annulla."""
    visti: dict[int, tuple] = {}  # slot -> occ
    for c in lista:
        if c["bi"] == bi:
            visti.setdefault(c["slot"], c["occ"])
    righe = [
        [InlineKeyboardButton(
            f"B{slot} — riposo {occ[0].strftime('%d/%m')}",
            callback_data=f"scs:slot:{slot}:{bi}",
        )]
        for slot, occ in sorted(visti.items(), key=lambda kv: kv[1][0])
    ]
    righe.append([InlineKeyboardButton("⬅️ Blocchi", callback_data="scs:blks")])
    righe.append([InlineKeyboardButton("✖️ Annulla", callback_data="scs:x")])
    return InlineKeyboardMarkup(righe)


def _vigili_kbd(lista: list[dict], slot: int, bi: int) -> InlineKeyboardMarkup:
    """Step 3: i vigili del salto scelto (in quel blocco) + Indietro (salti) + Annulla."""
    righe = [
        [InlineKeyboardButton(f"{c['cognome']} {c['nome']}",
                              callback_data=f"scs:sel:{c['id']}:{bi}")]
        for c in lista if c["slot"] == slot and c["bi"] == bi
    ]
    righe.append([InlineKeyboardButton("⬅️ Altri salti", callback_data=f"scs:slts:{bi}")])
    righe.append([InlineKeyboardButton("✖️ Annulla", callback_data="scs:x")])
    return InlineKeyboardMarkup(righe)


def _miei_scambi_testo(miei: list[dict]) -> str:
    """Elenco delle proposte di scambio già aperte da A (lo bloccano nel blocco)."""
    righe = ["<b>Hai già una richiesta di scambio aperta</b>",
             "(ti blocca quel blocco finché non arriva una risposta):", ""]
    for s in miei:
        blocco = (date.fromisoformat(s["blocco_inizio"]), date.fromisoformat(s["blocco_fine"]))
        a_occ = cal.slot_dates_in_blocco(s["slot_a"], blocco)
        b_occ = cal.slot_dates_in_blocco(s["slot_b"], blocco)
        righe.append(
            f"• con <b>{s['b_cognome']}</b> (B{s['slot_b']}) — <i>{s['stato']}</i>\n"
            f"   cedi {_fmt(a_occ) if a_occ else '?'}, "
            f"prenderesti {_fmt(b_occ) if b_occ else '?'}"
        )
    return "\n".join(righe)


def _miei_scambi_kbd(miei: list[dict]) -> InlineKeyboardMarkup:
    """Un tasto 'Annulla' per ogni proposta aperta di A."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"↩️ Annulla la richiesta con {s['b_cognome']}",
                              callback_data=f"scs:acanc:{s['id']}")]
        for s in miei
    ])


def scambi_riepilogo(user: dict) -> tuple[list[str], list[list[InlineKeyboardButton]]]:
    """Righe (HTML) + bottoni 'Annulla' dei cambi salto del vigile, per la vista
    'le mie richieste' di pompiere. A può annullare i propri proposto/confermato."""
    righe: list[str] = []
    bottoni: list[list[InlineKeyboardButton]] = []
    for s in db.scambi_del_vigile(user["id"]):
        blocco = (date.fromisoformat(s["blocco_inizio"]), date.fromisoformat(s["blocco_fine"]))
        a_occ = cal.slot_dates_in_blocco(s["slot_a"], blocco)
        b_occ = cal.slot_dates_in_blocco(s["slot_b"], blocco)
        io_a       = (s["vigile_a_id"] == user["id"])
        altro      = s["b_cognome"] if io_a else s["a_cognome"]
        altro_slot = s["slot_b"]    if io_a else s["slot_a"]
        mio_occ    = a_occ if io_a else b_occ
        suo_occ    = b_occ if io_a else a_occ
        chi        = "proposto da te" if io_a else f"proposto da {s['a_cognome']}"
        righe.append(
            f"🔄 con <b>{altro}</b> (B{altro_slot}) — <i>{s['stato']}</i> · {chi}\n"
            f"   cedi {_fmt(mio_occ) if mio_occ else '?'}, "
            f"prendi {_fmt(suo_occ) if suo_occ else '?'}"
        )
        if io_a and s["stato"] in ("proposto", "confermato"):
            bottoni.append([InlineKeyboardButton(
                f"↩️ Annulla scambio con {altro}",
                callback_data=f"scs:acanc:{s['id']}")])
    return righe, bottoni


async def scambia_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    a = db.find_user_by_telegram_id(update.effective_user.id)
    if not a:
        await update.message.reply_text("Non sei registrato. Usa /start.")
        return

    # Proposte già aperte da A: le mostra con tasto Annulla (lo bloccano nel blocco).
    miei = db.scambi_attivi_di(a["id"])
    if miei:
        await update.message.reply_text(
            _miei_scambi_testo(miei), reply_markup=_miei_scambi_kbd(miei), parse_mode="HTML",
        )

    lista = _controparti(a)
    if lista is None:
        if not miei:
            await update.message.reply_text("Nessun salto futuro trovato per il tuo slot.")
        return
    if not lista:
        if not miei:
            await update.message.reply_text(
                "Nessuna controparte disponibile nei prossimi blocchi "
                "(riposi già passati, colleghi non registrati o già impegnati in uno scambio).",
            )
        return

    await update.message.reply_text(
        "Scambio salto turno.\n\nScegli il <b>blocco</b>:",
        reply_markup=_blocchi_kbd(lista),
        parse_mode="HTML",
    )


async def _step_mostra_blocchi(update, context, a):
    """Torna alla scelta del blocco."""
    lista = _controparti(a)
    if not lista:
        await update.callback_query.edit_message_text("Scambio non più disponibile.")
        return
    await update.callback_query.edit_message_text(
        "Scambio salto turno.\n\nScegli il <b>blocco</b>:",
        reply_markup=_blocchi_kbd(lista), parse_mode="HTML",
    )


async def _step_scegli_blocco(update, context, a, bi):
    """Scelto il blocco → mostra i salti disponibili in quel blocco."""
    lista = _controparti(a)
    if not lista:
        await update.callback_query.edit_message_text("Scambio non più disponibile.")
        return
    voci = [c for c in lista if c["bi"] == bi]
    if not voci:
        await update.callback_query.edit_message_text(
            "Blocco non più disponibile. Riprova con 🔄 Scambia salto."
        )
        return
    blocco = voci[0]["blocco"]
    a_occ = voci[0]["a_occ"]
    await update.callback_query.edit_message_text(
        f"Blocco <b>{blocco[0].strftime('%d/%m')} → {blocco[1].strftime('%d/%m')}</b>\n"
        f"Tu (B{a['salto_id']}) cedi <b>{_fmt(a_occ)}</b>\n\n"
        "Scegli il <b>salto</b> con cui scambiare:",
        reply_markup=_salti_kbd(lista, bi), parse_mode="HTML",
    )


async def _step_scegli_slot(update, context, a, slot, bi):
    """Mostra i vigili del salto scelto (cascata salto → vigili)."""
    lista = _controparti(a)
    if not lista:
        await update.callback_query.edit_message_text("Scambio non più disponibile.")
        return
    vigili = [c for c in lista if c["slot"] == slot and c["bi"] == bi]
    if not vigili:
        await update.callback_query.edit_message_text(
            "Nessun vigile disponibile in quel salto. Riprova con 🔄 Scambia salto."
        )
        return
    v0 = vigili[0]
    await update.callback_query.edit_message_text(
        f"Tu (B{a['salto_id']}) cedi <b>{_fmt(v0['a_occ'])}</b>\n"
        f"Salto <b>B{slot}</b> — riposo {_fmt(v0['occ'])}\n\n"
        "Scegli il vigile con cui scambiare:",
        reply_markup=_vigili_kbd(lista, slot, bi), parse_mode="HTML",
    )


async def _step_seleziona(update, context, a, b_id, bi):
    lista = _controparti(a)
    if not lista:
        await update.callback_query.edit_message_text("Scambio non più disponibile.")
        return
    b = _find(lista, b_id, bi)
    if b is None:
        await update.callback_query.edit_message_text("Controparte non più valida.")
        return
    testo = (
        f"Confermi la proposta di scambio?\n\n"
        f"• Tu (B{a['salto_id']}) cedi il riposo <b>{_fmt(b['a_occ'])}</b>\n"
        f"• {b['cognome']} (B{b['slot']}) cede <b>{_fmt(b['occ'])}</b>\n\n"
        f"Dopo lo scambio riposerai nei giorni di {b['cognome']}."
    )
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Proponi", callback_data=f"scs:go:{b_id}:{bi}"),
        InlineKeyboardButton("✖️ Annulla", callback_data="scs:x"),
    ]])
    await update.callback_query.edit_message_text(testo, reply_markup=markup, parse_mode="HTML")


async def _step_proponi(update, context, a, b_id, bi):
    lista = _controparti(a)
    if not lista:
        await update.callback_query.edit_message_text("Scambio non più disponibile.")
        return
    b = _find(lista, b_id, bi)
    if b is None:
        await update.callback_query.edit_message_text("Controparte non più valida.")
        return

    blocco = b["blocco"]
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


# ── A: ritira la propria proposta (prima dell'approvazione) ──────────────────────

async def _step_a_annulla_chiedi(update, context, sid):
    """Tap su Annulla → chiede conferma (doppia conferma) prima di ritirare."""
    q = update.callback_query
    s = db.get_scambio(sid)
    if not s or s["stato"] not in ("proposto", "confermato"):
        await q.edit_message_text("Richiesta non più annullabile (già gestita o approvata).")
        return
    if update.effective_user.id != s["a_tg"]:
        await q.answer("Non è una tua richiesta.", show_alert=True)
        return
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Sì, annulla", callback_data=f"scs:acanck:{sid}"),
        InlineKeyboardButton("✖️ No",          callback_data="scs:acancno"),
    ]])
    await q.edit_message_text(
        f"Vuoi annullare la richiesta di scambio salto con <b>{s['b_cognome']}</b>?",
        reply_markup=markup, parse_mode="HTML",
    )


async def _step_a_annulla(update, context, sid):
    """A annulla la sua richiesta finché è proposto/confermato (no override ancora
    scritti → basta lo stato 'annullato' a liberare il lock del blocco)."""
    q = update.callback_query
    s = db.get_scambio(sid)
    if not s or s["stato"] not in ("proposto", "confermato"):
        await q.edit_message_text("Richiesta non più annullabile (già gestita o approvata).")
        return
    if update.effective_user.id != s["a_tg"]:
        await q.answer("Non è una tua richiesta.", show_alert=True)
        return

    era = s["stato"]
    db.annulla_scambio(sid)
    await q.edit_message_text(
        "↩️ Richiesta di scambio annullata. Quel blocco torna libero — "
        "riapri 🔄 Scambia salto per le nuove opzioni."
    )
    await _notifica(context, s["b_tg"],
                    f"↩️ {s['a_cognome']} ha annullato la richiesta di scambio salto.")
    # Se B aveva già confermato, la proposta era in coda alla fureria: avvisala.
    if era == "confermato":
        for fid in TELEGRAM_FURERIA_IDS:
            await _notifica(context, fid,
                            f"↩️ {s['a_cognome']} ha annullato lo scambio con "
                            f"{s['b_cognome']} (era in attesa di approvazione).")


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

    if azione == "blk":
        await _step_scegli_blocco(update, context, a, int(parts[2]))
    elif azione == "blks":
        await _step_mostra_blocchi(update, context, a)
    elif azione == "slot":
        await _step_scegli_slot(update, context, a, int(parts[2]), int(parts[3]))
    elif azione == "slts":
        await _step_scegli_blocco(update, context, a, int(parts[2]))
    elif azione == "sel":
        await _step_seleziona(update, context, a, int(parts[2]), int(parts[3]))
    elif azione == "go":
        await _step_proponi(update, context, a, int(parts[2]), int(parts[3]))
    elif azione == "acanc":
        await _step_a_annulla_chiedi(update, context, int(parts[2]))
    elif azione == "acanck":
        await _step_a_annulla(update, context, int(parts[2]))
    elif azione == "acancno":
        await q.edit_message_text("Annullamento non eseguito. Lo scambio resta valido.")
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
