import Link from "next/link";
import type { Route } from "next";
import { notFound } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getTeam, listFixturesForTeam } from "@/lib/api/fixtures";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import type { FixtureWithTeams } from "@/lib/types";
import { formatKickoff, resolveFixtureDate } from "@/lib/utils";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ teamId: string }>;
};

function fixtureAlreadyPlayed(fixture: FixtureWithTeams): boolean {
  if (fixture.is_finished || fixture.home_score !== null || fixture.away_score !== null) {
    return true;
  }

  const scheduledAt = resolveFixtureDate(fixture.kickoff_at, fixture.event_date);
  return scheduledAt ? scheduledAt.getTime() < Date.now() : false;
}

function formatScore(fixture: FixtureWithTeams): string {
  if (fixture.home_score === null || fixture.away_score === null) {
    return "Sin marcador";
  }

  return `${fixture.home_score} - ${fixture.away_score}`;
}

function opponentForTeam(fixture: FixtureWithTeams, teamId: string) {
  const isHome = fixture.home_team_id === teamId;

  return {
    side: isHome ? "Local" : "Visita",
    opponent: isHome ? fixture.away_team : fixture.home_team,
  };
}

function FixtureList({
  fixtures,
  teamId,
  emptyMessage,
}: {
  fixtures: FixtureWithTeams[];
  teamId: string;
  emptyMessage: string;
}) {
  if (fixtures.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyMessage}</p>;
  }

  return (
    <div className="space-y-3">
      {fixtures.map((fixture) => {
        const { side, opponent } = opponentForTeam(fixture, teamId);

        return (
          <div
            key={fixture.id}
            className="rounded-lg border bg-background/80 px-4 py-3"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{side}</Badge>
                  <span className="text-xs text-muted-foreground">
                    {fixture.round ?? fixture.season ?? "Sin ronda"}
                  </span>
                </div>
                <Link
                  href={`/matches/${fixture.id}` as Route}
                  className="text-sm font-medium hover:underline"
                >
                  vs {opponent.name}
                </Link>
                <div className="text-xs text-muted-foreground">
                  {formatKickoff(fixture.kickoff_at, fixture.event_date)}
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">
                  Estado
                </div>
                <div className="text-sm font-medium">{fixture.status}</div>
                <div className="text-xs text-muted-foreground">
                  {formatScore(fixture)}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default async function TeamPage({ params }: PageProps) {
  const { teamId } = await params;

  const supabase = await createSupabaseServerClient().catch(() => null);
  if (!supabase) notFound();

  const [team, fixtures] = await Promise.all([
    getTeam(supabase, teamId).catch(() => null),
    listFixturesForTeam(supabase, teamId).catch(() => []),
  ]);

  if (!team) {
    notFound();
  }

  const pastFixtures = fixtures.filter(fixtureAlreadyPlayed);
  const upcomingFixtures = fixtures.filter((fixture) => !fixtureAlreadyPlayed(fixture));
  const recentFixtures = pastFixtures.slice(-5).reverse();
  const nextFixtures = upcomingFixtures.slice(0, 5);

  return (
    <article className="space-y-6">
      <Link
        href={"/teams" as Route}
        className="text-xs text-muted-foreground hover:text-foreground"
      >
        ← Volver al listado de equipos
      </Link>

      <header className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{team.short_name ?? "Equipo"}</Badge>
          <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
            Perfil de equipo
          </span>
        </div>
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{team.name}</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Vista operativa del equipo con los partidos ya jugados y los
            proximos compromisos disponibles en el dataset local.
          </p>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>Fixtures cargados</CardDescription>
            <CardTitle>{fixtures.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Jugados</CardDescription>
            <CardTitle>{pastFixtures.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Por jugar</CardDescription>
            <CardTitle>{upcomingFixtures.length}</CardTitle>
          </CardHeader>
        </Card>
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Ultimos 5 partidos</CardTitle>
            <CardDescription>
              Ordenados del mas reciente al mas antiguo.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FixtureList
              fixtures={recentFixtures}
              teamId={team.id}
              emptyMessage="Aun no hay partidos previos para este equipo en los datos locales."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Proximos 5 partidos</CardTitle>
            <CardDescription>
              Ordenados cronologicamente segun kickoff.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FixtureList
              fixtures={nextFixtures}
              teamId={team.id}
              emptyMessage="No hay partidos futuros cargados para este equipo."
            />
          </CardContent>
        </Card>
      </div>
    </article>
  );
}
