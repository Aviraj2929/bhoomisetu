"""
Application configuration.

Loads .env from the project root (one level above the backend/ directory)
and exposes all settings as a typed singleton `settings`.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ────────────────────────────────────────────────────────────────
# Try loading from <repo-root>/.env  (the canonical location)
# Fall back to the current working directory if not found.
_ROOT_ENV = Path(__file__).parent.parent.parent / ".env"   # backend/app/core/ → repo root
_CWD_ENV  = Path(os.getcwd()) / ".env"

if _ROOT_ENV.exists():
    load_dotenv(dotenv_path=_ROOT_ENV, override=False)
elif _CWD_ENV.exists():
    load_dotenv(dotenv_path=_CWD_ENV, override=False)
else:
    load_dotenv(override=False)   # try default discovery


class Settings:
    PROJECT_NAME: str  = os.getenv("PROJECT_NAME", "BhoomiSetu")
    API_V1_STR:   str  = os.getenv("API_V1_STR", "/api/v1")
    SECRET_KEY:   str  = os.getenv("SECRET_KEY", "bhoomisetu-secret-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Database
    POSTGRES_SERVER:   str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT:     str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER:     str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB:       str = os.getenv("POSTGRES_DB", "bhoomisetu_db")
    DATABASE_URL:      str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:@localhost:5432/bhoomisetu_db",
    )

    # Storage
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")
    STORAGE_DIR:  str = os.getenv("STORAGE_DIR", "./data/storage")

    # AI / OCR
    AI_PROVIDER:    str = os.getenv("AI_PROVIDER", "mock")
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")


settings = Settings()
