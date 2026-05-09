"""Test connessione SMTP Zimbra — eseguire con: python test_smtp.py"""
import getpass
from email_service import test_smtp
from config import SMTP_HOST, SMTP_PORT

email = input("Email istituzionale (es. mario.rossi@vigilfuoco.it): ").strip()
password = getpass.getpass("Password Zimbra: ")

print(f"\nConessione a {SMTP_HOST}:{SMTP_PORT} ... ", end="", flush=True)
if test_smtp(email, password):
    print("OK — SMTP funziona!")
else:
    print("ERRORE — controlla host, porta o credenziali (vedi log sopra)")
