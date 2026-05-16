from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import User
from backend.schemas.api import SimulateRequest
from backend.services.pipeline_service import predict_pipeline
from backend.utils.auth import get_current_user
from backend.utils.risk_scoring import UserHealthInputs

router = APIRouter()


def _build_inputs(req: SimulateRequest) -> UserHealthInputs:
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


def _build_overridden_inputs(req: SimulateRequest) -> UserHealthInputs:
    return UserHealthInputs(
        gender=req.gender,
        age=float(req.age),
        bmi=float(req.simulate_bmi if req.simulate_bmi is not None else req.bmi),
        blood_glucose_level=float(
            req.simulate_blood_glucose_level
            if req.simulate_blood_glucose_level is not None
            else req.blood_glucose_level
        ),
        hba1c_level=float(req.hba1c_level),
        smoking_history=req.simulate_smoking_history
        if req.simulate_smoking_history is not None
        else req.smoking_history,
        hypertension=int(req.hypertension),
        heart_disease=int(req.heart_disease),
        activity_level=req.simulate_activity_level
        if req.simulate_activity_level is not None
        else req.activity_level,
        sleep_hours=float(
            req.simulate_sleep_hours if req.simulate_sleep_hours is not None else req.sleep_hours
        ),
        stress_level=req.stress_level,
        diet_type=req.diet_type,
        work_type=req.work_type,
        blood_pressure=req.blood_pressure,
    )


@router.post("/simulate")
def simulate_lifestyle(
    req: SimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        base_inputs = _build_inputs(req)
        simulated_inputs = _build_overridden_inputs(req)

        base_result = predict_pipeline(
            inputs=base_inputs,
            user_id=current_user.user_id,
            db=db,
        )
        simulated_result = predict_pipeline(
            inputs=simulated_inputs,
            user_id=current_user.user_id,
            db=db,
        )

        return {
            "base": base_result,
            "simulated": simulated_result,
            "delta": {
                "diabetes_risk_change": simulated_result["disease_scores"]["diabetes"]["probability"]
                - base_result["disease_scores"]["diabetes"]["probability"],
                "heart_disease_risk_change": simulated_result["disease_scores"]["heart_disease"]["probability"]
                - base_result["disease_scores"]["heart_disease"]["probability"],
                "hypertension_risk_change": simulated_result["disease_scores"]["hypertension"]["probability"]
                - base_result["disease_scores"]["hypertension"]["probability"],
                "health_index_change": simulated_result["health_index"]["score"]
                - base_result["health_index"]["score"],
            },
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")

