"""Tests for POST /predict."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_predict_returns_probabilities_summing_to_one(client: TestClient) -> None:
    response = client.post("/predict", json={"fixture_id": "demo-001"})
    assert response.status_code == 200
    payload = response.json()
    probs = payload["probabilities"]
    assert abs(probs["home"] + probs["draw"] + probs["away"] - 1.0) < 1e-9
    assert payload["fixture_id"] == "demo-001"
    assert payload["model_version"] == "mock-v0"


def test_predict_includes_resolved_features(client: TestClient) -> None:
    response = client.post("/predict", json={"fixture_id": "demo-001"})
    payload = response.json()
    expected_keys = {
        "home_points_last_5",
        "away_points_last_5",
        "home_goal_diff_last_5",
        "away_goal_diff_last_5",
        "home_rest_days",
        "away_rest_days",
        "head_to_head_home_points_last_3",
    }
    assert set(payload["features"].keys()) == expected_keys


def test_predict_is_deterministic(client: TestClient) -> None:
    first = client.post("/predict", json={"fixture_id": "demo-003"}).json()
    second = client.post("/predict", json={"fixture_id": "demo-003"}).json()
    assert first["probabilities"] == second["probabilities"]


def test_predict_home_dominance_beats_away_dominance(client: TestClient) -> None:
    # demo-001 is a home-dominant fixture, demo-002 is away-dominant.
    home_dominant = client.post("/predict", json={"fixture_id": "demo-001"}).json()
    away_dominant = client.post("/predict", json={"fixture_id": "demo-002"}).json()
    assert home_dominant["probabilities"]["home"] > home_dominant["probabilities"]["away"]
    assert away_dominant["probabilities"]["away"] > away_dominant["probabilities"]["home"]


def test_predict_unknown_fixture_returns_404(client: TestClient) -> None:
    response = client.post("/predict", json={"fixture_id": "does-not-exist"})
    assert response.status_code == 404


def test_predict_unknown_model_returns_404(client: TestClient) -> None:
    response = client.post(
        "/predict",
        json={"fixture_id": "demo-001", "model_id": "not-a-real-model"},
    )
    assert response.status_code == 404
