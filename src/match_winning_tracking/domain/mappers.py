from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime, time
from typing import Any

TERMINAL_MATCH_STATUSES = {
    "aet",
    "after extra time",
    "after penalties",
    "finished",
    "ft",
    "full time",
    "match finished",
}


def map_league(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "thesportsdb",
        "source_league_id": required_int(payload.get("idLeague"), field_name="idLeague"),
        "name": payload.get("strLeague"),
        "alternate_name": payload.get("strLeagueAlternate"),
        "country": payload.get("strCountry"),
        "sport": payload.get("strSport"),
        "website": payload.get("strWebsite"),
        "badge_url": payload.get("strBadge"),
        "current_season": payload.get("strCurrentSeason"),
        "api_football_league_id": parse_int(payload.get("idAPIfootball")),
        "api_football_v3_league_id": parse_int(payload.get("idAPIfootballv3")),
        "payload": payload,
    }


def map_team(payload: dict[str, Any], *, source_league_id: int) -> dict[str, Any]:
    return {
        "source": "thesportsdb",
        "source_team_id": required_int(payload.get("idTeam"), field_name="idTeam"),
        "source_league_id": source_league_id,
        "name": payload.get("strTeam"),
        "short_name": payload.get("strTeamShort"),
        "alternate_name": payload.get("strAlternate"),
        "formed_year": parse_int(payload.get("intFormedYear")),
        "country": payload.get("strCountry"),
        "stadium": payload.get("strStadium"),
        "website": payload.get("strWebsite"),
        "badge_url": payload.get("strBadge"),
        "jersey_url": payload.get("strEquipment"),
        "fanart_url": payload.get("strFanart1"),
        "description": payload.get("strDescriptionEN"),
        "gender": payload.get("strGender"),
        "payload": payload,
    }


def map_player(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "thesportsdb",
        "source_player_id": required_int(payload.get("idPlayer"), field_name="idPlayer"),
        "source_team_id": parse_int(payload.get("idTeam")),
        "name": payload.get("strPlayer"),
        "alternate_name": payload.get("strPlayerAlternate"),
        "position": payload.get("strPosition"),
        "birth_date": parse_date(payload.get("dateBorn")),
        "nationality": payload.get("strNationality"),
        "height": payload.get("strHeight"),
        "weight": payload.get("strWeight"),
        "cutout_url": payload.get("strCutout"),
        "thumb_url": payload.get("strThumb"),
        "render_url": payload.get("strRender"),
        "team_name": payload.get("strTeam"),
        "is_current": True,
        "payload": payload,
    }


def map_fixture(payload: dict[str, Any], *, source_league_id: int) -> dict[str, Any]:
    home_score = parse_int(payload.get("intHomeScore"))
    away_score = parse_int(payload.get("intAwayScore"))
    status = stringify(payload.get("strStatus")) or "Unknown"
    event_date = parse_date(payload.get("dateEvent"))
    kickoff_at = parse_match_datetime(payload)
    is_finished = is_finished_status(status)

    return {
        "source": "thesportsdb",
        "source_event_id": required_int(payload.get("idEvent"), field_name="idEvent"),
        "source_league_id": source_league_id,
        "season": stringify(payload.get("strSeason"))
        or (event_date.isoformat()[:4] if event_date else None),
        "round_text": stringify(payload.get("strRound")) or stringify(payload.get("intRound")),
        "event_date": event_date,
        "kickoff_at": kickoff_at,
        "status": status,
        "home_team_id": parse_int(payload.get("idHomeTeam")),
        "away_team_id": parse_int(payload.get("idAwayTeam")),
        "home_team_name": payload.get("strHomeTeam"),
        "away_team_name": payload.get("strAwayTeam"),
        "home_score": home_score,
        "away_score": away_score,
        "home_penalties": parse_int(payload.get("intHomePenaltyScore")),
        "away_penalties": parse_int(payload.get("intAwayPenaltyScore")),
        "venue": payload.get("strVenue"),
        "country": payload.get("strCountry"),
        "is_finished": is_finished,
        "is_postponed": is_postponed_status(status),
        "winner": result_label(home_score, away_score) if is_finished else None,
        "video_url": payload.get("strVideo"),
        "thumb_url": payload.get("strThumb"),
        "banner_url": payload.get("strBanner"),
        "payload": payload,
    }


def map_standing(
    payload: dict[str, Any],
    *,
    source_league_id: int,
    season: str,
    fetched_at: datetime,
) -> dict[str, Any]:
    source_team_id = required_int(payload.get("idTeam"), field_name="idTeam")
    standing_updated_at = parse_datetime(payload.get("dateUpdated"))
    snapshot_anchor = standing_updated_at or fetched_at

    return {
        "snapshot_key": build_snapshot_key(
            "thesportsdb",
            str(source_league_id),
            season,
            str(source_team_id),
            snapshot_anchor.isoformat(),
        ),
        "source": "thesportsdb",
        "source_league_id": source_league_id,
        "season": season,
        "source_standing_id": parse_int(payload.get("idStanding")),
        "source_team_id": source_team_id,
        "team_name": payload.get("strTeam"),
        "position": parse_int(payload.get("intRank")),
        "matches_played": parse_int(payload.get("intPlayed")),
        "wins": parse_int(payload.get("intWin")),
        "draws": parse_int(payload.get("intDraw")),
        "losses": parse_int(payload.get("intLoss")),
        "goals_for": parse_int(payload.get("intGoalsFor")),
        "goals_against": parse_int(payload.get("intGoalsAgainst")),
        "goal_difference": parse_int(payload.get("intGoalDifference")),
        "points": parse_int(payload.get("intPoints")),
        "form": payload.get("strForm"),
        "standing_updated_at": standing_updated_at,
        "fetched_at": fetched_at,
        "payload": payload,
    }


def extract_team_aliases_from_team(payload: dict[str, Any]) -> list[dict[str, Any]]:
    source_team_id = required_int(payload.get("idTeam"), field_name="idTeam")
    candidates = [
        ("canonical", payload.get("strTeam")),
        ("short_name", payload.get("strTeamShort")),
        ("alternate_name", payload.get("strAlternate")),
    ]
    return build_alias_records(source_team_id, candidates)


def extract_team_aliases_from_fixture(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[tuple[int | None, list[tuple[str, Any]]]] = [
        (
            parse_int(payload.get("idHomeTeam")),
            [("fixture_home_name", payload.get("strHomeTeam"))],
        ),
        (
            parse_int(payload.get("idAwayTeam")),
            [("fixture_away_name", payload.get("strAwayTeam"))],
        ),
    ]

    records: list[dict[str, Any]] = []
    for source_team_id, alias_candidates in candidates:
        if source_team_id is None:
            continue
        records.extend(build_alias_records(source_team_id, alias_candidates))
    return records


def extract_team_aliases_from_standing(payload: dict[str, Any]) -> list[dict[str, Any]]:
    source_team_id = parse_int(payload.get("idTeam"))
    if source_team_id is None:
        return []
    return build_alias_records(source_team_id, [("standing_name", payload.get("strTeam"))])


def dedupe_alias_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, int, str], dict[str, Any]] = {}
    for record in records:
        deduped[
            (
                str(record["source"]),
                int(record["source_team_id"]),
                str(record["alias_normalized"]),
            )
        ] = record
    return list(deduped.values())


def build_alias_records(
    source_team_id: int,
    candidates: list[tuple[str, Any]],
) -> list[dict[str, Any]]:
    aliases: list[dict[str, Any]] = []
    for alias_type, raw_alias in candidates:
        alias = stringify(raw_alias)
        if alias is None:
            continue
        aliases.append(
            {
                "source": "thesportsdb",
                "source_team_id": source_team_id,
                "alias": alias,
                "alias_normalized": normalize_alias(alias),
                "alias_type": alias_type,
            }
        )
    return aliases


def normalize_alias(value: str) -> str:
    return " ".join(value.split()).casefold()


def result_label(home_score: int | None, away_score: int | None) -> str | None:
    if home_score is None or away_score is None:
        return None
    if home_score > away_score:
        return "H"
    if home_score < away_score:
        return "A"
    return "D"


def is_finished_status(status: str) -> bool:
    return status.casefold() in TERMINAL_MATCH_STATUSES


def is_postponed_status(status: str) -> bool:
    return status.casefold() in {"postponed", "cancelled", "abandoned"}


def parse_match_datetime(payload: dict[str, Any]) -> datetime | None:
    timestamp = parse_datetime(payload.get("strTimestamp"))
    if timestamp is not None:
        return timestamp

    event_date = parse_date(payload.get("dateEvent"))
    if event_date is None:
        return None

    raw_time = stringify(payload.get("strTime"))
    if raw_time is None:
        return datetime.combine(event_date, time.min, tzinfo=UTC)

    normalized = raw_time.replace("Z", "+00:00")
    try:
        parsed_time = time.fromisoformat(normalized)
    except ValueError:
        return datetime.combine(event_date, time.min, tzinfo=UTC)

    if parsed_time.tzinfo is None:
        parsed_time = parsed_time.replace(tzinfo=UTC)
    return datetime.combine(event_date, parsed_time)


def parse_datetime(value: Any) -> datetime | None:
    text = stringify(value)
    if text is None:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_date(value: Any) -> date | None:
    text = stringify(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    text = stringify(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def required_int(value: Any, *, field_name: str) -> int:
    parsed = parse_int(value)
    if parsed is None:
        raise ValueError(f"Expected integer value for {field_name}")
    return parsed


def stringify(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_snapshot_key(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
