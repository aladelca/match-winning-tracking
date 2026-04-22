import type { SupabaseClient } from "@supabase/supabase-js";

import type { Fixture, FixtureWithTeams, Team } from "@/lib/types";

const FIXTURE_COLUMNS =
  "id,season,round,home_team_id,away_team_id,kickoff_at,home_score,away_score,status,venue";
const TEAM_COLUMNS = "id,name,short_name,logo_url";

async function listTeamsByIds(
  supabase: SupabaseClient,
  ids: string[],
): Promise<Team[]> {
  if (ids.length === 0) return [];
  const { data, error } = await supabase
    .from("teams")
    .select(TEAM_COLUMNS)
    .in("id", ids);
  if (error) throw error;
  return (data as Team[]) ?? [];
}

function hydrateFixtures(
  fixtures: Fixture[],
  teams: Team[],
): FixtureWithTeams[] {
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

export async function listUpcomingFixtures(
  supabase: SupabaseClient,
  limit: number = 10,
): Promise<FixtureWithTeams[]> {
  const { data, error } = await supabase
    .from("fixtures")
    .select(FIXTURE_COLUMNS)
    .order("kickoff_at", { ascending: true })
    .limit(limit);
  if (error) throw error;
  const fixtures = (data as Fixture[]) ?? [];
  const teamIds = Array.from(
    new Set(fixtures.flatMap((f) => [f.home_team_id, f.away_team_id])),
  );
  const teams = await listTeamsByIds(supabase, teamIds);
  return hydrateFixtures(fixtures, teams);
}

export async function getFixture(
  supabase: SupabaseClient,
  fixtureId: string,
): Promise<FixtureWithTeams | null> {
  const { data, error } = await supabase
    .from("fixtures")
    .select(FIXTURE_COLUMNS)
    .eq("id", fixtureId)
    .limit(1);
  if (error) throw error;
  const fixture = ((data as Fixture[]) ?? [])[0];
  if (!fixture) return null;
  const teams = await listTeamsByIds(supabase, [
    fixture.home_team_id,
    fixture.away_team_id,
  ]);
  return hydrateFixtures([fixture], teams)[0] ?? null;
}

export async function getTeam(
  supabase: SupabaseClient,
  teamId: string,
): Promise<Team | null> {
  const { data, error } = await supabase
    .from("teams")
    .select(TEAM_COLUMNS)
    .eq("id", teamId)
    .limit(1);
  if (error) throw error;
  return ((data as Team[]) ?? [])[0] ?? null;
}

export async function listFixturesForTeam(
  supabase: SupabaseClient,
  teamId: string,
): Promise<FixtureWithTeams[]> {
  const { data, error } = await supabase
    .from("fixtures")
    .select(FIXTURE_COLUMNS)
    .or(`home_team_id.eq.${teamId},away_team_id.eq.${teamId}`)
    .order("kickoff_at", { ascending: true })
    .limit(50);
  if (error) throw error;
  const fixtures = (data as Fixture[]) ?? [];
  const teamIds = Array.from(
    new Set(fixtures.flatMap((f) => [f.home_team_id, f.away_team_id])),
  );
  const teams = await listTeamsByIds(supabase, teamIds);
  return hydrateFixtures(fixtures, teams);
}
