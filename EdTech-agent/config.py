import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
APP_PORT = int(os.getenv("APP_PORT", 8000))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
DISABLE_SSL_VERIFY = os.getenv("DISABLE_SSL_VERIFY", "0") == "1"
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "students.json")
