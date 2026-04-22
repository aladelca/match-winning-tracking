# Frontend

Next.js 15 App Router + TypeScript + Tailwind + Supabase.

## Arranque rápido

```bash
cp .env.local.example .env.local
# pegar NEXT_PUBLIC_SUPABASE_ANON_KEY desde `supabase start`

npm install
npm run dev
```

## Scripts

- `npm run dev` — servidor de desarrollo en `http://localhost:3000`
- `npm run build` — build de producción
- `npm run start` — sirve el build
- `npm run lint` — ESLint con `next/core-web-vitals`
- `npm run typecheck` — `tsc --noEmit`

## Dependencias externas

- API de predicciones en `NEXT_PUBLIC_PREDICTIONS_API_URL` (por defecto `http://127.0.0.1:8000`).
- Supabase local en `NEXT_PUBLIC_SUPABASE_URL` (por defecto `http://127.0.0.1:54321`).

## Estructura

```
app/              rutas App Router
components/       UI primitives (shadcn-style) + componentes de dominio
lib/api/          wrappers tipados para la API de predicciones
lib/supabase/     clientes server y browser
lib/types.ts      tipos compartidos (Fixture, Team, PredictResponse, ...)
```
