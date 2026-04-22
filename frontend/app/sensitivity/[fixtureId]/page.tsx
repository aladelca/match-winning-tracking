import Link from "next/link";
import type { Route } from "next";
import { notFound } from "next/navigation";

import { SensitivityPanel } from "@/components/sensitivity-panel";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { getFixture } from "@/lib/api/fixtures";
import { formatKickoff } from "@/lib/utils";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ fixtureId: string }>;
};

export default async function SensitivityPage({ params }: PageProps) {
  const { fixtureId } = await params;
  const supabase = await createSupabaseServerClient().catch(() => null);
  const fixture = supabase
    ? await getFixture(supabase, fixtureId).catch(() => null)
    : null;
  if (!fixture) notFound();

  return (
    <article className="space-y-6">
      <Link
        href={`/matches/${fixture.id}` as Route}
        className="text-xs text-muted-foreground hover:text-foreground"
      >
        ← Volver al detalle del partido
      </Link>

      <header className="space-y-1">
        <div className="text-xs text-muted-foreground">
          {fixture.round ?? fixture.season ?? "Sin ronda"} ·{" "}
          {formatKickoff(fixture.kickoff_at, fixture.event_date)}
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">
          Sensibilidad: {fixture.home_team.name} vs {fixture.away_team.name}
        </h1>
        <p className="text-sm text-muted-foreground">
          Mueve los controles para ver cómo cambian las probabilidades respecto
          al baseline.
        </p>
      </header>

      <SensitivityPanel fixtureId={fixture.id} />
    </article>
  );
}
