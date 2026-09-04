import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/Lisbon")
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "EUR")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:3000")
SESSION_SECRET = os.getenv("SESSION_SECRET", "finas-dev-secret")
SESSION_DAYS = int(os.getenv("SESSION_DAYS", "30"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
LOGIN_CODE_MINUTES = int(os.getenv("LOGIN_CODE_MINUTES", "5"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID", "")
ALERT_MINUTES = int(os.getenv("ALERT_MINUTES", "5"))
ALLOWED_TELEGRAM_IDS = os.getenv("ALLOWED_TELEGRAM_IDS", "")
BOT_MAX_MESSAGES = int(os.getenv("BOT_MAX_MESSAGES", "20"))
BOT_RATE_WINDOW_SECONDS = int(os.getenv("BOT_RATE_WINDOW_SECONDS", "60"))
API_MAX_REQUESTS = int(os.getenv("API_MAX_REQUESTS", "120"))
API_RATE_WINDOW_SECONDS = int(os.getenv("API_RATE_WINDOW_SECONDS", "60"))
DB_CONNECT_SECONDS = int(os.getenv("DB_CONNECT_SECONDS", "5"))
