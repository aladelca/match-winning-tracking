import Link from "next/link";
import type { Route } from "next";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PredictionBar } from "@/components/prediction-bar";
import type { FixtureWithTeams, Probabilities } from "@/lib/types";
import { formatKickoff } from "@/lib/utils";

export interface FixtureCardProps {
  fixture: FixtureWithTeams;
  probabilities: Probabilities | null;
  error?: string | null;
}

function pickFavorite(probs: Probabilities): "home" | "draw" | "away" {
  const entries: Array<["home" | "draw" | "away", number]> = [
    ["home", probs.home],
    ["draw", probs.draw],
    ["away", probs.away],
  ];
  entries.sort((a, b) => b[1] - a[1]);
  return entries[0][0];
}

function favoriteLabel(pick: "home" | "draw" | "away"): string {
  return pick === "home" ? "Local" : pick === "draw" ? "Empate" : "Visita";
}

export function FixtureCard({ fixture, probabilities, error }: FixtureCardProps) {
  const href = `/matches/${fixture.id}` as Route;
  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader className="space-y-2">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{fixture.round ?? fixture.season ?? "Sin ronda"}</span>
          <span>{formatKickoff(fixture.kickoff_at, fixture.event_date)}</span>
        </div>
        <CardTitle className="text-base">
          <Link href={href} className="hover:underline">
            {fixture.home_team.name}{" "}
            <span className="text-muted-foreground">vs</span>{" "}
            {fixture.away_team.name}
          </Link>
        </CardTitle>
        {probabilities && (
          <div>
            <Badge variant={pickFavorite(probabilities)}>
              Favorito: {favoriteLabel(pickFavorite(probabilities))}
            </Badge>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {probabilities ? (
          <PredictionBar probabilities={probabilities} />
        ) : (
          <p className="text-xs text-muted-foreground">
            {error ?? "Predicción no disponible"}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
