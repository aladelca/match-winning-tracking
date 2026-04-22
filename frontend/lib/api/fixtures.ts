import type { SupabaseClient } from "@supabase/supabase-js";

import type { Fixture, FixtureWithTeams, Team } from "@/lib/types";

const FIXTURE_COLUMNS = [
  "source",
  "source_event_id",
  "source_league_id",
  "season",
  "round_text",
  "event_date",
  "kickoff_at",
  "status",
  "home_team_id",
  "away_team_id",
  "home_team_name",
  "away_team_name",
  "home_score",
  "away_score",
  "venue",
  "is_finished",
  "is_postponed",
].join(",");

const TEAM_COLUMNS = [
  "source",
  "source_team_id",
  "source_league_id",
  "name",
  "short_name",
  "badge_url",
].join(",");

type TeamRef = {
  source: string;
  sourceId: number;
};

type TeamRow = {
  source: string;
  source_team_id: number;
  source_league_id: number;
  name: string | null;
  short_name: string | null;
  badge_url: string | null;
};

type FixtureRow = {
  source: string;
  source_event_id: number;
  source_league_id: number;
  season: string | null;
  round_text: string | null;
  event_date: string | null;
  kickoff_at: string | null;
  status: string | null;
  home_team_id: number | null;
  away_team_id: number | null;
  home_team_name: string | null;
  away_team_name: string | null;
  home_score: number | null;
  away_score: number | null;
  venue: string | null;
  is_finished: boolean | null;
  is_postponed: boolean | null;
};

function buildFixtureId(source: string, sourceEventId: number): string {
  return `${source}:${sourceEventId}`;
}

function buildTeamId(source: string, sourceTeamId: number): string {
  return `${source}:${sourceTeamId}`;
}

function parseScopedId(id: string): TeamRef {
  const [source, rawId] = id.split(":", 2);
  const sourceId = Number(rawId);

  if (!source || !Number.isInteger(sourceId)) {
    throw new Error(`Invalid scoped id: ${id}`);
  }

  return { source, sourceId };
}

function mapTeam(row: TeamRow): Team {
  return {
    id: buildTeamId(row.source, row.source_team_id),
    source: row.source,
    source_team_id: row.source_team_id,
    source_league_id: row.source_league_id,
    name: row.name ?? `Team ${row.source_team_id}`,
    short_name: row.short_name,
    logo_url: row.badge_url,
  };
}

function mapFixture(row: FixtureRow): Fixture | null {
  if (row.home_team_id === null || row.away_team_id === null) {
    return null;
  }

  return {
    id: buildFixtureId(row.source, row.source_event_id),
    source: row.source,
    source_event_id: row.source_event_id,
    source_league_id: row.source_league_id,
    season: row.season,
    round: row.round_text,
    event_date: row.event_date,
    kickoff_at: row.kickoff_at,
    home_team_id: buildTeamId(row.source, row.home_team_id),
    away_team_id: buildTeamId(row.source, row.away_team_id),
    home_team_name: row.home_team_name,
    away_team_name: row.away_team_name,
    home_score: row.home_score,
    away_score: row.away_score,
    status: row.status ?? "scheduled",
    venue: row.venue,
    is_finished: row.is_finished ?? false,
    is_postponed: row.is_postponed ?? false,
  };
}

function fallbackTeam(
  source: string,
  sourceTeamId: number,
  name: string | null,
): Team {
  return {
    id: buildTeamId(source, sourceTeamId),
    source,
    source_team_id: sourceTeamId,
    source_league_id: 0,
    name: name ?? `Team ${sourceTeamId}`,
    short_name: null,
    logo_url: null,
  };
}

async function listTeamsByRefs(
  supabase: SupabaseClient,
  refs: TeamRef[],
): Promise<Team[]> {
  if (refs.length === 0) return [];

  const refsBySource = new Map<string, Set<number>>();
  for (const ref of refs) {
    const ids = refsBySource.get(ref.source) ?? new Set<number>();
    ids.add(ref.sourceId);
    refsBySource.set(ref.source, ids);
  }

  const batches = await Promise.all(
    Array.from(refsBySource.entries()).map(async ([source, ids]) => {
      const { data, error } = await supabase
        .from("teams")
        .select(TEAM_COLUMNS)
        .eq("source", source)
        .in("source_team_id", Array.from(ids));

      if (error) throw error;
      return (((data ?? []) as unknown as TeamRow[])).map(mapTeam);
    }),
  );

  return batches.flat();
}

export async function listTeams(
  supabase: SupabaseClient,
  limit?: number,
): Promise<Team[]> {
  let query = supabase
    .from("teams")
    .select(TEAM_COLUMNS)
    .order("name", { ascending: true });

  if (typeof limit === "number") {
    query = query.limit(limit);
  }

  const { data, error } = await query;
  if (error) throw error;
  return (((data ?? []) as unknown as TeamRow[])).map(mapTeam);
}

function sortFixtures(fixtures: Fixture[]): Fixture[] {
  return [...fixtures].sort((left, right) => {
    const leftKey = left.kickoff_at ?? left.event_date ?? "";
    const rightKey = right.kickoff_at ?? right.event_date ?? "";
    return leftKey.localeCompare(rightKey);
  });
}

function hydrateFixtures(
  fixtures: Fixture[],
  teams: Team[],
): FixtureWithTeams[] {
  const teamMap = new Map(teams.map((team) => [team.id, team]));

  return fixtures.map((fixture) => {
    const homeRef = parseScopedId(fixture.home_team_id);
    const awayRef = parseScopedId(fixture.away_team_id);

    const home_team =
      teamMap.get(fixture.home_team_id) ??
      fallbackTeam(fixture.source, homeRef.sourceId, fixture.home_team_name);
    const away_team =
      teamMap.get(fixture.away_team_id) ??
      fallbackTeam(fixture.source, awayRef.sourceId, fixture.away_team_name);

    return { ...fixture, home_team, away_team };
  });
}

export async function listUpcomingFixtures(
  supabase: SupabaseClient,
  limit: number = 10,
): Promise<FixtureWithTeams[]> {
  const { data, error } = await supabase
    .from("fixtures")
    .select(FIXTURE_COLUMNS)
    .eq("is_finished", false)
    .order("event_date", { ascending: true })
    .order("kickoff_at", { ascending: true })
    .limit(limit * 5);

  if (error) throw error;

  const fixtures = sortFixtures(
    (((data ?? []) as unknown as FixtureRow[]).map(mapFixture).filter(Boolean) as Fixture[]),
  ).slice(0, limit);

  const teamRefs = fixtures.flatMap((fixture) => [
    parseScopedId(fixture.home_team_id),
    parseScopedId(fixture.away_team_id),
  ]);
  const teams = await listTeamsByRefs(supabase, teamRefs);
  return hydrateFixtures(fixtures, teams);
}

export async function getFixture(
  supabase: SupabaseClient,
  fixtureId: string,
): Promise<FixtureWithTeams | null> {
  const fixtureRef = parseScopedId(fixtureId);

  const { data, error } = await supabase
    .from("fixtures")
    .select(FIXTURE_COLUMNS)
    .eq("source", fixtureRef.source)
    .eq("source_event_id", fixtureRef.sourceId)
    .limit(1);

  if (error) throw error;

  const row = (((data ?? []) as unknown as FixtureRow[]))[0];
  if (!row) return null;

  const fixture = mapFixture(row);
  if (!fixture) return null;

  const teams = await listTeamsByRefs(supabase, [
    parseScopedId(fixture.home_team_id),
    parseScopedId(fixture.away_team_id),
  ]);

  return hydrateFixtures([fixture], teams)[0] ?? null;
}

export async function getTeam(
  supabase: SupabaseClient,
  teamId: string,
): Promise<Team | null> {
  const teamRef = parseScopedId(teamId);

  const { data, error } = await supabase
    .from("teams")
    .select(TEAM_COLUMNS)
    .eq("source", teamRef.source)
    .eq("source_team_id", teamRef.sourceId)
    .limit(1);

  if (error) throw error;

  const team = (((data ?? []) as unknown as TeamRow[]))[0];
  return team ? mapTeam(team) : null;
}

export async function listFixturesForTeam(
  supabase: SupabaseClient,
  teamId: string,
): Promise<FixtureWithTeams[]> {
  const teamRef = parseScopedId(teamId);

  const { data, error } = await supabase
    .from("fixtures")
    .select(FIXTURE_COLUMNS)
    .eq("source", teamRef.source)
    .or(`home_team_id.eq.${teamRef.sourceId},away_team_id.eq.${teamRef.sourceId}`)
    .order("event_date", { ascending: true })
    .order("kickoff_at", { ascending: true })
    .limit(50);

  if (error) throw error;

  const fixtures = sortFixtures(
    (((data ?? []) as unknown as FixtureRow[]).map(mapFixture).filter(Boolean) as Fixture[]),
  );
  const teams = await listTeamsByRefs(
    supabase,
    fixtures.flatMap((fixture) => [
      parseScopedId(fixture.home_team_id),
      parseScopedId(fixture.away_team_id),
    ]),
  );

  return hydrateFixtures(fixtures, teams);
}
