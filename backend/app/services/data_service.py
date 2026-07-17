"""Data ingestion, cleaning, and loading utilities."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from app.core.logging import logger


class DataLoadError(Exception):
    """Raised when a dataset cannot be loaded."""


def load_dataframe(file_path: str, source_type: str) -> pd.DataFrame:
    """Load a DataFrame from a file path based on the declared source type."""
    path = Path(file_path)
    if not path.exists():
        raise DataLoadError(f"File not found: {file_path}")

    try:
        if source_type == "csv":
            return pd.read_csv(path)
        if source_type in ("excel", "xlsx", "xls"):
            return pd.read_excel(path)
        if source_type == "json":
            return _read_json(path)
    except Exception as exc:  # noqa: BLE001
        raise DataLoadError(f"Failed to parse {source_type}: {exc}") from exc
    raise DataLoadError(f"Unsupported source type: {source_type}")


def _read_json(path: Path) -> pd.DataFrame:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return pd.json_normalize(value)
        return pd.json_normalize(data)
    return pd.json_normalize(data)


def load_from_sql(connection_uri: str, query: str) -> pd.DataFrame:
    """Load a DataFrame from a SQL database using a read-only query."""
    lowered = query.strip().lower()
    if not lowered.startswith("select") and not lowered.startswith("with"):
        raise DataLoadError("Only read-only SELECT/WITH queries are permitted.")
    try:
        engine = create_engine(connection_uri, pool_pre_ping=True)
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    except Exception as exc:  # noqa: BLE001
        raise DataLoadError(f"SQL load failed: {exc}") from exc


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Apply automatic, non-destructive cleaning and return applied actions."""
    actions: list[str] = []
    cleaned = df.copy()

    # Normalise column names
    original_cols = list(cleaned.columns)
    cleaned.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_")
        for c in cleaned.columns
    ]
    if original_cols != list(cleaned.columns):
        actions.append("Normalised column names to snake_case.")

    # Drop fully empty rows/columns
    before_rows = len(cleaned)
    cleaned = cleaned.dropna(how="all")
    if len(cleaned) != before_rows:
        actions.append(f"Removed {before_rows - len(cleaned)} fully empty rows.")

    empty_cols = [c for c in cleaned.columns if cleaned[c].isna().all()]
    if empty_cols:
        cleaned = cleaned.drop(columns=empty_cols)
        actions.append(f"Dropped {len(empty_cols)} fully empty column(s).")

    # Remove exact duplicate rows
    dup = int(cleaned.duplicated().sum())
    if dup:
        cleaned = cleaned.drop_duplicates()
        actions.append(f"Removed {dup} duplicate row(s).")

    # Trim whitespace on object columns
    for col in cleaned.select_dtypes(include="object").columns:
        cleaned[col] = cleaned[col].astype(str).str.strip()

    # Attempt numeric / datetime coercion for object columns
    for col in cleaned.select_dtypes(include="object").columns:
        coerced = pd.to_numeric(cleaned[col], errors="coerce")
        if coerced.notna().mean() > 0.9:
            cleaned[col] = coerced
            actions.append(f"Coerced column '{col}' to numeric.")
            continue
        dt = pd.to_datetime(cleaned[col], errors="coerce", format="mixed")
        if dt.notna().mean() > 0.9:
            cleaned[col] = dt
            actions.append(f"Coerced column '{col}' to datetime.")

    logger.info("Cleaning applied %d action(s)." % len(actions))
    return cleaned, actions


def impute_missing(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Impute missing values: median for numeric, mode for categorical."""
    actions: list[str] = []
    out = df.copy()
    for col in out.columns:
        missing = int(out[col].isna().sum())
        if missing == 0:
            continue
        if pd.api.types.is_numeric_dtype(out[col]):
            fill = out[col].median()
            out[col] = out[col].fillna(fill)
            actions.append(f"Imputed {missing} missing in '{col}' with median.")
        else:
            mode = out[col].mode(dropna=True)
            fill = mode.iloc[0] if not mode.empty else "unknown"
            out[col] = out[col].fillna(fill)
            actions.append(f"Imputed {missing} missing in '{col}' with mode.")
    return out, actions
