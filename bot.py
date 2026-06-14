"""
Entry point del bot VVF Ferie — Comando Provinciale VVF Genova.
"""

import logging
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

import database as db
import outbox_drain
from config import TELEGRAM_BOT_TOKEN
from handlers.pompiere import (
    annulla_richiesta_callback,
    build_aggiorna_password_handler,
    build_ferie_handler,
    build_start_handler,
    mie_richieste,
)
from handlers.fureria import build_agenda_handler
from handlers.scambio import build_scambio_handlers

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── HTTP server minimale: solo health-check per Fly (GET /) ────────────────────
# La generazione ODT è stata spostata nel gestionale (FoglioRenderer, dal DB).

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass  # silenzio nei log


class _DualStackServer(HTTPServer):
    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


def _start_http_server():
    server = _DualStackServer(("::", 8080), HealthHandler)
    logger.info("HTTP health server in ascolto su :8080 (dual-stack)")
    server.serve_forever()


# ── Telegram bot ──────────────────────────────────────────────────────────────

def main() -> None:
    db.init_db()
    logger.info("Database inizializzato.")

    threading.Thread(target=_start_http_server, daemon=True).start()
    outbox_drain.start()   # coda notifiche dal gestionale (ferie approvate, ecc.)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # ── Pompiere ──────────────────────────────────────────────────────────────
    app.add_handler(build_start_handler())
    app.add_handler(build_aggiorna_password_handler())
    app.add_handler(build_ferie_handler())
    app.add_handler(CommandHandler("mie_richieste", mie_richieste))
    app.add_handler(MessageHandler(filters.Regex("^📋 Le mie richieste$"), mie_richieste))
    app.add_handler(CallbackQueryHandler(annulla_richiesta_callback, pattern=r"^annulla:"))

    # ── Fureria ───────────────────────────────────────────────────────────────
    app.add_handler(build_agenda_handler())

    # ── Scambio salto turno ─────────────────────────────────────────────────────
    for h in build_scambio_handlers():
        app.add_handler(h)

    logger.info("Bot avviato.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
