from __future__ import annotations

from sqlalchemy.orm import Session

from backend.services.disease_service import evaluate_disease_risk_profile
from backend.services.health_index_service import calculate_preventive_health_index
from backend.services.forecast_service import forecast_risk_trend
from backend.services.anomaly_service import detect_clinical_anomalies
from backend.services.adaptive_service import generate_adaptive_insights
from backend.services.recommendation_service import generate_recommendations
from backend.services.shap_service import shap_explain_single_instance
from backend.utils.risk_scoring import UserHealthInputs, calculate_rule_based_risks


def predict_pipeline(
    inputs: UserHealthInputs,
    user_id: str,
    db: Session,
) -> dict:
    base_inputs = {
        "gender": inputs.gender,
        "age": inputs.age,
        "hypertension": inputs.hypertension,
        "heart_disease": inputs.heart_disease,
        "smoking_history": inputs.smoking_history,
        "bmi": inputs.bmi,
        "HbA1c_level": inputs.hba1c_level,
        "blood_glucose_level": inputs.blood_glucose_level,
        "activity_level": inputs.activity_level,
        "sleep_hours": inputs.sleep_hours,
        "stress_level": inputs.stress_level,
        "diet_type": inputs.diet_type,
        "work_type": inputs.work_type,
        "blood_pressure": inputs.blood_pressure,
    }

    disease_profile = evaluate_disease_risk_profile(inputs)
    rule_risks = calculate_rule_based_risks(inputs, diabetes_risk_prob=disease_profile["disease_scores"]["diabetes"]["probability"])

    disease_risk_map = {
        key: {"score": round(value["probability"] * 100.0, 2)}
        for key, value in disease_profile["disease_scores"].items()
    }
    disease_risk_map["heart_disease_risk"] = disease_risk_map.get("heart_disease", {"score": 0.0})
    disease_risk_map["hypertension_risk"] = disease_risk_map.get("hypertension", {"score": 0.0})
    disease_risk_map["cardiovascular_risk"] = disease_risk_map.get("cardiovascular_risk", {"score": 0.0})
    disease_risk_map["metabolic_syndrome"] = disease_risk_map.get("metabolic_syndrome", {"score": 0.0})
    disease_risk_map["obesity"] = disease_risk_map.get("obesity", {"score": 0.0})

    health_index = calculate_preventive_health_index(inputs, {
        **rule_risks,
        **disease_risk_map,
    })
    risk_forecast = forecast_risk_trend(inputs, {
        **rule_risks,
        **disease_risk_map,
    })
    clinical_anomalies = detect_clinical_anomalies(user_id, inputs, db)
    adaptive_insights = generate_adaptive_insights(user_id, health_index["score"], inputs, db)
    explanations = shap_explain_single_instance(base_inputs)

    recommendations = generate_recommendations(
        gender=inputs.gender,
        age=inputs.age,
        bmi=inputs.bmi,
        blood_glucose_level=inputs.blood_glucose_level,
        hba1c_level=inputs.hba1c_level,
        smoking_history=inputs.smoking_history,
        hypertension=inputs.hypertension,
        heart_disease=inputs.heart_disease,
        activity_level=inputs.activity_level,
        sleep_hours=inputs.sleep_hours,
        diabetes_risk_prob=disease_profile["disease_scores"]["diabetes"]["probability"],
        rule_risks=rule_risks,
        health_index=health_index,
        anomalies=clinical_anomalies,
        adaptive_insights=adaptive_insights,
    )

    confidence = {
        disease: disease_profile["disease_scores"][disease]["confidence"]
        for disease in ["diabetes", "heart_disease", "hypertension"]
    }
    confidence["overall"] = round(
        sum(disease_profile["disease_scores"][d]["probability"] for d in ["diabetes", "heart_disease", "hypertension"]) / 3.0 * 100.0,
        2,
    )

    return {
        "inputs": base_inputs,
        "overall_risk_score": disease_profile["overall_risk_score"],
        "overall_risk_level": disease_profile["overall_risk_level"],
        "disease_scores": disease_profile["disease_scores"],
        "grouped_scores": disease_profile.get("grouped_scores", {}),
        "diabetes_risk": disease_profile["disease_scores"]["diabetes"]["probability"],
        "diabetes_risk_level": disease_profile["disease_scores"]["diabetes"]["risk_level"],
        "rule_risks": rule_risks,
        "health_index": health_index,
        "health_category": health_index["category"],
        "health_dashboard": disease_profile.get("health_dashboard", {}),
        "risk_forecast": risk_forecast,
        "anomalies": clinical_anomalies,
        "adaptive_insights": adaptive_insights,
        "recommendations": recommendations,
        "explanations": explanations,
        "dependency_explanations": disease_profile["dependency_explanations"],
        "confidence": confidence,
    }
