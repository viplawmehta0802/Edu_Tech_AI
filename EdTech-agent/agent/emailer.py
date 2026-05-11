"""
Simple SMTP welcome email helper.
Sends only if SMTP_HOST is configured; otherwise no-ops and returns False.
"""
import logging
import smtplib
import ssl
from email.message import EmailMessage

from config import (
    APP_NAME,
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
)

log = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(SMTP_HOST)


def _is_valid_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    local, _, domain = email.rpartition("@")
    return bool(local) and "." in domain


def send_welcome_email(to_email: str, name: str, grade: int) -> bool:
    """Send a welcome email. Returns True if sent, False if skipped or failed."""
    if not is_configured():
        log.info("SMTP not configured — skipping welcome email for %s", to_email)
        return False
    if not _is_valid_email(to_email):
        log.warning("Invalid email, not sending: %r", to_email)
        return False

    subject = f"Welcome to {APP_NAME}! 🎓"
    text_body = (
        f"Hi {name or 'there'},\n\n"
        f"Welcome to {APP_NAME} — your personal AI learning assistant.\n\n"
        f"Your account is ready:\n"
        f"  • Email: {to_email}\n"
        f"  • Grade: {grade}\n\n"
        "You can now sign in with your email and start exploring:\n"
        "  • Ask the Tutor anything\n"
        "  • Generate adaptive quizzes\n"
        "  • Upload PDFs and turn highlights into short notes\n\n"
        "Happy learning!\n"
        f"— The {APP_NAME} team\n"
    )
    html_body = f"""\
<html>
  <body style="font-family:Inter,Arial,sans-serif;background:#f8fafc;padding:24px;color:#0f172a">
    <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:16px;padding:28px;border:1px solid #e2e8f0">
      <h1 style="margin:0 0 12px;font-size:22px">Welcome to {APP_NAME}! 🎓</h1>
      <p>Hi {name or 'there'},</p>
      <p>Your account is ready. You can now sign in with your email and start learning.</p>
      <table style="font-size:14px;color:#475569;margin:12px 0">
        <tr><td><strong>Email</strong></td><td style="padding-left:12px">{to_email}</td></tr>
        <tr><td><strong>Grade</strong></td><td style="padding-left:12px">{grade}</td></tr>
      </table>
      <ul style="color:#475569;font-size:14px">
        <li>Ask the Tutor anything</li>
        <li>Generate adaptive quizzes</li>
        <li>Upload PDFs and turn highlights into short notes</li>
      </ul>
      <p style="margin-top:24px;color:#64748b;font-size:12px">— The {APP_NAME} team</p>
    </div>
  </body>
</html>
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        if SMTP_PORT == 465:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=15) as server:
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.ehlo()
                if SMTP_USE_TLS:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        log.info("Welcome email sent to %s", to_email)
        return True
    except Exception as e:
        log.warning("Failed to send welcome email to %s: %s", to_email, e)
        return False
