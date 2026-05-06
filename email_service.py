import logging
import smtplib
from datetime import date
from email.message import EmailMessage

from config import SMTP_HOST, SMTP_PORT, CAPOTURNO_EMAIL

logger = logging.getLogger(__name__)

TIPO_LABEL = {
    "D":  "Diurno 🌅",
    "N":  "Notturno 🌙",
    "DN": "Diurno + Notturno 🌅🌙",
}


def _smtp_connect(email: str, password: str) -> smtplib.SMTP:
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


def send_ferie_request(
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
    d = date.fromisoformat(data_iso)
    tipo_str = TIPO_LABEL.get(tipo, tipo)
    data_str = d.strftime("%d/%m/%Y")

    msg = EmailMessage()
    msg["From"] = pompiere_email
    msg["To"] = CAPOTURNO_EMAIL
    msg["Reply-To"] = pompiere_email
    msg["Subject"] = f"[Richiesta Ferie #{request_id}] {pompiere_nome} {pompiere_cognome} — {data_str} {tipo_str}"
    msg.set_content(
        f"Nuova richiesta di ferie\n\n"
        f"Vigile:         {pompiere_nome} {pompiere_cognome}\n"
        f"Distaccamento:  {distaccamento}\n"
        f"Gruppo turno:   {gruppo}\n"
        f"Data:           {data_str}\n"
        f"Turno:          {tipo_str}\n\n"
        f"Per rispondere usa direttamente Rispondi a questa email."
    )

    try:
        with _smtp_connect(pompiere_email, pompiere_password) as smtp:
            smtp.send_message(msg)
        logger.info("Email richiesta #%d inviata da %s", request_id, pompiere_email)
        return True
    except Exception as e:
        logger.error("Errore invio email richiesta #%d: %s", request_id, e)
        return False
