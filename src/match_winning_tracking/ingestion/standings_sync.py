from __future__ import annotations

from collections.abc import Sequence

from match_winning_tracking.clients.thesportsdb import TheSportsDBClient
from match_winning_tracking.config import Settings
from match_winning_tracking.domain.mappers import (
    dedupe_alias_records,
    extract_team_aliases_from_standing,
    map_standing,
)
from match_winning_tracking.storage.postgres import PostgresStore


def sync_standings(
    store: PostgresStore,
    client: TheSportsDBClient,
    settings: Settings,
    *,
    seasons: Sequence[str] | None = None,
) -> dict[str, int]:
    effective_seasons = tuple(seasons or [settings.league.current_season])
    run_id = store.create_sync_run(
        "sync-standings",
        {"league_id": settings.league.source_league_id, "seasons": list(effective_seasons)},
    )

    rows_written = 0
    try:
        with store.connection() as connection:
            for season in effective_seasons:
                response = client.get_standings(settings.league.source_league_id, season)
                store.store_raw_payload(connection, response)

                payloads = response.items("table")
                standing_records = [
                    map_standing(
                        payload,
                        source_league_id=settings.league.source_league_id,
                        season=season,
                        fetched_at=response.received_at,
                    )
                    for payload in payloads
                ]
                alias_records = dedupe_alias_records(
                    [
                        alias
                        for payload in payloads
                        for alias in extract_team_aliases_from_standing(payload)
                    ]
                )

                rows_written += store.upsert_standings(connection, standing_records)
                rows_written += store.upsert_team_aliases(connection, alias_records)

            connection.commit()

        store.finish_sync_run(run_id, status="success", rows_written=rows_written)
        return {"season_count": len(effective_seasons), "rows_written": rows_written}
    except Exception as exc:
        store.finish_sync_run(
            run_id, status="failed", rows_written=rows_written, error_text=str(exc)
        )
        raise
