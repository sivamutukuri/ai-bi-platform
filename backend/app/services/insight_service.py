"""Rule-based automatic insight generation from analysis outputs."""
from __future__ import annotations


def generate_insights(
    quality: dict, eda: dict, importance: dict
) -> list[dict]:
    """Derive human-readable insights from computed analysis artifacts."""
    insights: list[dict] = []

    score = quality.get("quality_score", 0)
    if score >= 90:
        sev = "info"
        msg = "Dataset quality is excellent and ready for analysis."
    elif score >= 70:
        sev = "warning"
        msg = "Dataset quality is acceptable but has minor issues to review."
    else:
        sev = "critical"
        msg = "Dataset quality is low; cleaning is strongly recommended."
    insights.append(
        {"title": f"Data quality score: {score}/100", "detail": msg, "severity": sev}
    )

    if quality.get("duplicate_rows"):
        insights.append(
            {
                "title": "Duplicate records present",
                "detail": (
                    f"{quality['duplicate_rows']} duplicate rows were found and "
                    "should be de-duplicated before modelling."
                ),
                "severity": "warning",
            }
        )

    for col in quality.get("columns", []):
        if col["missing_pct"] >= 40:
            insights.append(
                {
                    "title": f"High missingness in '{col['name']}'",
                    "detail": (
                        f"{col['missing_pct']}% of values are missing; consider "
                        "imputation or dropping the column."
                    ),
                    "severity": "critical",
                }
            )

    top_pairs = eda.get("correlation", {}).get("top_pairs", [])
    for pair in top_pairs[:3]:
        if abs(pair["corr"]) >= 0.7:
            rel = "positively" if pair["corr"] > 0 else "negatively"
            insights.append(
                {
                    "title": (
                        f"Strong correlation: {pair['x']} & {pair['y']}"
                    ),
                    "detail": (
                        f"These features are {rel} correlated "
                        f"(r = {pair['corr']}), which may indicate redundancy."
                    ),
                    "severity": "info",
                }
            )

    trend = eda.get("trend", {})
    if trend.get("available"):
        insights.append(
            {
                "title": f"{trend['metric']} trend is {trend['direction']}",
                "detail": (
                    f"Over the observed period, {trend['metric']} shows a "
                    f"{trend['direction']} trend (slope {trend['slope']})."
                ),
                "severity": "info",
            }
        )

    if importance.get("available"):
        top = importance["importances"][:3]
        names = ", ".join(i["feature"] for i in top)
        insights.append(
            {
                "title": f"Key drivers of {importance['target']}",
                "detail": (
                    f"The most influential features are: {names} "
                    f"(model: {importance['backend']})."
                ),
                "severity": "info",
            }
        )

    return insights


def build_kpis(quality: dict, eda: dict) -> list[dict]:
    """Build KPI card definitions for the dashboard."""
    corr = eda.get("correlation", {}).get("top_pairs", [])
    strongest = corr[0]["corr"] if corr else 0.0
    return [
        {"label": "Rows", "value": quality.get("total_rows", 0), "icon": "rows"},
        {"label": "Columns", "value": quality.get("total_columns", 0), "icon": "cols"},
        {
            "label": "Quality Score",
            "value": quality.get("quality_score", 0),
            "suffix": "/100",
            "icon": "quality",
        },
        {
            "label": "Missing Values",
            "value": quality.get("total_missing", 0),
            "icon": "missing",
        },
        {
            "label": "Duplicates",
            "value": quality.get("duplicate_rows", 0),
            "icon": "dup",
        },
        {
            "label": "Max Correlation",
            "value": round(abs(strongest), 2),
            "icon": "corr",
        },
    ]
