from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import Alert, DeviceReading, User
from backend.schemas.api import DeviceReadingCreateRequest
from backend.services.anomaly_service import anomaly_detector
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/devices", tags=["devices"])


def _maybe_create_alerts(db: Session, user_id: str, reading: DeviceReading) -> None:
    if reading.heart_rate_bpm is not None and reading.heart_rate_bpm >= 120:
        db.add(
            Alert(
                user_id=user_id,
                severity="critical",
                category="heart_rate",
                title="High heart rate detected",
                message=f"Your heart rate is {reading.heart_rate_bpm:.0f} bpm. Consider resting and consult a doctor if this persists.",
                meta={"heart_rate_bpm": reading.heart_rate_bpm, "recorded_at": str(reading.recorded_at)},
            )
        )
    if reading.sleep_minutes is not None and reading.sleep_minutes <= 5 * 60:
        db.add(
            Alert(
                user_id=user_id,
                severity="warning",
                category="sleep",
                title="Low sleep detected",
                message=f"Sleep recorded: {reading.sleep_minutes} minutes. Aim for 7–9 hours for better preventive health outcomes.",
                meta={"sleep_minutes": reading.sleep_minutes, "recorded_at": str(reading.recorded_at)},
            )
        )
    if reading.steps is not None and reading.steps <= 2000:
        db.add(
            Alert(
                user_id=user_id,
                severity="info",
                category="activity",
                title="Low activity today",
                message=f"Steps recorded: {reading.steps}. A short walk can improve your overall health.",
                meta={"steps": reading.steps, "recorded_at": str(reading.recorded_at)},
            )
        )

    # Anomaly detection
    reading_data = [{
        'id': reading.id,
        'timestamp': reading.recorded_at,
        'heart_rate': reading.heart_rate_bpm,
        'steps': reading.steps,
        'sleep_hours': reading.sleep_minutes / 60 if reading.sleep_minutes else None,
        'weight': reading.payload.get('weight_kg'),
        'glucose': reading.payload.get('glucose_mmol'),
    }]

    anomalies = anomaly_detector.detect_anomalies(reading_data)
    for anomaly in anomalies:
        db.add(
            Alert(
                user_id=user_id,
                severity="warning",
                category="anomaly",
                title="Unusual health pattern detected",
                message=anomaly['description'],
                meta={
                    'anomaly_score': anomaly['anomaly_score'],
                    'features': anomaly['features'],
                    'recorded_at': str(reading.recorded_at)
                },
            )
        )


@router.post("/data")
def ingest_device_data(
    req: DeviceReadingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = DeviceReading(
        user_id=current_user.user_id,
        source=req.source,
        recorded_at=req.recorded_at,
        heart_rate_bpm=req.heart_rate_bpm,
        steps=req.steps,
        sleep_minutes=req.sleep_minutes,
        payload=req.payload,
    )
    db.add(row)
    _maybe_create_alerts(db, current_user.user_id, row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "id": row.id}


@router.post("/train-anomaly-detector")
def train_anomaly_detector(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Train anomaly detection model on user's historical data"""
    # Get user's historical readings
    readings = (
        db.query(DeviceReading)
        .filter(DeviceReading.user_id == current_user.user_id)
        .order_by(DeviceReading.recorded_at)
        .all()
    )

    if len(readings) < 10:
        return {"ok": False, "detail": "Not enough data to train anomaly detector. Need at least 10 readings."}

    # Prepare data for training
    data = []
    for r in readings:
        data.append({
            'heart_rate': r.heart_rate_bpm,
            'steps': r.steps,
            'sleep_hours': r.sleep_minutes / 60 if r.sleep_minutes else None,
            'weight': r.payload.get('weight_kg'),
            'glucose': r.payload.get('glucose_mmol'),
        })

    df = pd.DataFrame(data)
    anomaly_detector.train(df)

    return {"ok": True, "message": "Anomaly detector trained successfully"}

