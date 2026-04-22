from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from match_winning_tracking.storage.postgres import PostgresStore


@dataclass(frozen=True, slots=True)
class CompletedMatch:
    played_at: datetime
    goals_for: int
    goals_against: int


@dataclass(frozen=True, slots=True)
class TeamForm:
    matches_played: int
    points: int
    goals_for: int
    goals_against: int

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


def label_result(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "H"
    if home_score < away_score:
        return "A"
    return "D"


def compute_recent_form(
    matches: Sequence[CompletedMatch],
    *,
    before: datetime,
    limit: int = 5,
) -> TeamForm:
    recent_matches = sorted(
        (match for match in matches if match.played_at < before),
        key=lambda match: match.played_at,
        reverse=True,
    )[:limit]

    points = 0
    goals_for = 0
    goals_against = 0
    for match in recent_matches:
        goals_for += match.goals_for
        goals_against += match.goals_against
        if match.goals_for > match.goals_against:
            points += 3
        elif match.goals_for == match.goals_against:
            points += 1

    return TeamForm(
        matches_played=len(recent_matches),
        points=points,
        goals_for=goals_for,
        goals_against=goals_against,
    )


def compute_rest_days(previous_match_at: datetime | None, current_match_at: datetime) -> int | None:
    if previous_match_at is None:
        return None
    return (current_match_at.date() - previous_match_at.date()).days


def build_training_base(store: PostgresStore) -> int:
    return store.refresh_training_base()
