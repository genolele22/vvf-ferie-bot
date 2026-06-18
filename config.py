import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
# Comma-separated list of Telegram user IDs with fureria access, e.g. "997982711,123456789"
TELEGRAM_FURERIA_IDS: list[int] = [
    int(x.strip()) for x in os.environ["TELEGRAM_FURERIA_IDS"].split(",")
]

SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
FURERIA_EMAIL = os.environ["FURERIA_EMAIL"]
ENCRYPTION_KEY = os.environ["ENCRYPTION_KEY"]

# IMAP: serve per depositare una copia delle mail inviate nella cartella "Inviati"
# (l'SMTP da solo non lo fa). Default derivato dall'host SMTP (smtp-s → imap-s).
IMAP_HOST = os.environ.get("IMAP_HOST") or SMTP_HOST.replace("smtp", "imap")
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))

MYSQL_HOST     = os.environ.get("MYSQL_HOST",     "127.0.0.1")
MYSQL_PORT     = int(os.environ.get("MYSQL_PORT",    "3306"))
MYSQL_USER     = os.environ.get("MYSQL_USER",     "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "vvf_turno_b")

CALENDARIO_PATH = os.environ.get("CALENDARIO_PATH", os.path.join(os.path.dirname(__file__), "data", "calendario.json"))
ODT_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "data", "templates")

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
