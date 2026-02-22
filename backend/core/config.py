from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    app_name: str = "Arras Contract API"
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./arras_dev.db"))
    auto_create_schema: bool = Field(
        default_factory=lambda: os.getenv("AUTO_CREATE_SCHEMA", "false").lower() in {"1", "true", "yes"}
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if origin.strip()
        ]
    )
    cors_origin_regex: str = Field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGIN_REGEX",
            r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$",
        )
    )
    openai_api_key: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-5-mini"))
    openai_transcription_model: str = Field(
        default_factory=lambda: os.getenv("OPENAI_TRANSCRIPTION_MODEL", "whisper-1")
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
