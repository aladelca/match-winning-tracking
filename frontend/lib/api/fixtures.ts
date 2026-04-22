import type { Fixture, FixtureWithTeams, Team } from "@/lib/types";

type SupabaseLike = {
  from: (table: string) => {
    select: (columns: string) => {
      order?: (
        column: string,
        options: { ascending: boolean },
      ) => { limit: (n: number) => Promise<{ data: unknown; error: unknown }> };
      in?: (
        column: string,
        values: string[],
      ) => Promise<{ data: unknown; error: unknown }>;
      eq?: (
        column: string,
        value: string,
      ) => Promise<{ data: unknown; error: unknown }>;
    };
  };
};

async function listTeamsByIds(
  supabase: SupabaseLike,
  ids: string[],
): Promise<Team[]> {
  if (ids.length === 0) return [];
  const query = supabase.from("teams").select("id,name,short_name,logo_url");
  if (!query.in) return [];
  const { data, error } = await query.in("id", ids);
  if (error) throw error;
  return (data as Team[]) ?? [];
}

export async function listUpcomingFixtures(
  supabase: SupabaseLike,
  limit: number = 10,
): Promise<FixtureWithTeams[]> {
  const query = supabase
    .from("fixtures")
    .select(
      "id,season,round,home_team_id,away_team_id,kickoff_at,home_score,away_score,status,venue",
    );
  if (!query.order) return [];
  const { data, error } = await query
    .order("kickoff_at", { ascending: true })
    .limit(limit);
  if (error) throw error;
  const fixtures = (data as Fixture[]) ?? [];
  const teamIds = Array.from(
    new Set(fixtures.flatMap((f) => [f.home_team_id, f.away_team_id])),
  );
  const teams = await listTeamsByIds(supabase, teamIds);
  const teamMap = new Map(teams.map((t) => [t.id, t]));
  return fixtures
    .map((fixture) => {
      const home_team = teamMap.get(fixture.home_team_id);
      const away_team = teamMap.get(fixture.away_team_id);
      if (!home_team || !away_team) return null;
      return { ...fixture, home_team, away_team };
    })
    .filter((f): f is FixtureWithTeams => f !== null);
}

export async function getFixture(
  supabase: SupabaseLike,
  fixtureId: string,
): Promise<FixtureWithTeams | null> {
  const query = supabase
    .from("fixtures")
    .select(
      "id,season,round,home_team_id,away_team_id,kickoff_at,home_score,away_score,status,venue",
    );
  if (!query.eq) return null;
  const { data, error } = await query.eq("id", fixtureId);
  if (error) throw error;
  const fixture = (data as Fixture[])?.[0];
  if (!fixture) return null;
  const teams = await listTeamsByIds(supabase, [
    fixture.home_team_id,
    fixture.away_team_id,
  ]);
  const teamMap = new Map(teams.map((t) => [t.id, t]));
  const home_team = teamMap.get(fixture.home_team_id);
  const away_team = teamMap.get(fixture.away_team_id);
  if (!home_team || !away_team) return null;
  return { ...fixture, home_team, away_team };
}

export async function getTeam(
  supabase: SupabaseLike,
  teamId: string,
): Promise<Team | null> {
  const query = supabase.from("teams").select("id,name,short_name,logo_url");
  if (!query.eq) return null;
  const { data, error } = await query.eq("id", teamId);
  if (error) throw error;
  return ((data as Team[]) ?? [])[0] ?? null;
}

export async function listFixturesForTeam(
  supabase: SupabaseLike,
  teamId: string,
): Promise<FixtureWithTeams[]> {
  const query = supabase
    .from("fixtures")
    .select(
      "id,season,round,home_team_id,away_team_id,kickoff_at,home_score,away_score,status,venue",
    );
  if (!query.order) return [];
  const { data, error } = await query
    .order("kickoff_at", { ascending: true })
    .limit(50);
  if (error) throw error;
  const fixtures = (data as Fixture[]) ?? [];
  const related = fixtures.filter(
    (f) => f.home_team_id === teamId || f.away_team_id === teamId,
  );
  const ids = Array.from(
    new Set(related.flatMap((f) => [f.home_team_id, f.away_team_id])),
  );
  const teams = await listTeamsByIds(supabase, ids);
  const teamMap = new Map(teams.map((t) => [t.id, t]));
  return related
    .map((fixture) => {
      const home_team = teamMap.get(fixture.home_team_id);
      const away_team = teamMap.get(fixture.away_team_id);
      if (!home_team || !away_team) return null;
      return { ...fixture, home_team, away_team };
    })
    .filter((f): f is FixtureWithTeams => f !== null);
}
