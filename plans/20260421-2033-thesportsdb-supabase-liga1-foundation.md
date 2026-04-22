# Base de Datos Liga 1 con TheSportsDB y Supabase

## Goal

- Bootstrapping this repository to ingest Liga 1 Peru data from TheSportsDB into Supabase, persist normalized and raw records, and expose an ML-ready base dataset for later result prediction work.
- Prioritize a no-cost data path that is resilient to free-tier limits and can be refreshed incrementally after the initial backfill.

## Request Snapshot

- User request: "Creo que vamos por TheSportsDB y veamos hasta donde podemos llenar la data, para trabajar con bases de datos, utiliza supabase. Crea un plan detallado para poder implementar esto."
- Owner or issue: `match-winning-tracking-rql`
- Plan file: `plans/20260421-2033-thesportsdb-supabase-liga1-foundation.md`

## Current State

- The repo is effectively empty. Inspected files: `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`.
- There is no existing application code, no `pyproject.toml`, no `supabase/` directory, no tests, and no Python lint/type-check configuration in the repo.
- Local instructions require using `bd` for task tracking. There were no open issues, so `match-winning-tracking-rql` was created and claimed for this planning work.
- Available local tooling was verified from the repo root:
  - `python3` -> `Python 3.12.0`
  - `uv` available at `/Users/adrianalarcon/.local/bin/uv`
  - `supabase` CLI available at `/opt/homebrew/bin/supabase`
  - `ruff` and `mypy` are installed globally
- Because there is no existing stack to preserve and the end goal is machine learning, the implementation should standardize on Python plus `uv` for dependency and runner management.

## Findings

- `lookupleague.php?id=4688` returns the target competition metadata for Liga 1 Peru, including `idLeague=4688`, `idAPIfootball=8006`, `idAPIfootballv3=281`, `strCurrentSeason=2026`, and official website `liga1.pe`.
- `search_all_teams.php?l=Peruvian_Primera_Division` returns real current league teams for Peru, including `Alianza Lima` with `idTeam=138311`. This endpoint is viable for the team dimension.
- `lookup_all_players.php?id=138311` returns a current squad payload for Alianza Lima. Current roster ingestion is viable.
- `lookuptable.php?l=4688&s=2026` returns standings rows for the league and includes `dateUpdated`, `strForm`, and points/goals columns. This is suitable for snapshot storage.
- `lookuptable.php?l=4688&s=2025` returned rows with `intPlayed=18`, which suggests stage-specific or tournament-phase semantics rather than a guaranteed season-wide aggregate table. Standings should be stored as snapshots, not treated as the canonical historical truth for feature generation.
- `eventsseason.php?id=4688&s=2025` and `eventsseason.php?id=4688&s=2026` return valid fixture records, but the free tier is capped at 15 results per call. This endpoint cannot be the primary source for a full historical season backfill.
- `search_all_seasons.php?id=4688` returned only five seasons (`2020` to `2024`) on the demo key, while direct season calls and the league page indicate newer seasons exist. The seasons endpoint cannot be treated as a complete catalog under the free tier.
- `eventsday.php?d=2026-04-19&l=4688` returned all sampled Liga 1 matches for that date, and `eventsday.php?d=2025-02-09&l=4688` returned five matches for that date. Daily backfill via `eventsday` is the safest no-cost path around the `eventsseason` cap.
- `lookupeventstats.php?id=2204391` and `lookuplineup.php?id=2204391` both returned `null` for the sampled event. Event-level stats and lineups are not reliable enough to make phase 1 depend on them.
- `lookupteam.php?id=138311` returned inconsistent data on the demo key during sampling. Team detail ingestion should not depend on `lookupteam.php` until endpoint behavior is revalidated with the exact team IDs in implementation.
- TheSportsDB official docs confirm:
  - free V1 API with key `123`
  - free rate limit of 30 requests per minute
  - V2 is premium only
  - website scraping is discouraged; official endpoints should be used instead

## Scope

### In scope

- Initialize a Python project with `uv` and repository-level `ruff`, `mypy`, and `pytest` configuration.
- Initialize Supabase locally and define SQL migrations for normalized ingestion tables plus an analytics schema.
- Implement TheSportsDB V1 client wrappers for the endpoints that sampled correctly:
  - `lookupleague.php`
  - `search_all_teams.php`
  - `lookup_all_players.php`
  - `eventsday.php`
  - `lookuptable.php`
- Implement idempotent ingestion workflows for:
  - league metadata
  - current teams
  - current rosters
  - daily fixture backfill from `2020-01-01` through today, plus short-horizon future fixtures
  - standings snapshots for active and explicitly requested seasons
- Store both normalized records and raw JSON payloads for audit/debugging.
- Build an ML-ready base dataset from historical fixtures using only pre-match information that can be derived without future leakage.
- Add CLI commands and documentation so the dataset can be rebuilt and refreshed from the repo root.

### Out of scope

- Model training, hyperparameter tuning, model registry, or prediction serving.
- Frontend/dashboard work.
- Alternative sources such as API-Football, FBref, or official Liga 1 scraping.
- Historical lineup/statistics enrichment from `lookuplineup.php` or `lookupeventstats.php` until endpoint quality is revalidated.
- Historical player rosters by season. Phase 1 only needs current squad ingestion because feature engineering will rely on fixtures first.

## File Plan

| Path | Action | Details |
| --- | --- | --- |
| `README.md` | modify | Document project purpose, local setup, Supabase commands, ingestion commands, and known TheSportsDB free-tier caveats. |
| `.env.example` | create | Declare `THESPORTSDB_API_KEY`, `SUPABASE_DB_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `LIGA1_LEAGUE_ID`, `BACKFILL_START_DATE`, and refresh window settings. |
| `pyproject.toml` | create | Define Python package metadata, runtime/dev dependencies, `uv` scripts, and `ruff`/`mypy`/`pytest` configuration. |
| `config/leagues.yml` | create | Store source configuration for Liga 1 Peru (`idLeague=4688`, start date, refresh windows, optional season overrides). |
| `supabase/config.toml` | create | Initialize local Supabase project config. |
| `supabase/seed.sql` | create | Optional seed for source metadata defaults if that simplifies local development. |
| `supabase/migrations/<ts>_create_core_ingestion_tables.sql` | create | Create `public.leagues`, `public.league_seasons`, `public.teams`, `public.team_aliases`, `public.players`, `public.fixtures`, `public.standings_snapshots`, `public.sync_runs`, and `public.raw_thesportsdb_payloads`. |
| `supabase/migrations/<ts>_create_analytics_objects.sql` | create | Create `analytics` schema and `analytics.training_matches_base` view or materialized view. |
| `src/match_winning_tracking/__init__.py` | create | Package root. |
| `src/match_winning_tracking/config.py` | create | Typed settings loader from environment and static league config. |
| `src/match_winning_tracking/clients/thesportsdb.py` | create | Implement rate-limited client for supported V1 endpoints and raw response capture keys. |
| `src/match_winning_tracking/storage/postgres.py` | create | Manage Postgres connections, transactions, and batch upsert helpers against Supabase Postgres. |
| `src/match_winning_tracking/storage/sql.py` | create | Hold parameterized SQL statements or helper builders for idempotent inserts/upserts. |
| `src/match_winning_tracking/domain/mappers.py` | create | Map raw payloads into normalized league, team, player, fixture, alias, and standings records. |
| `src/match_winning_tracking/ingestion/reference_sync.py` | create | Sync league metadata, current teams, and discovered league seasons. |
| `src/match_winning_tracking/ingestion/players_sync.py` | create | Load current roster data per current team. |
| `src/match_winning_tracking/ingestion/fixtures_backfill.py` | create | Iterate date by date using `eventsday.php`, persist fixtures and raw payloads, and support resume/idempotency. |
| `src/match_winning_tracking/ingestion/standings_sync.py` | create | Snapshot current or requested-season standings into `public.standings_snapshots`. |
| `src/match_winning_tracking/features/training_base.py` | create | Generate leakage-safe base features from finished fixtures and optional latest-prior standings snapshots. |
| `src/match_winning_tracking/cli.py` | create | Expose CLI commands such as `sync-reference`, `sync-players`, `backfill-fixtures`, `sync-standings`, and `build-training-base`. |
| `tests/clients/test_thesportsdb.py` | create | Unit tests for endpoint wrappers, request parameter construction, and free-tier fallback behavior. |
| `tests/domain/test_mappers.py` | create | Unit tests for fixture/team/player/standings mapping and alias extraction. |
| `tests/ingestion/test_fixtures_backfill.py` | create | Unit tests for date iteration, resume logic, and idempotent fixture upserts. |
| `tests/features/test_training_base.py` | create | Verify no future leakage and correct result/rolling feature derivation. |
| `tests/integration/test_local_supabase_sync.py` | create | Integration smoke test against local Supabase after migrations are applied. |

## Data and Contract Changes

- New environment variables:
  - `THESPORTSDB_API_KEY`
  - `SUPABASE_DB_URL`
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `LIGA1_LEAGUE_ID`
  - `BACKFILL_START_DATE`
  - `FUTURE_FIXTURES_DAYS`
  - `FIXTURE_REFRESH_LOOKBACK_DAYS`
- New database tables:
  - `public.leagues`
    - One row per external league source ID.
  - `public.league_seasons`
    - Seasons discovered or configured for a league, because the free seasons endpoint is incomplete.
  - `public.teams`
    - Canonical team rows keyed by TheSportsDB `idTeam`.
  - `public.team_aliases`
    - Alternate team names observed in fixtures and standings, required because names vary (`Cusco` vs `Cusco FC`, `UTC` vs `Universidad Técnica de Cajamarca`).
  - `public.players`
    - Current roster data keyed by TheSportsDB `idPlayer`.
  - `public.fixtures`
    - One row per TheSportsDB `idEvent`, including season, round, teams, kickoff timestamps, scores, venue, status, postponement flag, and media URLs.
  - `public.standings_snapshots`
    - Time-stamped standings rows keyed by `idStanding` plus snapshot metadata.
  - `public.sync_runs`
    - Job observability: job type, params, started/finished times, status, row counts, error text.
  - `public.raw_thesportsdb_payloads`
    - Raw JSON payloads keyed by endpoint plus request fingerprint for replay and debugging.
- New analytics object:
  - `analytics.training_matches_base`
    - One row per finished fixture with leakage-safe derived columns such as:
      - `target_result` (`H`, `D`, `A`)
      - `home_points_last_5`, `away_points_last_5`
      - `home_goals_for_last_5`, `home_goals_against_last_5`
      - `away_goals_for_last_5`, `away_goals_against_last_5`
      - `home_goal_diff_last_5`, `away_goal_diff_last_5`
      - `home_rest_days`, `away_rest_days`
      - `head_to_head_home_points_last_3` and `head_to_head_away_points_last_3` if enough prior meetings exist
      - `season`, `round`, `match_date`

## Implementation Steps

1. Bootstrap the repo as a Python application.
   - Create `pyproject.toml`, package layout under `src/`, test layout under `tests/`, and `.env.example`.
   - Standardize on `uv` runners so every command in docs and CI is reproducible.

2. Initialize Supabase and create the database foundation.
   - Run `supabase init` and commit `supabase/config.toml`.
   - Add the first migration for core normalized tables and indexes.
   - Add the second migration for the `analytics` schema and derived dataset objects.

3. Implement config and persistence primitives.
   - Add typed settings in `src/match_winning_tracking/config.py`.
   - Use direct Postgres access against Supabase for ingestion writes because bulk upserts are more natural than routing everything through the Supabase HTTP client.
   - Add transactional helpers for batched upserts and sync-run logging.

4. Implement the TheSportsDB client around the validated endpoints.
   - Enforce a soft client-side rate limit below 30 requests/minute.
   - Centralize request fingerprinting so every successful and failed fetch can be written to `public.raw_thesportsdb_payloads`.
   - Treat `eventsseason.php` and `search_all_seasons.php` as advisory only; do not use them to drive the primary backfill loop.

5. Build reference sync first.
   - Load league metadata from `lookupleague.php?id=4688`.
   - Load current teams from `search_all_teams.php?l=Peruvian_Primera_Division`.
   - Upsert canonical teams and aliases discovered from fixture/standings payloads.
   - Register seasons in `public.league_seasons` from configured year range rather than trusting the limited seasons endpoint.

6. Build fixture ingestion around daily polling.
   - Backfill from `BACKFILL_START_DATE=2020-01-01` through current date using `eventsday.php?d=<date>&l=4688`.
   - After the historical pass, refresh a rolling window such as `today - 7 days` through `today + 14 days` to catch score corrections, schedule changes, and upcoming matches.
   - Upsert by `idEvent`, not by team/date text fields.
   - Capture all raw payloads for dates even when `events` is `null` so reruns remain observable.

7. Add standings snapshots as a secondary signal.
   - Snapshot current-season standings on demand and after each daily sync.
   - Store `dateUpdated` and the time the snapshot was fetched.
   - Do not rely on standings as the primary historical source for feature derivation because stage semantics are not guaranteed.

8. Add current roster ingestion.
   - For each current Liga 1 team, call `lookup_all_players.php?id=<idTeam>`.
   - Store only current player-team membership in phase 1.
   - Keep roster data independent from the ML base until historical roster quality is validated.

9. Build the ML-ready base dataset.
   - Derive training rows from finished fixtures only.
   - Compute rolling team form strictly from matches that occurred before the target fixture date.
   - Use standings snapshots only when a strictly earlier snapshot exists; otherwise fall back to fixture-derived form.
   - Prefer deterministic SQL or SQL-plus-Python transforms that can be rerun idempotently from source tables.

10. Add CLI wiring and documentation.
    - Expose commands such as:
      - `uv run python -m match_winning_tracking.cli sync-reference`
      - `uv run python -m match_winning_tracking.cli sync-players`
      - `uv run python -m match_winning_tracking.cli backfill-fixtures`
      - `uv run python -m match_winning_tracking.cli sync-standings`
      - `uv run python -m match_winning_tracking.cli build-training-base`
    - Document the intended order of execution and recovery steps after partial failures.

11. Add automated tests and validation.
    - Cover payload mapping, alias creation, backfill iteration, idempotent upserts, and feature leakage prevention.
    - Add at least one local Supabase smoke test that applies migrations, runs a narrowed backfill window, and verifies rows landed in normalized tables.

## Tests

- Unit: `tests/clients/test_thesportsdb.py` cover rate limiting, endpoint selection, and free-tier fallback logic.
- Unit: `tests/domain/test_mappers.py` cover fixture/team/player/standings normalization and alias extraction.
- Unit: `tests/ingestion/test_fixtures_backfill.py` cover date-window iteration, `events=null` handling, and upsert idempotency by `idEvent`.
- Unit: `tests/features/test_training_base.py` verify `target_result` labeling and that rolling features do not use same-match or future data.
- Integration: `tests/integration/test_local_supabase_sync.py` validate migrations plus a small local backfill window against Supabase Postgres.
- Regression: Ensure `eventsseason.php` is never used as the authoritative backfill source and `lookupteam.php` inconsistencies do not break team ingestion.

## Validation

- Install deps: `uv sync`
- Start local database: `supabase start`
- Apply migrations/reset local DB: `supabase db reset`
- Format: `uv run ruff format --check src tests`
- Lint: `uv run ruff check src tests`
- Types: `uv run mypy src`
- Tests: `uv run pytest`
- Smoke sync: `uv run python -m match_winning_tracking.cli sync-reference && uv run python -m match_winning_tracking.cli backfill-fixtures --from 2026-04-18 --to 2026-04-21 && uv run python -m match_winning_tracking.cli build-training-base`

## Risks and Mitigations

- TheSportsDB free-tier endpoint caps and partial results -> Drive historical backfill by `eventsday.php` on a per-date basis and persist raw payloads for auditing.
- Team name drift across payloads -> Key all joins by TheSportsDB IDs and persist `public.team_aliases` from observed names.
- Standings semantics may represent tournament stage rather than full-year table -> Store standings as snapshots only and compute core ML features from fixtures.
- Some detail endpoints can return `null` or inconsistent demo-key data -> Make lineups/event stats optional and do not block the pipeline on `lookupteam.php`.
- Current rosters are not historical rosters -> Keep player ingestion separate from phase-1 model features.
- Empty repo means every file is net new -> Start with a narrow Liga 1-only slice and keep alternative leagues and sources out of scope.

## Open Questions

- None

## Acceptance Criteria

- The repo contains a runnable Python project scaffolded with `uv`, plus `ruff`, `mypy`, and `pytest` configuration.
- Supabase local development is initialized and migrations create the normalized ingestion schema plus the analytics schema.
- A backfill command can populate Liga 1 fixtures from TheSportsDB by iterating dates, not by relying on truncated season endpoints.
- Current teams and current player rosters for Liga 1 can be synced into Supabase.
- Standings snapshots can be fetched and stored without being treated as the sole historical truth.
- `analytics.training_matches_base` can be rebuilt from normalized tables and contains only leakage-safe pre-match features.
- README setup docs explain how to start Supabase, run the sync commands, and understand the free-tier limitations that shaped the design.

## Definition of Done

- Python scaffold, Supabase config, migrations, CLI entry points, and docs are implemented.
- Tests cover endpoint mapping, ingestion logic, and feature derivation.
- `ruff format --check`, `ruff check`, `mypy`, and `pytest` pass from the repo root.
- A local Supabase smoke run proves that normalized Liga 1 data lands in the database and the training base can be generated.
- This plan is updated if endpoint behavior or scope changes during implementation.
