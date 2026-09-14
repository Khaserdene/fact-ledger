"""Тохиргоо: backend/.env файлаас уншина (.env.example-ийг хуулж үүсгэнэ)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AI provider: "manual" | "gemini" | "claude"
    ai_provider: str = "manual"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-pro"

    anthropic_api_key: str = ""
    claude_model: str = "claude-opus-4-8"

    # Fuzzy тулгалтын босгууд (0-100)
    fuzzy_dedup_threshold: int = 87
    fuzzy_link_threshold: int = 85
    fuzzy_merge_threshold: int = 92


@lru_cache
def get_settings() -> Settings:
    return Settings()
