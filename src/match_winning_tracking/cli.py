from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from match_winning_tracking.clients.thesportsdb import TheSportsDBClient
from match_winning_tracking.config import DEFAULT_CONFIG_PATH, Settings, load_settings
from match_winning_tracking.features.training_base import build_training_base
from match_winning_tracking.ingestion.fixtures_backfill import backfill_fixtures
from match_winning_tracking.ingestion.players_sync import sync_players
from match_winning_tracking.ingestion.reference_sync import sync_reference
from match_winning_tracking.ingestion.standings_sync import sync_standings
from match_winning_tracking.storage.postgres import PostgresStore


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = load_settings(args.config)
    store = PostgresStore(settings.supabase_db_url)

    with build_client(settings) as client:
        if args.command == "sync-reference":
            result = sync_reference(store, client, settings)
        elif args.command == "sync-players":
            result = sync_players(store, client, settings)
        elif args.command == "backfill-fixtures":
            result = backfill_fixtures(
                store,
                client,
                settings,
                from_date=parse_optional_date(args.from_date),
                to_date=parse_optional_date(args.to_date),
            )
        elif args.command == "sync-standings":
            result = sync_standings(store, client, settings, seasons=args.season)
        elif args.command == "build-training-base":
            row_count = build_training_base(store)
            result = {"training_rows": row_count}
        else:
            raise ValueError(f"Unsupported command: {args.command}")

    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="match-winning-tracking")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the league configuration YAML file.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("sync-reference")
    subparsers.add_parser("sync-players")

    backfill = subparsers.add_parser("backfill-fixtures")
    backfill.add_argument("--from", dest="from_date")
    backfill.add_argument("--to", dest="to_date")

    standings = subparsers.add_parser("sync-standings")
    standings.add_argument("--season", action="append", help="Season to sync, e.g. 2026")

    subparsers.add_parser("build-training-base")
    return parser


def build_client(settings: Settings) -> TheSportsDBClient:
    return TheSportsDBClient(
        api_key=settings.thesportsdb_api_key,
        base_url=settings.thesportsdb_base_url,
    )


def parse_optional_date(raw_value: str | None) -> date | None:
    if raw_value is None:
        return None
    return date.fromisoformat(raw_value)


if __name__ == "__main__":
    raise SystemExit(main())
