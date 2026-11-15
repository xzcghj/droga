"""Ustawienia aplikacji czytane ze zmiennych środowiskowych i pliku .env."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    # ../.env = główny katalog repo (uruchomienie z backend/), .env = katalog bieżący (wygrywa).
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    llm_provider: Literal["gemini", "claude", "none"] = "gemini"
    gemini_api_key: str | None = None
    anthropic_api_key: str | None = None
    llm_model: str | None = None

    osm_user_agent: str = "pol-drogi/1.0 (contact@example.com)"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    database_url: str = "sqlite:///./data/app.db"

    nominatim_url: str = "https://nominatim.openstreetmap.org"
    osrm_base_url: str = "https://routing.openstreetmap.de"
    overpass_urls: Annotated[list[str], NoDecode] = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ]
    http_timeout_s: float = 8.0
    seed_demo: bool = True

    @field_validator("cors_origins", "overpass_urls", mode="before")
    @classmethod
    def _split_commas(cls, value: object) -> object:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @field_validator("gemini_api_key", "anthropic_api_key", "llm_model", mode="before")
    @classmethod
    def _blank_is_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value
