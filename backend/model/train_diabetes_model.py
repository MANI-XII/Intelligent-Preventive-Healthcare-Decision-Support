from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier


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

TARGET_COLUMNS = ["diabetes", "heart_disease", "hypertension"]
MODEL_NAMES = {
    "diabetes": "diabetes_model.joblib",
    "heart_disease": "heart_disease_model.joblib",
    "hypertension": "hypertension_model.joblib",
}


def build_preprocessor() -> ColumnTransformer:
    numeric_features = [
        "age",
        "hypertension",
        "heart_disease",
        "bmi",
        "HbA1c_level",
        "blood_glucose_level",
        "sleep_hours",
    ]
    categorical_features = ["gender", "smoking_history", "activity_level"]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )


def _ensure_behavioral_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "activity_level" not in df.columns:
        df["activity_level"] = np.where(df["bmi"].astype(float) >= 30.0, "low", "moderate")
    if "sleep_hours" not in df.columns:
        df["sleep_hours"] = np.clip(7.5 - (df["bmi"].astype(float) - 24.0) * 0.08, 4.0, 9.0)
    return df


def _train_model(X_train, y_train, X_test, y_test, output_path: Path) -> dict:
    model = RandomForestClassifier(n_estimators=200, max_depth=9, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
    }
    joblib.dump(model, output_path)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset_path",
        type=str,
        default=str(Path(__file__).resolve().parents[2] / "diabetes_prediction_dataset.csv"),
    )
    parser.add_argument("--output_dir", type=str, default=str(Path(__file__).resolve().parent))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.dataset_path)
    df = df.replace("No Info", np.nan)
    df = _ensure_behavioral_features(df)

    for c in ["age", "bmi", "HbA1c_level", "blood_glucose_level", "hypertension", "heart_disease", "sleep_hours"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    X = df[FEATURE_COLS]
    metadata = {
        "feature_names": FEATURE_COLS,
        "numeric_features": ["age", "hypertension", "heart_disease", "bmi", "HbA1c_level", "blood_glucose_level", "sleep_hours"],
        "categorical_features": ["gender", "smoking_history", "activity_level"],
        "models": {},
    }

    preprocessor = build_preprocessor()
    X_prepared = preprocessor.fit_transform(X)

    for target in TARGET_COLUMNS:
        if target not in df.columns:
            raise ValueError(f"Expected dataset to contain target column '{target}'")

        y = df[target].astype(int)
        X_train, X_test, y_train, y_test = train_test_split(
            X_prepared, y, test_size=0.2, random_state=42, stratify=y
        )
        model_output_path = output_dir / MODEL_NAMES[target]
        metrics = _train_model(X_train, y_train, X_test, y_test, model_output_path)
        metadata["models"][target] = {
            "model_path": str(model_output_path.name),
            "metrics": metrics,
        }
        print(f"Trained {target} model. Metrics: {metrics}")

    preprocessor_path = output_dir / "health_preprocessor.joblib"
    joblib.dump(preprocessor, preprocessor_path)
    metadata["preprocessor_path"] = str(preprocessor_path.name)

    metadata_path = output_dir / "health_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))

    print(f"Saved preprocessor: {preprocessor_path}")
    print(f"Saved metadata: {metadata_path}")


if __name__ == "__main__":
    main()

