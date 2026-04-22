"""POST /predict: probabilities for a given fixture."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from match_winning_tracking.api.config import ApiSettings, load_settings
from match_winning_tracking.api.schemas import PredictRequest, PredictResponse
from match_winning_tracking.api.services.feature_loader import (
    FixtureNotFoundError,
    load_features,
)
from match_winning_tracking.api.services.mock_predictor import predict as run_predict
from match_winning_tracking.api.services.models_catalog import (
    MOCK_MODEL_ID,
    feature_schema,
)

router = APIRouter()


@router.post("/predict", response_model=PredictResponse, tags=["predictions"])
def predict(
    request: PredictRequest,
    settings: Annotated[ApiSettings, Depends(load_settings)],
) -> PredictResponse:
    try:
        schema = feature_schema(request.model_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown model_id: {exc.args[0]}",
        ) from exc

    try:
        features = load_features(
            fixture_id=request.fixture_id,
            feature_schema=schema,
            db_url=settings.supabase_db_url,
        )
    except FixtureNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"fixture not found: {exc.args[0]}",
        ) from exc

    return PredictResponse(
        fixture_id=request.fixture_id,
        model_version=request.model_id or MOCK_MODEL_ID,
        features=features,
        probabilities=run_predict(features),
    )
