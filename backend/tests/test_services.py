"""Unit tests for the analytics, profiling, and pipeline services."""
import numpy as np
import pandas as pd
import pytest

from app.services import (
    analytics_service,
    data_service,
    insight_service,
    llm_service,
    ml_service,
    pipeline_service,
    profiling_service,
)


@pytest.fixture()
def sample_df():
    rng = np.random.default_rng(0)
    n = 100
    x = rng.normal(50, 10, n)
    return pd.DataFrame(
        {
            "region": rng.choice(["N", "S", "E", "W"], n),
            "units": rng.integers(1, 50, n),
            "price": x,
            "revenue": x * 3 + rng.normal(0, 5, n),
        }
    )


def test_clean_removes_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    cleaned, actions = data_service.clean_dataframe(df)
    assert len(cleaned) == 2
    assert any("duplicate" in a.lower() for a in actions)


def test_outlier_detection():
    series = pd.Series([1, 2, 3, 4, 5, 1000])
    assert profiling_service.detect_outliers_iqr(series) == 1


def test_quality_report_structure(sample_df):
    report = profiling_service.build_quality_report(sample_df)
    assert 0 <= report["quality_score"] <= 100
    assert report["total_rows"] == 100
    assert len(report["columns"]) == sample_df.shape[1]


def test_correlation_matrix(sample_df):
    corr = analytics_service.correlation_matrix(sample_df)
    assert "price" in corr["columns"]
    assert corr["top_pairs"]


def test_feature_importance(sample_df):
    result = ml_service.feature_importance(sample_df, target="revenue")
    assert result["available"] is True
    assert result["importances"]


def test_pipeline_end_to_end(sample_df):
    result = pipeline_service.analyse_dataframe(sample_df, target="revenue")
    assert "quality" in result
    assert "eda" in result
    assert "insights" in result
    assert result["executive_summary"]["summary"]


def test_nl_query_fallback(sample_df):
    resp = llm_service.answer_question(sample_df, "how many rows are there?")
    assert resp["used_llm"] is False
    assert "100" in resp["answer"]


def test_insights_generated(sample_df):
    quality = profiling_service.build_quality_report(sample_df)
    eda = analytics_service.run_eda(sample_df)
    importance = ml_service.feature_importance(sample_df, "revenue")
    insights = insight_service.generate_insights(quality, eda, importance)
    assert insights
    assert all("title" in i and "severity" in i for i in insights)
