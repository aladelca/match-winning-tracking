INSERT_SYNC_RUN = """
insert into public.sync_runs (
    job_name,
    params,
    status
) values (
    %(job_name)s,
    %(params)s::jsonb,
    'running'
)
returning id
"""

COMPLETE_SYNC_RUN = """
update public.sync_runs
set
    status = %(status)s,
    finished_at = now(),
    rows_written = %(rows_written)s,
    rows_skipped = %(rows_skipped)s,
    error_text = %(error_text)s
where id = %(id)s
"""

UPSERT_RAW_PAYLOAD = """
insert into public.raw_thesportsdb_payloads (
    source,
    request_fingerprint,
    endpoint,
    request_params,
    response_status,
    requested_at,
    received_at,
    payload,
    error_text
) values (
    %(source)s,
    %(request_fingerprint)s,
    %(endpoint)s,
    %(request_params)s::jsonb,
    %(response_status)s,
    %(requested_at)s,
    %(received_at)s,
    %(payload)s::jsonb,
    %(error_text)s
)
on conflict (request_fingerprint) do update
set
    response_status = excluded.response_status,
    requested_at = excluded.requested_at,
    received_at = excluded.received_at,
    payload = excluded.payload,
    error_text = excluded.error_text
"""

UPSERT_LEAGUE = """
insert into public.leagues (
    source,
    source_league_id,
    name,
    alternate_name,
    country,
    sport,
    website,
    badge_url,
    current_season,
    api_football_league_id,
    api_football_v3_league_id,
    payload
) values (
    %(source)s,
    %(source_league_id)s,
    %(name)s,
    %(alternate_name)s,
    %(country)s,
    %(sport)s,
    %(website)s,
    %(badge_url)s,
    %(current_season)s,
    %(api_football_league_id)s,
    %(api_football_v3_league_id)s,
    %(payload)s::jsonb
)
on conflict (source, source_league_id) do update
set
    name = excluded.name,
    alternate_name = excluded.alternate_name,
    country = excluded.country,
    sport = excluded.sport,
    website = excluded.website,
    badge_url = excluded.badge_url,
    current_season = excluded.current_season,
    api_football_league_id = excluded.api_football_league_id,
    api_football_v3_league_id = excluded.api_football_v3_league_id,
    payload = excluded.payload
"""

UPSERT_LEAGUE_SEASON = """
insert into public.league_seasons (
    source,
    source_league_id,
    season,
    is_configured,
    is_current
) values (
    %(source)s,
    %(source_league_id)s,
    %(season)s,
    %(is_configured)s,
    %(is_current)s
)
on conflict (source, source_league_id, season) do update
set
    is_configured = excluded.is_configured,
    is_current = excluded.is_current
"""

UPSERT_TEAM = """
insert into public.teams (
    source,
    source_team_id,
    source_league_id,
    name,
    short_name,
    alternate_name,
    formed_year,
    country,
    stadium,
    website,
    badge_url,
    jersey_url,
    fanart_url,
    description,
    gender,
    payload
) values (
    %(source)s,
    %(source_team_id)s,
    %(source_league_id)s,
    %(name)s,
    %(short_name)s,
    %(alternate_name)s,
    %(formed_year)s,
    %(country)s,
    %(stadium)s,
    %(website)s,
    %(badge_url)s,
    %(jersey_url)s,
    %(fanart_url)s,
    %(description)s,
    %(gender)s,
    %(payload)s::jsonb
)
on conflict (source, source_team_id) do update
set
    source_league_id = excluded.source_league_id,
    name = excluded.name,
    short_name = excluded.short_name,
    alternate_name = excluded.alternate_name,
    formed_year = excluded.formed_year,
    country = excluded.country,
    stadium = excluded.stadium,
    website = excluded.website,
    badge_url = excluded.badge_url,
    jersey_url = excluded.jersey_url,
    fanart_url = excluded.fanart_url,
    description = excluded.description,
    gender = excluded.gender,
    payload = excluded.payload
"""

UPSERT_TEAM_ALIAS = """
insert into public.team_aliases (
    source,
    source_team_id,
    alias,
    alias_normalized,
    alias_type
) values (
    %(source)s,
    %(source_team_id)s,
    %(alias)s,
    %(alias_normalized)s,
    %(alias_type)s
)
on conflict (source, source_team_id, alias_normalized) do update
set
    alias = excluded.alias,
    alias_type = excluded.alias_type
"""

UPSERT_PLAYER = """
insert into public.players (
    source,
    source_player_id,
    source_team_id,
    name,
    alternate_name,
    position,
    birth_date,
    nationality,
    height,
    weight,
    cutout_url,
    thumb_url,
    render_url,
    team_name,
    is_current,
    payload
) values (
    %(source)s,
    %(source_player_id)s,
    %(source_team_id)s,
    %(name)s,
    %(alternate_name)s,
    %(position)s,
    %(birth_date)s,
    %(nationality)s,
    %(height)s,
    %(weight)s,
    %(cutout_url)s,
    %(thumb_url)s,
    %(render_url)s,
    %(team_name)s,
    %(is_current)s,
    %(payload)s::jsonb
)
on conflict (source, source_player_id) do update
set
    source_team_id = excluded.source_team_id,
    name = excluded.name,
    alternate_name = excluded.alternate_name,
    position = excluded.position,
    birth_date = excluded.birth_date,
    nationality = excluded.nationality,
    height = excluded.height,
    weight = excluded.weight,
    cutout_url = excluded.cutout_url,
    thumb_url = excluded.thumb_url,
    render_url = excluded.render_url,
    team_name = excluded.team_name,
    is_current = excluded.is_current,
    payload = excluded.payload
"""

MARK_TEAM_PLAYERS_NOT_CURRENT = """
update public.players
set
    is_current = false,
    updated_at = now()
where source = %(source)s
  and source_team_id = %(source_team_id)s
"""

UPSERT_FIXTURE = """
insert into public.fixtures (
    source,
    source_event_id,
    source_league_id,
    season,
    round_text,
    event_date,
    kickoff_at,
    status,
    home_team_id,
    away_team_id,
    home_team_name,
    away_team_name,
    home_score,
    away_score,
    home_penalties,
    away_penalties,
    venue,
    country,
    is_finished,
    is_postponed,
    winner,
    video_url,
    thumb_url,
    banner_url,
    payload
) values (
    %(source)s,
    %(source_event_id)s,
    %(source_league_id)s,
    %(season)s,
    %(round_text)s,
    %(event_date)s,
    %(kickoff_at)s,
    %(status)s,
    %(home_team_id)s,
    %(away_team_id)s,
    %(home_team_name)s,
    %(away_team_name)s,
    %(home_score)s,
    %(away_score)s,
    %(home_penalties)s,
    %(away_penalties)s,
    %(venue)s,
    %(country)s,
    %(is_finished)s,
    %(is_postponed)s,
    %(winner)s,
    %(video_url)s,
    %(thumb_url)s,
    %(banner_url)s,
    %(payload)s::jsonb
)
on conflict (source, source_event_id) do update
set
    source_league_id = excluded.source_league_id,
    season = excluded.season,
    round_text = excluded.round_text,
    event_date = excluded.event_date,
    kickoff_at = excluded.kickoff_at,
    status = excluded.status,
    home_team_id = excluded.home_team_id,
    away_team_id = excluded.away_team_id,
    home_team_name = excluded.home_team_name,
    away_team_name = excluded.away_team_name,
    home_score = excluded.home_score,
    away_score = excluded.away_score,
    home_penalties = excluded.home_penalties,
    away_penalties = excluded.away_penalties,
    venue = excluded.venue,
    country = excluded.country,
    is_finished = excluded.is_finished,
    is_postponed = excluded.is_postponed,
    winner = excluded.winner,
    video_url = excluded.video_url,
    thumb_url = excluded.thumb_url,
    banner_url = excluded.banner_url,
    payload = excluded.payload
"""

UPSERT_STANDING_SNAPSHOT = """
insert into public.standings_snapshots (
    snapshot_key,
    source,
    source_league_id,
    season,
    source_standing_id,
    source_team_id,
    team_name,
    position,
    matches_played,
    wins,
    draws,
    losses,
    goals_for,
    goals_against,
    goal_difference,
    points,
    form,
    standing_updated_at,
    fetched_at,
    payload
) values (
    %(snapshot_key)s,
    %(source)s,
    %(source_league_id)s,
    %(season)s,
    %(source_standing_id)s,
    %(source_team_id)s,
    %(team_name)s,
    %(position)s,
    %(matches_played)s,
    %(wins)s,
    %(draws)s,
    %(losses)s,
    %(goals_for)s,
    %(goals_against)s,
    %(goal_difference)s,
    %(points)s,
    %(form)s,
    %(standing_updated_at)s,
    %(fetched_at)s,
    %(payload)s::jsonb
)
on conflict (snapshot_key) do update
set
    position = excluded.position,
    matches_played = excluded.matches_played,
    wins = excluded.wins,
    draws = excluded.draws,
    losses = excluded.losses,
    goals_for = excluded.goals_for,
    goals_against = excluded.goals_against,
    goal_difference = excluded.goal_difference,
    points = excluded.points,
    form = excluded.form,
    standing_updated_at = excluded.standing_updated_at,
    fetched_at = excluded.fetched_at,
    payload = excluded.payload
"""

SELECT_CURRENT_TEAMS = """
select source_team_id
from public.teams
where source = %(source)s
  and source_league_id = %(source_league_id)s
order by name
"""

REFRESH_TRAINING_BASE = """
refresh materialized view analytics.training_matches_base
"""

COUNT_TRAINING_BASE = """
select count(*) as count
from analytics.training_matches_base
"""
