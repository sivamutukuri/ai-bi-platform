"""Pydantic v2 schemas for request/response validation."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------- Datasets ----------
class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str | None = None
    source_type: str
    status: str
    row_count: int | None = None
    column_count: int | None = None
    schema_json: dict[str, Any] | None = None
    created_at: datetime


class SQLConnectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    connection_uri: str = Field(min_length=1)
    query: str = Field(min_length=1)
    description: str | None = None


# ---------- Analysis ----------
class ColumnProfile(BaseModel):
    name: str
    dtype: str
    missing: int
    missing_pct: float
    unique: int
    outliers: int = 0
    mean: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None
    top: Any | None = None


class QualityReport(BaseModel):
    quality_score: float
    total_rows: int
    total_columns: int
    duplicate_rows: int
    total_missing: int
    columns: list[ColumnProfile]
    issues: list[str]


class Insight(BaseModel):
    title: str
    detail: str
    severity: Literal["info", "warning", "critical"] = "info"


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float


class NLQueryRequest(BaseModel):
    dataset_id: str
    question: str = Field(min_length=3, max_length=1000)


class NLQueryResponse(BaseModel):
    answer: str
    used_llm: bool
    generated_code: str | None = None
    result_preview: list[dict[str, Any]] | None = None


class ExecutiveSummaryResponse(BaseModel):
    summary: str
    used_llm: bool


class ReportRequest(BaseModel):
    dataset_id: str
    fmt: Literal["pdf", "excel"]
    title: str | None = None
