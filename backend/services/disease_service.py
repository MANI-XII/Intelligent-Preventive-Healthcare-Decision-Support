from __future__ import annotations

from backend.services.model_service import (
    predict_diabetes_probability,
    predict_heart_disease_probability,
    predict_hypertension_probability,
)
from backend.utils.risk_scoring import (
    UserHealthInputs,
    bmi_status,
    calculate_rule_based_risks,
)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _risk_level(score: float) -> str:
    if score >= 0.66:
        return "High"
    if score >= 0.33:
        return "Moderate"
    return "Low"


def _format_probability(score: float) -> float:
    return round(_clamp(score) * 100.0, 2)


def _is_high(score: float) -> bool:
    return score >= 0.66


def predict_obesity_probability(inputs: UserHealthInputs) -> float:
    if inputs.bmi >= 30.0:
        return 1.0
    return _clamp((inputs.bmi - 24.0) / 10.0)


def apply_dependency_adjustments(
    inputs: UserHealthInputs,
    base_scores: dict,
) -> tuple[dict, list[str]]:
    explanations: list[str] = []
    adjusted_scores = base_scores.copy()

    diabetes_prob = adjusted_scores["diabetes"]["probability"]
    heart_prob = adjusted_scores["heart_disease"]["probability"]
    hypertension_prob = adjusted_scores["hypertension"]["probability"]
    obesity_prob = adjusted_scores["obesity"]["probability"]
    metabolic_prob = adjusted_scores["metabolic_syndrome"]["probability"]
    ckd_prob = adjusted_scores["chronic_kidney_disease"]["probability"]
    cardio_prob = adjusted_scores["cardiovascular_risk"]["probability"]
    stroke_prob = adjusted_scores["stroke_risk"]["probability"]
    cholesterol_prob = adjusted_scores["cholesterol_disorder"]["probability"]

    if _is_high(diabetes_prob):
        increase = 0.12
        heart_prob = _clamp(heart_prob + increase)
        ckd_prob = _clamp(ckd_prob + 0.10)
        stroke_prob = _clamp(stroke_prob + 0.08)
        explanations.append(
            "Heart disease, kidney disease, and stroke risk increased because diabetes risk is High."
        )

    if inputs.bmi >= 30.0:
        diabetes_prob = _clamp(diabetes_prob + 0.10)
        hypertension_prob = _clamp(hypertension_prob + 0.10)
        metabolic_prob = _clamp(metabolic_prob + 0.08)
        explanations.append(
            "Diabetes, hypertension, and metabolic syndrome risks increased due to obesity."
        )

    if _is_high(hypertension_prob):
        stroke_prob = _clamp(stroke_prob + 0.12)
        ckd_prob = _clamp(ckd_prob + 0.12)
        explanations.append(
            "Stroke and kidney disease risk increased because hypertension is High."
        )

    if _is_high(cholesterol_prob):
        cardio_prob = _clamp(cardio_prob + 0.14)
        explanations.append(
            "Cardiovascular disease risk increased because cholesterol disorder risk is High."
        )

    high_conditions = sum(
        _is_high(val["probability"]) for key, val in adjusted_scores.items() if key in {
            "diabetes",
            "heart_disease",
            "hypertension",
            "obesity",
            "metabolic_syndrome",
            "cholesterol_disorder",
        }
    )
    if high_conditions >= 2:
        cardio_prob = _clamp(cardio_prob + 0.15)
        explanations.append(
            "Overall cardiovascular risk increased because multiple related conditions are High."
        )

    adjusted_scores["diabetes"] = {
        **adjusted_scores["diabetes"],
        "probability": diabetes_prob,
        "risk_level": _risk_level(diabetes_prob),
    }
    adjusted_scores["heart_disease"] = {
        **adjusted_scores["heart_disease"],
        "probability": heart_prob,
        "risk_level": _risk_level(heart_prob),
    }
    adjusted_scores["hypertension"] = {
        **adjusted_scores["hypertension"],
        "probability": hypertension_prob,
        "risk_level": _risk_level(hypertension_prob),
    }
    adjusted_scores["metabolic_syndrome"] = {
        **adjusted_scores["metabolic_syndrome"],
        "probability": metabolic_prob,
        "risk_level": _risk_level(metabolic_prob),
    }
    adjusted_scores["chronic_kidney_disease"] = {
        **adjusted_scores["chronic_kidney_disease"],
        "probability": ckd_prob,
        "risk_level": _risk_level(ckd_prob),
    }
    adjusted_scores["cardiovascular_risk"] = {
        **adjusted_scores["cardiovascular_risk"],
        "probability": cardio_prob,
        "risk_level": _risk_level(cardio_prob),
    }
    adjusted_scores["stroke_risk"] = {
        **adjusted_scores["stroke_risk"],
        "probability": stroke_prob,
        "risk_level": _risk_level(stroke_prob),
    }
    adjusted_scores["cholesterol_disorder"] = {
        **adjusted_scores["cholesterol_disorder"],
        "probability": cholesterol_prob,
        "risk_level": _risk_level(cholesterol_prob),
    }

    return adjusted_scores, explanations


def evaluate_disease_risk_profile(inputs: UserHealthInputs) -> dict:
    diabetes_prob = predict_diabetes_probability(
        {
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
        }
    )

    heart_prob = predict_heart_disease_probability(
        {
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
        },
        diabetes_prob,
    )

    hypertension_prob = predict_hypertension_probability(
        {
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
        }
    )

    rule_risks = calculate_rule_based_risks(inputs, diabetes_risk_prob=diabetes_prob)
    obesity_prob = predict_obesity_probability(inputs)
    metabolic_prob = rule_risks["metabolic_syndrome"]["score"] / 100.0
    stroke_prob = rule_risks["stroke_risk"]["score"] / 100.0
    kidney_prob = rule_risks["kidney_disease_risk"]["score"] / 100.0
    cholesterol_prob = rule_risks["cholesterol_risk"]["score"] / 100.0
    cardio_prob = rule_risks["cardiovascular_disease"]["score"] / 100.0
    prediabetes_prob = rule_risks["prediabetes"]["score"] / 100.0
    lifestyle_prob = rule_risks["lifestyle_disease_index"]["score"] / 100.0

    base_scores = {
        "diabetes": {
            "probability": diabetes_prob,
            "risk_level": _risk_level(diabetes_prob),
            "confidence": _format_probability(diabetes_prob),
        },
        "prediabetes": {
            "probability": prediabetes_prob,
            "risk_level": _risk_level(prediabetes_prob),
            "confidence": _format_probability(prediabetes_prob),
        },
        "obesity": {
            "probability": obesity_prob,
            "risk_level": "High" if obesity_prob >= 1.0 else _risk_level(obesity_prob),
            "confidence": _format_probability(obesity_prob),
            "status": bmi_status(inputs.bmi),
        },
        "metabolic_syndrome": {
            "probability": metabolic_prob,
            "risk_level": _risk_level(metabolic_prob),
            "confidence": _format_probability(metabolic_prob),
        },
        "heart_disease": {
            "probability": heart_prob,
            "risk_level": _risk_level(heart_prob),
            "confidence": _format_probability(heart_prob),
        },
        "hypertension": {
            "probability": hypertension_prob,
            "risk_level": _risk_level(hypertension_prob),
            "confidence": _format_probability(hypertension_prob),
        },
        "stroke_risk": {
            "probability": stroke_prob,
            "risk_level": _risk_level(stroke_prob),
            "confidence": _format_probability(stroke_prob),
        },
        "cardiovascular_risk": {
            "probability": cardio_prob,
            "risk_level": _risk_level(cardio_prob),
            "confidence": _format_probability(cardio_prob),
        },
        "chronic_kidney_disease": {
            "probability": kidney_prob,
            "risk_level": _risk_level(kidney_prob),
            "confidence": _format_probability(kidney_prob),
        },
        "cholesterol_disorder": {
            "probability": cholesterol_prob,
            "risk_level": _risk_level(cholesterol_prob),
            "confidence": _format_probability(cholesterol_prob),
        },
        "lifestyle_risk_index": {
            "probability": lifestyle_prob,
            "risk_level": _risk_level(lifestyle_prob),
            "confidence": _format_probability(lifestyle_prob),
        },
    }

    adjusted_scores, explanations = apply_dependency_adjustments(inputs, base_scores)

    overall_score = round(
        sum(score["probability"] for score in adjusted_scores.values())
        / len(adjusted_scores)
        * 100.0,
        2,
    )
    overall_level = _risk_level(overall_score / 100.0)

    grouped_scores = {
        "metabolic": [
            {"id": "diabetes", "name": "Diabetes", **adjusted_scores["diabetes"]},
            {"id": "prediabetes", "name": "Prediabetes", **adjusted_scores["prediabetes"]},
            {"id": "obesity", "name": "Obesity", **adjusted_scores["obesity"]},
            {"id": "metabolic_syndrome", "name": "Metabolic Syndrome", **adjusted_scores["metabolic_syndrome"]},
        ],
        "cardiovascular": [
            {"id": "heart_disease", "name": "Heart Disease", **adjusted_scores["heart_disease"]},
            {"id": "hypertension", "name": "Hypertension", **adjusted_scores["hypertension"]},
            {"id": "stroke_risk", "name": "Stroke Risk", **adjusted_scores["stroke_risk"]},
            {"id": "cardiovascular_risk", "name": "Cardiovascular Risk", **adjusted_scores["cardiovascular_risk"]},
        ],
        "other": [
            {"id": "chronic_kidney_disease", "name": "Kidney Disease", **adjusted_scores["chronic_kidney_disease"]},
            {"id": "cholesterol_disorder", "name": "Cholesterol Disorder", **adjusted_scores["cholesterol_disorder"]},
            {"id": "lifestyle_risk_index", "name": "Lifestyle Risk Index", **adjusted_scores["lifestyle_risk_index"]},
        ],
    }

    return {
        "disease_scores": adjusted_scores,
        "grouped_scores": grouped_scores,
        "dependency_explanations": explanations,
        "overall_risk_score": overall_score,
        "overall_risk_level": overall_level,
        "rule_risks": rule_risks,
        "health_dashboard": {
            "overall_health_score": rule_risks["overall_health_score"],
            "bmi_status": rule_risks["bmi_status"],
        },
    }
