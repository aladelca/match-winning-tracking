from __future__ import annotations

from datetime import UTC, datetime

from match_winning_tracking.features.training_base import (
    CompletedMatch,
    compute_recent_form,
    compute_rest_days,
    label_result,
)


def test_label_result() -> None:
    assert label_result(2, 1) == "H"
    assert label_result(1, 2) == "A"
    assert label_result(0, 0) == "D"


def test_compute_recent_form_excludes_same_match_and_future_rows() -> None:
    before = datetime(2026, 4, 20, 18, 0, tzinfo=UTC)
    form = compute_recent_form(
        [
            CompletedMatch(datetime(2026, 4, 19, 18, 0, tzinfo=UTC), 2, 1),
            CompletedMatch(datetime(2026, 4, 12, 18, 0, tzinfo=UTC), 1, 1),
            CompletedMatch(datetime(2026, 4, 20, 18, 0, tzinfo=UTC), 5, 0),
            CompletedMatch(datetime(2026, 4, 21, 18, 0, tzinfo=UTC), 3, 1),
        ],
        before=before,
    )

    assert form.matches_played == 2
    assert form.points == 4
    assert form.goals_for == 3
    assert form.goals_against == 2


def test_compute_rest_days() -> None:
    previous_match_at = datetime(2026, 4, 15, 18, 0, tzinfo=UTC)
    current_match_at = datetime(2026, 4, 20, 20, 0, tzinfo=UTC)

    assert compute_rest_days(previous_match_at, current_match_at) == 5
    assert compute_rest_days(None, current_match_at) is None
