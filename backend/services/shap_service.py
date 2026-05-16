from __future__ import annotations

import base64
import io
from functools import lru_cache
from pathlib import Path

import joblib
import matplotlib

# Backend rendering for servers (no GUI).
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

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


def _dataset_path() -> Path:
    # backend/services -> backend -> repo root
    return Path(__file__).resolve().parents[2] / "diabetes_prediction_dataset.csv"


@lru_cache(maxsize=1)
def _load_artifacts():
    model_path = Path(settings.diabetes_model_path)
    preprocessor_path = Path(settings.diabetes_preprocessor_path)
    model = joblib.load(model_path)
    preprocessor = joblib.load(preprocessor_path)
    return model, preprocessor


@lru_cache(maxsize=1)
def _background_transformed(sample_size: int = 600) -> tuple[np.ndarray, list[str]]:
    """
    Background for SHAP expectation. We sample from the training dataset
    to keep runtime reasonable.
    """
    model, preprocessor = _load_artifacts()
    df = pd.read_csv(_dataset_path())
    df = df.replace("No Info", np.nan)
    for c in ["age", "bmi", "HbA1c_level", "blood_glucose_level", "hypertension", "heart_disease"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    if "activity_level" not in df.columns:
        df["activity_level"] = np.where(df["bmi"].astype(float) >= 30.0, "low", "moderate")
    if "sleep_hours" not in df.columns:
        df["sleep_hours"] = np.clip(7.5 - (df["bmi"].astype(float) - 24.0) * 0.08, 4.0, 9.0)

    X = df[FEATURE_COLS]
    if len(X) > sample_size:
        X = X.sample(sample_size, random_state=42)
    X_t = preprocessor.transform(X)
    feature_names_out = list(preprocessor.get_feature_names_out())
    return X_t, feature_names_out


def _extract_class1_shap_values(shap_values, n_features: int) -> np.ndarray:
    """
    shap.TreeExplainer returns different shapes depending on model and shap version.
    We normalize to (n_features,) for a single sample.
    """
    if isinstance(shap_values, list) and len(shap_values) >= 2:
        # Binary classification often returns [class0, class1]
        values_class1 = shap_values[1]
        # values_class1 can be (n_samples, n_features)
        if values_class1.ndim == 2:
            return values_class1[0]
        if values_class1.ndim == 1:
            return values_class1
    # Some versions return a single array with class dimension at the end:
    #   (n_samples, n_features, n_classes)
    if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        # Defensive: if only one class dim exists, fall back to index 0.
        class_dim = shap_values.shape[-1]
        class_index = 1 if class_dim > 1 else 0
        return shap_values[0, :, class_index]

    # Some versions return a single array for the positive class already.
    if hasattr(shap_values, "ndim") and shap_values.ndim == 2:
        return shap_values[0]
    if hasattr(shap_values, "ndim") and shap_values.ndim == 1:
        return shap_values
    raise ValueError("Unsupported SHAP values format for class extraction.")


def shap_explain_single_instance(inputs: dict) -> dict:
    model, preprocessor = _load_artifacts()
    X = pd.DataFrame([{c: inputs.get(c) for c in FEATURE_COLS}])
    X_t = preprocessor.transform(X)

    background_t, feature_names_out = _background_transformed()

    # For tree models, TreeExplainer is appropriate.
    # We keep default model_output for compatibility; values are still interpretable relatively.
    explainer = shap.TreeExplainer(model, background_t)
    shap_values = explainer.shap_values(X_t)

    n_features = len(feature_names_out)
    shap_vec = _extract_class1_shap_values(shap_values, n_features=n_features)

    # Aggregate contributions into the requested human-friendly groups.
    shap_vec = np.asarray(shap_vec).reshape(-1)

    def sum_by_substring(substr: str) -> float:
        mask = [substr.lower() in name.lower() for name in feature_names_out]
        if not any(mask):
            return 0.0
        return float(np.sum(shap_vec[np.array(mask)]))

    age_contrib = sum_by_substring("age")
    bmi_contrib = sum_by_substring("bmi")
    glucose_contrib = sum_by_substring("blood_glucose_level")
    hba1c_contrib = sum_by_substring("HbA1c_level".lower())
    smoking_contrib = sum_by_substring("smoking_history")
    activity_contrib = sum_by_substring("activity_level")
    sleep_contrib = sum_by_substring("sleep_hours")

    # For "feature importance", we provide absolute contribution magnitude ranking.
    contributions = {
        "Age": age_contrib,
        "BMI": bmi_contrib,
        "Glucose": glucose_contrib,
        "HbA1c": hba1c_contrib,
        "Smoking": smoking_contrib,
        "Activity": activity_contrib,
        "Sleep": sleep_contrib,
    }

    feature_importance = dict(
        sorted(
            {k: abs(v) for k, v in contributions.items()}.items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )

    # Build a small chart showing signed contributions.
    items = list(contributions.items())
    items.sort(key=lambda kv: abs(kv[1]), reverse=True)
    labels = [k for k, _ in items]
    values = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["#ef4444" if v > 0 else "#3b82f6" for v in values]
    ax.bar(labels, values, color=colors)
    ax.axhline(0, color="#111827", linewidth=1)
    ax.set_title("SHAP contributions (single prediction)")
    ax.set_ylabel("Contribution")
    ax.tick_params(axis="x", rotation=20)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160)
    plt.close(fig)
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode("utf-8")

    # Base value for reference (expected_value). Might be scalar or array.
    expected_value = explainer.expected_value
    if isinstance(expected_value, (list, tuple, np.ndarray)):
        base_value = float(expected_value[1]) if len(expected_value) > 1 else float(expected_value[0])
    else:
        base_value = float(expected_value)

    ordered_features = [k for k in feature_importance.keys()]
    top_features = ordered_features[:2] if ordered_features else []
    causal_explanation = (
        f"High {top_features[0]} and {top_features[1]} are the main causes of risk." if len(top_features) >= 2 else
        f"{top_features[0]} is a leading contributor to risk." if len(top_features) == 1 else
        "Review the feature contributions for why this prediction was made."
    )

    return {
        "base_value": base_value,
        "contributions": contributions,
        "feature_importance": feature_importance,
        "causal_explanation": causal_explanation,
        "shap_chart_base64": chart_base64,
    }

