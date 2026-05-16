from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import DeviceReading, PredictionHistory, User
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/health-score", tags=["health-score"])


@router.get("")
def get_health_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Preventive health score (MVP):
    - Uses latest stored prediction overall_health_score if present
    - Applies small adjustments using latest wearable readings if present
    """
    pred = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.user_id)
        .order_by(PredictionHistory.created_at.desc())
        .first()
    )
    base_score = float(pred.overall_health_score) if pred else 50.0

    reading = (
        db.query(DeviceReading)
        .filter(DeviceReading.user_id == current_user.user_id)
        .order_by(DeviceReading.recorded_at.desc())
        .first()
    )
    adj = 0.0
    wearable = None
    if reading:
        wearable = {
            "recorded_at": reading.recorded_at,
            "heart_rate_bpm": reading.heart_rate_bpm,
            "steps": reading.steps,
            "sleep_minutes": reading.sleep_minutes,
        }
        if reading.steps is not None:
            if reading.steps >= 8000:
                adj += 3.0
            elif reading.steps <= 2000:
                adj -= 3.0
        if reading.sleep_minutes is not None:
            if reading.sleep_minutes >= 7 * 60:
                adj += 2.0
            elif reading.sleep_minutes <= 5 * 60:
                adj -= 2.0
        if reading.heart_rate_bpm is not None:
            if reading.heart_rate_bpm >= 120:
                adj -= 3.0
            elif reading.heart_rate_bpm <= 50:
                adj -= 1.5

    score = max(0.0, min(100.0, base_score + adj))
    return {"ok": True, "data": {"score": round(score, 2), "base_score": round(base_score, 2), "adjustment": round(adj, 2), "wearable": wearable}}

