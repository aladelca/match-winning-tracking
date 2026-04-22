"""Deterministic heuristic used in place of the real predictive model.

The intent is to stay contract-compatible with the eventual real model while
being fully reproducible. No randomness is used: same feature dict always
yields the same probability triplet.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from match_winning_tracking.api.schemas import Probabilities

HOME_ADVANTAGE = 1.0
TEMPERATURE = 3.0
DRAW_LOGIT = 0.35

# Clamp to avoid 0.0/1.0 degenerate outputs so consumers always see a 3-way split.
MIN_PROB = 0.01


def _contribution(features: Mapping[str, float]) -> float:
    points_diff = features.get("home_points_last_5", 0.0) - features.get("away_points_last_5", 0.0)
    goal_diff = features.get("home_goal_diff_last_5", 0.0) - features.get(
        "away_goal_diff_last_5", 0.0
    )
    rest_diff = features.get("home_rest_days", 0.0) - features.get("away_rest_days", 0.0)
    h2h = features.get("head_to_head_home_points_last_3", 0.0) - 4.5
    return 0.25 * points_diff + 0.20 * goal_diff + 0.10 * rest_diff + 0.15 * h2h + HOME_ADVANTAGE


def predict(features: Mapping[str, float]) -> Probabilities:
    """Return calibrated-looking probabilities from a feature dict."""

    score = _contribution(features) / TEMPERATURE
    logits = (score, DRAW_LOGIT, -score)
    max_logit = max(logits)
    exps = tuple(math.exp(x - max_logit) for x in logits)
    total = sum(exps)
    raw = tuple(value / total for value in exps)

    home, draw, away = (max(value, MIN_PROB) for value in raw)
    normalizer = home + draw + away
    return Probabilities(
        home=home / normalizer,
        draw=draw / normalizer,
        away=away / normalizer,
    )
