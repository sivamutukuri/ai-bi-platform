"""LLM integration for natural-language querying and summaries.

Uses an OpenAI-compatible client when an API key is configured, and
falls back to deterministic pandas-based logic so the platform remains
fully functional without an LLM key.
"""
from __future__ import annotations

import io
import re
from contextlib import redirect_stdout

import pandas as pd

from app.core.config import settings
from app.core.logging import logger


def _llm_available() -> bool:
    return bool(settings.LLM_API_KEY)


def _get_client():  # pragma: no cover - requires network/key
    from openai import OpenAI

    return OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL or None,
    )


def _dataset_context(df: pd.DataFrame) -> str:
    cols = ", ".join(f"{c} ({df[c].dtype})" for c in df.columns)
    return f"Columns: {cols}. Rows: {len(df)}."


def answer_question(df: pd.DataFrame, question: str) -> dict:
    """Answer a natural-language question about the DataFrame."""
    if _llm_available():
        try:
            return _answer_with_llm(df, question)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM NL query failed, falling back: %s" % exc)
    return _answer_with_heuristics(df, question)


def _answer_with_llm(df: pd.DataFrame, question: str) -> dict:  # pragma: no cover
    client = _get_client()
    prompt = (
        "You are a data analyst. Given a pandas DataFrame named df with "
        f"{_dataset_context(df)} write a single line of python using df that "
        "computes the answer. Return ONLY code, no explanation.\n"
        f"Question: {question}"
    )
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    code = resp.choices[0].message.content.strip()
    code = re.sub(r"^```(python)?|```$", "", code, flags=re.MULTILINE).strip()
    result = _safe_eval(df, code)
    return {
        "answer": str(result),
        "used_llm": True,
        "generated_code": code,
        "result_preview": _preview(result),
    }


def _answer_with_heuristics(df: pd.DataFrame, question: str) -> dict:
    """Keyword-based fallback covering common analytical questions."""
    q = question.lower()
    numeric = df.select_dtypes(include="number")

    def match(col_hint: str) -> str | None:
        for col in df.columns:
            if col.lower() in q or col_hint in col.lower():
                return col
        return None

    if any(k in q for k in ("how many rows", "number of rows", "count of rows")):
        answer = f"The dataset has {len(df)} rows."
    elif "average" in q or "mean" in q:
        col = next((c for c in numeric.columns if c.lower() in q), None)
        answer = (
            f"The average of {col} is {round(df[col].mean(), 4)}."
            if col
            else "Please specify a numeric column for the average."
        )
    elif "max" in q or "highest" in q:
        col = next((c for c in numeric.columns if c.lower() in q), None)
        answer = (
            f"The maximum of {col} is {df[col].max()}."
            if col
            else "Please specify a numeric column."
        )
    elif "min" in q or "lowest" in q:
        col = next((c for c in numeric.columns if c.lower() in q), None)
        answer = (
            f"The minimum of {col} is {df[col].min()}."
            if col
            else "Please specify a numeric column."
        )
    elif "sum" in q or "total" in q:
        col = next((c for c in numeric.columns if c.lower() in q), None)
        answer = (
            f"The total of {col} is {round(df[col].sum(), 4)}."
            if col
            else "Please specify a numeric column."
        )
    else:
        answer = (
            "I could not confidently parse that question without an LLM key. "
            f"The dataset has {len(df)} rows and {df.shape[1]} columns."
        )

    return {
        "answer": answer,
        "used_llm": False,
        "generated_code": None,
        "result_preview": None,
    }


def _safe_eval(df: pd.DataFrame, code: str):  # pragma: no cover
    allowed = {"df": df, "pd": pd}
    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            return eval(code, {"__builtins__": {}}, allowed)  # noqa: S307
        except Exception:  # noqa: BLE001
            exec(code, {"__builtins__": {}}, allowed)  # noqa: S102
    return buf.getvalue().strip() or "Executed."


def _preview(result):
    if isinstance(result, pd.DataFrame):
        return result.head(10).to_dict(orient="records")
    if isinstance(result, pd.Series):
        return result.head(10).reset_index().to_dict(orient="records")
    return None


def executive_summary(quality: dict, eda: dict, insights: list[dict]) -> dict:
    """Generate an executive summary, optionally via the LLM."""
    if _llm_available():
        try:
            return _summary_with_llm(quality, eda, insights)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM summary failed, falling back: %s" % exc)
    return _summary_with_template(quality, eda, insights)


def _summary_with_llm(quality, eda, insights) -> dict:  # pragma: no cover
    client = _get_client()
    findings = "\n".join(f"- {i['title']}: {i['detail']}" for i in insights)
    prompt = (
        "Write a concise executive summary (max 180 words) for business "
        "stakeholders based on these data findings:\n"
        f"Rows: {quality.get('total_rows')}, Columns: "
        f"{quality.get('total_columns')}, Quality: "
        f"{quality.get('quality_score')}/100.\nFindings:\n{findings}"
    )
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return {"summary": resp.choices[0].message.content.strip(), "used_llm": True}


def _summary_with_template(quality, eda, insights) -> dict:
    lines = [
        f"This dataset contains {quality.get('total_rows', 0)} records across "
        f"{quality.get('total_columns', 0)} columns with an overall data "
        f"quality score of {quality.get('quality_score', 0)}/100.",
    ]
    if quality.get("total_missing"):
        lines.append(
            f"There are {quality['total_missing']} missing values that may "
            "require attention before deeper analysis."
        )
    trend = eda.get("trend", {})
    if trend.get("available"):
        lines.append(
            f"The primary metric ({trend['metric']}) shows a "
            f"{trend['direction']} trend over time."
        )
    key = [i for i in insights if i["severity"] != "info"][:2]
    for i in key:
        lines.append(i["detail"])
    lines.append(
        "Overall, the data is suitable for exploratory analysis; addressing "
        "the highlighted quality issues will improve reliability."
    )
    return {"summary": " ".join(lines), "used_llm": False}
