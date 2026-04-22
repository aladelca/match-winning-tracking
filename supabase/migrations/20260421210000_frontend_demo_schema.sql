-- Minimal schema for the frontend MVP to function standalone.
--
-- Uses CREATE IF NOT EXISTS throughout so the upcoming data-foundation
-- migrations (which define the authoritative shape of these tables) can layer
-- additional columns with ALTER TABLE without colliding.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS public.teams (
    id           text PRIMARY KEY,
    name         text NOT NULL,
    short_name   text,
    logo_url     text
);

CREATE TABLE IF NOT EXISTS public.fixtures (
    id              text PRIMARY KEY,
    season          text NOT NULL,
    round           text,
    home_team_id    text NOT NULL REFERENCES public.teams(id),
    away_team_id    text NOT NULL REFERENCES public.teams(id),
    kickoff_at      timestamptz NOT NULL,
    home_score      integer,
    away_score      integer,
    status          text NOT NULL DEFAULT 'scheduled',
    venue           text
);

CREATE INDEX IF NOT EXISTS fixtures_kickoff_at_idx
    ON public.fixtures (kickoff_at);
CREATE INDEX IF NOT EXISTS fixtures_home_team_idx
    ON public.fixtures (home_team_id);
CREATE INDEX IF NOT EXISTS fixtures_away_team_idx
    ON public.fixtures (away_team_id);

CREATE TABLE IF NOT EXISTS analytics.training_matches_base (
    fixture_id                       text PRIMARY KEY,
    home_points_last_5               numeric,
    away_points_last_5               numeric,
    home_goal_diff_last_5            numeric,
    away_goal_diff_last_5            numeric,
    home_rest_days                   numeric,
    away_rest_days                   numeric,
    head_to_head_home_points_last_3  numeric
);
