"""Runtime configuration for the mock predictions API."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiSettings:
    host: str
    port: int
    cors_origins: tuple[str, ...]
    model_version: str
    supabase_db_url: str | None


def load_settings() -> ApiSettings:
    raw_origins = os.getenv("API_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    origins = tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
    return ApiSettings(
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
        cors_origins=origins,
        model_version=os.getenv("MOCK_MODEL_VERSION", "mock-v0"),
        supabase_db_url=os.getenv("SUPABASE_DB_URL") or None,
    )
