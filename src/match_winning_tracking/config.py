from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, cast

import yaml

DEFAULT_CONFIG_PATH = Path("config/leagues.yml")
DEFAULT_SUPABASE_DB_URL = "postgresql://postgres:postgres@127.0.0.1:55422/postgres"
DEFAULT_SUPABASE_URL = "http://127.0.0.1:55421"


@dataclass(frozen=True, slots=True)
class LeagueConfig:
    key: str
    source: str
    source_league_id: int
    league_name: str
    country: str
    sport: str
    current_season: str
    backfill_start_date: date
    future_fixtures_days: int
    fixture_refresh_lookback_days: int
    season_start_year: int


@dataclass(frozen=True, slots=True)
class Settings:
    thesportsdb_api_key: str
    thesportsdb_base_url: str
    supabase_db_url: str
    supabase_url: str
    supabase_service_role_key: str | None
    league: LeagueConfig


def load_settings(config_path: Path | str = DEFAULT_CONFIG_PATH) -> Settings:
    load_local_env()
    league = load_league_config(Path(config_path))
    return Settings(
        thesportsdb_api_key=os.getenv("THESPORTSDB_API_KEY", "123"),
        thesportsdb_base_url=os.getenv(
            "THESPORTSDB_BASE_URL",
            "https://www.thesportsdb.com/api/v1/json",
        ).rstrip("/"),
        supabase_db_url=os.getenv("SUPABASE_DB_URL", DEFAULT_SUPABASE_DB_URL),
        supabase_url=os.getenv("SUPABASE_URL", DEFAULT_SUPABASE_URL),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") or None,
        league=league,
    )


def load_league_config(config_path: Path) -> LeagueConfig:
    raw_config = read_yaml(config_path)
    leagues = cast(dict[str, dict[str, Any]], raw_config.get("leagues", {}))
    if not leagues:
        raise ValueError(f"No league definitions found in {config_path}")

    requested_league_id = int(
        os.getenv("LIGA1_LEAGUE_ID", next(iter(leagues.values()))["source_league_id"])
    )

    for key, payload in leagues.items():
        if int(payload["source_league_id"]) != requested_league_id:
            continue

        configured_start_date = parse_iso_date(str(payload["backfill_start_date"]))
        backfill_start_date = parse_iso_date(
            os.getenv("BACKFILL_START_DATE", configured_start_date.isoformat())
        )

        return LeagueConfig(
            key=key,
            source=str(payload["source"]),
            source_league_id=int(payload["source_league_id"]),
            league_name=str(payload["league_name"]),
            country=str(payload["country"]),
            sport=str(payload["sport"]),
            current_season=str(payload["current_season"]),
            backfill_start_date=backfill_start_date,
            future_fixtures_days=int(
                os.getenv("FUTURE_FIXTURES_DAYS", str(payload["future_fixtures_days"]))
            ),
            fixture_refresh_lookback_days=int(
                os.getenv(
                    "FIXTURE_REFRESH_LOOKBACK_DAYS",
                    str(payload["fixture_refresh_lookback_days"]),
                )
            ),
            season_start_year=int(payload["season_start_year"]),
        )

    raise ValueError(f"League id {requested_league_id} is not configured in {config_path}")


def configured_seasons(league: LeagueConfig, *, today: date | None = None) -> tuple[str, ...]:
    effective_today = today or date.today()
    configured_end_year = max(int(league.current_season), effective_today.year)
    return tuple(str(year) for year in range(league.season_start_year, configured_end_year + 1))


def load_local_env(env_path: Path = Path(".env")) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        normalized_value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), normalized_value)


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected a mapping at the root of {path}")
    return cast(dict[str, Any], loaded)
