import { FixtureCard } from "@/components/fixture-card";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { listUpcomingFixtures } from "@/lib/api/fixtures";
import { fetchPrediction } from "@/lib/api/predictions";
import type { FixtureWithTeams, Probabilities } from "@/lib/types";

export const dynamic = "force-dynamic";

type Enriched = {
  fixture: FixtureWithTeams;
  probabilities: Probabilities | null;
  error: string | null;
};

async function loadFixtures(): Promise<FixtureWithTeams[]> {
  try {
    const supabase = await createSupabaseServerClient();
    return await listUpcomingFixtures(supabase, 10);
  } catch (error) {
    console.error("[dashboard] Supabase unreachable:", error);
    return [];
  }
}

async function enrich(fixture: FixtureWithTeams): Promise<Enriched> {
  try {
    const prediction = await fetchPrediction(fixture.id);
    return {
      fixture,
      probabilities: prediction.probabilities,
      error: null,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { fixture, probabilities: null, error: message };
  }
}

export default async function Home() {
  const fixtures = await loadFixtures();

  if (fixtures.length === 0) {
    return (
      <section className="space-y-4">
        <h1 className="text-2xl font-semibold tracking-tight">
          Próximos partidos
        </h1>
        <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
          <p className="mb-2 font-medium text-foreground">
            No hay partidos cargados todavía.
          </p>
          <p>
            Levanta Supabase local con <code>supabase start</code> y corre{" "}
            <code>supabase db reset</code>. Luego ejecuta la ingesta base del
            repositorio para poblar <code>public.fixtures</code> y{" "}
            <code>analytics.training_matches_base</code>. La guía completa está
            en el <code>README.md</code> del repositorio.
          </p>
        </div>
      </section>
    );
  }

  const enriched = await Promise.all(fixtures.map(enrich));

  return (
    <section className="space-y-4">
      <div className="flex items-baseline justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">
          Próximos partidos
        </h1>
        <span className="text-xs text-muted-foreground">
          {enriched.length} partidos · Modelo mock-v0
        </span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {enriched.map(({ fixture, probabilities, error }) => (
          <FixtureCard
            key={fixture.id}
            fixture={fixture}
            probabilities={probabilities}
            error={error}
          />
        ))}
      </div>
    </section>
  );
}
