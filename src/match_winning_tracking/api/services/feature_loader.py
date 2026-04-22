"""Load pre-match features for a fixture from Supabase with safe fallbacks.

The mock model consumes a fixed vector of leakage-safe features. When the row
is not present in ``analytics.training_matches_base`` (or the table / database
does not exist yet), we fall back to the defaults declared in the feature
schema so the frontend still renders something meaningful.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

import psycopg

from match_winning_tracking.api.schemas import FeatureSpec

logger = logging.getLogger(__name__)


class FixtureNotFoundError(LookupError):
    """Raised when the requested fixture does not exist in any known source."""


DEMO_FIXTURES: dict[str, dict[str, float]] = {
    "demo-001": {
        "home_points_last_5": 10,
        "away_points_last_5": 4,
        "home_goal_diff_last_5": 6,
        "away_goal_diff_last_5": -2,
        "home_rest_days": 6,
        "away_rest_days": 3,
        "head_to_head_home_points_last_3": 6,
    },
    "demo-002": {
        "home_points_last_5": 5,
        "away_points_last_5": 11,
        "home_goal_diff_last_5": -1,
        "away_goal_diff_last_5": 7,
        "home_rest_days": 4,
        "away_rest_days": 7,
        "head_to_head_home_points_last_3": 3,
    },
    "demo-003": {
        "home_points_last_5": 7,
        "away_points_last_5": 7,
        "home_goal_diff_last_5": 1,
        "away_goal_diff_last_5": 0,
        "home_rest_days": 5,
        "away_rest_days": 5,
        "head_to_head_home_points_last_3": 4,
    },
    "demo-004": {
        "home_points_last_5": 9,
        "away_points_last_5": 3,
        "home_goal_diff_last_5": 4,
        "away_goal_diff_last_5": -3,
        "home_rest_days": 7,
        "away_rest_days": 2,
        "head_to_head_home_points_last_3": 7,
    },
    "demo-005": {
        "home_points_last_5": 2,
        "away_points_last_5": 8,
        "home_goal_diff_last_5": -5,
        "away_goal_diff_last_5": 3,
        "home_rest_days": 3,
        "away_rest_days": 6,
        "head_to_head_home_points_last_3": 1,
    },
    "demo-006": {
        "home_points_last_5": 6,
        "away_points_last_5": 6,
        "home_goal_diff_last_5": 2,
        "away_goal_diff_last_5": 2,
        "home_rest_days": 4,
        "away_rest_days": 4,
        "head_to_head_home_points_last_3": 5,
    },
}


def _defaults_from_schema(features: Iterable[FeatureSpec]) -> dict[str, float]:
    return {spec.key: float(spec.default) for spec in features}


def _load_from_postgres(fixture_id: str, db_url: str) -> dict[str, float] | None:
    keys = [
        "home_points_last_5",
        "away_points_last_5",
        "home_goal_diff_last_5",
        "away_goal_diff_last_5",
        "home_rest_days",
        "away_rest_days",
        "head_to_head_home_points_last_3",
    ]
    columns = ", ".join(keys)
    query = f"SELECT {columns} FROM analytics.training_matches_base WHERE fixture_id = %s LIMIT 1"
    try:
        with psycopg.connect(db_url, connect_timeout=2) as conn, conn.cursor() as cur:
            cur.execute(query, (fixture_id,))
            row: tuple[Any, ...] | None = cur.fetchone()
            if row is None:
                return None
            return {key: float(value) for key, value in zip(keys, row, strict=True)}
    except psycopg.Error as exc:
        logger.info("feature_loader DB unreachable or missing: %s", exc)
        return None


def load_features(
    fixture_id: str,
    feature_schema: Iterable[FeatureSpec],
    db_url: str | None,
) -> dict[str, float]:
    """Return a feature dict for the given fixture.

    Resolution order: Postgres ``analytics.training_matches_base`` → demo
    fixtures table → schema defaults. A fixture that cannot be resolved in any
    source raises ``FixtureNotFoundError``.
    """

    specs = list(feature_schema)
    defaults = _defaults_from_schema(specs)

    if db_url:
        db_row = _load_from_postgres(fixture_id, db_url)
        if db_row is not None:
            return {**defaults, **db_row}

    if fixture_id in DEMO_FIXTURES:
        return {**defaults, **DEMO_FIXTURES[fixture_id]}

    raise FixtureNotFoundError(fixture_id)
