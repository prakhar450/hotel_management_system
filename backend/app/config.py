import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator

# Walk up from this file to find .env — works whether run from backend/ or project root
_here = Path(__file__).resolve().parent
_env_candidates = [_here / ".env", _here.parent / ".env", _here.parent.parent / ".env"]
_env_file = next((str(p) for p in _env_candidates if p.exists()), ".env")


class Settings(BaseSettings):
    DATABASE_URL: str
    ANTHROPIC_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key"
    CORS_ORIGINS: str = "http://localhost:5173"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: str) -> str:
        return v

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": _env_file, "extra": "ignore"}


settings = Settings()
