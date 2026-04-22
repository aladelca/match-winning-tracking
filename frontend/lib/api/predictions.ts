import { env } from "@/lib/env";
import type {
  ModelsResponse,
  PredictResponse,
  SensitivityResponse,
} from "@/lib/types";

async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${env.predictionsApiUrl()}${path}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(
      `Predictions API ${response.status} ${response.statusText}: ${body.slice(0, 160)}`,
    );
  }
  return response.json() as Promise<T>;
}

export function fetchModels(): Promise<ModelsResponse> {
  return apiFetch<ModelsResponse>("/models");
}

export function fetchPrediction(
  fixtureId: string,
  modelId?: string,
): Promise<PredictResponse> {
  return apiFetch<PredictResponse>("/predict", {
    method: "POST",
    body: JSON.stringify({ fixture_id: fixtureId, model_id: modelId }),
  });
}

export function fetchSensitivity(
  fixtureId: string,
  featureOverrides: Record<string, number>,
  modelId?: string,
): Promise<SensitivityResponse> {
  return apiFetch<SensitivityResponse>("/predict/sensitivity", {
    method: "POST",
    body: JSON.stringify({
      fixture_id: fixtureId,
      feature_overrides: featureOverrides,
      model_id: modelId,
    }),
  });
}
