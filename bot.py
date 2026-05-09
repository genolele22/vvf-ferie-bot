"""
Entry point del bot VVF Ferie — Comando Provinciale VVF Genova.
"""

import logging

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

import database as db
from config import TELEGRAM_BOT_TOKEN
from handlers.pompiere import (
    build_aggiorna_password_handler,
    build_ferie_handler,
    build_start_handler,
    mie_richieste,
)
from handlers.capoturno import pending, pending_data

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    db.init_db()
    logger.info("Database inizializzato.")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # ── Pompiere ──────────────────────────────────────────────────────────────
    app.add_handler(build_start_handler())
    app.add_handler(build_aggiorna_password_handler())
    app.add_handler(build_ferie_handler())
    app.add_handler(CommandHandler("mie_richieste", mie_richieste))
    app.add_handler(MessageHandler(filters.Regex("^📋 Le mie richieste$"), mie_richieste))

    # ── Capoturno (solo consultazione) ────────────────────────────────────────
    app.add_handler(CommandHandler("pending",      pending))
    app.add_handler(CommandHandler("pending_data", pending_data))
    app.add_handler(MessageHandler(filters.Regex("^📋 Richieste in attesa$"), pending))
    app.add_handler(MessageHandler(filters.Regex("^📅 Per mese$"),            pending_data))

    logger.info("Bot avviato.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
