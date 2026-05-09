import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CAPOTURNO_ID = int(os.environ["TELEGRAM_CAPOTURNO_ID"])

SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
CAPOTURNO_EMAIL = os.environ["CAPOTURNO_EMAIL"]
ENCRYPTION_KEY = os.environ["ENCRYPTION_KEY"]

DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "vvf_ferie.db"))
CALENDARIO_PATH = os.environ.get("CALENDARIO_PATH", os.path.join(os.path.dirname(__file__), "data", "calendario.json"))
