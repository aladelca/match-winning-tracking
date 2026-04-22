from __future__ import annotations

import json
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import psycopg
from psycopg.rows import dict_row

from match_winning_tracking.storage import sql

if TYPE_CHECKING:
    from match_winning_tracking.clients.thesportsdb import ApiResponse


JsonMapping = Mapping[str, Any]


class PostgresStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as connection:
            yield connection

    def create_sync_run(self, job_name: str, params: JsonMapping) -> int:
        with self.connection() as connection:
            row = self.fetch_one(
                connection,
                sql.INSERT_SYNC_RUN,
                {"job_name": job_name, "params": dump_json(params)},
            )
            connection.commit()
        return int(row["id"])

    def finish_sync_run(
        self,
        run_id: int,
        *,
        status: str,
        rows_written: int,
        rows_skipped: int = 0,
        error_text: str | None = None,
    ) -> None:
        with self.connection() as connection:
            self.execute(
                connection,
                sql.COMPLETE_SYNC_RUN,
                {
                    "id": run_id,
                    "status": status,
                    "rows_written": rows_written,
                    "rows_skipped": rows_skipped,
                    "error_text": error_text,
                },
            )
            connection.commit()

    def store_raw_payload(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        response: ApiResponse,
        *,
        source: str = "thesportsdb",
        error_text: str | None = None,
    ) -> None:
        self.execute(
            connection,
            sql.UPSERT_RAW_PAYLOAD,
            {
                "source": source,
                "request_fingerprint": response.request_fingerprint,
                "endpoint": response.endpoint,
                "request_params": dump_json(dict(response.params)),
                "response_status": response.status_code,
                "requested_at": response.requested_at,
                "received_at": response.received_at,
                "payload": dump_json(response.payload),
                "error_text": error_text,
            },
        )

    def execute(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        query: str,
        params: JsonMapping | None = None,
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(query, params)

    def execute_many(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        query: str,
        rows: Sequence[JsonMapping],
    ) -> int:
        if not rows:
            return 0
        with connection.cursor() as cursor:
            cursor.executemany(query, rows)
        return len(rows)

    def fetch_all(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        query: str,
        params: JsonMapping | None = None,
    ) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        return rows

    def fetch_one(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        query: str,
        params: JsonMapping | None = None,
    ) -> dict[str, Any]:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
        if row is None:
            raise LookupError("Expected at least one row")
        return row

    def upsert_league(
        self, connection: psycopg.Connection[dict[str, Any]], record: JsonMapping
    ) -> int:
        self.execute(
            connection, sql.UPSERT_LEAGUE, dict(record, payload=dump_json(record["payload"]))
        )
        return 1

    def upsert_league_seasons(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        records: Sequence[JsonMapping],
    ) -> int:
        return self.execute_many(connection, sql.UPSERT_LEAGUE_SEASON, records)

    def upsert_teams(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        records: Sequence[JsonMapping],
    ) -> int:
        prepared = [dict(record, payload=dump_json(record["payload"])) for record in records]
        return self.execute_many(connection, sql.UPSERT_TEAM, prepared)

    def upsert_team_aliases(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        records: Sequence[JsonMapping],
    ) -> int:
        return self.execute_many(connection, sql.UPSERT_TEAM_ALIAS, records)

    def upsert_players(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        *,
        team_id: int,
        source: str,
        records: Sequence[JsonMapping],
    ) -> int:
        self.execute(
            connection,
            sql.MARK_TEAM_PLAYERS_NOT_CURRENT,
            {"source": source, "source_team_id": team_id},
        )
        prepared = [dict(record, payload=dump_json(record["payload"])) for record in records]
        return self.execute_many(connection, sql.UPSERT_PLAYER, prepared)

    def upsert_fixtures(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        records: Sequence[JsonMapping],
    ) -> int:
        prepared = [dict(record, payload=dump_json(record["payload"])) for record in records]
        return self.execute_many(connection, sql.UPSERT_FIXTURE, prepared)

    def upsert_standings(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        records: Sequence[JsonMapping],
    ) -> int:
        prepared = [dict(record, payload=dump_json(record["payload"])) for record in records]
        return self.execute_many(connection, sql.UPSERT_STANDING_SNAPSHOT, prepared)

    def get_current_team_ids(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        *,
        source: str,
        source_league_id: int,
    ) -> list[int]:
        rows = self.fetch_all(
            connection,
            sql.SELECT_CURRENT_TEAMS,
            {"source": source, "source_league_id": source_league_id},
        )
        return [int(row["source_team_id"]) for row in rows]

    def refresh_training_base(self) -> int:
        with self.connection() as connection:
            self.execute(connection, sql.REFRESH_TRAINING_BASE)
            row = self.fetch_one(connection, sql.COUNT_TRAINING_BASE)
            connection.commit()
        return int(row["count"])


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
