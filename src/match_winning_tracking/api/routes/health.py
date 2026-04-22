"""Liveness endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from match_winning_tracking.api.config import ApiSettings, load_settings
from match_winning_tracking.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["meta"])
def health(settings: Annotated[ApiSettings, Depends(load_settings)]) -> HealthResponse:
    return HealthResponse(status="ok", model_version=settings.model_version)
