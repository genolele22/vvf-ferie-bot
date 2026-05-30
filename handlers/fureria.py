"""
Handlers per la fureria: /pending, /pending_data, genera_foglio.
La risposta alle richieste avviene via email (Rispondi direttamente al messaggio ricevuto).
"""

import csv
import io
import logging
from calendar import monthrange
from datetime import date, datetime

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

import database as db
from config import TELEGRAM_FURERIA_IDS

logger = logging.getLogger(__name__)

MENU_FURERIA = ReplyKeyboardMarkup(
    [
        ["📋 Richieste in attesa"],
        ["📅 Richiedi ferie", "📋 Le mie richieste"],
        ["🔑 Aggiorna password"],
    ],
    resize_keyboard=True,
)

TIPO_LABEL = {
    "D":  "Diurno ☀️",
    "N":  "Notturno 🌙",
    "DN": "Diurno + Notturno 🌅🌙",
}

AGE_PERIODO = 0


async def _check_fureria(update: Update) -> bool:
    if update.effective_user.id not in TELEGRAM_FURERIA_IDS:
        await update.message.reply_text("Comando riservato alla fureria.")
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
    if not await _check_fureria(update):
        return

    richieste = db.get_pending_requests()
    if not richieste:
        await update.message.reply_text("Nessuna richiesta in attesa.", reply_markup=MENU_FURERIA)
        return

    for i, r in enumerate(richieste):
        kbd = MENU_FURERIA if i == len(richieste) - 1 else None
        await update.message.reply_text(_format_request(r), parse_mode="Markdown", reply_markup=kbd)


# ═══════════════════════════════════════════════════════════════════════════════
# /pending_data [YYYY-MM] — richieste in attesa per mese
# ═══════════════════════════════════════════════════════════════════════════════

async def pending_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_fureria(update):
        return

    if context.args:
        anno_mese = context.args[0]
    else:
        oggi = date.today()
        anno_mese = f"{oggi.year:04d}-{oggi.month:02d}"

    richieste = db.get_pending_requests_by_month(anno_mese)
    if not richieste:
        await update.message.reply_text(f"Nessuna richiesta in attesa per {anno_mese}.", reply_markup=MENU_FURERIA)
        return

    for i, r in enumerate(richieste):
        kbd = MENU_FURERIA if i == len(richieste) - 1 else None
        await update.message.reply_text(_format_request(r), parse_mode="Markdown", reply_markup=kbd)




# ═══════════════════════════════════════════════════════════════════════════════
# Agenda CSV — resoconto ferie per periodo
# ═══════════════════════════════════════════════════════════════════════════════

STATO_LABEL = {
    "pending":  "In attesa",
    "approved": "Approvata",
    "rejected": "Rifiutata",
}
CSV_HEADERS = ["Cognome", "Nome", "Distaccamento", "Gruppo", "Data", "Tipo Turno", "Stato", "Richiesto il"]


def _parse_periodo(testo: str) -> tuple[str, str] | None:
    """
    Accetta:
      - MM/AAAA          → primo e ultimo giorno del mese
      - GG/MM/AAAA       → singolo giorno
      - GG/MM/AAAA-GG/MM/AAAA  (o con spazio attorno al trattino)
    Ritorna (da_iso, a_iso) o None se non riconosce il formato.
    """
    testo = testo.strip()

    # intervallo: due date separate da trattino (con o senza spazi)
    if "-" in testo and testo.count("/") >= 4:
        parts = [p.strip() for p in testo.split("-", 1)]
        if len(parts) == 2 and "/" in parts[0] and "/" in parts[1]:
            try:
                da = datetime.strptime(parts[0], "%d/%m/%Y").date()
                a  = datetime.strptime(parts[1], "%d/%m/%Y").date()
                return da.isoformat(), a.isoformat()
            except ValueError:
                pass

    # mese intero MM/AAAA
    try:
        d = datetime.strptime(testo, "%m/%Y")
        da = date(d.year, d.month, 1)
        a  = date(d.year, d.month, monthrange(d.year, d.month)[1])
        return da.isoformat(), a.isoformat()
    except ValueError:
        pass

    # singolo giorno GG/MM/AAAA
    try:
        d = datetime.strptime(testo, "%d/%m/%Y").date()
        return d.isoformat(), d.isoformat()
    except ValueError:
        pass

    return None


def _genera_csv(richieste: list) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(CSV_HEADERS)
    for r in richieste:
        d  = date.fromisoformat(r["data_richiesta"])
        ts = r["created_at"][:10] if r["created_at"] else ""
        w.writerow([
            r["cognome"],
            r["nome"],
            r["distaccamento"],
            r["gruppo_turno"],
            d.strftime("%d/%m/%Y"),
            r["tipo_turno"],
            STATO_LABEL.get(r["stato"], r["stato"]),
            ts,
        ])
    return buf.getvalue().encode("utf-8-sig")   # BOM per compatibilità Excel italiano


async def agenda_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _check_fureria(update):
        return ConversationHandler.END
    await update.message.reply_text(
        "Inserisci il periodo per l'agenda:\n\n"
        "• *MM/AAAA* — mese intero (es. 05/2026)\n"
        "• *GG/MM/AAAA-GG/MM/AAAA* — intervallo date\n"
        "• *GG/MM/AAAA* — singolo giorno",
        parse_mode="Markdown",
    )
    return AGE_PERIODO


async def agenda_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    periodo = _parse_periodo(update.message.text)
    if periodo is None:
        await update.message.reply_text(
            "Formato non riconosciuto. Esempi: 05/2026 — 01/05/2026-31/05/2026"
        )
        return AGE_PERIODO

    da_iso, a_iso = periodo
    richieste = db.get_requests_by_period(da_iso, a_iso)

    if not richieste:
        da_fmt = date.fromisoformat(da_iso).strftime("%d/%m/%Y")
        a_fmt  = date.fromisoformat(a_iso).strftime("%d/%m/%Y")
        label  = da_fmt if da_iso == a_iso else f"{da_fmt} – {a_fmt}"
        await update.message.reply_text(
            f"Nessuna richiesta trovata per il periodo {label}.",
            reply_markup=MENU_FURERIA,
        )
        return ConversationHandler.END

    csv_bytes = _genera_csv(richieste)
    da_fmt    = date.fromisoformat(da_iso).strftime("%d/%m/%Y")
    a_fmt     = date.fromisoformat(a_iso).strftime("%d/%m/%Y")
    label     = da_fmt if da_iso == a_iso else f"{da_fmt}–{a_fmt}"
    filename  = f"ferie_{da_iso}_{a_iso}.csv".replace("-", "")

    await update.message.reply_document(
        document=io.BytesIO(csv_bytes),
        filename=filename,
        caption=f"📊 Ferie {label} — {len(richieste)} richieste",
        reply_markup=MENU_FURERIA,
    )
    return ConversationHandler.END


async def agenda_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Annullato.", reply_markup=MENU_FURERIA)
    return ConversationHandler.END


def build_agenda_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("agenda", agenda_start),
            MessageHandler(filters.Regex("^📊 Agenda CSV$"), agenda_start),
        ],
        states={
            AGE_PERIODO: [MessageHandler(filters.TEXT & ~filters.COMMAND, agenda_periodo)],
        },
        fallbacks=[CommandHandler("cancel", agenda_cancel)],
        name="agenda_conv",
        persistent=False,
    )


