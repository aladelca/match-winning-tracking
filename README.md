# Match Winning Tracking

Base local para ingerir datos de Liga 1 Peru desde TheSportsDB hacia Supabase y, sobre esa misma base, exponer un mock API de predicciones y un frontend para explorar partidos y sensibilidad.

## Stack

- Python 3.12
- `uv` para dependencias y ejecucion
- Supabase local para Postgres y PostgREST
- TheSportsDB V1 (`api key` gratuita `123`)
- `FastAPI` en `src/match_winning_tracking/api/` para `/health`, `/models`, `/predict` y `/predict/sensitivity`
- `Next.js 15` en `frontend/` para dashboard, detalle del partido, sensibilidad y perfiles de equipo

## Decisiones de datos

- Liga objetivo: `Liga 1 Peru` (`idLeague=4688`)
- Fuente principal: `TheSportsDB`
- Backfill historico: `eventsday.php`
- No se usa `eventsseason.php` como fuente historica autoritativa porque la capa gratuita devuelve resultados truncados

## Requisitos locales

- `uv`
- `supabase`
- Docker Desktop o un runtime compatible para `supabase start`

## Setup base

1. Copia variables base:

```bash
cp -f .env.example .env
cp -f frontend/.env.local.example frontend/.env.local
```

2. Instala dependencias:

```bash
uv sync
npm --prefix frontend install
```

3. Levanta Supabase local y aplica migraciones:

```bash
supabase start
supabase db reset
```

4. Completa `SUPABASE_ANON_KEY` y `NEXT_PUBLIC_SUPABASE_ANON_KEY` con la key anon que imprime `supabase start`.

Puertos locales reservados por este repo:

- Supabase API: `55421`
- Postgres: `55422`
- Studio: `55423`
- Inbucket: `55424`
- Analytics: `55427`
- Mock predictions API: `8000`
- Frontend: `3000`

## Cargar datos reales

```bash
uv run python -m match_winning_tracking.cli sync-reference
uv run python -m match_winning_tracking.cli sync-players
uv run python -m match_winning_tracking.cli backfill-fixtures --from 2026-04-18 --to 2026-04-21
uv run python -m match_winning_tracking.cli sync-standings --season 2026
uv run python -m match_winning_tracking.cli build-training-base
```

Flujo recomendado:

1. Sincronizar metadatos de liga y equipos.
2. Hacer backfill de fixtures por fecha.
3. Sincronizar standings.
4. Sincronizar planteles actuales.
5. Refrescar `analytics.training_matches_base`.

## Frontend y mock API

Inicia la API mock y el frontend en terminales separadas:

```bash
uv run match-winning-tracking-api
npm --prefix frontend run dev
```

La app queda disponible en `http://localhost:3000` y la API en `http://127.0.0.1:8000`. Si aun no corriste la ingesta, el dashboard quedara vacio y mostrara el estado sin datos.

## Rutas principales

- `/` dashboard con proximos partidos y predicciones mock
- `/matches/[fixtureId]` detalle del partido y vector de features usado
- `/sensitivity/[fixtureId]` sliders para sensibilidad sobre el baseline
- `/teams` indice de equipos disponibles
- `/teams/[teamId]` historial reciente y proximos partidos de un equipo

## Checks utiles

```bash
uv run ruff format --check src tests
uv run ruff check src tests
uv run mypy src
uv run pytest
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

## Limitaciones conocidas de TheSportsDB free tier

- Limite de 30 requests por minuto.
- `eventsseason.php` devuelve una muestra truncada y no sirve para backfill completo.
- `search_all_seasons.php` puede devolver temporadas incompletas.
- `lookuplineup.php` y `lookupeventstats.php` pueden retornar `null`.
