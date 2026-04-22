from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

import pytest

from match_winning_tracking.clients.thesportsdb import ApiResponse
from match_winning_tracking.config import LeagueConfig, Settings
from match_winning_tracking.ingestion.reference_sync import (
    IncompleteTeamListError,
    sync_reference,
)


@dataclass
class DummyConnection:
    committed: bool = False

    def commit(self) -> None:
        self.committed = True


@dataclass
class FakeStore:
    finish_calls: list[dict[str, Any]] = field(default_factory=list)
    upsert_calls: int = 0

    @contextmanager
    def connection(self) -> Any:
        yield DummyConnection()

    def create_sync_run(self, *_: Any, **__: Any) -> int:
        return 1

    def finish_sync_run(self, run_id: int, **kwargs: Any) -> None:
        self.finish_calls.append({"run_id": run_id, **kwargs})

    def store_raw_payload(self, *_: Any, **__: Any) -> None:
        self.upsert_calls += 1

    def upsert_league(self, *_: Any, **__: Any) -> int:
        self.upsert_calls += 1
        return 1

    def upsert_league_seasons(self, *_: Any, **__: Any) -> int:
        self.upsert_calls += 1
        return 1

    def upsert_teams(self, *_: Any, **__: Any) -> int:
        self.upsert_calls += 1
        return 1

    def upsert_team_aliases(self, *_: Any, **__: Any) -> int:
        self.upsert_calls += 1
        return 1


class FakeClient:
    def __init__(self, *, league_response: ApiResponse, teams_response: ApiResponse) -> None:
        self.league_response = league_response
        self.teams_response = teams_response

    def get_league(self, _: int) -> ApiResponse:
        return self.league_response

    def get_teams_by_league_name(self, _: str) -> ApiResponse:
        return self.teams_response


def test_sync_reference_rejects_partial_team_lists() -> None:
    store = FakeStore()
    client = FakeClient(
        league_response=build_response(
            "lookupleague.php",
            {"id": "4688"},
            {"leagues": [{"idLeague": "4688", "strLeague": "Liga 1"}]},
        ),
        teams_response=build_response(
            "search_all_teams.php",
            {"l": "Peruvian_Primera_Division"},
            {
                "teams": [
                    {"idTeam": "138311", "strTeam": "Alianza Lima"},
                    {"idTeam": "138449", "strTeam": "Universitario"},
                ]
            },
        ),
    )

    with pytest.raises(IncompleteTeamListError):
        sync_reference(store, client, build_settings())

    assert store.upsert_calls == 0
    assert store.finish_calls[-1]["status"] == "failed"


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
            expected_current_team_count=18,
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
