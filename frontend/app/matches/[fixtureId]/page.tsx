import Link from "next/link";
import type { Route } from "next";
import { notFound } from "next/navigation";
import { ArrowRight, MapPin, Calendar, Trophy } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PredictionBar } from "@/components/prediction-bar";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { getFixture } from "@/lib/api/fixtures";
import { fetchPrediction } from "@/lib/api/predictions";
import { formatKickoff } from "@/lib/utils";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ fixtureId: string }>;
};

export default async function MatchDetail({ params }: PageProps) {
  const { fixtureId } = await params;

  const supabase = await createSupabaseServerClient().catch(() => null);
  const fixture = supabase ? await getFixture(supabase, fixtureId).catch(() => null) : null;

  if (!fixture) {
    notFound();
  }

  const prediction = await fetchPrediction(fixtureId).catch((error: unknown) => {
    console.error("[match-detail] prediction failed:", error);
    return null;
  });

  return (
    <article className="space-y-6">
      <Link
        href={"/" as Route}
        className="text-xs text-muted-foreground hover:text-foreground"
      >
        ← Volver al dashboard
      </Link>

      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          {fixture.round && <span>{fixture.round}</span>}
          <span>·</span>
          <span>Temporada {fixture.season ?? "s/d"}</span>
          <Badge variant="outline">{fixture.status}</Badge>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">
          <Link
            href={`/teams/${fixture.home_team.id}` as Route}
            className="hover:underline"
          >
            {fixture.home_team.name}
          </Link>{" "}
          <span className="text-muted-foreground">vs</span>{" "}
          <Link
            href={`/teams/${fixture.away_team.id}` as Route}
            className="hover:underline"
          >
            {fixture.away_team.name}
          </Link>
        </h1>
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <Calendar className="h-4 w-4" />
            {formatKickoff(fixture.kickoff_at, fixture.event_date)}
          </span>
          {fixture.venue && (
            <span className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4" />
              {fixture.venue}
            </span>
          )}
          <span className="flex items-center gap-1.5">
            <Trophy className="h-4 w-4" />
            Modelo {prediction?.model_version ?? "mock-v0"}
          </span>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Predicción</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {prediction ? (
              <PredictionBar probabilities={prediction.probabilities} size="lg" />
            ) : (
              <p className="text-sm text-muted-foreground">
                No se pudo obtener la predicción. Verifica que la API de
                predicciones esté corriendo en{" "}
                <code>NEXT_PUBLIC_PREDICTIONS_API_URL</code>.
              </p>
            )}
            <div className="pt-2">
              <Link
                href={`/sensitivity/${fixture.id}` as Route}
                className={buttonVariants({ variant: "outline" })}
              >
                Analizar sensibilidad
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Features usadas</CardTitle>
          </CardHeader>
          <CardContent>
            {prediction ? (
              <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
                {Object.entries(prediction.features).map(([key, value]) => (
                  <div key={key} className="contents">
                    <dt className="text-muted-foreground">{key}</dt>
                    <dd className="text-right font-mono">
                      {Number(value).toFixed(2)}
                    </dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="text-sm text-muted-foreground">—</p>
            )}
          </CardContent>
        </Card>
      </div>
    </article>
  );
}
