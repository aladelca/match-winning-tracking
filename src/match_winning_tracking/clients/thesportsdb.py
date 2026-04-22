from __future__ import annotations

import hashlib
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import urlencode

import httpx


class TheSportsDBError(RuntimeError):
    """Raised when TheSportsDB returns an invalid or unsuccessful response."""


@dataclass(frozen=True, slots=True)
class ApiResponse:
    endpoint: str
    params: Mapping[str, str]
    requested_at: datetime
    received_at: datetime
    status_code: int
    payload: dict[str, Any]
    request_fingerprint: str

    def items(self, key: str) -> list[dict[str, Any]]:
        value = self.payload.get(key)
        if value is None:
            return []
        if not isinstance(value, list):
            raise TheSportsDBError(
                f"Expected list payload at key '{key}' for endpoint {self.endpoint}"
            )
        return [item for item in value if isinstance(item, dict)]


def build_request_fingerprint(endpoint: str, params: Mapping[str, str]) -> str:
    encoded_params = urlencode(sorted((key, value) for key, value in params.items()))
    return hashlib.sha256(f"{endpoint}?{encoded_params}".encode()).hexdigest()


class TheSportsDBClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        requests_per_minute: int = 25,
        timeout_seconds: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._minimum_interval_seconds = 60.0 / requests_per_minute
        self._last_request_started_at: float | None = None
        self._owns_client = http_client is None
        self._http_client = http_client or httpx.Client(timeout=timeout_seconds)

    def __enter__(self) -> TheSportsDBClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._http_client.close()

    def get_league(self, league_id: int) -> ApiResponse:
        return self.request_json("lookupleague.php", {"id": str(league_id)})

    def get_teams_by_league_name(self, league_name: str) -> ApiResponse:
        return self.request_json("search_all_teams.php", {"l": league_name})

    def get_players_for_team(self, team_id: int) -> ApiResponse:
        return self.request_json("lookup_all_players.php", {"id": str(team_id)})

    def get_events_on_day(self, event_date: date, league_id: int) -> ApiResponse:
        return self.request_json(
            "eventsday.php",
            {
                "d": event_date.isoformat(),
                "l": str(league_id),
            },
        )

    def get_standings(self, league_id: int, season: str) -> ApiResponse:
        return self.request_json(
            "lookuptable.php",
            {
                "l": str(league_id),
                "s": season,
            },
        )

    def request_json(self, endpoint: str, params: Mapping[str, str]) -> ApiResponse:
        self._respect_rate_limit()
        requested_at = datetime.now(tz=UTC)
        response = self._http_client.get(self._build_url(endpoint), params=dict(params))
        received_at = datetime.now(tz=UTC)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TheSportsDBError(
                f"TheSportsDB request failed for {endpoint}: {exc.response.status_code}"
            ) from exc

        payload = response.json()
        if not isinstance(payload, dict):
            raise TheSportsDBError(f"Unexpected payload type for {endpoint}: {type(payload)!r}")

        return ApiResponse(
            endpoint=endpoint,
            params=dict(params),
            requested_at=requested_at,
            received_at=received_at,
            status_code=response.status_code,
            payload=payload,
            request_fingerprint=build_request_fingerprint(endpoint, params),
        )

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{self.api_key}/{endpoint}"

    def _respect_rate_limit(self) -> None:
        if self._last_request_started_at is None:
            self._last_request_started_at = time.monotonic()
            return

        elapsed = time.monotonic() - self._last_request_started_at
        remaining = self._minimum_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_started_at = time.monotonic()
