"""
Central configuration. Everything the app needs is pulled from environment
variables so the exact same code runs locally, in Docker, and on Railway/Render.

Copy backend/.env.example to backend/.env and fill in real values before running.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "Immigration Doc Reviewer"
    ENV: str = "development"
    SECRET_KEY: str = "change-me-in-prod"
    FRONTEND_URL: str = "http://localhost:3000"

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/immigration_reviewer"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Auth ---
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- LLM providers (fill in the ones you actually use) ---
    # Mistral is EU-hosted -> preferred for GDPR-sensitive client documents (passports, etc).
    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-large-latest"
    MISTRAL_OCR_MODEL: str = "mistral-ocr-latest"

    # Gemini used as a fallback / for very long multi-document context windows.
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    DEFAULT_LLM_PROVIDER: str = "mistral"  # "mistral" | "gemini"

    # --- File storage ---
    # Local disk for MVP. Swap for S3-compatible storage (Cloudflare R2, Backblaze B2)
    # by replacing app/services/storage.py without touching anything else.
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 25

    # --- Stripe ---
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_STANDARD: str = ""  # $100/mo plan, per the pricing model

    # --- Email (case-ready notifications) ---
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "cases@yourdomain.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
