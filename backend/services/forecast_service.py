from __future__ import annotations

from backend.utils.risk_scoring import UserHealthInputs


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def forecast_risk_trend(
    inputs: UserHealthInputs,
    disease_risks: dict,
) -> list[dict]:
    """Create a 3- and 6-month projected risk trend based on current lifestyle and clinical signals."""
    diabetes_base = disease_risks.get("diabetes", {}).get("score", 0.0)
    heart_base = disease_risks.get("heart_disease_risk", {}).get("score", 0.0)
    hypertension_base = disease_risks.get("hypertension_risk", {}).get("score", 0.0)

    drift = 0.0
    if inputs.activity_level == "low":
        drift += 4.0
    if inputs.activity_level == "high":
        drift -= 2.0
    if inputs.smoking_history == "current":
        drift += 3.0
    if inputs.bmi >= 30:
        drift += 2.0
    if inputs.sleep_hours < 6:
        drift += 1.5
    if inputs.sleep_hours >= 7:
        drift -= 1.0

    diabetes_drift = drift * 0.65
    heart_drift = drift * 0.55
    hypertension_drift = drift * 0.50

    forecast = []
    for months in [0, 3, 6]:
        multiplier = months / 3.0
        forecast.append(
            {
                "months_ahead": months,
                "diabetes_risk": round(_clamp(diabetes_base + diabetes_drift * multiplier), 2),
                "heart_disease_risk": round(_clamp(heart_base + heart_drift * multiplier), 2),
                "hypertension_risk": round(_clamp(hypertension_base + hypertension_drift * multiplier), 2),
            }
        )

    return forecast
