import logging
import smtplib
from email.message import EmailMessage
from app.config import settings

logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, body: str) -> None:
    if not settings.smtp_host or not settings.smtp_from:
        logger.warning("SMTP is not configured; email to %s was not sent", to)
        return
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except Exception:
        logger.exception("Email delivery failed for recipient %s", to)
