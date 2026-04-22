# Match Winning Tracking

Base local para ingerir datos de Liga 1 Perú desde TheSportsDB hacia Supabase y construir una vista materializada lista para futuros experimentos de machine learning.

## Stack

- Python 3.12
- `uv` para dependencias y ejecución
- Supabase local para Postgres
- TheSportsDB V1 (`api key` gratuita `123`)

## Decisiones de datos

- Liga objetivo: `Liga 1 Perú` (`idLeague=4688`)
- Fuente principal: `TheSportsDB`
- Backfill histórico: `eventsday.php`
- No se usa `eventsseason.php` como fuente histórica autoritativa porque la capa gratuita devuelve resultados truncados

## Requisitos locales

- `uv`
- `supabase`
- Docker Desktop o un runtime compatible para `supabase start`

## Setup

```bash
cp .env.example .env
uv sync
supabase start
supabase db reset
```

Puertos locales reservados por este repo:

- API: `55421`
- Postgres: `55422`
- Studio: `55423`
- Inbucket: `55424`
- Analytics: `55427`

## Comandos principales

```bash
uv run python -m match_winning_tracking.cli sync-reference
uv run python -m match_winning_tracking.cli sync-players
uv run python -m match_winning_tracking.cli backfill-fixtures --from 2026-04-18 --to 2026-04-21
uv run python -m match_winning_tracking.cli sync-standings --season 2026
uv run python -m match_winning_tracking.cli build-training-base
```

## Flujo recomendado

1. Sincronizar metadatos de liga y equipos.
2. Hacer backfill de fixtures por fecha.
3. Sincronizar standings.
4. Sincronizar planteles actuales.
5. Refrescar `analytics.training_matches_base`.

## Validación

```bash
uv run ruff format --check src tests
uv run ruff check src tests
uv run mypy src
uv run pytest
```

## Limitaciones conocidas de TheSportsDB free tier

- Límite de 30 requests por minuto.
- `eventsseason.php` devuelve una muestra truncada y no sirve para backfill completo.
- `search_all_seasons.php` puede devolver temporadas incompletas.
- `lookuplineup.php` y `lookupeventstats.php` pueden retornar `null`.

## Resultado esperado

Después de correr la ingesta local, las tablas normalizadas viven en `public` y la base para entrenamiento queda disponible en `analytics.training_matches_base`.
