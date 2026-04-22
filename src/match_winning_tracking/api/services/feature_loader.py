"""Load pre-match features for a fixture from the authoritative backend schema.

Resolution order:

1. `analytics.training_matches_base` when the fixture already exists there.
2. On-demand feature derivation from `public.fixtures` for upcoming matches.
3. In-memory demo fixtures used by the API tests.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import Any

import psycopg

from match_winning_tracking.api.schemas import FeatureSpec
from match_winning_tracking.features.training_base import (
    CompletedMatch,
    compute_recent_form,
    compute_rest_days,
)
from match_winning_tracking.storage.postgres import PostgresStore

logger = logging.getLogger(__name__)


class FixtureNotFoundError(LookupError):
    """Raised when the requested fixture does not exist in any known source."""


@dataclass(frozen=True, slots=True)
class FixtureContext:
    source: str
    source_event_id: int
    match_timestamp: datetime
    home_team_id: int
    away_team_id: int


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


def _parse_live_fixture_id(fixture_id: str) -> tuple[str, int] | None:
    if ":" in fixture_id:
        source, raw_source_event_id = fixture_id.split(":", 1)
        if source and raw_source_event_id.isdigit():
            return source, int(raw_source_event_id)
        return None

    if fixture_id.isdigit():
        return "thesportsdb", int(fixture_id)

    return None


def _coerce_match_timestamp(
    kickoff_at: datetime | None,
    event_date: date | None,
) -> datetime | None:
    if kickoff_at is not None:
        return kickoff_at if kickoff_at.tzinfo is not None else kickoff_at.replace(tzinfo=UTC)
    if event_date is None:
        return None
    return datetime.combine(event_date, time.min, tzinfo=UTC)


def _load_from_training_base(
    store: PostgresStore,
    *,
    source_event_id: int,
) -> dict[str, float] | None:
    query = """
        select
            home_points_last_5,
            away_points_last_5,
            home_goal_diff_last_5,
            away_goal_diff_last_5,
            home_rest_days,
            away_rest_days,
            head_to_head_home_points_last_3
        from analytics.training_matches_base
        where source_event_id = %(source_event_id)s
        limit 1
    """

    with store.connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"source_event_id": source_event_id})
        row = cursor.fetchone()

    if row is None:
        return None

    return {
        "home_points_last_5": float(row["home_points_last_5"]),
        "away_points_last_5": float(row["away_points_last_5"]),
        "home_goal_diff_last_5": float(row["home_goal_diff_last_5"]),
        "away_goal_diff_last_5": float(row["away_goal_diff_last_5"]),
        "home_rest_days": float(row["home_rest_days"]) if row["home_rest_days"] is not None else 0.0,
        "away_rest_days": float(row["away_rest_days"]) if row["away_rest_days"] is not None else 0.0,
        "head_to_head_home_points_last_3": float(row["head_to_head_home_points_last_3"]),
    }


def _load_fixture_context(
    store: PostgresStore,
    *,
    source: str,
    source_event_id: int,
) -> FixtureContext | None:
    query = """
        select
            source,
            source_event_id,
            home_team_id,
            away_team_id,
            event_date,
            kickoff_at
        from public.fixtures
        where source = %(source)s
          and source_event_id = %(source_event_id)s
        limit 1
    """

    with store.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {"source": source, "source_event_id": source_event_id},
        )
        row = cursor.fetchone()

    if row is None:
        return None

    if row["home_team_id"] is None or row["away_team_id"] is None:
        return None

    match_timestamp = _coerce_match_timestamp(row["kickoff_at"], row["event_date"])
    if match_timestamp is None:
        return None

    return FixtureContext(
        source=str(row["source"]),
        source_event_id=int(row["source_event_id"]),
        match_timestamp=match_timestamp,
        home_team_id=int(row["home_team_id"]),
        away_team_id=int(row["away_team_id"]),
    )


def _load_completed_matches(
    store: PostgresStore,
    *,
    source: str,
    team_ids: Sequence[int],
    before: datetime,
) -> list[Mapping[str, Any]]:
    query = """
        select
            home_team_id,
            away_team_id,
            home_score,
            away_score,
            event_date,
            kickoff_at
        from public.fixtures
        where source = %(source)s
          and is_finished is true
          and home_score is not null
          and away_score is not null
          and home_team_id is not null
          and away_team_id is not null
          and event_date is not null
          and coalesce(kickoff_at, event_date::timestamp at time zone 'UTC') < %(before)s
          and (
            home_team_id = any(%(team_ids)s)
            or away_team_id = any(%(team_ids)s)
          )
        order by coalesce(kickoff_at, event_date::timestamp at time zone 'UTC') desc
    """

    with store.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {"source": source, "before": before, "team_ids": list(team_ids)},
        )
        rows = cursor.fetchall()

    return list(rows)


def _build_completed_matches_for_team(
    rows: Sequence[Mapping[str, Any]],
    *,
    team_id: int,
) -> list[CompletedMatch]:
    completed_matches: list[CompletedMatch] = []

    for row in rows:
        match_timestamp = _coerce_match_timestamp(
            row["kickoff_at"],
            row["event_date"],
        )
        if match_timestamp is None:
            continue

        if int(row["home_team_id"]) == team_id:
            goals_for = int(row["home_score"])
            goals_against = int(row["away_score"])
        elif int(row["away_team_id"]) == team_id:
            goals_for = int(row["away_score"])
            goals_against = int(row["home_score"])
        else:
            continue

        completed_matches.append(
            CompletedMatch(
                played_at=match_timestamp,
                goals_for=goals_for,
                goals_against=goals_against,
            )
        )

    return completed_matches


def _head_to_head_home_points(
    rows: Sequence[Mapping[str, Any]],
    *,
    home_team_id: int,
    away_team_id: int,
) -> float:
    head_to_head_rows = [
        row
        for row in rows
        if {
            int(row["home_team_id"]),
            int(row["away_team_id"]),
        }
        == {home_team_id, away_team_id}
    ][:3]

    home_points = 0
    for row in head_to_head_rows:
        home_score = int(row["home_score"])
        away_score = int(row["away_score"])

        if home_score == away_score:
            home_points += 1
            continue

        home_team_won = (
            int(row["home_team_id"]) == home_team_id and home_score > away_score
        ) or (
            int(row["away_team_id"]) == home_team_id and away_score > home_score
        )
        if home_team_won:
            home_points += 3

    return float(home_points)


def _load_live_fixture_features(
    store: PostgresStore,
    *,
    source: str,
    source_event_id: int,
    defaults: Mapping[str, float],
) -> dict[str, float] | None:
    cached = _load_from_training_base(store, source_event_id=source_event_id)
    if cached is not None:
        return {**defaults, **cached}

    fixture = _load_fixture_context(
        store,
        source=source,
        source_event_id=source_event_id,
    )
    if fixture is None:
        return None

    rows = _load_completed_matches(
        store,
        source=fixture.source,
        team_ids=[fixture.home_team_id, fixture.away_team_id],
        before=fixture.match_timestamp,
    )

    home_matches = _build_completed_matches_for_team(rows, team_id=fixture.home_team_id)
    away_matches = _build_completed_matches_for_team(rows, team_id=fixture.away_team_id)

    home_form = compute_recent_form(home_matches, before=fixture.match_timestamp, limit=5)
    away_form = compute_recent_form(away_matches, before=fixture.match_timestamp, limit=5)
    home_previous_match = max((match.played_at for match in home_matches), default=None)
    away_previous_match = max((match.played_at for match in away_matches), default=None)

    features: dict[str, float] = {
        "home_points_last_5": float(home_form.points),
        "away_points_last_5": float(away_form.points),
        "home_goal_diff_last_5": float(home_form.goal_difference),
        "away_goal_diff_last_5": float(away_form.goal_difference),
        "head_to_head_home_points_last_3": _head_to_head_home_points(
            rows,
            home_team_id=fixture.home_team_id,
            away_team_id=fixture.away_team_id,
        ),
    }

    home_rest_days = compute_rest_days(home_previous_match, fixture.match_timestamp)
    away_rest_days = compute_rest_days(away_previous_match, fixture.match_timestamp)
    if home_rest_days is not None:
        features["home_rest_days"] = float(home_rest_days)
    if away_rest_days is not None:
        features["away_rest_days"] = float(away_rest_days)

    return {**defaults, **features}


def load_features(
    fixture_id: str,
    feature_schema: Iterable[FeatureSpec],
    db_url: str | None,
) -> dict[str, float]:
    """Return a feature dict for the given fixture."""

    specs = list(feature_schema)
    defaults = _defaults_from_schema(specs)
    live_fixture_id = _parse_live_fixture_id(fixture_id)

    if db_url and live_fixture_id is not None:
        try:
            store = PostgresStore(db_url)
            live_features = _load_live_fixture_features(
                store,
                source=live_fixture_id[0],
                source_event_id=live_fixture_id[1],
                defaults=defaults,
            )
            if live_features is not None:
                return live_features
        except psycopg.Error as exc:
            logger.info("feature_loader DB unreachable or query failed: %s", exc)

    if fixture_id in DEMO_FIXTURES:
        return {**defaults, **DEMO_FIXTURES[fixture_id]}

    raise FixtureNotFoundError(fixture_id)
