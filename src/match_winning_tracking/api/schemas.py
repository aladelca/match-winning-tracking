"""Pydantic schemas for the mock predictions API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    model_version: str


class FeatureSpec(BaseModel):
    key: str
    label: str
    min: float
    max: float
    default: float


class ModelInfo(BaseModel):
    id: str
    description: str
    features: list[FeatureSpec]


class ModelsResponse(BaseModel):
    models: list[ModelInfo]


class Probabilities(BaseModel):
    home: float = Field(ge=0.0, le=1.0)
    draw: float = Field(ge=0.0, le=1.0)
    away: float = Field(ge=0.0, le=1.0)


class PredictRequest(BaseModel):
    fixture_id: str
    model_id: str | None = None


class PredictResponse(BaseModel):
    fixture_id: str
    model_version: str
    features: dict[str, float]
    probabilities: Probabilities


class SensitivityRequest(BaseModel):
    fixture_id: str
    feature_overrides: dict[str, float] = Field(default_factory=dict)
    model_id: str | None = None


class SensitivityBranch(BaseModel):
    features: dict[str, float]
    probabilities: Probabilities


class DeltaTriplet(BaseModel):
    home: float
    draw: float
    away: float


class SensitivityResponse(BaseModel):
    fixture_id: str
    model_version: str
    baseline: SensitivityBranch
    modified: SensitivityBranch
    deltas: DeltaTriplet
