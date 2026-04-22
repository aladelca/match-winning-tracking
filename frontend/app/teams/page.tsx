import Link from "next/link";
import type { Route } from "next";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { listTeams } from "@/lib/api/fixtures";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

async function loadTeams() {
  try {
    const supabase = await createSupabaseServerClient();
    return await listTeams(supabase);
  } catch (error) {
    console.error("[teams] Supabase unreachable:", error);
    return [];
  }
}

export default async function TeamsPage() {
  const teams = await loadTeams();

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
          Liga 1 Peru
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Equipos</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Navega por los equipos cargados en Supabase local para revisar su
          actividad reciente y los siguientes partidos sincronizados por la
          ingesta local.
        </p>
      </header>

      {teams.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
          No hay equipos cargados todavia. Corre la ingesta base para poblar{" "}
          <code>public.teams</code>.
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {teams.map((team) => (
            <Card key={team.id} className="transition-shadow hover:shadow-md">
              <CardHeader className="space-y-3">
                <Badge variant="outline" className="w-fit">
                  {team.short_name ?? "Equipo"}
                </Badge>
                <div className="space-y-1">
                  <CardTitle className="text-xl">
                    <Link
                      href={`/teams/${team.id}` as Route}
                      className="hover:underline"
                    >
                      {team.name}
                    </Link>
                  </CardTitle>
                  <CardDescription>
                    Perfil del equipo y listado de fixtures asociados.
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <Link
                  href={`/teams/${team.id}` as Route}
                  className="text-sm font-medium text-foreground hover:underline"
                >
                  Ver perfil completo →
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
