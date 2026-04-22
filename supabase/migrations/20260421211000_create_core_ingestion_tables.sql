create or replace function public.set_current_timestamp_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists public.leagues (
  source text not null,
  source_league_id bigint not null,
  name text,
  alternate_name text,
  country text,
  sport text,
  website text,
  badge_url text,
  current_season text,
  api_football_league_id bigint,
  api_football_v3_league_id bigint,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (source, source_league_id)
);

create table if not exists public.league_seasons (
  source text not null,
  source_league_id bigint not null,
  season text not null,
  is_configured boolean not null default true,
  is_current boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (source, source_league_id, season),
  constraint league_seasons_league_fk
    foreign key (source, source_league_id)
    references public.leagues (source, source_league_id)
    on delete cascade
);

create table if not exists public.teams (
  source text not null,
  source_team_id bigint not null,
  source_league_id bigint not null,
  name text,
  short_name text,
  alternate_name text,
  formed_year integer,
  country text,
  stadium text,
  website text,
  badge_url text,
  jersey_url text,
  fanart_url text,
  description text,
  gender text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (source, source_team_id)
);

create table if not exists public.team_aliases (
  source text not null,
  source_team_id bigint not null,
  alias text not null,
  alias_normalized text not null,
  alias_type text not null,
  created_at timestamptz not null default now(),
  primary key (source, source_team_id, alias_normalized)
);

create table if not exists public.players (
  source text not null,
  source_player_id bigint not null,
  source_team_id bigint,
  name text,
  alternate_name text,
  position text,
  birth_date date,
  nationality text,
  height text,
  weight text,
  cutout_url text,
  thumb_url text,
  render_url text,
  team_name text,
  is_current boolean not null default true,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (source, source_player_id)
);

create table if not exists public.fixtures (
  source text not null,
  source_event_id bigint not null,
  source_league_id bigint not null,
  season text,
  round_text text,
  event_date date,
  kickoff_at timestamptz,
  status text,
  home_team_id bigint,
  away_team_id bigint,
  home_team_name text,
  away_team_name text,
  home_score integer,
  away_score integer,
  home_penalties integer,
  away_penalties integer,
  venue text,
  country text,
  is_finished boolean not null default false,
  is_postponed boolean not null default false,
  winner text,
  video_url text,
  thumb_url text,
  banner_url text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (source, source_event_id)
);

create table if not exists public.standings_snapshots (
  snapshot_key text not null,
  source text not null,
  source_league_id bigint not null,
  season text not null,
  source_standing_id bigint,
  source_team_id bigint not null,
  team_name text,
  position integer,
  matches_played integer,
  wins integer,
  draws integer,
  losses integer,
  goals_for integer,
  goals_against integer,
  goal_difference integer,
  points integer,
  form text,
  standing_updated_at timestamptz,
  fetched_at timestamptz not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (snapshot_key)
);

create table if not exists public.sync_runs (
  id bigint generated always as identity primary key,
  job_name text not null,
  params jsonb not null default '{}'::jsonb,
  status text not null default 'running',
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  rows_written integer not null default 0,
  rows_skipped integer not null default 0,
  error_text text
);

create table if not exists public.raw_thesportsdb_payloads (
  source text not null,
  request_fingerprint text not null,
  endpoint text not null,
  request_params jsonb not null default '{}'::jsonb,
  response_status integer,
  requested_at timestamptz not null,
  received_at timestamptz not null,
  payload jsonb,
  error_text text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (request_fingerprint)
);

create index if not exists fixtures_event_date_idx on public.fixtures (event_date);
create index if not exists fixtures_season_idx on public.fixtures (season);
create index if not exists fixtures_finished_idx on public.fixtures (is_finished, event_date);
create index if not exists fixtures_team_date_idx on public.fixtures (home_team_id, away_team_id, event_date);
create index if not exists standings_team_idx on public.standings_snapshots (source_team_id, season, fetched_at desc);
create index if not exists raw_payloads_endpoint_idx on public.raw_thesportsdb_payloads (endpoint, requested_at desc);

drop trigger if exists set_leagues_updated_at on public.leagues;
create trigger set_leagues_updated_at
before update on public.leagues
for each row execute function public.set_current_timestamp_updated_at();

drop trigger if exists set_league_seasons_updated_at on public.league_seasons;
create trigger set_league_seasons_updated_at
before update on public.league_seasons
for each row execute function public.set_current_timestamp_updated_at();

drop trigger if exists set_teams_updated_at on public.teams;
create trigger set_teams_updated_at
before update on public.teams
for each row execute function public.set_current_timestamp_updated_at();

drop trigger if exists set_players_updated_at on public.players;
create trigger set_players_updated_at
before update on public.players
for each row execute function public.set_current_timestamp_updated_at();

drop trigger if exists set_fixtures_updated_at on public.fixtures;
create trigger set_fixtures_updated_at
before update on public.fixtures
for each row execute function public.set_current_timestamp_updated_at();

drop trigger if exists set_standings_snapshots_updated_at on public.standings_snapshots;
create trigger set_standings_snapshots_updated_at
before update on public.standings_snapshots
for each row execute function public.set_current_timestamp_updated_at();

drop trigger if exists set_raw_thesportsdb_payloads_updated_at on public.raw_thesportsdb_payloads;
create trigger set_raw_thesportsdb_payloads_updated_at
before update on public.raw_thesportsdb_payloads
for each row execute function public.set_current_timestamp_updated_at();
