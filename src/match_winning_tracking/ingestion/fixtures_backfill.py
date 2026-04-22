from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta

from match_winning_tracking.clients.thesportsdb import TheSportsDBClient
from match_winning_tracking.config import Settings
from match_winning_tracking.domain.mappers import (
    dedupe_alias_records,
    extract_team_aliases_from_fixture,
    map_fixture,
)
from match_winning_tracking.storage.postgres import PostgresStore


def backfill_fixtures(
    store: PostgresStore,
    client: TheSportsDBClient,
    settings: Settings,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict[str, int]:
    effective_from, effective_to = resolve_backfill_window(
        settings, from_date=from_date, to_date=to_date
    )
    run_id = store.create_sync_run(
        "backfill-fixtures",
        {
            "league_id": settings.league.source_league_id,
            "from_date": effective_from.isoformat(),
            "to_date": effective_to.isoformat(),
        },
    )

    rows_written = 0
    empty_days = 0
    try:
        with store.connection() as connection:
            for current_day in iter_date_range(effective_from, effective_to):
                response = client.get_events_on_day(current_day, settings.league.source_league_id)
                store.store_raw_payload(connection, response)

                payloads = [
                    payload
                    for payload in response.items("events")
                    if str(payload.get("idLeague")) == str(settings.league.source_league_id)
                ]
                if not payloads:
                    empty_days += 1
                    continue

                fixture_records = [
                    map_fixture(payload, source_league_id=settings.league.source_league_id)
                    for payload in payloads
                ]
                alias_records = dedupe_alias_records(
                    [
                        alias
                        for payload in payloads
                        for alias in extract_team_aliases_from_fixture(payload)
                    ]
                )
                rows_written += store.upsert_fixtures(connection, fixture_records)
                rows_written += store.upsert_team_aliases(connection, alias_records)

            connection.commit()

        store.finish_sync_run(
            run_id, status="success", rows_written=rows_written, rows_skipped=empty_days
        )
        return {
            "date_count": count_days(effective_from, effective_to),
            "empty_days": empty_days,
            "rows_written": rows_written,
        }
    except Exception as exc:
        store.finish_sync_run(
            run_id,
            status="failed",
            rows_written=rows_written,
            rows_skipped=empty_days,
            error_text=str(exc),
        )
        raise


def resolve_backfill_window(
    settings: Settings,
    *,
    from_date: date | None,
    to_date: date | None,
) -> tuple[date, date]:
    effective_to = to_date or (date.today() + timedelta(days=settings.league.future_fixtures_days))
    effective_from = from_date or settings.league.backfill_start_date
    if effective_from > effective_to:
        raise ValueError("from_date must be on or before to_date")
    return effective_from, effective_to


def iter_date_range(start: date, end: date) -> Iterator[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def count_days(start: date, end: date) -> int:
    return (end - start).days + 1
