from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from match_winning_tracking.clients.thesportsdb import ApiResponse
from match_winning_tracking.config import LeagueConfig, Settings
from match_winning_tracking.ingestion.fixtures_backfill import (
    backfill_fixtures,
    iter_date_range,
    resolve_backfill_window,
)


@dataclass
class DummyConnection:
    committed: bool = False

    def commit(self) -> None:
        self.committed = True


@dataclass
class FakeStore:
    fixtures: list[dict[str, Any]] = field(default_factory=list)
    aliases: list[dict[str, Any]] = field(default_factory=list)
    raw_payload_fingerprints: list[str] = field(default_factory=list)
    finish_calls: list[dict[str, Any]] = field(default_factory=list)

    @contextmanager
    def connection(self) -> Any:
        yield DummyConnection()

    def create_sync_run(self, *_: Any, **__: Any) -> int:
        return 1

    def finish_sync_run(self, run_id: int, **kwargs: Any) -> None:
        self.finish_calls.append({"run_id": run_id, **kwargs})

    def store_raw_payload(self, _: DummyConnection, response: ApiResponse, **__: Any) -> None:
        self.raw_payload_fingerprints.append(response.request_fingerprint)

    def upsert_fixtures(self, _: DummyConnection, records: list[dict[str, Any]]) -> int:
        self.fixtures.extend(records)
        return len(records)

    def upsert_team_aliases(self, _: DummyConnection, records: list[dict[str, Any]]) -> int:
        self.aliases.extend(records)
        return len(records)


class FakeClient:
    def __init__(self, responses: dict[date, ApiResponse]) -> None:
        self.responses = responses

    def get_events_on_day(self, event_date: date, league_id: int) -> ApiResponse:
        assert league_id == 4688
        return self.responses[event_date]


def test_iter_date_range_is_inclusive() -> None:
    days = list(iter_date_range(date(2026, 4, 19), date(2026, 4, 21)))

    assert days == [date(2026, 4, 19), date(2026, 4, 20), date(2026, 4, 21)]


def test_resolve_backfill_window_uses_config_defaults() -> None:
    settings = build_settings()

    start, end = resolve_backfill_window(
        settings,
        from_date=date(2026, 4, 1),
        to_date=date(2026, 4, 3),
    )

    assert start == date(2026, 4, 1)
    assert end == date(2026, 4, 3)


def test_backfill_fixtures_handles_empty_days() -> None:
    store = FakeStore()
    client = FakeClient(
        {
            date(2026, 4, 19): build_response(
                "eventsday.php",
                {"d": "2026-04-19", "l": "4688"},
                {"events": None},
            ),
            date(2026, 4, 20): build_response(
                "eventsday.php",
                {"d": "2026-04-20", "l": "4688"},
                {
                    "events": [
                        {
                            "idEvent": "2204391",
                            "idLeague": "4688",
                            "strSeason": "2026",
                            "dateEvent": "2026-04-20",
                            "strTimestamp": "2026-04-20T20:00:00+00:00",
                            "strStatus": "Match Finished",
                            "idHomeTeam": "138311",
                            "idAwayTeam": "138449",
                            "strHomeTeam": "Alianza Lima",
                            "strAwayTeam": "Universitario",
                            "intHomeScore": "1",
                            "intAwayScore": "0",
                        }
                    ]
                },
            ),
        }
    )

    result = backfill_fixtures(
        store,
        client,
        build_settings(),
        from_date=date(2026, 4, 19),
        to_date=date(2026, 4, 20),
    )

    assert result["date_count"] == 2
    assert result["empty_days"] == 1
    assert len(store.fixtures) == 1
    assert store.finish_calls[-1]["status"] == "success"


def build_settings() -> Settings:
    return Settings(
        thesportsdb_api_key="123",
        thesportsdb_base_url="https://www.thesportsdb.com/api/v1/json",
        supabase_db_url="postgresql://postgres:postgres@127.0.0.1:55422/postgres",
        supabase_url="http://127.0.0.1:55421",
        supabase_service_role_key=None,
        league=LeagueConfig(
            key="liga1_peru",
            source="thesportsdb",
            source_league_id=4688,
            league_name="Peruvian_Primera_Division",
            country="Peru",
            sport="Soccer",
            current_season="2026",
            backfill_start_date=date(2020, 1, 1),
            future_fixtures_days=14,
            fixture_refresh_lookback_days=7,
            season_start_year=2020,
        ),
    )


def build_response(endpoint: str, params: dict[str, str], payload: dict[str, Any]) -> ApiResponse:
    timestamp = datetime(2026, 4, 21, 12, 0, tzinfo=UTC)
    return ApiResponse(
        endpoint=endpoint,
        params=params,
        requested_at=timestamp,
        received_at=timestamp,
        status_code=200,
        payload=payload,
        request_fingerprint=f"{endpoint}:{params}",
    )
