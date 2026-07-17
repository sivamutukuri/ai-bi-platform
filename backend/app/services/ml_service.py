"""Machine-learning utilities: automatic feature importance.

Chooses the best available gradient-boosting backend (XGBoost or
LightGBM) with a scikit-learn RandomForest fallback, auto-detecting
whether the target is categorical (classification) or continuous
(regression).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.preprocessing import LabelEncoder

from app.core.logging import logger

try:  # pragma: no cover - optional dependency
    from xgboost import XGBClassifier, XGBRegressor

    _HAS_XGB = True
except Exception:  # noqa: BLE001
    _HAS_XGB = False

try:  # pragma: no cover - optional dependency
    from lightgbm import LGBMClassifier, LGBMRegressor

    _HAS_LGBM = True
except Exception:  # noqa: BLE001
    _HAS_LGBM = False


def _is_classification(y: pd.Series) -> bool:
    if y.dtype == object or str(y.dtype).startswith("category"):
        return True
    return y.nunique() <= max(10, int(0.05 * len(y)))


def _encode_features(x: pd.DataFrame) -> pd.DataFrame:
    encoded = x.copy()
    for col in encoded.select_dtypes(include=["object", "category"]).columns:
        encoded[col] = LabelEncoder().fit_transform(encoded[col].astype(str))
    for col in encoded.select_dtypes(include=["datetime", "datetimetz"]).columns:
        encoded[col] = encoded[col].astype("int64", errors="ignore")
    return encoded.fillna(encoded.median(numeric_only=True)).fillna(0)


def _select_model(classification: bool):
    if classification:
        if _HAS_XGB:
            return XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.9, eval_metric="logloss", verbosity=0,
            ), "xgboost"
        if _HAS_LGBM:
            return LGBMClassifier(n_estimators=200, verbose=-1), "lightgbm"
        return RandomForestClassifier(n_estimators=200, random_state=42), "random_forest"
    if _HAS_XGB:
        return XGBRegressor(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.9, verbosity=0,
        ), "xgboost"
    if _HAS_LGBM:
        return LGBMRegressor(n_estimators=200, verbose=-1), "lightgbm"
    return RandomForestRegressor(n_estimators=200, random_state=42), "random_forest"


def feature_importance(df: pd.DataFrame, target: str | None = None) -> dict:
    """Compute feature importance for a target column.

    If no target is supplied, the last numeric column is used as a proxy.
    """
    if df.shape[1] < 2 or len(df) < 10:
        return {"available": False, "reason": "Not enough data for modelling."}

    if target is None or target not in df.columns:
        numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric:
            return {"available": False, "reason": "No numeric target available."}
        target = numeric[-1]

    y = df[target].dropna()
    x = df.loc[y.index].drop(columns=[target])
    if x.empty:
        return {"available": False, "reason": "No feature columns."}

    x_enc = _encode_features(x)
    classification = _is_classification(y)
    if classification:
        y = LabelEncoder().fit_transform(y.astype(str))

    model, backend = _select_model(classification)
    try:
        model.fit(x_enc, y)
        importances = getattr(model, "feature_importances_", None)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Feature importance failed: %s" % exc)
        return {"available": False, "reason": str(exc)}

    if importances is None:
        return {"available": False, "reason": "Model exposed no importances."}

    items = sorted(
        (
            {"feature": col, "importance": round(float(imp), 6)}
            for col, imp in zip(x_enc.columns, importances)
        ),
        key=lambda d: d["importance"],
        reverse=True,
    )
    return {
        "available": True,
        "target": target,
        "task": "classification" if classification else "regression",
        "backend": backend,
        "importances": items[:20],
    }
