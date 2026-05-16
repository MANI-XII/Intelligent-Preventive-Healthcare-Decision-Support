from __future__ import annotations

from backend.utils.risk_scoring import UserHealthInputs


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _category_from_score(score: float) -> str:
    if score < 30:
        return "High risk"
    if score < 70:
        return "Moderate"
    return "Healthy"


def calculate_preventive_health_index(
    inputs: UserHealthInputs,
    disease_risks: dict,
) -> dict:
    """Compute a normalized Dynamic Preventive Health Index (DPHI)."""
    # Clinical component: lower values are better.
    bmi_component = _clamp((inputs.bmi - 18.5) / 16.5 * 100.0)
    glucose_component = _clamp((inputs.blood_glucose_level - 80.0) / 120.0 * 100.0)
    hba1c_component = _clamp((inputs.hba1c_level - 4.5) / 4.0 * 100.0)
    age_component = _clamp((inputs.age - 20.0) / 60.0 * 100.0)

    # Lifestyle adjustment pulls down risk when activity and sleep are better.
    activity_score = 100.0 - (inputs.activity_level_score() * 100.0)
    sleep_score = _clamp((8.0 - inputs.sleep_hours) / 4.0 * 100.0)
    smoking_risk = 100.0 * inputs.smoking_weight()

    clinical_value = 100.0 - (0.30 * bmi_component + 0.25 * glucose_component + 0.20 * hba1c_component + 0.15 * age_component)
    lifestyle_value = 100.0 - (0.35 * activity_score + 0.30 * sleep_score + 0.35 * smoking_risk)

    diabetes_risk = disease_risks.get("diabetes", {}).get("score", 0.0)
    heart_risk = disease_risks.get("heart_disease_risk", {}).get("score", 0.0)
    hypertension_risk = disease_risks.get("hypertension_risk", {}).get("score", 0.0)
    cardio_risk = disease_risks.get("cardiovascular_risk", {}).get("score", 0.0)
    metabolic_risk = disease_risks.get("metabolic_syndrome", {}).get("score", 0.0)
    obesity_risk = disease_risks.get("obesity", {}).get("score", 0.0)

    predicted_risk_value = 100.0 - (
        0.30 * diabetes_risk
        + 0.20 * heart_risk
        + 0.15 * hypertension_risk
        + 0.15 * cardio_risk
        + 0.10 * metabolic_risk
        + 0.10 * obesity_risk
    )

    raw_score = 0.35 * clinical_value + 0.30 * lifestyle_value + 0.35 * predicted_risk_value
    final_score = _clamp(raw_score)
    category = _category_from_score(final_score)

    return {
        "score": round(final_score, 2),
        "category": category,
        "components": {
            "clinical": round(_clamp(clinical_value), 2),
            "lifestyle": round(_clamp(lifestyle_value), 2),
            "predicted_risk": round(_clamp(predicted_risk_value), 2),
        },
    }
