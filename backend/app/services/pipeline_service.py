"""End-to-end analysis pipeline orchestrating all services."""
from __future__ import annotations

import pandas as pd

from app.services import (
    analytics_service,
    data_service,
    insight_service,
    llm_service,
    ml_service,
    profiling_service,
)


def analyse_dataframe(df: pd.DataFrame, target: str | None = None) -> dict:
    """Run cleaning, profiling, EDA, ML, and insight generation."""
    cleaned, clean_actions = data_service.clean_dataframe(df)

    quality = profiling_service.build_quality_report(cleaned)
    eda = analytics_service.run_eda(cleaned)
    importance = ml_service.feature_importance(cleaned, target)
    insights = insight_service.generate_insights(quality, eda, importance)
    kpis = insight_service.build_kpis(quality, eda)
    summary = llm_service.executive_summary(quality, eda, insights)

    return {
        "cleaning_actions": clean_actions,
        "quality": quality,
        "eda": eda,
        "feature_importance": importance,
        "insights": insights,
        "kpis": kpis,
        "executive_summary": summary,
        "schema": profiling_service.build_schema(cleaned),
        "row_count": int(len(cleaned)),
        "column_count": int(cleaned.shape[1]),
    }


def load_dataset_dataframe(file_path: str, source_type: str) -> pd.DataFrame:
    """Convenience loader used by the API layer."""
    return data_service.load_dataframe(file_path, source_type)
