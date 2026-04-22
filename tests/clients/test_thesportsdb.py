from __future__ import annotations

from collections.abc import Iterator

import httpx

from match_winning_tracking.clients.thesportsdb import (
    TheSportsDBClient,
    build_request_fingerprint,
)


def test_build_request_fingerprint_is_order_independent() -> None:
    fingerprint_a = build_request_fingerprint("eventsday.php", {"d": "2026-04-21", "l": "4688"})
    fingerprint_b = build_request_fingerprint("eventsday.php", {"l": "4688", "d": "2026-04-21"})

    assert fingerprint_a == fingerprint_b


def test_get_events_on_day_uses_expected_endpoint_and_params() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/123/eventsday.php")
        assert request.url.params["d"] == "2026-04-21"
        assert request.url.params["l"] == "4688"
        return httpx.Response(200, json={"events": [{"idEvent": "1"}]})

    client = TheSportsDBClient(
        api_key="123",
        base_url="https://www.thesportsdb.com/api/v1/json",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = client.get_events_on_day(__import__("datetime").date(2026, 4, 21), 4688)

    assert response.items("events")[0]["idEvent"] == "1"


def test_rate_limit_waits_between_calls(monkeypatch) -> None:
    sleep_calls: list[float] = []
    monotonic_values: Iterator[float] = iter([0.0, 0.2, 1.0])

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"leagues": [{"idLeague": "4688"}]})

    monkeypatch.setattr(
        "match_winning_tracking.clients.thesportsdb.time.monotonic",
        lambda: next(monotonic_values),
    )
    monkeypatch.setattr(
        "match_winning_tracking.clients.thesportsdb.time.sleep",
        lambda seconds: sleep_calls.append(seconds),
    )

    client = TheSportsDBClient(
        api_key="123",
        base_url="https://www.thesportsdb.com/api/v1/json",
        requests_per_minute=60,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    client.get_league(4688)
    client.get_league(4688)

    assert sleep_calls == [0.8]
