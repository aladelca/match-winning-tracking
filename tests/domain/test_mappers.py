from __future__ import annotations

from datetime import UTC, datetime

from match_winning_tracking.domain.mappers import (
    dedupe_alias_records,
    extract_team_aliases_from_fixture,
    map_fixture,
    map_standing,
)


def test_map_fixture_marks_finished_and_sets_winner() -> None:
    record = map_fixture(
        {
            "idEvent": "2204391",
            "idLeague": "4688",
            "strSeason": "2026",
            "dateEvent": "2026-04-19",
            "strTimestamp": "2026-04-19T20:00:00+00:00",
            "strStatus": "Match Finished",
            "idHomeTeam": "138311",
            "idAwayTeam": "138449",
            "strHomeTeam": "Alianza Lima",
            "strAwayTeam": "Universitario",
            "intHomeScore": "2",
            "intAwayScore": "1",
        },
        source_league_id=4688,
    )

    assert record["is_finished"] is True
    assert record["winner"] == "H"
    assert record["kickoff_at"] == datetime(2026, 4, 19, 20, 0, tzinfo=UTC)


def test_fixture_aliases_are_deduped() -> None:
    records = dedupe_alias_records(
        extract_team_aliases_from_fixture(
            {
                "idHomeTeam": "138311",
                "strHomeTeam": "Alianza Lima",
                "idAwayTeam": "138449",
                "strAwayTeam": "Universitario",
            }
        )
        + extract_team_aliases_from_fixture(
            {
                "idHomeTeam": "138311",
                "strHomeTeam": "Alianza Lima",
                "idAwayTeam": "138449",
                "strAwayTeam": "Universitario",
            }
        )
    )

    assert len(records) == 2


def test_map_standing_builds_snapshot_key() -> None:
    record = map_standing(
        {
            "idStanding": "1",
            "idTeam": "138311",
            "strTeam": "Alianza Lima",
            "intRank": "1",
            "intPlayed": "10",
            "intWin": "7",
            "intDraw": "2",
            "intLoss": "1",
            "intGoalsFor": "18",
            "intGoalsAgainst": "7",
            "intGoalDifference": "11",
            "intPoints": "23",
            "strForm": "WWDWW",
            "dateUpdated": "2026-04-21T18:00:00+00:00",
        },
        source_league_id=4688,
        season="2026",
        fetched_at=datetime(2026, 4, 21, 18, 5, tzinfo=UTC),
    )

    assert record["position"] == 1
    assert isinstance(record["snapshot_key"], str)
    assert len(record["snapshot_key"]) == 64
