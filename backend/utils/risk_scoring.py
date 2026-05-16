from __future__ import annotations

import re
from dataclasses import dataclass


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _risk_level_from_score(score: float) -> str:
    if score >= 66:
        return "High"
    if score >= 33:
        return "Moderate"
    return "Low"


def bmi_status(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def smoking_weight(smoking_history: str) -> float:
    s = (smoking_history or "").strip().lower()
    if s in {"current", "smoker", "yes"}:
        return 1.0
    if s in {"former", "ex-smoker"}:
        return 0.6
    if s in {"never", "no"}:
        return 0.1
    return 0.4  # unknown / not current / ever / no info


@dataclass(frozen=True)
class UserHealthInputs:
    gender: str
    age: float
    bmi: float
    blood_glucose_level: float
    hba1c_level: float
    smoking_history: str
    hypertension: int  # 0/1
    heart_disease: int  # 0/1
    activity_level: str = "moderate"
    sleep_hours: float = 7.0
    stress_level: str = "moderate"
    diet_type: str = "balanced"
    work_type: str = "mixed"
    blood_pressure: str | None = None

    def activity_level_score(self) -> float:
        s = (self.activity_level or "moderate").strip().lower()
        if s == "high":
            return 0.15
        if s == "moderate":
            return 0.40
        if s == "low":
            return 0.85
        return 0.55

    def sleep_risk(self) -> float:
        return _clamp((8.0 - self.sleep_hours) / 6.0, 0.0, 1.0)

    def smoking_weight(self) -> float:
        return smoking_weight(self.smoking_history)

    def stress_score(self) -> float:
        s = (self.stress_level or "moderate").strip().lower()
        if s == "low":
            return 0.18
        if s == "moderate":
            return 0.45
        if s == "high":
            return 0.82
        return 0.50

    def diet_score(self) -> float:
        s = (self.diet_type or "balanced").strip().lower()
        if s == "balanced":
            return 0.18
        if s == "low-sugar":
            return 0.22
        if s == "vegetarian":
            return 0.24
        if s == "high-carb":
            return 0.72
        if s == "high-fat":
            return 0.78
        return 0.48

    def work_type_score(self) -> float:
        s = (self.work_type or "mixed").strip().lower()
        if s == "active":
            return 0.22
        if s == "mixed":
            return 0.50
        if s == "sedentary":
            return 0.85
        return 0.50

    def blood_pressure_score(self) -> float:
        if not self.blood_pressure:
            return 0.40
        parts = [int(v) for v in re.findall(r"\d+", self.blood_pressure)]
        if len(parts) >= 2:
            systolic, diastolic = parts[0], parts[1]
            if systolic >= 140 or diastolic >= 90:
                return 0.95
            if systolic >= 130 or diastolic >= 85:
                return 0.75
            if systolic >= 120 or diastolic >= 80:
                return 0.40
            return 0.15
        return 0.40


def _age_component(age: float) -> float:
    # 20-> small, 80-> 1.0
    return _clamp((age - 20.0) / 60.0, 0.0, 1.0)


def _bmi_component(bmi: float) -> float:
    # BMI 18.5..35 roughly -> 0..1
    return _clamp((bmi - 18.5) / (35.0 - 18.5), 0.0, 1.0)


def _glucose_component(glucose: float) -> float:
    # 80..200 roughly -> 0..1
    return _clamp((glucose - 80.0) / (200.0 - 80.0), 0.0, 1.0)


def _hba1c_component(hba1c: float) -> float:
    # 4.5..8.5 -> 0..1
    return _clamp((hba1c - 4.5) / (8.5 - 4.5), 0.0, 1.0)


def calculate_rule_based_risks(
    inputs: UserHealthInputs,
    diabetes_risk_prob: float | None = None,
) -> dict:
    """
    Deterministic, explainable, rule-based risk scoring.

    Scores are returned as percentages (0-100).
    """
    age_c = _age_component(inputs.age)
    bmi_c = _bmi_component(inputs.bmi)
    glucose_c = _glucose_component(inputs.blood_glucose_level)
    hba1c_c = _hba1c_component(inputs.hba1c_level)
    smoke_c = inputs.smoking_weight()
    activity_c = inputs.activity_level_score()
    sleep_c = inputs.sleep_risk()
    stress_c = inputs.stress_score()
    diet_c = inputs.diet_score()
    work_c = inputs.work_type_score()
    bp_c = inputs.blood_pressure_score()

    is_obese = inputs.bmi >= 30.0
    has_prediabetes_hba1c = 5.7 <= inputs.hba1c_level <= 6.4
    has_prediabetes_glucose = 100 <= inputs.blood_glucose_level <= 125

    # Each disease score is a weighted mixture of components.
    prediabetes_score = _clamp(
        (
            0.30 * hba1c_c
            + 0.20 * glucose_c
            + 0.14 * bmi_c
            + 0.10 * age_c
            + 0.08 * activity_c
            + 0.06 * sleep_c
            + 0.06 * diet_c
            + 0.06 * stress_c
        )
        * 100
        + (18.0 if has_prediabetes_hba1c else 0.0)
        + (10.0 if has_prediabetes_glucose else 0.0),
        0,
        100,
    )

    hypertension_score = _clamp(
        (
            0.36 * age_c
            + 0.18 * bmi_c
            + 0.14 * smoke_c
            + 0.10 * activity_c
            + 0.08 * sleep_c
            + 0.08 * bp_c
            + 0.06 * stress_c
        )
        * 100
        + (25.0 if inputs.hypertension == 1 else 0.0),
        0,
        100,
    )

    heart_disease_score = _clamp(
        (
            0.28 * age_c
            + 0.20 * bmi_c
            + 0.20 * smoke_c
            + 0.14 * hba1c_c
            + 0.06 * activity_c
            + 0.04 * sleep_c
            + 0.06 * bp_c
            + 0.06 * stress_c
            + 0.06 * diet_c
        )
        * 100
        + (30.0 if inputs.heart_disease == 1 else 0.0)
        + (15.0 if diabetes_risk_prob is not None and diabetes_risk_prob >= 0.6 else 0.0),
        0,
        100,
    )

    stroke_score = _clamp(
        (
            0.38 * age_c
            + 0.24 * hypertension_score / 100
            + 0.16 * smoke_c
            + 0.10 * activity_c
            + 0.12 * stress_c
        )
        * 100,
        0,
        100,
    )

    kidney_disease_score = _clamp(
        (
            0.48 * hba1c_c
            + 0.22 * glucose_c
            + 0.16 * age_c
            + 0.06 * activity_c
            + 0.08 * diet_c
        )
        * 100
        + (15.0 if diabetes_risk_prob is not None and diabetes_risk_prob >= 0.6 else 0.0),
        0,
        100,
    )

    cholesterol_score = _clamp(
        (
            0.32 * bmi_c
            + 0.24 * glucose_c
            + 0.20 * smoke_c
            + 0.10 * sleep_c
            + 0.08 * diet_c
        )
        * 100
        + (10.0 if is_obese else 0.0),
        0,
        100,
    )

    metabolic_syndrome_score = _clamp(
        (
            0.30 * bmi_c
            + 0.24 * hypertension_score / 100
            + 0.26 * glucose_c
            + 0.08 * activity_c
            + 0.12 * stress_c
        )
        * 100
        + (12.0 if inputs.hypertension == 1 else 0.0),
        0,
        100,
    )

    cardiovascular_disease_score = _clamp(
        (0.25 * heart_disease_score + 0.25 * hypertension_score + 0.20 * cholesterol_score + 0.30 * smoke_c * 100) / 1.0,
        0,
        100,
    )

    lifestyle_disease_index_score = _clamp(
        (
            0.18 * prediabetes_score
            + 0.18 * hypertension_score
            + 0.18 * heart_disease_score
            + 0.14 * stroke_score
            + 0.10 * kidney_disease_score
            + 0.10 * cholesterol_score
            + 0.12 * metabolic_syndrome_score
        ),
        0,
        100,
    )

    overall_health_score = _clamp(100.0 - (lifestyle_disease_index_score * 0.85), 0, 100)

    risks = {
        "prediabetes": {
            "risk_level": _risk_level_from_score(prediabetes_score),
            "score": round(prediabetes_score, 2),
        },
        "hypertension_risk": {
            "risk_level": _risk_level_from_score(hypertension_score),
            "score": round(hypertension_score, 2),
        },
        "heart_disease_risk": {
            "risk_level": _risk_level_from_score(heart_disease_score),
            "score": round(heart_disease_score, 2),
        },
        "obesity": {
            "risk_level": "High" if is_obese else _risk_level_from_score(bmi_c * 100),
            "score": round(bmi_c * 100, 2),
            "bmi_status": bmi_status(inputs.bmi),
        },
        "stroke_risk": {
            "risk_level": _risk_level_from_score(stroke_score),
            "score": round(stroke_score, 2),
        },
        "kidney_disease_risk": {
            "risk_level": _risk_level_from_score(kidney_disease_score),
            "score": round(kidney_disease_score, 2),
        },
        "cholesterol_risk": {
            "risk_level": _risk_level_from_score(cholesterol_score),
            "score": round(cholesterol_score, 2),
        },
        "metabolic_syndrome": {
            "risk_level": _risk_level_from_score(metabolic_syndrome_score),
            "score": round(metabolic_syndrome_score, 2),
        },
        "cardiovascular_disease": {
            "risk_level": _risk_level_from_score(cardiovascular_disease_score),
            "score": round(cardiovascular_disease_score, 2),
        },
        "lifestyle_disease_index": {
            "risk_level": _risk_level_from_score(lifestyle_disease_index_score),
            "score": round(lifestyle_disease_index_score, 2),
        },
        "overall_health_score": round(overall_health_score, 2),
    }

    # Add explicit top-level BMI classification for convenience.
    risks["bmi_status"] = bmi_status(inputs.bmi)

    return risks

