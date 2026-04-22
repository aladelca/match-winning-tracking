from __future__ import annotations

from match_winning_tracking.clients.thesportsdb import TheSportsDBClient
from match_winning_tracking.config import Settings
from match_winning_tracking.domain.mappers import map_player
from match_winning_tracking.storage.postgres import PostgresStore


def sync_players(
    store: PostgresStore,
    client: TheSportsDBClient,
    settings: Settings,
) -> dict[str, int]:
    run_id = store.create_sync_run(
        "sync-players",
        {"league_id": settings.league.source_league_id, "league_key": settings.league.key},
    )

    rows_written = 0
    teams_processed = 0
    try:
        with store.connection() as connection:
            team_ids = store.get_current_team_ids(
                connection,
                source=settings.league.source,
                source_league_id=settings.league.source_league_id,
            )

            for team_id in team_ids:
                response = client.get_players_for_team(team_id)
                store.store_raw_payload(connection, response)
                player_records = [map_player(payload) for payload in response.items("player")]
                rows_written += store.upsert_players(
                    connection,
                    team_id=team_id,
                    source=settings.league.source,
                    records=player_records,
                )
                teams_processed += 1

            connection.commit()

        store.finish_sync_run(run_id, status="success", rows_written=rows_written)
        return {"teams_processed": teams_processed, "player_rows": rows_written}
    except Exception as exc:
        store.finish_sync_run(
            run_id, status="failed", rows_written=rows_written, error_text=str(exc)
        )
        raise
