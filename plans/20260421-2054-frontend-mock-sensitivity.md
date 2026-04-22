# Frontend MVP con Modelo Mock y Análisis de Sensibilidad

## Goal

- Construir un frontend local, compartible sin login, para visualizar predicciones de partidos de Liga 1 Perú y ejecutar análisis de sensibilidad contra un modelo predictivo.
- El modelo real aún no existe. El frontend se desarrolla contra un servicio mock en FastAPI que respeta el contrato que usará el modelo final, de modo que luego sea sustituible sin tocar la UI.
- Mantener todo en ejecución local: Supabase local, API mock local, Next.js local. Cero despliegues remotos en esta fase.

## Request Snapshot

- User request: "revisa el repositorio... quiero crear un frontend asociado, estoy trabajando con supabase... tener un lugar donde podamos ver las predicciones y hacer llamados via api al modelo predictivo para hacer analisis de sensibilidad".
- Clarificaciones confirmadas: (1) modelo mockeado, (2) sólo entorno local, (3) app pública sin login.
- Owner / branch: `feat/frontend-init` (rama efímera, merge local a `main`).
- Plan file: `plans/20260421-2054-frontend-mock-sensitivity.md`.

## Current State

- Repo prácticamente vacío en esta rama: `AGENTS.md`, `CLAUDE.md`, `README.md` placeholder, `.gitignore`, config de beads. No hay código aplicativo ni carpeta `frontend/`.
- El worktree paralelo `~/personales/match-tracking/match-winning-tracking/` tiene WIP sin commitear del plan de datos (`pyproject.toml`, `src/match_winning_tracking/`, `supabase/config.toml`, `config/leagues.yml`) — es la base que eventualmente poblará las tablas que este frontend leerá. El frontend no depende de que ese WIP esté mergeado.
- Plan de datos existente: `plans/20260421-2033-thesportsdb-supabase-liga1-foundation.md` (en el worktree paralelo). Define el esquema `public.{leagues,teams,fixtures,standings_snapshots,players}` y la vista `analytics.training_matches_base`. El frontend lee de estas tablas y asume sus contratos.
- Supabase local ya está configurado en ese plan: API en `54321`, DB en `54322`, Studio en `54323`. El frontend reutiliza la misma instancia.
- Beads: 0 issues. No hay trabajo en curso bloqueante.
- Python 3.12 + `uv` es el toolchain ya elegido; FastAPI se suma como dependencia en el mismo paquete.

## Findings

- Stack recomendado para Supabase + UI moderna: **Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui**. Es el camino canónico documentado por Supabase y minimiza fricción con `@supabase/ssr`.
- Supabase local expone Postgres vía PostgREST en `http://127.0.0.1:54321`. Con la `anon key` de `supabase start`, el frontend puede leer tablas sin login siempre que RLS esté apagada o exista policy de lectura pública.
- FastAPI es la opción más barata para el mock porque (a) reusa Python 3.12 + `uv`, (b) puede leer las mismas features que construirá el modelo real desde `analytics.training_matches_base`, (c) evita reimplementar lógica de features en TypeScript.
- Para análisis de sensibilidad, el mock necesita un **vector de features nombrado y estable** que la UI pueda manipular. Elegir 6-8 features de la lista ya planeada para `analytics.training_matches_base` (`home_points_last_5`, `away_points_last_5`, `home_goal_diff_last_5`, `away_goal_diff_last_5`, `home_rest_days`, `away_rest_days`, `head_to_head_home_points_last_3`). Si la tabla está vacía, el mock usa valores por defecto.
- "Compartible sin login" + local = no hay Vercel ni Supabase cloud. "Compartir" en esta fase significa que otra persona pueda clonar y levantar con un solo comando, o que se exponga vía túnel (ngrok/cloudflared) puntualmente. No diseñamos auth ni RLS estricta, pero dejamos el hook para agregarla después.
- shadcn/ui cubre gratis los primitives que necesitamos (Card, Slider, Button, Progress, Tabs, Badge). Sin library de charts pesada: `recharts` alcanza para la barra H/D/A y el gráfico de sensibilidad.

## Scope

### In scope

- Servicio FastAPI `match-winning-tracking-api` dentro del paquete Python existente, con endpoints `/health`, `/models`, `/predict`, `/predict/sensitivity`.
- Mock determinístico del predictor: dado un `fixture_id` y un vector de features (tomado de DB o override), retorna probabilidades `home/draw/away` vía heurística logística sobre diferencial de forma + ventaja local. Repetible para la misma entrada.
- Carpeta `frontend/` con app Next.js 15 App Router + TypeScript + Tailwind + shadcn/ui.
- Cliente Supabase con `@supabase/ssr` y env wiring para anon key local.
- Vistas: dashboard (`/`), detalle de partido (`/matches/[fixtureId]`), panel de sensibilidad (`/sensitivity/[fixtureId]`), perfil de equipo (`/teams/[teamId]`).
- Seed de demo: 6 partidos + 6 equipos sintéticos en `supabase/seed.sql` para que la UI muestre contenido aun sin correr la ingesta.
- Script único de desarrollo (`justfile` o `Makefile`) que levanta Supabase, la API mock y el frontend.
- Docs en README raíz con instrucciones de arranque y puertos.
- CORS permisivo (localhost only) en FastAPI.

### Out of scope

- Modelo predictivo real, entrenamiento, registro de modelos o persistencia de predicciones en tabla dedicada. El mock responde on-demand; no se persiste.
- Autenticación, roles, RLS estricta. Todas las tablas consumidas por el frontend quedan en lectura abierta vía anon key local.
- Despliegue remoto (Vercel, Supabase cloud, Fly, Railway). Cualquier hosting queda para fase posterior.
- Notificaciones, suscripciones realtime, websockets.
- i18n, dark mode toggle, responsive avanzado más allá de lo que shadcn/ui entrega por defecto.
- Tests E2E (Playwright/Cypress). Se cubre con tests unitarios de la API y type-checking del frontend.
- Integración con el WIP de ingesta en el worktree paralelo. El frontend funciona con seed; cuando la ingesta se mergee, las mismas tablas se llenarán con datos reales sin cambios en la UI.

## File Plan

| Path | Action | Details |
| --- | --- | --- |
| `pyproject.toml` | modify | Añadir `fastapi>=0.115`, `uvicorn[standard]>=0.32` a dependencies; registrar script `match-winning-tracking-api = "match_winning_tracking.api.main:run"`. |
| `.env.example` | modify | Agregar `API_HOST`, `API_PORT`, `API_CORS_ORIGINS`, `MOCK_MODEL_VERSION`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_PREDICTIONS_API_URL`. |
| `src/match_winning_tracking/api/__init__.py` | create | Marker de paquete. |
| `src/match_winning_tracking/api/main.py` | create | App FastAPI, wiring de routers, middleware CORS, función `run()` para uvicorn. |
| `src/match_winning_tracking/api/schemas.py` | create | Pydantic models: `FeatureVector`, `PredictionResponse`, `SensitivityRequest`, `SensitivityResponse`, `ModelInfo`. |
| `src/match_winning_tracking/api/routes/health.py` | create | `GET /health` retorna `{"status":"ok", "model_version":...}`. |
| `src/match_winning_tracking/api/routes/models.py` | create | `GET /models` lista versiones disponibles (sólo `mock-v0` por ahora) con su `feature_schema` (nombres, rangos sugeridos, defaults). |
| `src/match_winning_tracking/api/routes/predict.py` | create | `POST /predict` toma `fixture_id`, carga features desde DB o defaults, corre mock, retorna probabilidades + feature vector usado. |
| `src/match_winning_tracking/api/routes/sensitivity.py` | create | `POST /predict/sensitivity` toma `fixture_id` + `feature_overrides: dict[str,float]`, retorna baseline, modified, deltas por clase. |
| `src/match_winning_tracking/api/services/feature_loader.py` | create | Lee fixture + features desde Supabase Postgres (`analytics.training_matches_base` o fallback a defaults si no hay fila). |
| `src/match_winning_tracking/api/services/mock_predictor.py` | create | Heurística determinística: softmax sobre `[w_h·diff_form + home_advantage, w_d·0, w_a·(−diff_form)]`. Clampeado para que nunca retorne 0 ni 1 exactos. |
| `supabase/seed.sql` | modify | Poblar 6 equipos Liga 1 reales (IDs placeholder), 6 fixtures con fechas futuras, 0 standings. Idempotente vía `INSERT ... ON CONFLICT DO NOTHING`. |
| `frontend/package.json` | create | Next 15, React 19, TypeScript 5, Tailwind 4, `@supabase/supabase-js`, `@supabase/ssr`, `recharts`, `lucide-react`, `class-variance-authority`, `clsx`, `tailwind-merge`. |
| `frontend/tsconfig.json` | create | Config estándar Next + path alias `@/*`. |
| `frontend/next.config.ts` | create | Config mínima; `experimental.typedRoutes = true`. |
| `frontend/tailwind.config.ts` | create | Paths estándar; preset shadcn. |
| `frontend/postcss.config.mjs` | create | Tailwind PostCSS. |
| `frontend/app/globals.css` | create | Tailwind base + tokens shadcn. |
| `frontend/app/layout.tsx` | create | Root layout con nav (Home / Partidos / Equipos) y font. |
| `frontend/app/page.tsx` | create | Dashboard. Server component: lee próximos fixtures de Supabase, hace fetch paralelo a `/predict` por cada uno, renderiza grid de `FixtureCard`. |
| `frontend/app/matches/[fixtureId]/page.tsx` | create | Detalle: metadata del fixture, barra de predicción, features usadas (read-only), link a panel de sensibilidad. |
| `frontend/app/sensitivity/[fixtureId]/page.tsx` | create | Panel interactivo (client component): sliders por feature, chart de probabilidades baseline vs modified. |
| `frontend/app/teams/[teamId]/page.tsx` | create | Perfil de equipo: últimos fixtures + próximos. |
| `frontend/components/fixture-card.tsx` | create | Card con equipos, kickoff y barra H/D/A. |
| `frontend/components/prediction-bar.tsx` | create | Barra stacked H/D/A con labels y porcentajes. |
| `frontend/components/sensitivity-panel.tsx` | create | UI de sliders + chart + botón reset. |
| `frontend/components/ui/{button,card,slider,badge,tabs,progress}.tsx` | create | Primitives shadcn añadidos vía `pnpm dlx shadcn add`. |
| `frontend/lib/supabase/server.ts` | create | Factory server-side con `createServerClient`. |
| `frontend/lib/supabase/browser.ts` | create | Factory browser-side con `createBrowserClient`. |
| `frontend/lib/api/predictions.ts` | create | Wrappers tipados sobre la API FastAPI (`fetchPrediction`, `fetchSensitivity`, `fetchModels`). |
| `frontend/lib/types.ts` | create | Tipos compartidos `Fixture`, `Team`, `Prediction`, `FeatureVector`, `ModelInfo`. |
| `frontend/.env.local.example` | create | Variables `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_PREDICTIONS_API_URL`. |
| `frontend/README.md` | create | Cómo arrancar sólo el frontend, convenciones, comandos. |
| `tests/api/test_predict.py` | create | Tests FastAPI: contract de `/predict`, estabilidad determinística, CORS headers. |
| `tests/api/test_sensitivity.py` | create | Tests: overrides aplican correctamente, deltas sumados a baseline dan modified, probabilidades suman 1.0 ± ε. |
| `tests/api/test_models.py` | create | Test: `/models` lista `mock-v0` con feature schema completo. |
| `justfile` | create | Targets: `dev` (Supabase + API + frontend en paralelo), `api`, `web`, `db-reset`, `fmt`, `lint`, `test`. |
| `README.md` | modify | Sección "Frontend local" con pasos mínimos: `supabase start` → `uv run match-winning-tracking-api` → `pnpm --dir frontend dev`. |

## Data and Contract Changes

### Sin cambios de esquema DB

No se crean tablas nuevas. El frontend lee las tablas ya planeadas en el plan de datos (`public.fixtures`, `public.teams`, `analytics.training_matches_base`). Si esas tablas aún no existen cuando el frontend se ejecute, el seed de `supabase/seed.sql` provee datos mínimos.

### Nuevas variables de entorno

- `API_HOST=127.0.0.1`
- `API_PORT=8000`
- `API_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`
- `MOCK_MODEL_VERSION=mock-v0`
- `NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY=<valor emitido por supabase start>`
- `NEXT_PUBLIC_PREDICTIONS_API_URL=http://127.0.0.1:8000`

### Contrato de API (congelado para sobrevivir al reemplazo por modelo real)

```
GET /health
  → 200 { "status": "ok", "model_version": "mock-v0" }

GET /models
  → 200 {
      "models": [
        {
          "id": "mock-v0",
          "description": "Heuristic mock predictor",
          "features": [
            { "key": "home_points_last_5",            "label": "Home points (last 5)",            "min": 0,  "max": 15, "default": 7 },
            { "key": "away_points_last_5",            "label": "Away points (last 5)",            "min": 0,  "max": 15, "default": 7 },
            { "key": "home_goal_diff_last_5",         "label": "Home goal diff (last 5)",         "min": -10,"max": 10, "default": 0 },
            { "key": "away_goal_diff_last_5",         "label": "Away goal diff (last 5)",         "min": -10,"max": 10, "default": 0 },
            { "key": "home_rest_days",                "label": "Home rest days",                  "min": 0,  "max": 14, "default": 5 },
            { "key": "away_rest_days",                "label": "Away rest days",                  "min": 0,  "max": 14, "default": 5 },
            { "key": "head_to_head_home_points_last_3","label": "H2H home points (last 3)",        "min": 0,  "max": 9,  "default": 4 }
          ]
        }
      ]
    }

POST /predict
  body  { "fixture_id": "string", "model_id": "mock-v0" (optional) }
  → 200 {
      "fixture_id": "...",
      "model_version": "mock-v0",
      "features": { "home_points_last_5": 7, ... },
      "probabilities": { "home": 0.48, "draw": 0.27, "away": 0.25 }
    }

POST /predict/sensitivity
  body  {
    "fixture_id": "string",
    "feature_overrides": { "home_rest_days": 2, "away_points_last_5": 12 },
    "model_id": "mock-v0" (optional)
  }
  → 200 {
      "fixture_id": "...",
      "model_version": "mock-v0",
      "baseline": { "features": {...}, "probabilities": {...} },
      "modified": { "features": {...}, "probabilities": {...} },
      "deltas":   { "home": -0.07, "draw": +0.02, "away": +0.05 }
    }
```

Errores: `404` si `fixture_id` no existe en DB, `422` si un override cae fuera de rango, `500` para fallas internas.

## Implementation Steps

1. **API mock — scaffolding**
   - Añadir FastAPI + uvicorn a `pyproject.toml`, correr `uv sync`.
   - Crear `src/match_winning_tracking/api/` con `main.py`, `schemas.py` y un router `/health`. Validar con `uv run uvicorn match_winning_tracking.api.main:app --reload`.

2. **API mock — feature loader**
   - Implementar `feature_loader.py` que reciba `fixture_id` y devuelva un dict de features. Si la fila no existe en `analytics.training_matches_base`, retornar defaults del schema.
   - Conexión reusa `SUPABASE_DB_URL` vía `psycopg`. Una conexión por request es aceptable para local.

3. **API mock — predictor**
   - Implementar `mock_predictor.py` con función `predict(features: dict) -> {home, draw, away}`.
   - Heurística: `diff = (home_points_last_5 - away_points_last_5) + 0.5·(home_goal_diff_last_5 - away_goal_diff_last_5) + rest_advantage + h2h_advantage`. Aplicar softmax sobre `[diff + HOME_ADV, 0, -diff]` con temperatura configurable.
   - Determinístico: misma entrada → misma salida. No usar `random`.

4. **API mock — endpoints públicos**
   - Implementar `/models`, `/predict`, `/predict/sensitivity`.
   - Para sensibilidad: cargar baseline, aplicar overrides sobre el dict de features, recomputar, calcular deltas.
   - Validar ranges usando el mismo schema que expone `/models` (fuente única de verdad).

5. **API mock — CORS + tests**
   - Habilitar `CORSMiddleware` con origins desde env.
   - Tests pytest bajo `tests/api/` usando `TestClient`. Cubrir: happy path, override fuera de rango (422), fixture inexistente (404), determinismo.

6. **Frontend — scaffolding**
   - `pnpm create next-app frontend --ts --tailwind --app --eslint --src-dir=false --import-alias "@/*"`.
   - `pnpm --dir frontend dlx shadcn init` + añadir primitives necesarios (`button`, `card`, `slider`, `badge`, `progress`, `tabs`).
   - Crear `lib/supabase/{server,browser}.ts`, `lib/api/predictions.ts`, `lib/types.ts`.
   - Layout raíz con nav mínimo.

7. **Frontend — dashboard**
   - Server component `app/page.tsx`: query a `public.fixtures` ordenados por `kickoff_at` ascendente, próximos 10.
   - Fetch paralelo a `/predict` por cada fixture (`Promise.all` en el server).
   - Renderizar grid de `FixtureCard` con `PredictionBar`.
   - Manejar estado "sin data" con mensaje claro.

8. **Frontend — detalle de partido**
   - `app/matches/[fixtureId]/page.tsx`: fetch fixture + teams + predicción.
   - Mostrar features usadas como tabla read-only.
   - Botón "Analizar sensibilidad" que linkea a `/sensitivity/[fixtureId]`.

9. **Frontend — panel de sensibilidad**
   - Client component en `app/sensitivity/[fixtureId]/page.tsx`.
   - Al montar, fetch a `/models` + `/predict` para obtener schema + baseline.
   - Estado local: dict de overrides. Sliders shadcn para cada feature (min/max/step del schema).
   - Debounce 200ms → llamada a `/predict/sensitivity`.
   - Render: `PredictionBar` baseline vs modified, chart de deltas con `recharts`, botón reset.

10. **Frontend — perfil de equipo**
    - `app/teams/[teamId]/page.tsx`: últimos 5 fixtures + próximos 5. Sin predicciones (fuera de scope en esta vista).

11. **Seed + DX**
    - Poblar `supabase/seed.sql` con equipos Liga 1 y fixtures de ejemplo.
    - Crear `justfile` con `just dev` que corre `supabase start`, `uv run match-winning-tracking-api` y `pnpm --dir frontend dev` en paralelo (usar `concurrently` o `foreman`, o simplemente 3 targets separados para que el usuario elija).
    - Actualizar `README.md` con sección de arranque del frontend.

12. **Tests + validación**
    - API: `uv run pytest tests/api`.
    - Frontend: `pnpm --dir frontend lint && pnpm --dir frontend typecheck && pnpm --dir frontend build`.
    - QA manual: levantar stack completo, navegar dashboard → partido → sensibilidad, mover sliders, verificar que probabilidades cambian coherentemente (más puntos locales → sube home, menos descanso → baja la clase correspondiente).

## Tests

- **Unit API** (`tests/api/test_predict.py`): contrato de respuesta, determinismo (dos calls idénticas retornan misma probabilidad al epsilon float), fixture inexistente → 404, probabilidades suman ≈1.
- **Unit API** (`tests/api/test_sensitivity.py`): override válido aplica correctamente, override fuera de rango → 422, baseline + deltas reproducen modified, determinismo.
- **Unit API** (`tests/api/test_models.py`): `/models` expone al menos `mock-v0` con todas las features esperadas y tipos correctos.
- **Unit API** (`tests/api/test_mock_predictor.py`): heurística responde a cambios de features en la dirección esperada (más `home_points_last_5` → sube `home`, sube `away_points_last_5` → sube `away`).
- **Frontend**: type-check (`tsc --noEmit`) y `next build` como regresión. Sin framework de tests unitarios en esta fase para no inflar el scope.
- **Manual**: script paso a paso en el `README.md` para QA humano del stack completo.

## Validation

- Python: `uv sync`
- Supabase local: `supabase start && supabase db reset`
- API mock: `uv run uvicorn match_winning_tracking.api.main:app --reload`
- Frontend: `pnpm --dir frontend install && pnpm --dir frontend dev`
- Lint Python: `uv run ruff format --check src tests && uv run ruff check src tests`
- Types Python: `uv run mypy src`
- Tests Python: `uv run pytest tests/api`
- Lint/types frontend: `pnpm --dir frontend lint && pnpm --dir frontend typecheck`
- Build frontend: `pnpm --dir frontend build`
- Smoke manual:
  1. `just dev` (o los tres comandos separados)
  2. Abrir `http://localhost:3000` → ver fixtures con barras de predicción.
  3. Click en un fixture → `/matches/[id]` muestra features + predicción.
  4. Click "Analizar sensibilidad" → mover sliders → la barra responde.

## Risks and Mitigations

- **Tablas de Supabase aún no existen cuando el frontend se ejecute** → el seed provee datos mínimos; `feature_loader` usa defaults cuando no hay fila en `analytics.training_matches_base`.
- **El contrato del mock y el del modelo real divergen más adelante** → `/models` es la fuente única de verdad del schema de features; cuando llegue el modelo real, sólo cambia la implementación interna y se añade `v1` en paralelo a `mock-v0`.
- **Drift en nombres de features** entre mock, DB y UI → los `feature.key` son idénticos a las columnas de `analytics.training_matches_base`; cualquier cambio se propaga en un solo lugar.
- **Rendimiento del dashboard** por fetch paralelo a `/predict` por cada fixture → aceptable en local con 10 fixtures; si crece, cachear con `unstable_cache` de Next o persistir predicciones en tabla dedicada (fuera de scope).
- **CORS mal configurado** bloquea el panel de sensibilidad → tests de API cubren headers CORS y el `.env.example` documenta los origins.
- **Anon key local expuesta públicamente al hacer share via túnel** → al no haber RLS, cualquier lector puede escribir si alguien descubre el service_role. Compartir sólo la URL de Next.js (no las de Supabase/API directas) vía túnel; documentarlo en README.
- **Determinismo del mock** si se introduce `random` accidentalmente → tests explícitos de determinismo previenen regresión.

## Open Questions

- ¿Quieres persistir snapshots de predicciones mock en una tabla `public.predictions` para que el dashboard lea de DB en vez de llamar al API en cada carga? Por ahora quedó fuera de scope; si priorizas velocidad de carga en demos, lo añadimos.
- ¿Preferencia de package manager para el frontend: `pnpm`, `npm` o `bun`? El plan asume `pnpm`; cambio a otro es trivial.
- ¿`justfile` o `Makefile` para el target `dev`? Asumido `justfile` por sintaxis más limpia; si no tienes `just` instalado, cambiamos a Makefile.

## Acceptance Criteria

- Correr `supabase start`, `uv run match-winning-tracking-api` y `pnpm --dir frontend dev` en paralelo levanta los tres servicios sin errores.
- `http://localhost:3000` muestra al menos 6 fixtures con barra de probabilidad poblada por la API mock.
- `/matches/[fixtureId]` muestra predicción y tabla de features.
- `/sensitivity/[fixtureId]` permite mover sliders y actualiza la barra/chart en menos de 500ms por interacción.
- `/teams/[teamId]` muestra últimos y próximos fixtures del equipo.
- `GET /models` retorna al menos `mock-v0` con schema completo de features.
- `POST /predict` y `POST /predict/sensitivity` respetan el contrato documentado.
- `uv run pytest tests/api` pasa. `pnpm --dir frontend build` pasa.
- README raíz explica cómo arrancar el stack desde cero.

## Definition of Done

- Todos los archivos del File Plan creados o modificados.
- Lint + types + build en verde tanto en Python como en TypeScript.
- Tests de API pasan y cubren los casos listados en la sección Tests.
- Epic y tasks en beads creados y correctamente enlazados por dependencias.
- Plan actualizado si durante la implementación se cambia el contrato de API o el file plan.
- Commit en `feat/frontend-init` con el trabajo; la rama queda lista para merge local a `main`.
