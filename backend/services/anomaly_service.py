from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any
import os
from pathlib import Path
from sqlalchemy.orm import Session

from backend.db.models import PredictionHistory


class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = Path(__file__).resolve().parent.parent / "model" / "anomaly_detector.joblib"
        self.scaler_path = Path(__file__).resolve().parent.parent / "model" / "anomaly_scaler.joblib"

    def train(self, data: pd.DataFrame) -> None:
        """Train anomaly detection model on historical data"""
        # Features for anomaly detection
        features = ['heart_rate', 'steps', 'sleep_hours', 'weight', 'glucose']
        X = data[features].dropna()

        if len(X) < 10:
            # Not enough data for training
            return

        # Scale the data
        X_scaled = self.scaler.fit_transform(X)

        # Train Isolation Forest
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,  # Assume 10% anomalies
            random_state=42
        )
        self.model.fit(X_scaled)
        self.is_trained = True

        # Save model
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

    def load_model(self) -> None:
        """Load pre-trained model"""
        if self.model_path.exists() and self.scaler_path.exists():
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.is_trained = True

    def detect_anomalies(self, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in new readings"""
        if not self.is_trained:
            self.load_model()
            if not self.is_trained:
                return []  # No model available

        anomalies = []
        for reading in readings:
            features = {
                'heart_rate': reading.get('heart_rate'),
                'steps': reading.get('steps'),
                'sleep_hours': reading.get('sleep_hours'),
                'weight': reading.get('weight'),
                'glucose': reading.get('glucose')
            }

            # Check if we have enough features
            feature_values = [v for v in features.values() if v is not None]
            if len(feature_values) < 3:  # Need at least 3 features
                continue

            # Prepare data for prediction
            X = pd.DataFrame([features])
            X_scaled = self.scaler.transform(X.fillna(X.mean()))

            # Predict anomaly (-1 for anomaly, 1 for normal)
            prediction = self.model.predict(X_scaled)[0]

            if prediction == -1:  # Anomaly detected
                anomaly_score = self.model.decision_function(X_scaled)[0]
                anomalies.append({
                    'reading_id': reading.get('id'),
                    'timestamp': reading.get('timestamp'),
                    'anomaly_score': float(anomaly_score),
                    'features': features,
                    'description': self._get_anomaly_description(features)
                })

        return anomalies

    def _get_anomaly_description(self, features: Dict[str, float]) -> str:
        """Generate human-readable description of the anomaly"""
        descriptions = []

        if features.get('heart_rate') and features['heart_rate'] > 120:
            descriptions.append("elevated heart rate")
        elif features.get('heart_rate') and features['heart_rate'] < 50:
            descriptions.append("abnormally low heart rate")

        if features.get('steps') and features['steps'] < 500:
            descriptions.append("very low activity")
        elif features.get('steps') and features['steps'] > 20000:
            descriptions.append("extremely high activity")

        if features.get('sleep_hours') and features['sleep_hours'] < 4:
            descriptions.append("insufficient sleep")
        elif features.get('sleep_hours') and features['sleep_hours'] > 12:
            descriptions.append("excessive sleep")

        if features.get('glucose') and features['glucose'] > 200:
            descriptions.append("high blood glucose")
        elif features.get('glucose') and features['glucose'] < 70:
            descriptions.append("low blood glucose")

        if descriptions:
            return f"Unusual pattern detected: {', '.join(descriptions)}"
        else:
            return "Unusual health pattern detected"


def detect_clinical_anomalies(user_id: str, inputs: Any, db: Session) -> dict:
    """Compare the current clinical input against thresholds and recent history."""
    anomalies: list[str] = []

    if inputs.blood_glucose_level >= 200:
        anomalies.append("Critical glucose level detected; consult a clinician.")
    if inputs.bmi >= 35:
        anomalies.append("Severe obesity marker detected; weight reduction is recommended.")
    if inputs.hba1c_level >= 7.0:
        anomalies.append("HbA1c is in a high-risk range; review glucose control.")
    if inputs.activity_level == "low" and inputs.bmi >= 28:
        anomalies.append("Low activity plus high BMI indicates accelerating metabolic risk.")

    history = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == user_id)
        .order_by(PredictionHistory.created_at.desc())
        .limit(4)
        .all()
    )

    if history:
        latest = history[0]
        glucose_delta = abs(inputs.blood_glucose_level - float(latest.blood_glucose_level))
        bmi_delta = abs(inputs.bmi - float(latest.bmi))
        if glucose_delta >= 30:
            anomalies.append("Glucose change exceeds 30 mg/dL from your last submission.")
        if bmi_delta >= 2.0:
            anomalies.append("BMI change is unusually large for a short interval.")

    return {
        "anomaly_detected": len(anomalies) > 0,
        "anomalies": anomalies,
    }


# Global instance
anomaly_detector = AnomalyDetector()