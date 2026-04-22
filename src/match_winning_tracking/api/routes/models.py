"""Expose the catalog of available models and their feature schemas."""

from __future__ import annotations

from fastapi import APIRouter

from match_winning_tracking.api.schemas import ModelsResponse
from match_winning_tracking.api.services.models_catalog import list_models

router = APIRouter()


@router.get("/models", response_model=ModelsResponse, tags=["models"])
def models() -> ModelsResponse:
    return ModelsResponse(models=list_models())
