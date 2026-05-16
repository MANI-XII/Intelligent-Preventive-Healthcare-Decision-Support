from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from backend.config import settings


FEATURE_COLS = [
    "gender",
    "age",
    "hypertension",
    "heart_disease",
    "smoking_history",
    "bmi",
    "HbA1c_level",
    "blood_glucose_level",
    "activity_level",
    "sleep_hours",
]


@lru_cache(maxsize=1)
def _load_artifacts():
    diabetes_model_path = Path(settings.diabetes_model_path)
    heart_model_path = Path(settings.heart_disease_model_path)
    hypertension_model_path = Path(settings.hypertension_model_path)
    preprocessor_path = Path(settings.health_preprocessor_path)

    missing = []
    for path, name in [
        (diabetes_model_path, "diabetes model"),
        (heart_model_path, "heart disease model"),
        (hypertension_model_path, "hypertension model"),
        (preprocessor_path, "health preprocessor"),
    ]:
        if not path.exists():
            missing.append(f"{name}: {path}")
    if missing:
        raise FileNotFoundError(
            "Missing ML artifacts. Run the training script first. " + "; ".join(missing)
        )

    diabetes_model = joblib.load(diabetes_model_path)
    heart_model = joblib.load(heart_model_path)
    hypertension_model = joblib.load(hypertension_model_path)
    preprocessor = joblib.load(preprocessor_path)
    return diabetes_model, heart_model, hypertension_model, preprocessor


def _build_row(inputs: dict) -> pd.DataFrame:
    defaults = {
        "activity_level": "moderate",
        "sleep_hours": 7.0,
        "smoking_history": "never",
        "gender": "Male",
    }
    row = {c: inputs.get(c, defaults.get(c)) for c in FEATURE_COLS}
    return pd.DataFrame([row])


def predict_diabetes_probability(inputs: dict) -> float:
    diabetes_model, _, _, preprocessor = _load_artifacts()
    X = _build_row(inputs)
    X_t = preprocessor.transform(X)
    return float(diabetes_model.predict_proba(X_t)[:, 1][0])


def _map_activity_score(activity_level: str) -> float:
    level = (activity_level or "moderate").strip().lower()
    if level == "high":
        return 0.1
    if level == "low":
        return 0.85
    return 0.45


def _map_sleep_score(hours: float) -> float:
    try:
        value = float(hours)
    except Exception:
        return 0.35
    return max(0.0, min(1.0, (8.0 - value) / 6.0))


def _normalize(x: float, low: float, high: float) -> float:
    return max(0.0, min(1.0, (x - low) / (high - low))) if high > low else 0.0


def predict_heart_disease_probability(inputs: dict, diabetes_risk_prob: float | None = None) -> float:
    _, heart_model, _, preprocessor = _load_artifacts()
    X = _build_row(inputs)
    X_t = preprocessor.transform(X)
    model_prob = float(heart_model.predict_proba(X_t)[:, 1][0])

    # Dependency logic: increase heart disease risk when diabetes risk is high.
    adjustment = 0.08 if (diabetes_risk_prob or 0.0) >= 0.6 else 0.0
    return float(max(0.0, min(1.0, model_prob + adjustment)))


def predict_hypertension_probability(inputs: dict) -> float:
    _, _, hypertension_model, preprocessor = _load_artifacts()
    X = _build_row(inputs)
    X_t = preprocessor.transform(X)
    model_prob = float(hypertension_model.predict_proba(X_t)[:, 1][0])

    # mild rule-based smoothing toward current hypertension known status
    if int(inputs.get("hypertension", 0)) == 1:
        return float(max(0.0, min(1.0, model_prob + 0.05)))
    return model_prob


def get_feature_names_out() -> list[str]:
    _, _, _, preprocessor = _load_artifacts()
    return list(preprocessor.get_feature_names_out())

