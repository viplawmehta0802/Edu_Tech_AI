import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
APP_PORT = int(os.getenv("APP_PORT", 8000))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
DISABLE_SSL_VERIFY = os.getenv("DISABLE_SSL_VERIFY", "0") == "1"
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "students.json")

# ── SMTP (welcome email) ─────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "noreply@edubot.local")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "1") == "1"
APP_NAME = os.getenv("APP_NAME", "EduBot")

