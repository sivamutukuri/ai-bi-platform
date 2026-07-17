"""Data profiling, quality scoring, and outlier detection."""
from __future__ import annotations

import numpy as np
import pandas as pd


def detect_outliers_iqr(series: pd.Series) -> int:
    """Count outliers in a numeric series using the 1.5*IQR rule."""
    clean = series.dropna()
    if clean.empty:
        return 0
    q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((clean < lower) | (clean > upper)).sum())


def profile_column(df: pd.DataFrame, col: str) -> dict:
    """Build a per-column profile including stats and outliers."""
    series = df[col]
    total = len(series)
    missing = int(series.isna().sum())
    profile = {
        "name": col,
        "dtype": str(series.dtype),
        "missing": missing,
        "missing_pct": round(missing / total * 100, 2) if total else 0.0,
        "unique": int(series.nunique(dropna=True)),
        "outliers": 0,
        "mean": None,
        "std": None,
        "min": None,
        "max": None,
        "top": None,
    }
    if pd.api.types.is_numeric_dtype(series):
        clean = series.dropna()
        if not clean.empty:
            profile.update(
                mean=round(float(clean.mean()), 4),
                std=round(float(clean.std()), 4) if len(clean) > 1 else 0.0,
                min=float(clean.min()),
                max=float(clean.max()),
                outliers=detect_outliers_iqr(series),
            )
    else:
        mode = series.mode(dropna=True)
        profile["top"] = None if mode.empty else str(mode.iloc[0])
    return profile


def build_quality_report(df: pd.DataFrame) -> dict:
    """Produce a full data quality report with an overall score (0-100)."""
    total_rows = int(len(df))
    total_cols = int(df.shape[1])
    duplicate_rows = int(df.duplicated().sum())
    total_missing = int(df.isna().sum().sum())

    columns = [profile_column(df, c) for c in df.columns]
    total_cells = max(total_rows * total_cols, 1)

    completeness = 1 - (total_missing / total_cells)
    uniqueness = 1 - (duplicate_rows / total_rows) if total_rows else 1.0
    total_outliers = sum(c["outliers"] for c in columns)
    numeric_cells = max(
        sum(1 for c in columns if c["mean"] is not None) * total_rows, 1
    )
    validity = 1 - min(total_outliers / numeric_cells, 1.0)

    quality_score = round(
        (0.5 * completeness + 0.3 * uniqueness + 0.2 * validity) * 100, 1
    )

    issues: list[str] = []
    if duplicate_rows:
        issues.append(f"{duplicate_rows} duplicate row(s) detected.")
    if total_missing:
        issues.append(f"{total_missing} missing value(s) across the dataset.")
    for c in columns:
        if c["missing_pct"] > 30:
            issues.append(
                f"Column '{c['name']}' is {c['missing_pct']}% missing."
            )
        if c["outliers"] > 0:
            issues.append(
                f"Column '{c['name']}' has {c['outliers']} outlier(s)."
            )
    if not issues:
        issues.append("No major data quality issues detected.")

    return {
        "quality_score": quality_score,
        "total_rows": total_rows,
        "total_columns": total_cols,
        "duplicate_rows": duplicate_rows,
        "total_missing": total_missing,
        "columns": columns,
        "issues": issues,
    }


def build_schema(df: pd.DataFrame) -> dict:
    """Return a compact schema mapping of column -> dtype."""
    return {col: str(dtype) for col, dtype in df.dtypes.items()}
