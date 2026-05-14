"""Application configuration constants."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "inventory.db"
REPORTS_DIR = BASE_DIR / "reports"
EMAIL_LOG_PATH = REPORTS_DIR / "email_receipts.log"

APP_TITLE = "Store Inventory & POS System"
APP_GEOMETRY = "1220x760"
LOW_STOCK_THRESHOLD = 5

LOGIN_USERNAME = "admin"
LOGIN_PASSWORD_HASH = (
    "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
)

STORE_NAME = "ElectroHub"


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


EMAIL_ENABLED = _env_flag("STORE_POS_EMAIL_ENABLED", True)
SMTP_HOST = os.getenv("STORE_POS_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("STORE_POS_SMTP_PORT", "465"))
SMTP_USE_SSL = _env_flag("STORE_POS_SMTP_USE_SSL", SMTP_PORT == 465)
SMTP_USERNAME = os.getenv("STORE_POS_SMTP_USERNAME", "novawinter134@gmail.com")
SMTP_PASSWORD = os.getenv("STORE_POS_SMTP_PASSWORD", "dhks ibdf uxoi kvfi")
SMTP_FROM_NAME = os.getenv("STORE_POS_SMTP_FROM_NAME", "ElectroHub Store")
