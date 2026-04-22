"""Shared fixtures for API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from match_winning_tracking.api.config import ApiSettings
from match_winning_tracking.api.main import create_app


@pytest.fixture
def settings() -> ApiSettings:
    return ApiSettings(
        host="127.0.0.1",
        port=8000,
        cors_origins=("http://localhost:3000",),
        model_version="mock-v0",
        supabase_db_url=None,
    )


@pytest.fixture
def client(settings: ApiSettings) -> TestClient:
    return TestClient(create_app(settings))
