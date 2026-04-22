-- Demo seed so the frontend shows meaningful data on a clean clone,
-- even if the ingestion pipeline has not been run yet.
-- Idempotent: ON CONFLICT DO NOTHING. Fixture IDs match the demo set hard-coded
-- in match_winning_tracking.api.services.feature_loader so the API returns
-- features for the same set when the DB is unreachable.

INSERT INTO public.teams (id, name, short_name) VALUES
    ('t-alianza',  'Alianza Lima',          'ALI'),
    ('t-universitario', 'Universitario de Deportes', 'UNI'),
    ('t-cristal', 'Sporting Cristal',      'CRI'),
    ('t-melgar',  'FBC Melgar',            'MEL'),
    ('t-cienciano', 'Cienciano',           'CIE'),
    ('t-cusco',   'Cusco FC',              'CUS')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.fixtures (
    id, season, round, home_team_id, away_team_id, kickoff_at, status, venue
) VALUES
    ('demo-001', '2026', 'Apertura - Fecha 10', 't-alianza',      't-cienciano',    now() + interval '1 day',   'scheduled', 'Estadio Alejandro Villanueva'),
    ('demo-002', '2026', 'Apertura - Fecha 10', 't-cusco',        't-cristal',      now() + interval '2 days',  'scheduled', 'Estadio Inca Garcilaso de la Vega'),
    ('demo-003', '2026', 'Apertura - Fecha 10', 't-melgar',       't-universitario',now() + interval '3 days',  'scheduled', 'Estadio Monumental de la UNSA'),
    ('demo-004', '2026', 'Apertura - Fecha 11', 't-universitario','t-cusco',        now() + interval '7 days',  'scheduled', 'Estadio Monumental'),
    ('demo-005', '2026', 'Apertura - Fecha 11', 't-cienciano',    't-cristal',      now() + interval '8 days',  'scheduled', 'Estadio Inca Garcilaso de la Vega'),
    ('demo-006', '2026', 'Apertura - Fecha 11', 't-melgar',       't-alianza',      now() + interval '9 days',  'scheduled', 'Estadio Monumental de la UNSA')
ON CONFLICT (id) DO NOTHING;

INSERT INTO analytics.training_matches_base (
    fixture_id,
    home_points_last_5, away_points_last_5,
    home_goal_diff_last_5, away_goal_diff_last_5,
    home_rest_days, away_rest_days,
    head_to_head_home_points_last_3
) VALUES
    ('demo-001', 10, 4, 6, -2, 6, 3, 6),
    ('demo-002',  5, 11, -1, 7, 4, 7, 3),
    ('demo-003',  7, 7, 1, 0, 5, 5, 4),
    ('demo-004',  9, 3, 4, -3, 7, 2, 7),
    ('demo-005',  2, 8, -5, 3, 3, 6, 1),
    ('demo-006',  6, 6, 2, 2, 4, 4, 5)
ON CONFLICT (fixture_id) DO NOTHING;
