from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any

from match_winning_tracking.clients.thesportsdb import TheSportsDBClient
from match_winning_tracking.config import Settings, configured_seasons
from match_winning_tracking.domain.mappers import (
    dedupe_alias_records,
    extract_team_aliases_from_team,
    map_league,
    map_team,
)
from match_winning_tracking.storage.postgres import PostgresStore


def sync_reference(
    store: PostgresStore,
    client: TheSportsDBClient,
    settings: Settings,
    *,
    today: date | None = None,
) -> dict[str, int]:
    run_id = store.create_sync_run(
        "sync-reference",
        {"league_id": settings.league.source_league_id, "league_key": settings.league.key},
    )

    rows_written = 0
    try:
        league_response = client.get_league(settings.league.source_league_id)
        teams_response = client.get_teams_by_league_name(settings.league.league_name)

        league_payload = first_or_raise(league_response.items("leagues"), "leagues")
        team_payloads = teams_response.items("teams")

        league_record = map_league(league_payload)
        season_records = build_league_seasons(settings, today=today)
        team_records = [
            map_team(payload, source_league_id=settings.league.source_league_id)
            for payload in team_payloads
        ]
        alias_records = dedupe_alias_records(
            [
                alias
                for payload in team_payloads
                for alias in extract_team_aliases_from_team(payload)
            ]
        )

        with store.connection() as connection:
            store.store_raw_payload(connection, league_response)
            store.store_raw_payload(connection, teams_response)
            rows_written += store.upsert_league(connection, league_record)
            rows_written += store.upsert_league_seasons(connection, season_records)
            rows_written += store.upsert_teams(connection, team_records)
            rows_written += store.upsert_team_aliases(connection, alias_records)
            connection.commit()

        store.finish_sync_run(run_id, status="success", rows_written=rows_written)
        return {
            "league_rows": 1,
            "season_rows": len(season_records),
            "team_rows": len(team_records),
            "alias_rows": len(alias_records),
        }
    except Exception as exc:
        store.finish_sync_run(
            run_id, status="failed", rows_written=rows_written, error_text=str(exc)
        )
        raise


def build_league_seasons(settings: Settings, *, today: date | None = None) -> list[dict[str, Any]]:
    active_seasons = configured_seasons(settings.league, today=today)
    return [
        {
            "source": settings.league.source,
            "source_league_id": settings.league.source_league_id,
            "season": season,
            "is_configured": True,
            "is_current": season == settings.league.current_season,
        }
        for season in active_seasons
    ]


def first_or_raise(items: Sequence[dict[str, Any]], key: str) -> dict[str, Any]:
    if not items:
        raise ValueError(f"TheSportsDB returned no items for '{key}'")
    return items[0]
