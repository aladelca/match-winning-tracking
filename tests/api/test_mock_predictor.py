"""Direct unit tests for the deterministic mock predictor."""

from __future__ import annotations

from match_winning_tracking.api.services.mock_predictor import predict


def _features(**overrides: float) -> dict[str, float]:
    base = {
        "home_points_last_5": 7,
        "away_points_last_5": 7,
        "home_goal_diff_last_5": 0,
        "away_goal_diff_last_5": 0,
        "home_rest_days": 5,
        "away_rest_days": 5,
        "head_to_head_home_points_last_3": 4,
    }
    base.update(overrides)
    return base


def test_predict_is_deterministic() -> None:
    first = predict(_features())
    second = predict(_features())
    assert first == second


def test_more_home_points_increases_home_probability() -> None:
    low = predict(_features(home_points_last_5=2))
    high = predict(_features(home_points_last_5=14))
    assert high.home > low.home
    assert high.away < low.away


def test_more_away_points_increases_away_probability() -> None:
    low = predict(_features(away_points_last_5=2))
    high = predict(_features(away_points_last_5=14))
    assert high.away > low.away
    assert high.home < low.home


def test_home_rest_advantage_tilts_toward_home() -> None:
    deficit = predict(_features(home_rest_days=0, away_rest_days=10))
    surplus = predict(_features(home_rest_days=10, away_rest_days=0))
    assert surplus.home > deficit.home


def test_probabilities_never_degenerate_to_zero() -> None:
    extreme = predict(
        _features(
            home_points_last_5=15,
            away_points_last_5=0,
            home_goal_diff_last_5=10,
            away_goal_diff_last_5=-10,
            head_to_head_home_points_last_3=9,
        )
    )
    assert extreme.away > 0
    assert extreme.draw > 0
    assert extreme.home < 1
