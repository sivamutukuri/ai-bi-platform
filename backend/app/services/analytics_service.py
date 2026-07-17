"""Exploratory data analysis: correlations, trends, distributions."""
from __future__ import annotations

import numpy as np
import pandas as pd


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()


def categorical_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=["object", "category"]).columns.tolist()


def datetime_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()


def descriptive_stats(df: pd.DataFrame) -> dict:
    """Return describe() output as a JSON-serialisable dict."""
    num = df.select_dtypes(include=[np.number])
    if num.empty:
        return {}
    desc = num.describe().replace({np.nan: None})
    return {col: desc[col].to_dict() for col in desc.columns}


def correlation_matrix(df: pd.DataFrame) -> dict:
    """Compute a Pearson correlation matrix for numeric columns."""
    num = df.select_dtypes(include=[np.number])
    if num.shape[1] < 2:
        return {"columns": [], "matrix": [], "top_pairs": []}
    corr = num.corr(numeric_only=True).round(4)
    columns = corr.columns.tolist()
    matrix = corr.replace({np.nan: None}).values.tolist()

    pairs = []
    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            value = corr.iloc[i, j]
            if pd.notna(value):
                pairs.append(
                    {
                        "x": columns[i],
                        "y": columns[j],
                        "corr": float(value),
                    }
                )
    pairs.sort(key=lambda p: abs(p["corr"]), reverse=True)
    return {"columns": columns, "matrix": matrix, "top_pairs": pairs[:10]}


def histogram(df: pd.DataFrame, column: str, bins: int = 20) -> dict:
    """Return histogram bin edges and counts for a numeric column."""
    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if series.empty:
        return {"bins": [], "counts": []}
    counts, edges = np.histogram(series, bins=bins)
    return {"bins": [round(float(e), 4) for e in edges], "counts": counts.tolist()}


def category_counts(df: pd.DataFrame, column: str, top: int = 10) -> dict:
    """Return the top-N value counts for a categorical column."""
    vc = df[column].astype(str).value_counts().head(top)
    return {"labels": vc.index.tolist(), "counts": vc.values.tolist()}


def trend_analysis(df: pd.DataFrame) -> dict:
    """Aggregate a numeric metric over the first datetime column, if any."""
    date_cols = datetime_columns(df)
    num_cols = numeric_columns(df)
    if not date_cols or not num_cols:
        return {"available": False}

    date_col, metric = date_cols[0], num_cols[0]
    tmp = df[[date_col, metric]].dropna().sort_values(date_col)
    if tmp.empty:
        return {"available": False}

    grouped = (
        tmp.set_index(date_col)
        .resample("D")[metric]
        .sum()
        .reset_index()
    )
    series = grouped[metric]
    if len(series) >= 2:
        x = np.arange(len(series))
        slope = float(np.polyfit(x, series.values, 1)[0])
        direction = "upward" if slope > 0 else "downward" if slope < 0 else "flat"
    else:
        slope, direction = 0.0, "flat"

    return {
        "available": True,
        "date_column": date_col,
        "metric": metric,
        "dates": grouped[date_col].dt.strftime("%Y-%m-%d").tolist(),
        "values": [round(float(v), 4) for v in series.tolist()],
        "slope": round(slope, 6),
        "direction": direction,
    }


def run_eda(df: pd.DataFrame) -> dict:
    """Bundle the core EDA outputs for the dashboard."""
    num_cols = numeric_columns(df)
    cat_cols = categorical_columns(df)
    return {
        "numeric_columns": num_cols,
        "categorical_columns": cat_cols,
        "datetime_columns": datetime_columns(df),
        "descriptive_stats": descriptive_stats(df),
        "correlation": correlation_matrix(df),
        "trend": trend_analysis(df),
        "histograms": {c: histogram(df, c) for c in num_cols[:6]},
        "category_distributions": {
            c: category_counts(df, c) for c in cat_cols[:6]
        },
    }
