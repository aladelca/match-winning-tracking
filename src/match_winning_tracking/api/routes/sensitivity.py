"""POST /predict/sensitivity: baseline vs modified with per-class deltas."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from match_winning_tracking.api.config import ApiSettings, load_settings
from match_winning_tracking.api.schemas import (
    DeltaTriplet,
    SensitivityBranch,
    SensitivityRequest,
    SensitivityResponse,
)
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


def _validate_overrides(
    overrides: dict[str, float], schema_keys: dict[str, tuple[float, float]]
) -> None:
    for key, value in overrides.items():
        if key not in schema_keys:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"unknown feature: {key}",
            )
        lo, hi = schema_keys[key]
        if value < lo or value > hi:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"feature {key}={value} out of range [{lo}, {hi}]",
            )


@router.post(
    "/predict/sensitivity",
    response_model=SensitivityResponse,
    tags=["predictions"],
)
def sensitivity(
    request: SensitivityRequest,
    settings: Annotated[ApiSettings, Depends(load_settings)],
) -> SensitivityResponse:
    try:
        schema = feature_schema(request.model_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown model_id: {exc.args[0]}",
        ) from exc

    schema_ranges = {spec.key: (float(spec.min), float(spec.max)) for spec in schema}
    _validate_overrides(request.feature_overrides, schema_ranges)

    try:
        baseline_features = load_features(
            fixture_id=request.fixture_id,
            feature_schema=schema,
            db_url=settings.supabase_db_url,
        )
    except FixtureNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"fixture not found: {exc.args[0]}",
        ) from exc

    modified_features = {**baseline_features, **request.feature_overrides}
    baseline_probs = run_predict(baseline_features)
    modified_probs = run_predict(modified_features)

    return SensitivityResponse(
        fixture_id=request.fixture_id,
        model_version=request.model_id or MOCK_MODEL_ID,
        baseline=SensitivityBranch(features=baseline_features, probabilities=baseline_probs),
        modified=SensitivityBranch(features=modified_features, probabilities=modified_probs),
        deltas=DeltaTriplet(
            home=modified_probs.home - baseline_probs.home,
            draw=modified_probs.draw - baseline_probs.draw,
            away=modified_probs.away - baseline_probs.away,
        ),
    )
