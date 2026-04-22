# Match Winning Tracking

MVP local para visualizar predicciones de partidos de Liga 1 Peru y probar analisis de sensibilidad contra un modelo mock expuesto por FastAPI.

## Stack

- `supabase` local para fixtures y equipos
- `FastAPI` en `src/match_winning_tracking/api/` para `/health`, `/models`, `/predict` y `/predict/sensitivity`
- `Next.js 15` en `frontend/` para dashboard, detalle del partido, sensibilidad y perfiles de equipo

## Arranque local

1. Copia variables base:

```bash
cp -f .env.example .env
cp -f frontend/.env.local.example frontend/.env.local
```

2. Levanta Supabase local y aplica seed:

```bash
supabase start
supabase db reset
```

3. Completa `SUPABASE_ANON_KEY` y `NEXT_PUBLIC_SUPABASE_ANON_KEY` con la key anon que imprime `supabase start`.

4. Instala dependencias del backend y frontend:

```bash
uv sync
npm --prefix frontend install
```

5. Inicia la API mock y el frontend en terminales separadas:

```bash
uv run match-winning-tracking-api
npm --prefix frontend run dev
```

La app queda disponible en `http://localhost:3000` y la API en `http://127.0.0.1:8000`.

## Rutas principales

- `/` dashboard con proximos partidos y predicciones mock
- `/matches/[fixtureId]` detalle del partido y vector de features usado
- `/sensitivity/[fixtureId]` sliders para sensibilidad sobre el baseline
- `/teams` indice de equipos disponibles
- `/teams/[teamId]` historial reciente y proximos partidos de un equipo

## Checks utiles

```bash
uv run pytest
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
```
