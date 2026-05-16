from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import PredictionHistory, User
from backend.schemas.api import PredictRequest
from backend.services.pipeline_service import predict_pipeline
from backend.utils.auth import get_current_user
from backend.utils.risk_scoring import UserHealthInputs

router = APIRouter()


def _prob_to_level(prob: float) -> str:
    if prob >= 0.66:
        return "High"
    if prob >= 0.33:
        return "Moderate"
    return "Low"


def _inputs_from_request(req: PredictRequest) -> UserHealthInputs:
    return UserHealthInputs(
        gender=req.gender,
        age=float(req.age),
        bmi=float(req.bmi),
        blood_glucose_level=float(req.blood_glucose_level),
        hba1c_level=float(req.hba1c_level),
        smoking_history=req.smoking_history,
        hypertension=int(req.hypertension),
        heart_disease=int(req.heart_disease),
        activity_level=req.activity_level,
        sleep_hours=float(req.sleep_hours),
        stress_level=req.stress_level,
        diet_type=req.diet_type,
        work_type=req.work_type,
        blood_pressure=req.blood_pressure,
    )


@router.post("/predict")
def predict_health(
    req: PredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        inputs = _inputs_from_request(req)
        payload = predict_pipeline(inputs=inputs, user_id=current_user.user_id, db=db)

        risk_breakdown = payload["rule_risks"].copy()
        risk_breakdown["health_index"] = payload["health_index"]
        risk_breakdown["risk_forecast"] = payload["risk_forecast"]
        risk_breakdown["anomalies"] = payload["anomalies"]
        risk_breakdown["adaptive_insights"] = payload["adaptive_insights"]

        diabetes_risk_value = payload.get(
            "diabetes_risk",
            payload["disease_scores"]["diabetes"]["probability"],
        )
        diabetes_risk_level_value = payload.get(
            "diabetes_risk_level",
            payload["disease_scores"]["diabetes"]["risk_level"],
        )

        db_row = PredictionHistory(
            user_id=current_user.user_id,
            created_at=dt.datetime.utcnow(),
            gender=req.gender,
            age=req.age,
            bmi=req.bmi,
            blood_glucose_level=req.blood_glucose_level,
            hba1c_level=req.hba1c_level,
            smoking_history=req.smoking_history,
            hypertension=req.hypertension,
            heart_disease=req.heart_disease,
            diabetes_risk=diabetes_risk_value,
            diabetes_risk_level=diabetes_risk_level_value,
            heart_risk_level=payload["disease_scores"]["heart_disease"]["risk_level"],
            bmi_status=payload["rule_risks"]["bmi_status"],
            overall_health_score=float(payload["health_index"]["score"]),
            risk_breakdown=risk_breakdown,
            recommendations=payload["recommendations"],
            shap_explanations=payload["explanations"],
        )
        db.add(db_row)
        db.commit()
        db.refresh(db_row)

        payload["prediction_id"] = db_row.id
        payload["ok"] = True
        return payload
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


@router.post("/predict/multi")
def predict_multi_disease(
    req: PredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = predict_health(req=req, db=db, current_user=current_user)
    return {
        "ok": True,
        "prediction_id": payload.get("prediction_id"),
        "health_index": payload.get("health_index"),
        "disease_scores": payload.get("disease_scores"),
        "recommendations": payload.get("recommendations"),
        "anomalies": payload.get("anomalies"),
        "raw": payload,
    }


@router.post("/predict/{disease}")
def predict_single_disease(
    disease: str,
    req: PredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Disease-specific prediction (MVP).
    Supported: diabetes, heart_disease, hypertension, obesity
    """
    inputs = _inputs_from_request(req)
    payload = predict_pipeline(inputs=inputs, user_id=current_user.user_id, db=db)
    d = disease.strip().lower()

    if d in {"diabetes"}:
        result = payload["disease_scores"]["diabetes"]
        return {
            "ok": True,
            "disease": "diabetes",
            "probability": result["probability"],
            "risk_level": result["risk_level"],
            "confidence": result["confidence"],
        }
    if d in {"heart", "heart_disease", "heartdisease"}:
        result = payload["disease_scores"]["heart_disease"]
        return {"ok": True, "disease": "heart_disease", **result}
    if d in {"hypertension", "bp"}:
        result = payload["disease_scores"]["hypertension"]
        return {"ok": True, "disease": "hypertension", **result}
    if d in {"obesity", "bmi"}:
        return {"ok": True, "disease": "obesity", **payload["rule_risks"]["obesity"]}

    raise HTTPException(status_code=400, detail=f"Unsupported disease '{disease}'")
