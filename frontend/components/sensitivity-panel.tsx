"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { PredictionBar } from "@/components/prediction-bar";
import {
  fetchModels,
  fetchSensitivity,
  fetchPrediction,
} from "@/lib/api/predictions";
import type {
  FeatureSpec,
  Probabilities,
  SensitivityResponse,
} from "@/lib/types";
import { formatPercent } from "@/lib/utils";

interface SensitivityPanelProps {
  fixtureId: string;
}

const DEBOUNCE_MS = 200;

function buildBaselineResponse(
  fixtureId: string,
  modelVersion: string,
  features: Record<string, number>,
  probabilities: Probabilities,
): SensitivityResponse {
  return {
    fixture_id: fixtureId,
    model_version: modelVersion,
    baseline: {
      features: { ...features },
      probabilities: { ...probabilities },
    },
    modified: {
      features: { ...features },
      probabilities: { ...probabilities },
    },
    deltas: {
      home: 0,
      draw: 0,
      away: 0,
    },
  };
}

export function SensitivityPanel({ fixtureId }: SensitivityPanelProps) {
  const [features, setFeatures] = useState<FeatureSpec[] | null>(null);
  const [baseline, setBaseline] = useState<Probabilities | null>(null);
  const [modelVersion, setModelVersion] = useState("mock-v0");
  const [baselineFeatures, setBaselineFeatures] = useState<Record<
    string,
    number
  > | null>(null);
  const [overrides, setOverrides] = useState<Record<string, number>>({});
  const [current, setCurrent] = useState<SensitivityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestToken = useRef(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [modelsResponse, prediction] = await Promise.all([
          fetchModels(),
          fetchPrediction(fixtureId),
        ]);
        if (cancelled) return;
        const catalog = modelsResponse.models[0];
        if (!catalog) {
          throw new Error("Predictions API returned no model catalog.");
        }

        const initialResponse = buildBaselineResponse(
          fixtureId,
          prediction.model_version,
          prediction.features,
          prediction.probabilities,
        );

        setFeatures(catalog.features);
        setBaseline(prediction.probabilities);
        setModelVersion(prediction.model_version);
        setBaselineFeatures(prediction.features);
        setOverrides({ ...prediction.features });
        setCurrent(initialResponse);
        setError(null);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [fixtureId]);

  useEffect(() => {
    if (!baseline || !baselineFeatures) return;

    const unchanged = Object.entries(baselineFeatures).every(
      ([key, value]) => Math.abs((overrides[key] ?? value) - value) < 1e-6,
    );

    if (unchanged) {
      setCurrent(
        buildBaselineResponse(fixtureId, modelVersion, baselineFeatures, baseline),
      );
      setError(null);
      return;
    }

    const nextToken = requestToken.current + 1;
    requestToken.current = nextToken;

    const timeoutId = window.setTimeout(async () => {
      try {
        const response = await fetchSensitivity(fixtureId, overrides);
        if (requestToken.current !== nextToken) return;
        setCurrent(response);
        setError(null);
      } catch (err) {
        if (requestToken.current !== nextToken) return;
        setError(err instanceof Error ? err.message : String(err));
      }
    }, DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [baseline, baselineFeatures, fixtureId, modelVersion, overrides]);

  const handleSlider = (key: string, value: number) => {
    setOverrides((prev) => ({ ...prev, [key]: value }));
  };

  const handleReset = () => {
    if (baselineFeatures) {
      setOverrides({ ...baselineFeatures });
    }
  };

  if (loading) {
    return (
      <p className="text-sm text-muted-foreground">Cargando predicción base…</p>
    );
  }

  if (error && !features) {
    return (
      <p className="text-sm text-[hsl(var(--away))]">
        No se pudo cargar el modelo: {error}
      </p>
    );
  }

  if (!features || !baseline) {
    return (
      <p className="text-sm text-muted-foreground">Sin datos del modelo.</p>
    );
  }

  const deltaData = current
    ? [
        {
          outcome: "Local",
          delta: current.deltas.home,
          fill: "hsl(var(--home))",
        },
        {
          outcome: "Empate",
          delta: current.deltas.draw,
          fill: "hsl(var(--draw))",
        },
        {
          outcome: "Visita",
          delta: current.deltas.away,
          fill: "hsl(var(--away))",
        },
      ]
    : [];

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Controles</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          {features.map((spec) => {
            const value = overrides[spec.key] ?? spec.default;
            const baselineValue = baselineFeatures?.[spec.key] ?? spec.default;
            const drifted = Math.abs(value - baselineValue) > 1e-6;
            return (
              <div key={spec.key} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <label
                    htmlFor={`slider-${spec.key}`}
                    className="font-medium"
                  >
                    {spec.label}
                  </label>
                  <span
                    className={
                      drifted
                        ? "font-mono text-foreground"
                        : "font-mono text-muted-foreground"
                    }
                  >
                    {value.toFixed(1)}
                  </span>
                </div>
                <Slider
                  id={`slider-${spec.key}`}
                  value={value}
                  onValueChange={(v) => handleSlider(spec.key, v)}
                  min={spec.min}
                  max={spec.max}
                  step={0.5}
                />
                <div className="flex justify-between text-[10px] text-muted-foreground">
                  <span>{spec.min}</span>
                  <span>baseline {baselineValue.toFixed(1)}</span>
                  <span>{spec.max}</span>
                </div>
              </div>
            );
          })}
          <Button variant="outline" onClick={handleReset} className="w-full">
            Restablecer baseline
          </Button>
        </CardContent>
      </Card>

      <div className="space-y-6">
        {error && (
          <p className="rounded-md border border-[hsl(var(--away))]/30 bg-[hsl(var(--away))]/10 px-3 py-2 text-xs text-[hsl(var(--away))]">
            No se pudo recalcular la sensibilidad: {error}
          </p>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Probabilidades</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Baseline
              </div>
              <PredictionBar probabilities={baseline} size="lg" />
            </div>
            <div>
              <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Modificado
              </div>
              {current ? (
                <PredictionBar
                  probabilities={current.modified.probabilities}
                  size="lg"
                />
              ) : (
                <p className="text-xs text-muted-foreground">Calculando…</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Deltas</CardTitle>
          </CardHeader>
          <CardContent>
            {current ? (
              <div className="space-y-4">
                <div className="h-40">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={deltaData}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="hsl(var(--border))"
                      />
                      <XAxis
                        dataKey="outcome"
                        stroke="hsl(var(--muted-foreground))"
                        fontSize={12}
                      />
                      <YAxis
                        domain={[-0.5, 0.5]}
                        tickFormatter={(v) =>
                          `${(Number(v) * 100).toFixed(0)}%`
                        }
                        stroke="hsl(var(--muted-foreground))"
                        fontSize={12}
                      />
                      <ReferenceLine
                        y={0}
                        stroke="hsl(var(--muted-foreground))"
                      />
                      <Tooltip
                        formatter={(value: number) => formatPercent(value, 2)}
                        contentStyle={{
                          background: "hsl(var(--card))",
                          border: "1px solid hsl(var(--border))",
                          borderRadius: "0.5rem",
                          fontSize: "0.75rem",
                        }}
                      />
                      <Bar dataKey="delta" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  {deltaData.map((entry) => (
                    <div
                      key={entry.outcome}
                      className="rounded border p-2 text-center"
                    >
                      <div className="text-muted-foreground">
                        {entry.outcome}
                      </div>
                      <div
                        className="font-mono font-semibold"
                        style={{ color: entry.fill }}
                      >
                        {entry.delta >= 0 ? "+" : ""}
                        {formatPercent(entry.delta, 2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Moviendo sliders se calcula el delta contra baseline.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
