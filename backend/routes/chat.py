from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.db.models import User
from backend.schemas.api import ChatRequest, ChatResponse
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


def _has_any(msg: str, terms: list[str]) -> bool:
    return any(term in msg for term in terms)


def _respond_with(reply: str, actions: list[str] | None = None) -> ChatResponse:
    return ChatResponse(reply=reply, suggested_actions=actions or [])


def _build_fallback(user_id: str) -> ChatResponse:
    return _respond_with(
        (
            f"Hi {user_id}! I can help with healthcare guidance, multi-disease risk prediction, report generation, "
            "goals, alerts, and explainability. Ask me about diabetes risk, heart disease, hypertension, "
            "health index, recommendations, or simulation."
        ),
        [
            "How do I lower diabetes risk?",
            "What is the preventive health index?",
            "How can I use the prediction dashboard?",
        ],
    )


def _project_guidance(msg: str, user_id: str) -> ChatResponse:
    if _has_any(msg, ["diabetes", "blood glucose", "hba1c"]):
        if _has_any(msg, ["risk", "chance", "probability"]):
            return _respond_with(
                (
                    "This system predicts diabetes risk using clinical data like BMI, blood glucose, HbA1c, "
                    "smoking history, sleep and activity. Use the Prediction page to see your risk score, "
                    "explainable feature drivers, and tailored recommendations."
                ),
                ["Open Prediction page", "Run a new prediction"],
            )
        if _has_any(msg, ["manage", "lower", "reduce", "prevent"]):
            return _respond_with(
                (
                    "To reduce diabetes risk, maintain a healthy BMI, improve diet and exercise regularly, "
                    "limit smoking, keep blood glucose in range, and prioritize 7–9 hours of sleep. "
                    "The app also suggests personalized preventive actions after prediction."
                ),
                ["Create a goal", "View recommendations"],
            )
        return _respond_with(
            (
                "Diabetes risk is evaluated by the model and explained through feature importance. "
                "You can query the prediction dashboard for the current risk and preventive suggestions."
            ),
            ["Run a prediction", "Check explainability"],
        )

    if _has_any(msg, ["heart disease", "cardio", "cardiovascular"]):
        if _has_any(msg, ["risk", "chance", "probability"]):
            return _respond_with(
                (
                    "Heart disease risk is estimated using factors such as age, BMI, hypertension, smoking history, "
                    "and lifestyle metrics. The dashboard reports this risk alongside diabetes and hypertension."
                ),
                ["Open Prediction page", "View risk summary"],
            )
        if _has_any(msg, ["manage", "lower", "reduce", "prevent"]):
            return _respond_with(
                (
                    "Reducing heart disease risk includes controlling blood pressure, staying physically active, "
                    "avoiding tobacco, and managing cholesterol. Regular monitoring and preventive goals help too."
                ),
                ["Create a heart health goal", "View goals"],
            )
        return _respond_with(
            (
                "Heart disease insights are part of the multi-disease risk overview in this system. "
                "Use the prediction assistant to review your current heart disease risk level."
            ),
            ["Run a new prediction", "Download report"],
        )

    if _has_any(msg, ["hypertension", "blood pressure", "high blood pressure"]):
        if _has_any(msg, ["risk", "chance", "probability"]):
            return _respond_with(
                (
                    "Hypertension risk is calculated using existing medical history, BMI, and lifestyle data. "
                    "Keeping your blood pressure in range can improve your overall preventive health score."
                ),
                ["Open Prediction page", "View health score"],
            )
        if _has_any(msg, ["manage", "lower", "reduce", "prevent"]):
            return _respond_with(
                (
                    "Managing hypertension includes reducing salt, exercising regularly, avoiding smoking, "
                    "and tracking blood pressure. The system can help you create preventive tasks around these actions."
                ),
                ["Create a goal", "Add a task"],
            )
        return _respond_with(
            (
                "Hypertension is one of the three risk domains modeled by the app. "
                "Predict to see your hypertension score and tailored recommendations."
            ),
            ["Predict hypertension risk", "Open Prediction page"],
        )

    if _has_any(msg, ["healthy index", "preventive index", "health index", "dphi"]):
        return _respond_with(
            (
                "The preventive health index combines disease risk, lifestyle metrics, and clinical factors into a single score. "
                "A higher score means better preventive health, and the app uses it to recommend actions you can take."
            ),
            ["View health score", "Run prediction"],
        )

    if _has_any(msg, ["explainable", "shap", "feature", "drivers", "interpretation"]):
        return _respond_with(
            (
                "Explainability shows which features influence your predicted risk most. "
                "For example, BMI, sleep hours, and smoking history can be major drivers. "
                "Use the Explainable Insights section after prediction to review them."
            ),
            ["Check explainability", "Run a prediction"],
        )

    if _has_any(msg, ["report", "pdf", "download report"]):
        return _respond_with(
            (
                "After running a prediction, you can download a PDF preventive health report from the Prediction page. "
                "The report summarizes risk levels, explanations, and recommended actions."
            ),
            ["Download PDF report", "Run a prediction"],
        )

    if _has_any(msg, ["goal", "goals", "target", "plan"]):
        return _respond_with(
            (
                "You can set preventive health goals in the Goals section, such as increasing activity, improving sleep, or lowering BMI. "
                "Goals help you stay focused on long-term risk reduction."
            ),
            ["Create a goal", "View goals"],
        )

    if _has_any(msg, ["alert", "alerts", "notification"]):
        return _respond_with(
            (
                "The Alerts section notifies you of abnormal health readings or important risk changes. "
                "Use it to stay proactive about follow-up actions."
            ),
            ["View alerts", "Check notifications"],
        )

    if _has_any(msg, ["simulate", "simulation", "forecast", "predictive"]):
        return _respond_with(
            (
                "Simulation helps you understand how changes in behavior or health metrics may affect future risk. "
                "Use the simulate feature to explore different preventive scenarios."
            ),
            ["Run a simulation", "Try different scenarios"],
        )

    if _has_any(msg, ["data", "dataset", "model", "training", "accuracy", "roc_auc"]):
        return _respond_with(
            (
                "This project uses machine learning models trained on clinical and lifestyle data. "
                "The system builds separate risk models for diabetes, heart disease, and hypertension and uses explainability to make the results understandable."
            ),
            ["View prediction dashboard", "Read model details"],
        )

    if _has_any(msg, ["hello", "hi", "hey", "greetings"]):
        return _respond_with(
            (
                f"Hello {user_id}! I am your preventive healthcare assistant. Ask me about risk prediction, goals, reports, or healthy behaviors."
            ),
            ["How do I lower diabetes risk?", "What is the health index?", "Show me recommendations"],
        )

    if _has_any(msg, ["how", "what", "why", "explain"]):
        return _respond_with(
            (
                "I can answer healthcare and project-related questions about this system. "
                "Ask about risk factors, prediction results, preventive advice, report generation, or how the dashboard works."
            ),
            ["How does prediction work?", "What should I do to lower risk?", "How do I create a goal?"],
        )

    return _build_fallback(user_id)


@router.post("", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    msg = req.message.strip().lower()
    return _project_guidance(msg, current_user.user_id)

