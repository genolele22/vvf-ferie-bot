import logging
import smtplib
from datetime import date
from email.message import EmailMessage

from config import SMTP_HOST, SMTP_PORT, FURERIA_EMAIL

logger = logging.getLogger(__name__)

TIPO_LABEL = {
    "D":  "Diurno ☀️",
    "N":  "Notturno 🌙",
    "DN": "Diurno + Notturno 🌅🌙",
}


def _smtp_connect(email: str, password: str) -> smtplib.SMTP:
    if SMTP_PORT == 465:
        smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
    else:
        smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        smtp.ehlo()
        smtp.starttls()
    smtp.login(email, password)
    return smtp


def test_smtp(email: str, password: str) -> bool:
    try:
        with _smtp_connect(email, password) as smtp:
            smtp.quit()
        return True
    except Exception as e:
        logger.warning("SMTP test fallito per %s: %s", email, e)
        return False


def send_ferie_requests(
    pompiere_email: str,
    pompiere_password: str,
    pompiere_nome: str,
    pompiere_cognome: str,
    distaccamento: str,
    gruppo: str,
    richieste: list[tuple[int, str, str]],  # (request_id, data_iso, tipo)
) -> bool:
    """Invia una singola email con tutte le richieste di ferie selezionate."""
    righe = "\n".join(
        f"  - {date.fromisoformat(data_iso).strftime('%d/%m/%Y')}  {TIPO_LABEL.get(tipo, tipo)}"
        for _, data_iso, tipo in richieste
    )
    ids_str = ", ".join(f"#{rid}" for rid, _, _ in richieste)

    if len(richieste) == 1:
        _, data_iso, tipo = richieste[0]
        data_str = date.fromisoformat(data_iso).strftime("%d/%m/%Y")
        subject = (
            f"[Richiesta Ferie] {pompiere_nome} {pompiere_cognome} "
            f"— {data_str} {TIPO_LABEL.get(tipo, tipo)}"
        )
    else:
        subject = (
            f"[Richiesta Ferie] {pompiere_nome} {pompiere_cognome} "
            f"— {len(richieste)} giorni"
        )

    msg = EmailMessage()
    msg["From"] = pompiere_email
    msg["To"] = FURERIA_EMAIL
    msg["Reply-To"] = pompiere_email
    msg["Subject"] = subject
    msg.set_content(
        f"Nuova richiesta di ferie\n\n"
        f"Vigile:         {pompiere_nome} {pompiere_cognome}\n"
        f"Distaccamento:  {distaccamento}\n"
        f"Gruppo turno:   {gruppo}\n\n"
        f"Giorni richiesti:\n{righe}\n\n"
        f"IDs richiesta: {ids_str}\n\n"
        f"Per rispondere usa direttamente Rispondi a questa email."
    )

    try:
        with _smtp_connect(pompiere_email, pompiere_password) as smtp:
            smtp.send_message(msg)
        logger.info("Email ferie inviata da %s (%s)", pompiere_email, ids_str)
        return True
    except Exception as e:
        logger.error("Errore invio email ferie %s: %s", ids_str, e)
        return False


def send_cancellation_email(
    pompiere_email: str,
    pompiere_password: str,
    pompiere_nome: str,
    pompiere_cognome: str,
    distaccamento: str,
    gruppo: str,
    request_id: int,
    data_iso: str,
    tipo: str,
) -> bool:
    """Notifica la fureria dell'annullamento di una richiesta di ferie."""
    data_str = date.fromisoformat(data_iso).strftime("%d/%m/%Y")
    tipo_str = TIPO_LABEL.get(tipo, tipo)

    msg = EmailMessage()
    msg["From"] = pompiere_email
    msg["To"] = FURERIA_EMAIL
    msg["Reply-To"] = pompiere_email
    msg["Subject"] = (
        f"[Annullamento Ferie] {pompiere_nome} {pompiere_cognome} "
        f"— {data_str} {tipo_str}"
    )
    msg.set_content(
        f"Annullamento richiesta ferie\n\n"
        f"Vigile:         {pompiere_nome} {pompiere_cognome}\n"
        f"Distaccamento:  {distaccamento}\n"
        f"Gruppo turno:   {gruppo}\n\n"
        f"Giorno annullato: {data_str}  {tipo_str}\n"
        f"ID richiesta:     #{request_id}\n"
    )

    try:
        with _smtp_connect(pompiere_email, pompiere_password) as smtp:
            smtp.send_message(msg)
        logger.info("Email annullamento inviata da %s (#%s)", pompiere_email, request_id)
        return True
    except Exception as e:
        logger.error("Errore invio email annullamento #%s: %s", request_id, e)
        return False
