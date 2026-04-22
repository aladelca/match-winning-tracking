from __future__ import annotations

import os

import psycopg
import pytest

pytestmark = pytest.mark.integration


def test_local_supabase_schema_smoke() -> None:
    dsn = os.getenv("SUPABASE_DB_URL", "postgresql://postgres:postgres@127.0.0.1:55422/postgres")

    try:
        with psycopg.connect(dsn, connect_timeout=2) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                select table_schema, table_name
                from information_schema.tables
                where table_schema = 'public'
                  and table_name in ('leagues', 'fixtures', 'sync_runs')
                union all
                select schemaname as table_schema, matviewname as table_name
                from pg_matviews
                where schemaname = 'analytics'
                  and matviewname = 'training_matches_base'
                """
            )
            rows = {(schema, name) for schema, name in cursor.fetchall()}
    except psycopg.OperationalError:
        pytest.skip("Local Supabase is not reachable")

    assert ("public", "leagues") in rows
    assert ("public", "fixtures") in rows
    assert ("public", "sync_runs") in rows
    assert ("analytics", "training_matches_base") in rows
