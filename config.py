import os
import secrets

_ROOT = os.path.abspath(os.path.dirname(__file__))
_INSTANCE = os.path.join(_ROOT, "instance")
os.makedirs(_INSTANCE, exist_ok=True)
_DB_PATH = os.path.join(_INSTANCE, "school.db")

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(_ROOT, ".env"))
except ImportError:
    pass


def _database_uri() -> str:
    """Build SQLAlchemy URI; normalize Render's postgres:// scheme."""
    uri = os.environ.get("DATABASE_URL")
    if not uri:
        return "sqlite:///" + _DB_PATH.replace("\\", "/")
    # Render/Heroku historically used postgres://; SQLAlchemy needs postgresql://
    if uri.startswith("postgres://"):
        uri = "postgresql://" + uri[len("postgres://") :]
    return uri


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional SMTP — set in .env to enable email alerts
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # API key for hardware RFID POST /rfid_scan (optional; empty = open for local dev)
    RFID_API_KEY = os.environ.get("RFID_API_KEY", "")
