export type Outcome = "home" | "draw" | "away";

export type Probabilities = Record<Outcome, number>;

export type FeatureSpec = {
  key: string;
  label: string;
  min: number;
  max: number;
  default: number;
};

export type ModelInfo = {
  id: string;
  description: string;
  features: FeatureSpec[];
};

export type ModelsResponse = {
  models: ModelInfo[];
};

export type PredictResponse = {
  fixture_id: string;
  model_version: string;
  features: Record<string, number>;
  probabilities: Probabilities;
};

export type SensitivityBranch = {
  features: Record<string, number>;
  probabilities: Probabilities;
};

export type SensitivityResponse = {
  fixture_id: string;
  model_version: string;
  baseline: SensitivityBranch;
  modified: SensitivityBranch;
  deltas: Probabilities;
};

export type Team = {
  id: string;
  source: string;
  source_team_id: number;
  source_league_id: number;
  name: string;
  short_name: string | null;
  logo_url: string | null;
};

export type Fixture = {
  id: string;
  source: string;
  source_event_id: number;
  source_league_id: number;
  season: string | null;
  round: string | null;
  event_date: string | null;
  kickoff_at: string | null;
  home_team_id: string;
  away_team_id: string;
  home_team_name: string | null;
  away_team_name: string | null;
  home_score: number | null;
  away_score: number | null;
  status: string;
  venue: string | null;
  is_finished: boolean;
  is_postponed: boolean;
};

export type FixtureWithTeams = Fixture & {
  home_team: Team;
  away_team: Team;
};
