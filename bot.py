"""
Entry point del bot VVF Ferie — Comando Provinciale VVF Genova.
"""

import logging
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

import database as db
import odt_service
from config import TELEGRAM_BOT_TOKEN
from handlers.pompiere import (
    annulla_richiesta_callback,
    build_aggiorna_password_handler,
    build_ferie_handler,
    build_start_handler,
    mie_richieste,
)
from handlers.fureria import build_agenda_handler

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── HTTP server interno per generazione ODT ───────────────────────────────────

class OdtHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
            return

        if parsed.path != "/odt":
            self.send_response(404)
            self.end_headers()
            return

        params   = parse_qs(parsed.query)
        data_iso = params.get("data", [None])[0]
        if not data_iso:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing ?data=YYYY-MM-DD")
            return

        odt_bytes = odt_service.genera_foglio(data_iso)
        if odt_bytes is None:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"No ODT for this date")
            return

        filename = f"servizio_{data_iso.replace('-', '')}.odt"
        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.oasis.opendocument.text")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(odt_bytes)))
        self.end_headers()
        self.wfile.write(odt_bytes)

    def log_message(self, *args):
        pass  # silenzio nei log


class _DualStackServer(HTTPServer):
    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


def _start_http_server():
    server = _DualStackServer(("::", 8080), OdtHandler)
    logger.info("HTTP ODT server in ascolto su :8080 (dual-stack)")
    server.serve_forever()


# ── Telegram bot ──────────────────────────────────────────────────────────────

def main() -> None:
    db.init_db()
    logger.info("Database inizializzato.")

    threading.Thread(target=_start_http_server, daemon=True).start()

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

    logger.info("Bot avviato.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
