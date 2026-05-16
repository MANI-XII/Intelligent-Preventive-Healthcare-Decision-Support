from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import HealthRecord, PredictionHistory, User
from backend.schemas.api import (
    HealthRecordCreateRequest,
    HealthRecordResponse,
    PredictionHistoryPoint,
    PredictionHistorySummary,
)
from backend.services.pipeline_service import predict_pipeline
from backend.utils.auth import get_current_user
from backend.utils.risk_scoring import UserHealthInputs

router = APIRouter(prefix="/health-data", tags=["health-data"])


def _normalize_blood_pressure(blood_pressure: str | None) -> str | None:
    if not blood_pressure:
        return None
    parts = re.findall(r"\d+", blood_pressure)
    if len(parts) >= 2:
        return f"{int(parts[0])}/{int(parts[1])}"
    return blood_pressure.strip()


def _estimate_hypertension_from_bp(blood_pressure: str | None) -> int | None:
    if not blood_pressure:
        return None
    parts = re.findall(r"\d+", blood_pressure)
    if len(parts) >= 2:
        systolic = int(parts[0])
        diastolic = int(parts[1])
        if systolic >= 140 or diastolic >= 90:
            return 1
        if systolic >= 130 or diastolic >= 85:
            return 1
    return 0


def _build_inputs(req: HealthRecordCreateRequest) -> UserHealthInputs:
    hypertension = req.hypertension
    if hypertension == 0 and req.blood_pressure:
        estimated = _estimate_hypertension_from_bp(req.blood_pressure)
        if estimated is not None:
            hypertension = estimated

    return UserHealthInputs(
        gender=req.gender,
        age=float(req.age),
        bmi=float(req.bmi),
        blood_glucose_level=float(req.blood_glucose_level),
        hba1c_level=float(req.hba1c_level),
        smoking_history=req.smoking_history,
        hypertension=int(hypertension),
        heart_disease=int(req.heart_disease),
        activity_level=req.activity_level,
        sleep_hours=float(req.sleep_hours),
        stress_level=req.stress_level,
        diet_type=req.diet_type,
        work_type=req.work_type,
        blood_pressure=_normalize_blood_pressure(req.blood_pressure),
    )


def _prediction_summary_from_row(row: PredictionHistory) -> PredictionHistorySummary:
    return {
        "id": row.id,
        "created_at": row.created_at,
        "diabetes_risk": row.diabetes_risk,
        "diabetes_risk_level": row.diabetes_risk_level,
        "heart_risk_level": row.heart_risk_level,
        "overall_health_score": row.overall_health_score,
        "bmi_status": row.bmi_status,
        "risk_breakdown": row.risk_breakdown,
    }


def _trend_point_from_row(row: PredictionHistory) -> PredictionHistoryPoint:
    hypertension_risk = 0.0
    heart_disease_risk = 0.0
    if isinstance(row.risk_breakdown, dict):
        hypertension_risk = row.risk_breakdown.get("hypertension_risk", {}).get("score", 0.0)
        heart_disease_risk = row.risk_breakdown.get("heart_disease_risk", {}).get("score", 0.0)

    return {
        "created_at": row.created_at,
        "diabetes_risk": row.diabetes_risk,
        "heart_disease_risk": heart_disease_risk,
        "hypertension_risk": hypertension_risk,
        "overall_health_score": row.overall_health_score,
    }


def _health_record_response(row: HealthRecord) -> HealthRecordResponse:
    return {
        "id": row.id,
        "created_at": row.created_at,
        "recorded_at": row.recorded_at,
        "gender": row.gender,
        "age": row.age,
        "bmi": row.bmi,
        "blood_glucose_level": row.blood_glucose_level,
        "hba1c_level": row.hba1c_level,
        "smoking_history": row.smoking_history,
        "hypertension": row.hypertension,
        "heart_disease": row.heart_disease,
        "activity_level": row.activity_level,
        "sleep_hours": row.sleep_hours,
        "stress_level": row.stress_level,
        "diet_type": row.diet_type,
        "work_type": row.work_type,
        "blood_pressure": row.blood_pressure,
        "notes": row.notes,
    }


@router.post("", response_model=dict)
def create_health_record(
    req: HealthRecordCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        normalized_bp = _normalize_blood_pressure(req.blood_pressure)
        record_hypertension = req.hypertension
        if record_hypertension == 0 and normalized_bp:
            estimated = _estimate_hypertension_from_bp(normalized_bp)
            if estimated == 1:
                record_hypertension = 1

        record = HealthRecord(
            user_id=current_user.user_id,
            created_at=datetime.utcnow(),
            recorded_at=datetime.utcnow(),
            gender=req.gender,
            age=req.age,
            bmi=req.bmi,
            blood_glucose_level=req.blood_glucose_level,
            hba1c_level=req.hba1c_level,
            smoking_history=req.smoking_history,
            hypertension=record_hypertension,
            heart_disease=req.heart_disease,
            activity_level=req.activity_level,
            sleep_hours=req.sleep_hours,
            stress_level=req.stress_level,
            diet_type=req.diet_type,
            work_type=req.work_type,
            blood_pressure=normalized_bp,
            notes=req.notes,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        inputs = _build_inputs(req)
        payload = predict_pipeline(inputs=inputs, user_id=current_user.user_id, db=db)

        history_row = PredictionHistory(
            user_id=current_user.user_id,
            created_at=datetime.utcnow(),
            gender=req.gender,
            age=req.age,
            bmi=req.bmi,
            blood_glucose_level=req.blood_glucose_level,
            hba1c_level=req.hba1c_level,
            smoking_history=req.smoking_history,
            hypertension=record_hypertension,
            heart_disease=req.heart_disease,
            diabetes_risk=payload.get("diabetes_risk"),
            diabetes_risk_level=payload.get("diabetes_risk_level"),
            heart_risk_level=payload["disease_scores"]["heart_disease"]["risk_level"],
            bmi_status=payload["rule_risks"]["bmi_status"],
            overall_health_score=float(payload["health_index"]["score"]),
            risk_breakdown={
                **payload["rule_risks"],
                "health_index": payload["health_index"],
                "risk_forecast": payload["risk_forecast"],
                "anomalies": payload["anomalies"],
                "adaptive_insights": payload["adaptive_insights"],
            },
            recommendations=payload["recommendations"],
            shap_explanations=payload.get("explanations"),
        )
        db.add(history_row)
        db.commit()
        db.refresh(history_row)

        return {
            "ok": True,
            "health_record": _health_record_response(record),
            "prediction": payload,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to save health record: {e}")


@router.get("/latest", response_model=dict)
def get_latest_health_record(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == current_user.user_id)
        .order_by(HealthRecord.recorded_at.desc(), HealthRecord.id.desc())
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No health records found for this user.")

    inputs = UserHealthInputs(
        gender=record.gender,
        age=float(record.age),
        bmi=float(record.bmi),
        blood_glucose_level=float(record.blood_glucose_level),
        hba1c_level=float(record.hba1c_level),
        smoking_history=record.smoking_history,
        hypertension=int(record.hypertension),
        heart_disease=int(record.heart_disease),
        activity_level=record.activity_level,
        sleep_hours=float(record.sleep_hours),
        stress_level=record.stress_level,
        diet_type=record.diet_type,
        work_type=record.work_type,
        blood_pressure=record.blood_pressure,
    )
    payload = predict_pipeline(inputs=inputs, user_id=current_user.user_id, db=db)

    return {
        "ok": True,
        "health_record": _health_record_response(record),
        "prediction": payload,
    }


@router.get("/history", response_model=dict)
def list_prediction_history(
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.user_id)
        .order_by(PredictionHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"ok": True, "history": [_prediction_summary_from_row(row) for row in rows]}


@router.get("/trend", response_model=dict)
def get_prediction_trend(
    limit: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.user_id)
        .order_by(PredictionHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"ok": True, "trend": [_trend_point_from_row(row) for row in reversed(rows)]}
