"""Tests for GET /models."""

from __future__ import annotations

from fastapi.testclient import TestClient

EXPECTED_FEATURE_KEYS = {
    "home_points_last_5",
    "away_points_last_5",
    "home_goal_diff_last_5",
    "away_goal_diff_last_5",
    "home_rest_days",
    "away_rest_days",
    "head_to_head_home_points_last_3",
}


def test_models_lists_mock_v0(client: TestClient) -> None:
    response = client.get("/models")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["models"]) == 1
    (model,) = payload["models"]
    assert model["id"] == "mock-v0"
    keys = {feature["key"] for feature in model["features"]}
    assert keys == EXPECTED_FEATURE_KEYS


def test_every_feature_has_schema_bounds(client: TestClient) -> None:
    response = client.get("/models")
    (model,) = response.json()["models"]
    for feature in model["features"]:
        assert feature["min"] < feature["max"]
        assert feature["min"] <= feature["default"] <= feature["max"]
        assert feature["label"]
