from __future__ import annotations

from backend.utils.risk_scoring import bmi_status


def _level_from_score(score: float) -> str:
    if score >= 66:
        return "High"
    if score >= 33:
        return "Moderate"
    return "Low"


def generate_recommendations(
    *,
    gender: str,
    age: float,
    bmi: float,
    blood_glucose_level: float,
    hba1c_level: float,
    smoking_history: str,
    hypertension: int,
    heart_disease: int,
    activity_level: str,
    sleep_hours: float,
    diabetes_risk_prob: float,
    rule_risks: dict,
    health_index: dict | None = None,
    anomalies: dict | None = None,
    adaptive_insights: dict | None = None,
) -> list[str]:
    recs: list[str] = []

    bmi_s = bmi_status(bmi)
    if bmi_s == "Obese":
        recs.append("Start a sustainable weight reduction plan with daily walking and strength training.")
        recs.append("Replace sugary drinks with water and high-fiber meals.")
    elif bmi_s == "Overweight":
        recs.append("Aim for gradual weight reduction using portion control and more movement.")
        recs.append("Swap refined carbs for vegetables, legumes, and lean protein.")

    if hba1c_level >= 6.5 or blood_glucose_level >= 126 or diabetes_risk_prob >= 0.6:
        recs.append("Reduce refined carbohydrates and choose low-GI options.")
        recs.append("Track meals and glucose patterns for data-driven adjustments.")
    elif 5.7 <= hba1c_level <= 6.4:
        recs.append("Prevent progression with daily activity and focused dietary changes.")
        recs.append("Reassess HbA1c in 3 months and follow a preventive plan.")

    if hypertension == 1 or rule_risks.get("hypertension_risk", {}).get("risk_level") in {"High", "Moderate"}:
        recs.append("Reduce sodium intake and avoid highly processed snacks.")
        recs.append("Include regular moderate-intensity exercise at least 3 times per week.")

    if heart_disease == 1 or rule_risks.get("heart_disease_risk", {}).get("risk_level") in {"High", "Moderate"}:
        recs.append("Follow a heart-healthy eating pattern rich in vegetables, nuts, and fish.")
        recs.append("Build safe cardiovascular activity into your weekly routine.")

    if rule_risks.get("cholesterol_risk", {}).get("risk_level") in {"High", "Moderate"}:
        recs.append("Monitor cholesterol and reduce saturated fat with plant-forward meals.")
        recs.append("Add soluble fiber and omega-3 rich foods to your daily diet.")

    if rule_risks.get("lifestyle_disease_index", {}).get("risk_level") in {"High", "Moderate"}:
        recs.append("Improve your lifestyle index with regular movement, stress reduction, and better sleep.")

    if rule_risks.get("metabolic_syndrome", {}).get("risk_level") == "High":
        recs.append("Address metabolic syndrome with glucose control, blood pressure monitoring, and weight management.")
    if rule_risks.get("obesity", {}).get("risk_level") == "High" or bmi_s == "Obese":
        recs.append("Focus on gradual weight loss through balanced nutrition and daily movement.")

    if rule_risks.get("kidney_disease_risk", {}).get("risk_level") in {"High", "Moderate"}:
        recs.append("Monitor kidney function and stay well-hydrated while limiting processed sodium.")

    if smoking_history == "current":
        recs.append("Create a smoking cessation plan with social support.")
        recs.append("Avoid environments with cigarette smoke and triggers.")
    elif smoking_history == "former":
        recs.append("Maintain your smoke-free status and avoid relapse triggers.")

    if activity_level == "low":
        recs.append("Break up sedentary time with short activity breaks every hour.")
    if activity_level == "high":
        recs.append("Keep your strong activity habit and monitor recovery.")

    if sleep_hours < 6:
        recs.append("Practice sleep hygiene: consistent bedtime, low screens, and a calm environment.")
    if sleep_hours >= 8:
        recs.append("Good sleep is a strong preventive factor; keep it consistent.")

    if health_index and health_index.get("category") == "High risk":
        recs.append("Schedule a follow-up evaluation with your healthcare provider.")

    if anomalies and anomalies.get("anomaly_detected"):
        recs.append("Review abnormal readings with your clinician or care team.")

    if adaptive_insights and adaptive_insights.get("adjustment_factor") < 0.98:
        recs.append("Focus on the top 2 risk drivers to improve your personalized health index.")

    if not recs:
        recs.append("Maintain your current healthy behaviors and continue regular monitoring.")

    return recs[:9]


def recommendations_to_tasks(recommendations: list[str]) -> list[dict]:
    """
    Convert recommendations into task objects.
    """
    tasks = []
    for i, r in enumerate(recommendations, start=1):
        tasks.append(
            {
                "title": r,
                "notes": None,
                "completed": False,
                "task_date": None,  # caller sets default
                "task_seq": i,
            }
        )
    return tasks

