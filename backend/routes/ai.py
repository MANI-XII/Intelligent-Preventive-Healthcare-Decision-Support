from __future__ import annotations

import re
from collections import Counter
from statistics import mean
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import BehaviorLog, DeviceReading, HealthRecord, PredictionHistory, User
from backend.schemas.api import (
    ChatRequest,
    ChatResponse,
    HealthRecordCreateRequest,
)
from backend.services.ai_service import ai_service
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


def _serialize_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _risk_level_score(level: str | None) -> float:
    if not level:
        return 0.0
    normalized = level.strip().lower()
    if normalized == "very high":
        return 90.0
    if normalized == "high":
        return 75.0
    if normalized == "moderate":
        return 50.0
    if normalized == "low":
        return 25.0
    return 0.0


def _to_percent(value: Any) -> int:
    if value is None:
        return 0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0
    if 0 <= numeric <= 1:
        numeric *= 100.0
    return int(round(max(0.0, min(100.0, numeric))))


def _extract_score(risk_breakdown: dict | None, key: str, fallback_level: str | None = None) -> int:
    if not isinstance(risk_breakdown, dict):
        return _to_percent(_risk_level_score(fallback_level))
    payload = risk_breakdown.get(key, {})
    if isinstance(payload, dict):
        if "score" in payload:
            return _to_percent(payload.get("score"))
        if "probability" in payload:
            return _to_percent(payload.get("probability"))
        if "risk_level" in payload:
            return _to_percent(_risk_level_score(payload.get("risk_level")))
    if key in risk_breakdown and not isinstance(risk_breakdown.get(key), dict):
        return _to_percent(risk_breakdown.get(key))
    return _to_percent(_risk_level_score(fallback_level))


def _parse_blood_pressure(value: str | None) -> tuple[int, int] | None:
    if not value:
        return None
    parts = re.findall(r"\d+", value)
    if len(parts) < 2:
        return None
    return int(parts[0]), int(parts[1])


def _trend_from_values(values: list[float | int | None], *, tolerance_ratio: float = 0.05, absolute_floor: float = 1.0) -> str:
    clean_values = [float(value) for value in values if value is not None]
    if len(clean_values) < 2:
        return "stable"
    half = max(1, len(clean_values) // 2)
    first_avg = mean(clean_values[:half])
    second_avg = mean(clean_values[-half:])
    delta = second_avg - first_avg
    threshold = max(abs(first_avg) * tolerance_ratio, absolute_floor)
    if delta > threshold:
        return "increasing"
    if delta < -threshold:
        return "decreasing"
    return "stable"


def _summarize_prediction(latest_prediction: PredictionHistory | None, latest_record: HealthRecord | None) -> dict:
    if latest_prediction is None and latest_record is None:
        return {
            "available": False,
            "diabetes_risk": 0,
            "heart_disease_risk": 0,
            "hypertension_risk": 0,
            "overall_health_score": None,
        }

    risk_breakdown = latest_prediction.risk_breakdown if latest_prediction else {}
    bmi_value = latest_prediction.bmi if latest_prediction else latest_record.bmi
    bmi_status = latest_prediction.bmi_status if latest_prediction else ("Overweight" if bmi_value and bmi_value >= 25 else "Normal")

    return {
        "available": True,
        "age": latest_record.age if latest_record else latest_prediction.age,
        "gender": latest_record.gender if latest_record else latest_prediction.gender,
        "bmi": bmi_value,
        "bmi_status": bmi_status,
        "blood_glucose_level": latest_prediction.blood_glucose_level if latest_prediction else latest_record.blood_glucose_level,
        "hba1c_level": latest_prediction.hba1c_level if latest_prediction else latest_record.hba1c_level,
        "smoking_history": latest_record.smoking_history if latest_record else latest_prediction.smoking_history,
        "hypertension": int(latest_record.hypertension if latest_record else latest_prediction.hypertension),
        "heart_disease": int(latest_record.heart_disease if latest_record else latest_prediction.heart_disease),
        "overall_health_score": round(float(latest_prediction.overall_health_score), 1) if latest_prediction else None,
        "diabetes_risk": _to_percent(latest_prediction.diabetes_risk if latest_prediction else 0),
        "heart_disease_risk": _extract_score(
            risk_breakdown,
            "heart_disease_risk",
            latest_prediction.heart_risk_level if latest_prediction else None,
        ),
        "hypertension_risk": _extract_score(
            risk_breakdown,
            "hypertension_risk",
            None,
        ),
        "bmi_risk": _extract_score(risk_breakdown, "bmi_risk", bmi_status),
        "adaptive_insights": risk_breakdown.get("adaptive_insights", {}) if isinstance(risk_breakdown, dict) else {},
        "risk_breakdown": risk_breakdown if isinstance(risk_breakdown, dict) else {},
    }


def _summarize_monitoring(
    prediction_rows: list[PredictionHistory],
    health_rows: list[HealthRecord],
    device_rows: list[DeviceReading],
) -> dict:
    glucose_series = [
        {"timestamp": _serialize_datetime(row.recorded_at), "value": row.blood_glucose_level}
        for row in health_rows
    ]
    bmi_series = [
        {"timestamp": _serialize_datetime(row.recorded_at), "value": row.bmi}
        for row in health_rows
    ]
    health_score_series = [
        {"timestamp": _serialize_datetime(row.created_at), "value": row.overall_health_score}
        for row in prediction_rows
    ]
    diabetes_risk_series = [
        {"timestamp": _serialize_datetime(row.created_at), "value": _to_percent(row.diabetes_risk)}
        for row in prediction_rows
    ]

    heart_rate_series = []
    steps_series = []
    sleep_series = []
    oxygen_series = []
    systolic_series = []
    diastolic_series = []

    for row in device_rows:
        timestamp = _serialize_datetime(row.recorded_at)
        if row.heart_rate_bpm is not None:
            heart_rate_series.append({"timestamp": timestamp, "value": row.heart_rate_bpm})
        if row.steps is not None:
            steps_series.append({"timestamp": timestamp, "value": row.steps})
        if row.sleep_minutes is not None:
            sleep_series.append({"timestamp": timestamp, "value": round(row.sleep_minutes / 60.0, 1)})
        if isinstance(row.payload, dict):
            oxygen_value = row.payload.get("oxygen_level")
            if oxygen_value is not None:
                oxygen_series.append({"timestamp": timestamp, "value": oxygen_value})
            bp = _parse_blood_pressure(row.payload.get("blood_pressure"))
            if bp:
                systolic_series.append({"timestamp": timestamp, "value": bp[0]})
                diastolic_series.append({"timestamp": timestamp, "value": bp[1]})

    for row in health_rows:
        bp = _parse_blood_pressure(row.blood_pressure)
        if bp:
            timestamp = _serialize_datetime(row.recorded_at)
            systolic_series.append({"timestamp": timestamp, "value": bp[0]})
            diastolic_series.append({"timestamp": timestamp, "value": bp[1]})
        if row.sleep_hours is not None:
            sleep_series.append({"timestamp": _serialize_datetime(row.recorded_at), "value": row.sleep_hours})

    trend_summary = {
        "blood_glucose_level": _trend_from_values([item["value"] for item in glucose_series], absolute_floor=5.0),
        "bmi": _trend_from_values([item["value"] for item in bmi_series], tolerance_ratio=0.02, absolute_floor=0.3),
        "overall_health_score": _trend_from_values([item["value"] for item in health_score_series], tolerance_ratio=0.03, absolute_floor=0.3),
        "diabetes_risk": _trend_from_values([item["value"] for item in diabetes_risk_series], absolute_floor=3.0),
        "heart_rate_bpm": _trend_from_values([item["value"] for item in heart_rate_series], absolute_floor=3.0),
        "steps": _trend_from_values([item["value"] for item in steps_series], tolerance_ratio=0.1, absolute_floor=500.0),
        "sleep_hours": _trend_from_values([item["value"] for item in sleep_series], tolerance_ratio=0.08, absolute_floor=0.4),
        "oxygen_level": _trend_from_values([item["value"] for item in oxygen_series], absolute_floor=1.0),
        "systolic_bp": _trend_from_values([item["value"] for item in systolic_series], absolute_floor=4.0),
        "diastolic_bp": _trend_from_values([item["value"] for item in diastolic_series], absolute_floor=3.0),
    }

    return {
        "available": any([prediction_rows, health_rows, device_rows]),
        "trend_summary": trend_summary,
        "recent_series": {
            "blood_glucose_level": glucose_series[-6:],
            "bmi": bmi_series[-6:],
            "overall_health_score": health_score_series[-6:],
            "diabetes_risk": diabetes_risk_series[-6:],
            "heart_rate_bpm": heart_rate_series[-8:],
            "steps": steps_series[-8:],
            "sleep_hours": sleep_series[-8:],
            "oxygen_level": oxygen_series[-8:],
            "systolic_bp": systolic_series[-8:],
            "diastolic_bp": diastolic_series[-8:],
        },
        "counts": {
            "prediction_points": len(prediction_rows),
            "health_records": len(health_rows),
            "device_readings": len(device_rows),
        },
    }


def _summarize_behavior(
    latest_record: HealthRecord | None,
    behavior_rows: list[BehaviorLog],
    device_rows: list[DeviceReading],
) -> dict:
    category_counts = Counter(row.category for row in behavior_rows)
    avg_steps = None
    step_values = [row.steps for row in device_rows if row.steps is not None]
    if step_values:
        avg_steps = round(mean(step_values))

    avg_sleep = None
    sleep_values = [row.sleep_minutes / 60.0 for row in device_rows if row.sleep_minutes is not None]
    if sleep_values:
        avg_sleep = round(mean(sleep_values), 1)

    return {
        "available": bool(latest_record or behavior_rows or device_rows),
        "profile_behavior": {
            "activity_level": latest_record.activity_level if latest_record else None,
            "sleep_hours": latest_record.sleep_hours if latest_record else None,
            "stress_level": latest_record.stress_level if latest_record else None,
            "diet_type": latest_record.diet_type if latest_record else None,
            "smoking_history": latest_record.smoking_history if latest_record else None,
        },
        "derived_metrics": {
            "average_steps": avg_steps,
            "average_sleep_hours": avg_sleep,
        },
        "category_counts": dict(category_counts),
        "recent_logs": [
            {
                "created_at": _serialize_datetime(row.created_at),
                "category": row.category,
                "value": row.value,
            }
            for row in behavior_rows[-8:]
        ],
    }


def _build_analysis(prediction_data: dict, monitoring_data: dict, behavior_data: dict) -> dict:
    if not prediction_data.get("available") and not monitoring_data.get("available") and not behavior_data.get("available"):
        return {
            "summary": "Not enough data is available yet to explain your health condition. Add a health record, a prediction, or a few behavior logs to unlock deeper insights.",
            "key_risk_drivers": [],
            "trend_insight": "There is not enough monitoring history to describe increasing, decreasing, or stable patterns yet.",
            "risk_interaction": "Risk interaction analysis will become more useful once prediction and monitoring data are available together.",
            "behavioral_insight": "Start logging activity, sleep, diet, or medication behavior to connect habits with your future risk trends.",
            "recommendations": [
                "Add a recent health record to establish your current baseline.",
                "Log activity, sleep, or diet behavior for several days in a row.",
                "Return to Insights after new data is recorded to see a fuller analysis.",
            ],
        }

    drivers: list[dict[str, Any]] = []
    diabetes_risk = prediction_data.get("diabetes_risk", 0)
    heart_risk = prediction_data.get("heart_disease_risk", 0)
    hypertension_risk = prediction_data.get("hypertension_risk", 0)
    bmi = prediction_data.get("bmi")
    glucose = prediction_data.get("blood_glucose_level")
    hba1c = prediction_data.get("hba1c_level")
    sleep_hours = behavior_data.get("profile_behavior", {}).get("sleep_hours")
    avg_steps = behavior_data.get("derived_metrics", {}).get("average_steps")
    stress_level = behavior_data.get("profile_behavior", {}).get("stress_level")
    diet_type = behavior_data.get("profile_behavior", {}).get("diet_type")
    smoking_history = behavior_data.get("profile_behavior", {}).get("smoking_history")

    if glucose is not None or hba1c is not None:
        impact = max(diabetes_risk, 35 if (glucose or 0) >= 140 else 20, 35 if (hba1c or 0) >= 6.5 else 20)
        if impact > 20:
            drivers.append({"factor": "Elevated glucose control markers", "impact_percent": min(100, int(round(impact)))})

    if bmi is not None and bmi >= 25:
        impact = max(prediction_data.get("bmi_risk", 0), 30 if bmi >= 30 else 22)
        drivers.append({"factor": "Higher-than-ideal body weight", "impact_percent": min(100, int(round(impact)))})

    if prediction_data.get("hypertension") or hypertension_risk >= 45:
        impact = max(hypertension_risk, 30)
        drivers.append({"factor": "Blood pressure strain", "impact_percent": min(100, int(round(impact)))})

    if prediction_data.get("heart_disease") or heart_risk >= 45:
        impact = max(heart_risk, 28)
        drivers.append({"factor": "Cardiovascular strain", "impact_percent": min(100, int(round(impact)))})

    if avg_steps is not None and avg_steps < 5000:
        drivers.append({"factor": "Low daily activity", "impact_percent": 24})

    if sleep_hours is not None and sleep_hours < 6.5:
        drivers.append({"factor": "Short sleep duration", "impact_percent": 18})

    if stress_level == "high":
        drivers.append({"factor": "High stress load", "impact_percent": 16})

    if smoking_history == "current":
        drivers.append({"factor": "Current smoking exposure", "impact_percent": 26})
    elif smoking_history == "former":
        drivers.append({"factor": "Past smoking history", "impact_percent": 14})

    deduped_drivers = []
    seen_factors = set()
    for item in sorted(drivers, key=lambda entry: entry["impact_percent"], reverse=True):
        if item["factor"] in seen_factors:
            continue
        seen_factors.add(item["factor"])
        deduped_drivers.append(item)
    top_drivers = deduped_drivers[:3]

    driver_names = ", ".join(item["factor"].lower() for item in top_drivers[:2]) or "limited available measurements"
    health_score = prediction_data.get("overall_health_score")
    if health_score is not None and health_score < 5:
        summary = f"Your current health picture suggests elevated preventive risk, mainly driven by {driver_names}. The combination of current prediction results, recent monitoring history, and behavior patterns points to areas that should be improved soon to avoid further deterioration."
    elif max(diabetes_risk, heart_risk, hypertension_risk) >= 65:
        summary = f"Your results show moderate-to-high risk concentrated around {driver_names}. The data suggests that several related factors are reinforcing each other rather than a single isolated issue."
    else:
        summary = f"Your overall health picture looks mixed but manageable, with the main pressure coming from {driver_names}. Some indicators appear stable, but the combined pattern still deserves routine monitoring and preventive action."

    trend_labels = {
        "blood_glucose_level": "blood glucose",
        "bmi": "body weight",
        "overall_health_score": "overall health score",
        "diabetes_risk": "diabetes risk",
        "heart_rate_bpm": "heart rate",
        "steps": "activity",
        "sleep_hours": "sleep",
        "oxygen_level": "oxygen level",
        "systolic_bp": "blood pressure",
    }
    increasing = [label for key, label in trend_labels.items() if monitoring_data.get("trend_summary", {}).get(key) == "increasing"]
    decreasing = [label for key, label in trend_labels.items() if monitoring_data.get("trend_summary", {}).get(key) == "decreasing"]
    stable = [label for key, label in trend_labels.items() if monitoring_data.get("trend_summary", {}).get(key) == "stable"]

    trend_parts = []
    if increasing:
        trend_parts.append(f"Increasing patterns are visible in {', '.join(increasing[:3])}.")
    if decreasing:
        trend_parts.append(f"Decreasing patterns are visible in {', '.join(decreasing[:3])}.")
    if stable:
        trend_parts.append(f"Relatively stable signals include {', '.join(stable[:3])}.")
    trend_insight = " ".join(trend_parts) or "Monitoring history is still limited, so trend analysis is based on only a few time points."

    if diabetes_risk >= 55 and (heart_risk >= 45 or hypertension_risk >= 45):
        risk_interaction = "Higher glucose-related risk appears to be interacting with cardiovascular strain. In practice, this means the same pattern that raises diabetes risk can also increase pressure on the heart and blood vessels."
    elif bmi is not None and bmi >= 27 and (heart_risk >= 40 or hypertension_risk >= 40):
        risk_interaction = "Excess body weight appears to be amplifying both blood pressure and heart-related risk. This creates a reinforcing cycle where one condition can make the others harder to control."
    elif smoking_history in {"current", "former"} and heart_risk >= 40:
        risk_interaction = "Smoking exposure and cardiovascular risk appear linked in your data. That combination can make recovery slower and can worsen long-term vascular health."
    else:
        risk_interaction = "Your risk pattern looks interconnected rather than isolated. Weight, glucose control, blood pressure, and day-to-day habits are likely influencing each other."

    behavior_signals = []
    if avg_steps is not None and avg_steps < 5000:
        behavior_signals.append("activity is below a helpful daily range")
    elif avg_steps is not None and avg_steps >= 7000:
        behavior_signals.append("activity is providing some protective support")
    if sleep_hours is not None and sleep_hours < 6.5:
        behavior_signals.append("sleep duration is shorter than ideal")
    if behavior_data.get("derived_metrics", {}).get("average_sleep_hours") is not None and behavior_data["derived_metrics"]["average_sleep_hours"] < 6.5:
        behavior_signals.append("recent monitored sleep also looks low")
    if stress_level == "high":
        behavior_signals.append("stress may be adding extra strain")
    if diet_type in {"high-carb", "high-fat"}:
        behavior_signals.append(f"the current {diet_type} diet pattern may be increasing metabolic pressure")
    if smoking_history == "current":
        behavior_signals.append("smoking is adding preventable cardiovascular risk")
    if not behavior_signals:
        behavioral_insight = "Your logged habits do not show a single dominant lifestyle risk right now, but continued tracking will help confirm whether activity, sleep, and diet are protecting your progress."
    else:
        behavioral_insight = "Behavior patterns suggest that " + ", ".join(behavior_signals[:4]) + ". These daily habits can meaningfully shift your risk over time, especially when they continue for weeks."

    recommendations: list[str] = []
    if any(item["factor"] == "Elevated glucose control markers" for item in top_drivers):
        recommendations.append("Focus on reducing sugary drinks and refined carbohydrates, and keep meal timing consistent to improve glucose control.")
    if any(item["factor"] == "Higher-than-ideal body weight" for item in top_drivers):
        recommendations.append("Aim for steady weekly weight improvement through portion control and regular movement rather than extreme short-term changes.")
    if any(item["factor"] == "Blood pressure strain" for item in top_drivers):
        recommendations.append("Monitor blood pressure regularly, reduce high-salt processed foods, and discuss persistent elevated readings with a clinician.")
    if avg_steps is not None and avg_steps < 5000:
        recommendations.append("Increase daily movement gradually, such as adding walks after meals or building toward a consistent weekly exercise routine.")
    if (sleep_hours is not None and sleep_hours < 6.5) or (
        behavior_data.get("derived_metrics", {}).get("average_sleep_hours") is not None
        and behavior_data["derived_metrics"]["average_sleep_hours"] < 6.5
    ):
        recommendations.append("Target 7 to 8 hours of sleep on most nights, because better sleep can support glucose control, appetite, and recovery.")
    if stress_level == "high":
        recommendations.append("Use a daily stress-reduction habit such as breathing exercises, walking, or short screen-free breaks to lower sustained stress load.")
    if not recommendations:
        recommendations.append("Keep tracking the same metrics consistently so early risk changes are easier to catch and act on.")
    recommendations = recommendations[:3]

    return {
        "summary": summary,
        "key_risk_drivers": top_drivers[:2],
        "trend_insight": trend_insight,
        "risk_interaction": risk_interaction,
        "behavioral_insight": behavioral_insight,
        "recommendations": recommendations,
    }


def _chat_suggested_actions(message: str) -> list[str]:
    msg = message.lower()
    if any(word in msg for word in ["report", "pdf", "download"]):
        return ["How do I generate a report?", "What is included in the report?", "Where do I find predictions?"]
    if any(word in msg for word in ["goal", "task", "plan"]):
        return ["How do I create a goal?", "How do tasks support goals?", "What goal should I start with?"]
    if any(word in msg for word in ["diabetes", "glucose", "hba1c", "risk"]):
        return ["How do I lower diabetes risk?", "What affects my glucose most?", "How does the prediction work?"]
    if any(word in msg for word in ["insight", "monitor", "trend"]):
        return ["What does the Insights page mean?", "How does monitoring work?", "Why is my trend increasing?"]
    return [
        "How do predictions work?",
        "What can the Insights page tell me?",
        "How do I improve my health score?",
    ]


def _prediction_status_summary(prediction_data: dict) -> str:
    if not prediction_data.get("available"):
        return "No saved prediction is available yet."

    diabetes = prediction_data.get("diabetes_risk", 0)
    heart = prediction_data.get("heart_disease_risk", 0)
    hypertension = prediction_data.get("hypertension_risk", 0)
    health_score = prediction_data.get("overall_health_score")
    highest = max(diabetes, heart, hypertension)

    if health_score is not None and health_score >= 8 and highest < 35:
        tone = "Overall this looks reassuring."
    elif highest >= 70 or (health_score is not None and health_score < 5):
        tone = "Overall this looks concerning and deserves action."
    else:
        tone = "Overall this looks mixed, with some areas that need attention."

    return (
        f"{tone} Latest saved results: diabetes risk {diabetes}%, heart disease risk {heart}%, "
        f"hypertension risk {hypertension}%, health score {health_score if health_score is not None else 'N/A'}."
    )


@router.post("/explain", response_model=dict)
def explain_prediction(
    req: HealthRecordCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate AI explanation for prediction results."""
    try:
        # For explanation, we need prediction data, so we'll simulate or get from recent prediction
        # In a real implementation, you might want to pass prediction_id or generate on the fly
        # For now, we'll use the input data to generate a mock prediction context

        prediction_data = {
            "diabetes_risk": 65.0,  # Mock values - in real app, get from actual prediction
            "heart_disease_risk": 45.0,
            "hypertension_risk": 55.0,
            "overall_health_score": 6.2,
            "bmi": req.bmi,
            "bmi_status": "Overweight" if req.bmi > 25 else "Normal",
            "blood_glucose_level": req.blood_glucose_level,
            "hba1c_level": req.hba1c_level,
            "smoking_history": req.smoking_history,
            "hypertension": req.hypertension,
            "heart_disease": req.heart_disease,
            "age": req.age,
            "gender": req.gender,
        }

        explanation = ai_service.generate_explanation(prediction_data)

        return {
            "ok": True,
            "explanation": explanation,
            "prediction_data": prediction_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {e}")


@router.post("/recommend", response_model=dict)
def get_recommendations(
    req: HealthRecordCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate personalized health recommendations."""
    try:
        health_data = {
            "age": req.age,
            "gender": req.gender,
            "bmi": req.bmi,
            "blood_glucose_level": req.blood_glucose_level,
            "hba1c_level": req.hba1c_level,
            "smoking_history": req.smoking_history,
            "hypertension": req.hypertension,
            "heart_disease": req.heart_disease,
            "activity_level": req.activity_level,
            "sleep_hours": req.sleep_hours,
            "stress_level": req.stress_level,
            "diet_type": req.diet_type,
        }

        risk_data = {
            "diabetes_risk": 65.0,  # Mock - should come from actual prediction
            "heart_disease_risk": 45.0,
            "overall_health_score": 6.2,
        }

        recommendations = ai_service.generate_recommendation(health_data, risk_data)

        return {
            "ok": True,
            "recommendations": recommendations,
            "health_data": health_data,
            "risk_data": risk_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {e}")


@router.post("/chat", response_model=ChatResponse)
def chat_with_ai(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chatbot endpoint for health-related questions."""
    try:
        latest_record = (
            db.query(HealthRecord)
            .filter(HealthRecord.user_id == current_user.user_id)
            .order_by(HealthRecord.recorded_at.desc())
            .first()
        )
        latest_prediction = (
            db.query(PredictionHistory)
            .filter(PredictionHistory.user_id == current_user.user_id)
            .order_by(PredictionHistory.created_at.desc(), PredictionHistory.id.desc())
            .first()
        )

        context = None
        prediction_data = _summarize_prediction(latest_prediction, latest_record)
        if latest_record or latest_prediction:
            context = {
                **prediction_data,
                "prediction_status_summary": _prediction_status_summary(prediction_data),
                "blood_pressure": latest_record.blood_pressure if latest_record else None,
                "sleep_hours": latest_record.sleep_hours if latest_record else None,
                "activity_level": latest_record.activity_level if latest_record else None,
                "stress_level": latest_record.stress_level if latest_record else None,
                "diet_type": latest_record.diet_type if latest_record else None,
            }

        reply = ai_service.chatbot_response(req.message, context)

        return ChatResponse(
            reply=reply,
            suggested_actions=_chat_suggested_actions(req.message),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate chat response: {e}")


@router.post("/insight", response_model=dict)
def get_health_insight(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate structured multi-source health insights."""
    try:
        prediction_rows = list(
            reversed(
                db.query(PredictionHistory)
                .filter(PredictionHistory.user_id == current_user.user_id)
                .order_by(PredictionHistory.created_at.desc())
                .limit(12)
                .all()
            )
        )
        health_rows = list(
            reversed(
                db.query(HealthRecord)
                .filter(HealthRecord.user_id == current_user.user_id)
                .order_by(HealthRecord.recorded_at.desc(), HealthRecord.id.desc())
                .limit(12)
                .all()
            )
        )
        device_rows = list(
            reversed(
                db.query(DeviceReading)
                .filter(DeviceReading.user_id == current_user.user_id)
                .order_by(DeviceReading.recorded_at.desc(), DeviceReading.id.desc())
                .limit(24)
                .all()
            )
        )
        behavior_rows = list(
            reversed(
                db.query(BehaviorLog)
                .filter(BehaviorLog.user_id == current_user.user_id)
                .order_by(BehaviorLog.created_at.desc(), BehaviorLog.id.desc())
                .limit(50)
                .all()
            )
        )

        latest_prediction = prediction_rows[-1] if prediction_rows else None
        latest_record = health_rows[-1] if health_rows else None

        prediction_data = _summarize_prediction(latest_prediction, latest_record)
        monitoring_data = _summarize_monitoring(prediction_rows, health_rows, device_rows)
        behavior_data = _summarize_behavior(latest_record, behavior_rows, device_rows)
        analysis = _build_analysis(prediction_data, monitoring_data, behavior_data)
        insight = ai_service.generate_multisource_insight(
            prediction_data=prediction_data,
            monitoring_data=monitoring_data,
            behavior_data=behavior_data,
            analysis=analysis,
        )

        return {
            "ok": True,
            "insight": insight,
            "analysis": analysis,
            "prediction_data": prediction_data,
            "monitoring_data": monitoring_data,
            "behavior_data": behavior_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insight: {e}")
