import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import traceback
import sys

# Resolve .env from project root (two levels up from this file: app/reminders/ -> app/ -> project/)
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(os.path.normpath(_env_path), override=True)

MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() in ("1", "true", "yes")
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

# Debug: Print loaded config
sys.stderr.write(f"[EMAIL CONFIG] MAIL_SERVER={MAIL_SERVER}, MAIL_PORT={MAIL_PORT}, MAIL_USE_TLS={MAIL_USE_TLS}, MAIL_USE_SSL={MAIL_USE_SSL}\n")
sys.stderr.write(f"[EMAIL CONFIG] MAIL_USERNAME={'***' if MAIL_USERNAME else 'NOT SET'}, MAIL_PASSWORD={'***' if MAIL_PASSWORD else 'NOT SET'}\n")
sys.stderr.write(f"[EMAIL CONFIG] Password first 4 chars: {MAIL_PASSWORD[:4] if MAIL_PASSWORD else 'NONE'}, .env loaded from: {os.path.normpath(_env_path)}\n")
sys.stderr.flush()

def send_email(to_email: str, subject: str, body: str) -> bool:
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        sys.stderr.write(f"[EMAIL] ⚠ SMTP credentials not configured. MAIL_USERNAME={'SET' if MAIL_USERNAME else 'NOT SET'}, MAIL_PASSWORD={'SET' if MAIL_PASSWORD else 'NOT SET'}\n")
        sys.stderr.flush()
        return False

    sys.stderr.write(f"[EMAIL] Sending email to {to_email}: {subject}\n")
    sys.stderr.flush()
    
    try:
        msg = EmailMessage()
        msg["From"] = MAIL_FROM or MAIL_USERNAME
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        if MAIL_USE_SSL:
            sys.stderr.write(f"[EMAIL] Connecting to {MAIL_SERVER}:{MAIL_PORT} (SSL)...\n")
            sys.stderr.flush()
            server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, timeout=30)
        else:
            sys.stderr.write(f"[EMAIL] Connecting to {MAIL_SERVER}:{MAIL_PORT} (SMTP)...\n")
            sys.stderr.flush()
            server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=30)

        server.ehlo()
        if MAIL_USE_TLS and not MAIL_USE_SSL:
            sys.stderr.write("[EMAIL] Starting TLS...\n")
            sys.stderr.flush()
            server.starttls()
            server.ehlo()

        sys.stderr.write(f"[EMAIL] Logging in as {MAIL_USERNAME}...\n")
        sys.stderr.flush()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        sys.stderr.write(f"✅ [EMAIL SENT] {to_email} -> {subject}\n")
        sys.stderr.flush()
        return True
    except Exception as e:
        sys.stderr.write(f"❌ [EMAIL FAILED] Error sending to {to_email}: {e}\n")
        sys.stderr.flush()
        traceback.print_exc(file=sys.stderr)
        return False
