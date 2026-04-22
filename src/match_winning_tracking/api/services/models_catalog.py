"""Registry of available mock models.

This module is the single source of truth for the feature schema exposed via
``GET /models``. Both the ``/predict`` and ``/predict/sensitivity`` routes
reuse this schema for default-population and override validation, guaranteeing
that UI and server never disagree about which features exist.
"""

from __future__ import annotations

from match_winning_tracking.api.schemas import FeatureSpec, ModelInfo

MOCK_MODEL_ID = "mock-v0"

_FEATURES: tuple[FeatureSpec, ...] = (
    FeatureSpec(
        key="home_points_last_5",
        label="Home points (last 5)",
        min=0,
        max=15,
        default=7,
    ),
    FeatureSpec(
        key="away_points_last_5",
        label="Away points (last 5)",
        min=0,
        max=15,
        default=7,
    ),
    FeatureSpec(
        key="home_goal_diff_last_5",
        label="Home goal diff (last 5)",
        min=-10,
        max=10,
        default=0,
    ),
    FeatureSpec(
        key="away_goal_diff_last_5",
        label="Away goal diff (last 5)",
        min=-10,
        max=10,
        default=0,
    ),
    FeatureSpec(
        key="home_rest_days",
        label="Home rest days",
        min=0,
        max=14,
        default=5,
    ),
    FeatureSpec(
        key="away_rest_days",
        label="Away rest days",
        min=0,
        max=14,
        default=5,
    ),
    FeatureSpec(
        key="head_to_head_home_points_last_3",
        label="H2H home points (last 3)",
        min=0,
        max=9,
        default=4,
    ),
)


def get_model(model_id: str | None = None) -> ModelInfo:
    resolved = model_id or MOCK_MODEL_ID
    if resolved != MOCK_MODEL_ID:
        raise LookupError(resolved)
    return ModelInfo(
        id=MOCK_MODEL_ID,
        description="Heuristic mock predictor (deterministic softmax over form deltas)",
        features=list(_FEATURES),
    )


def list_models() -> list[ModelInfo]:
    return [get_model()]


def feature_schema(model_id: str | None = None) -> list[FeatureSpec]:
    return list(get_model(model_id).features)
