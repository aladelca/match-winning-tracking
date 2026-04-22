"""Tests for POST /predict/sensitivity."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_sensitivity_empty_overrides_keeps_baseline_equal_to_modified(
    client: TestClient,
) -> None:
    response = client.post(
        "/predict/sensitivity",
        json={"fixture_id": "demo-001", "feature_overrides": {}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["baseline"]["probabilities"] == payload["modified"]["probabilities"]
    for key in ("home", "draw", "away"):
        assert abs(payload["deltas"][key]) < 1e-9


def test_sensitivity_override_changes_probabilities(client: TestClient) -> None:
    response = client.post(
        "/predict/sensitivity",
        json={
            "fixture_id": "demo-003",
            "feature_overrides": {"home_points_last_5": 15, "away_points_last_5": 0},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    # Overriding to strongly favor home should raise home probability.
    assert (
        payload["modified"]["probabilities"]["home"] > payload["baseline"]["probabilities"]["home"]
    )
    # Deltas must reconcile baseline + delta = modified.
    for key in ("home", "draw", "away"):
        baseline = payload["baseline"]["probabilities"][key]
        modified = payload["modified"]["probabilities"][key]
        delta = payload["deltas"][key]
        assert abs((baseline + delta) - modified) < 1e-9


def test_sensitivity_probabilities_sum_to_one(client: TestClient) -> None:
    response = client.post(
        "/predict/sensitivity",
        json={"fixture_id": "demo-001", "feature_overrides": {"home_rest_days": 0}},
    )
    payload = response.json()
    for branch in ("baseline", "modified"):
        probs = payload[branch]["probabilities"]
        assert abs(probs["home"] + probs["draw"] + probs["away"] - 1.0) < 1e-9


def test_sensitivity_out_of_range_returns_422(client: TestClient) -> None:
    response = client.post(
        "/predict/sensitivity",
        json={
            "fixture_id": "demo-001",
            "feature_overrides": {"home_points_last_5": 999},
        },
    )
    assert response.status_code == 422


def test_sensitivity_unknown_feature_returns_422(client: TestClient) -> None:
    response = client.post(
        "/predict/sensitivity",
        json={
            "fixture_id": "demo-001",
            "feature_overrides": {"not_a_feature": 5},
        },
    )
    assert response.status_code == 422


def test_sensitivity_unknown_fixture_returns_404(client: TestClient) -> None:
    response = client.post(
        "/predict/sensitivity",
        json={"fixture_id": "does-not-exist", "feature_overrides": {}},
    )
    assert response.status_code == 404
