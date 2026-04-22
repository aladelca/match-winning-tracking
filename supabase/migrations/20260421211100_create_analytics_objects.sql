create schema if not exists analytics;

create materialized view if not exists analytics.training_matches_base as
with finished_fixtures as (
  select
    source_event_id,
    source_league_id,
    season,
    round_text,
    event_date as match_date,
    coalesce(kickoff_at, event_date::timestamp at time zone 'UTC') as match_timestamp,
    home_team_id,
    away_team_id,
    home_team_name,
    away_team_name,
    home_score,
    away_score,
    case
      when home_score > away_score then 'H'
      when home_score < away_score then 'A'
      else 'D'
    end as target_result
  from public.fixtures
  where is_finished is true
    and home_score is not null
    and away_score is not null
    and home_team_id is not null
    and away_team_id is not null
    and event_date is not null
),
team_results as (
  select
    source_event_id,
    match_date,
    match_timestamp,
    home_team_id as team_id,
    away_team_id as opponent_team_id,
    home_score as goals_for,
    away_score as goals_against,
    case
      when home_score > away_score then 3
      when home_score = away_score then 1
      else 0
    end as points
  from finished_fixtures
  union all
  select
    source_event_id,
    match_date,
    match_timestamp,
    away_team_id as team_id,
    home_team_id as opponent_team_id,
    away_score as goals_for,
    home_score as goals_against,
    case
      when away_score > home_score then 3
      when away_score = home_score then 1
      else 0
    end as points
  from finished_fixtures
)
select
  f.source_event_id,
  f.source_league_id,
  f.season,
  f.round_text,
  f.match_date,
  f.match_timestamp,
  f.home_team_id,
  f.away_team_id,
  f.home_team_name,
  f.away_team_name,
  f.target_result,
  coalesce(home_form.matches_played, 0) as home_matches_last_5,
  coalesce(away_form.matches_played, 0) as away_matches_last_5,
  coalesce(home_form.points, 0) as home_points_last_5,
  coalesce(away_form.points, 0) as away_points_last_5,
  coalesce(home_form.goals_for, 0) as home_goals_for_last_5,
  coalesce(home_form.goals_against, 0) as home_goals_against_last_5,
  coalesce(away_form.goals_for, 0) as away_goals_for_last_5,
  coalesce(away_form.goals_against, 0) as away_goals_against_last_5,
  coalesce(home_form.goals_for, 0) - coalesce(home_form.goals_against, 0) as home_goal_diff_last_5,
  coalesce(away_form.goals_for, 0) - coalesce(away_form.goals_against, 0) as away_goal_diff_last_5,
  home_rest.rest_days as home_rest_days,
  away_rest.rest_days as away_rest_days,
  coalesce(head_to_head.home_points, 0) as head_to_head_home_points_last_3,
  coalesce(head_to_head.away_points, 0) as head_to_head_away_points_last_3,
  home_table.position as home_standing_position_prior,
  away_table.position as away_standing_position_prior,
  home_table.points as home_standing_points_prior,
  away_table.points as away_standing_points_prior
from finished_fixtures f
left join lateral (
  select
    count(*) as matches_played,
    coalesce(sum(points), 0) as points,
    coalesce(sum(goals_for), 0) as goals_for,
    coalesce(sum(goals_against), 0) as goals_against
  from (
    select points, goals_for, goals_against
    from team_results
    where team_id = f.home_team_id
      and match_timestamp < f.match_timestamp
    order by match_timestamp desc
    limit 5
  ) recent_home
) home_form on true
left join lateral (
  select
    count(*) as matches_played,
    coalesce(sum(points), 0) as points,
    coalesce(sum(goals_for), 0) as goals_for,
    coalesce(sum(goals_against), 0) as goals_against
  from (
    select points, goals_for, goals_against
    from team_results
    where team_id = f.away_team_id
      and match_timestamp < f.match_timestamp
    order by match_timestamp desc
    limit 5
  ) recent_away
) away_form on true
left join lateral (
  select (f.match_date - max(match_date))::integer as rest_days
  from team_results
  where team_id = f.home_team_id
    and match_timestamp < f.match_timestamp
) home_rest on true
left join lateral (
  select (f.match_date - max(match_date))::integer as rest_days
  from team_results
  where team_id = f.away_team_id
    and match_timestamp < f.match_timestamp
) away_rest on true
left join lateral (
  select
    coalesce(sum(
      case
        when prior.home_team_id = f.home_team_id and prior.home_score > prior.away_score then 3
        when prior.away_team_id = f.home_team_id and prior.away_score > prior.home_score then 3
        when prior.home_score = prior.away_score then 1
        else 0
      end
    ), 0) as home_points,
    coalesce(sum(
      case
        when prior.home_team_id = f.away_team_id and prior.home_score > prior.away_score then 3
        when prior.away_team_id = f.away_team_id and prior.away_score > prior.home_score then 3
        when prior.home_score = prior.away_score then 1
        else 0
      end
    ), 0) as away_points
  from (
    select *
    from finished_fixtures prior
    where prior.match_timestamp < f.match_timestamp
      and (
        (prior.home_team_id = f.home_team_id and prior.away_team_id = f.away_team_id)
        or (prior.home_team_id = f.away_team_id and prior.away_team_id = f.home_team_id)
      )
    order by prior.match_timestamp desc
    limit 3
  ) prior
) head_to_head on true
left join lateral (
  select position, points
  from public.standings_snapshots
  where source_league_id = f.source_league_id
    and season = f.season
    and source_team_id = f.home_team_id
    and coalesce(standing_updated_at, fetched_at) < f.match_timestamp
  order by coalesce(standing_updated_at, fetched_at) desc
  limit 1
) home_table on true
left join lateral (
  select position, points
  from public.standings_snapshots
  where source_league_id = f.source_league_id
    and season = f.season
    and source_team_id = f.away_team_id
    and coalesce(standing_updated_at, fetched_at) < f.match_timestamp
  order by coalesce(standing_updated_at, fetched_at) desc
  limit 1
) away_table on true
with no data;

create index if not exists training_matches_base_event_idx
on analytics.training_matches_base (source_event_id);

create index if not exists training_matches_base_match_date_idx
on analytics.training_matches_base (match_date);
