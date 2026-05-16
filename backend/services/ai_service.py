from __future__ import annotations

import json
import os
from typing import Any, Dict

import httpx
from openai import OpenAI

from backend.config import settings


class AIService:
    def __init__(self):
        configured_provider = (settings.ai_provider or os.getenv("AI_PROVIDER") or "openai").strip().lower()
        gemini_api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        openai_api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.provider = "mock"
        self.model_name = settings.openai_model
        api_key = openai_api_key

        if configured_provider == "gemini":
            api_key = gemini_api_key or openai_api_key
        elif configured_provider == "xai":
            api_key = openai_api_key

        if configured_provider == "gemini":
            self.use_mock = not bool(api_key and len(api_key) > 20)
        elif configured_provider == "xai":
            self.use_mock = not bool(api_key and len(api_key) > 20 and api_key.startswith("gsk_"))
        else:
            self.use_mock = not bool(api_key and len(api_key) > 20 and api_key.startswith("sk-"))

        if not self.use_mock:
            try:
                client_kwargs = {
                    "api_key": api_key,
                    "http_client": httpx.Client(
                        timeout=60.0,
                        follow_redirects=True,
                    ),
                }
                if configured_provider == "gemini":
                    self.provider = "gemini"
                    self.model_name = settings.gemini_model
                    client_kwargs["base_url"] = settings.gemini_api_base_url
                elif configured_provider == "xai" or api_key.startswith("gsk_"):
                    self.provider = "xai"
                    self.model_name = settings.xai_model
                    client_kwargs["base_url"] = settings.xai_api_base_url
                else:
                    self.provider = "openai"
                    self.model_name = settings.openai_model

                self.client = OpenAI(
                    **client_kwargs,
                )
            except Exception as exc:
                self.use_mock = True
                self.provider = "mock"
                print(f"[DEV MODE] Falling back to mock AI responses because AI client initialization failed: {exc}")
        else:
            print("[DEV MODE] Using mock AI responses. Set a valid provider and API key for OpenAI, xAI, or Gemini to enable real AI responses.")

    def _call_openai(self, prompt: str, max_tokens: int = 500) -> str:
        """Helper method to call the configured LLM provider with error handling."""
        if self.use_mock:
            return self._get_mock_response(prompt)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def _get_mock_response(self, prompt: str) -> str:
        """Return mock AI responses for development/testing."""
        if "explanation" in prompt.lower():
            return "Based on your health data, you have moderate diabetes risk (65%) and hypertension risk (55%). Your BMI of 27.5 indicates you are overweight. Focus on reducing sugar intake and increasing physical activity. Blood glucose levels are elevated at 145 mg/dL. Consider consulting with your healthcare provider for personalized management."
        elif "recommendation" in prompt.lower():
            return "1. Increase daily physical activity to 150 minutes per week of moderate exercise\n2. Adopt a low-glycemic diet with increased fiber intake\n3. Monitor blood glucose levels regularly, especially before meals\n4. Reduce sodium intake to manage hypertension\n5. Schedule quarterly check-ups with your healthcare provider to track progress"
        elif "chat" in prompt.lower() or "message" in prompt.lower():
            return "Thank you for reaching out. I'm here to help with your health questions. Based on your profile, I'd recommend focusing on lifestyle modifications first. Remember to track your metrics regularly and consult with your healthcare team for personalized advice."
        else:
            return "Mock response for development mode. Please set a valid AI provider and API key for real AI-generated content."

    def generate_explanation(self, prediction_data: Dict[str, Any]) -> str:
        """Generate natural language explanation from prediction results."""
        prompt = f"""
        Based on the following health prediction data, provide a clear, concise natural language explanation of the user's health risks and key indicators.

        Prediction Data:
        - Diabetes Risk: {prediction_data.get('diabetes_risk', 'N/A')}%
        - Heart Disease Risk: {prediction_data.get('heart_disease_risk', 'N/A')}%
        - Hypertension Risk: {prediction_data.get('hypertension_risk', 'N/A')}%
        - Overall Health Score: {prediction_data.get('overall_health_score', 'N/A')}
        - BMI: {prediction_data.get('bmi', 'N/A')}
        - BMI Status: {prediction_data.get('bmi_status', 'N/A')}
        - Blood Glucose Level: {prediction_data.get('blood_glucose_level', 'N/A')} mg/dL
        - HbA1c Level: {prediction_data.get('hba1c_level', 'N/A')}%
        - Smoking History: {prediction_data.get('smoking_history', 'N/A')}
        - Hypertension: {'Yes' if prediction_data.get('hypertension') else 'No'}
        - Heart Disease: {'Yes' if prediction_data.get('heart_disease') else 'No'}
        - Age: {prediction_data.get('age', 'N/A')}
        - Gender: {prediction_data.get('gender', 'N/A')}

        Provide a 2-3 sentence explanation focusing on the main risk factors and their implications.
        """
        return self._call_openai(prompt, max_tokens=300)

    def generate_recommendation(self, health_data: Dict[str, Any], risk_data: Dict[str, Any]) -> str:
        """Generate personalized health recommendations."""
        prompt = f"""
        Based on the user's health data and risk assessment, provide personalized, actionable recommendations to improve their health and reduce risks.

        Health Data:
        - Age: {health_data.get('age', 'N/A')}
        - Gender: {health_data.get('gender', 'N/A')}
        - BMI: {health_data.get('bmi', 'N/A')}
        - Blood Glucose Level: {health_data.get('blood_glucose_level', 'N/A')} mg/dL
        - HbA1c Level: {health_data.get('hba1c_level', 'N/A')}%
        - Smoking History: {health_data.get('smoking_history', 'N/A')}
        - Hypertension: {'Yes' if health_data.get('hypertension') else 'No'}
        - Heart Disease: {'Yes' if health_data.get('heart_disease') else 'No'}
        - Activity Level: {health_data.get('activity_level', 'N/A')}
        - Sleep Hours: {health_data.get('sleep_hours', 'N/A')}
        - Stress Level: {health_data.get('stress_level', 'N/A')}
        - Diet Type: {health_data.get('diet_type', 'N/A')}

        Risk Assessment:
        - Diabetes Risk: {risk_data.get('diabetes_risk', 'N/A')}%
        - Heart Disease Risk: {risk_data.get('heart_disease_risk', 'N/A')}%
        - Overall Health Score: {risk_data.get('overall_health_score', 'N/A')}

        Provide 3-5 specific, practical recommendations. Focus on diet, exercise, lifestyle changes, and medical follow-up if needed.
        """
        return self._call_openai(prompt, max_tokens=400)

    def chatbot_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate chatbot response to general or app-related questions."""
        if self.use_mock:
            return self._mock_chatbot_response(query, context)

        quick_reply = self._quick_chatbot_response(query, context)
        if quick_reply:
            return quick_reply

        context_str = ""
        if context:
            context_str = f"""
            User Context:
            Age: {context.get('age', 'N/A')}
            BMI: {context.get('bmi', 'N/A')}
            Glucose: {context.get('blood_glucose_level', 'N/A')}
            HbA1c: {context.get('hba1c_level', 'N/A')}
            Diabetes Risk: {context.get('diabetes_risk', 'N/A')}%
            Heart Risk: {context.get('heart_disease_risk', 'N/A')}%
            Hypertension Risk: {context.get('hypertension_risk', 'N/A')}%
            Health Score: {context.get('overall_health_score', 'N/A')}
            Blood Pressure: {context.get('blood_pressure', 'N/A')}
            Summary: {context.get('prediction_status_summary', 'N/A')}
            """

        prompt = f"""
        You are a healthcare app assistant.
        Answer clearly, directly, and briefly.
        Use the user context only when it is relevant.
        For app questions, explain the next step in the app.
        For personalized health-result questions, say whether the picture looks reassuring, mixed, or concerning, name the main drivers, and give 2-3 practical precautions.
        Do not invent missing values.
        Keep the answer under 120 words unless the user asks for more detail.

        {context_str}

        User Question: {query}

        Answer:
        """
        return self._call_openai(prompt, max_tokens=160)

    def _quick_chatbot_response(self, query: str, context: Dict[str, Any] | None = None) -> str | None:
        q = query.strip()
        ql = q.lower()

        if any(word in ql for word in ["hello", "hi", "hey"]):
            return "Hi! I can help with your predictions, reports, goals, monitoring, and general health-app questions."

        if any(word in ql for word in ["who are you", "what can you do", "help me"]):
            return "I can explain your predictions, suggest precautions, answer app questions, and help you understand your health data."

        if any(word in ql for word in ["report", "pdf", "download"]):
            return "Run a prediction first, then use the report option to download a summary of your risk levels, explanations, and recommendations."

        if any(word in ql for word in ["goal", "goals", "task", "tasks"]):
            return "Goals track bigger health targets, and Tasks break them into daily actions you can complete step by step."

        if context and any(
            phrase in ql
            for phrase in [
                "my prediction",
                "my result",
                "my results",
                "my score",
                "is it good",
                "is it bad",
                "how are my results",
                "explain my prediction",
            ]
        ):
            return self._mock_chatbot_response(query, context)

        return None

    def _mock_chatbot_response(self, query: str, context: Dict[str, Any] | None = None) -> str:
        q = query.strip()
        ql = q.lower()

        if context and any(
            phrase in ql
            for phrase in [
                "my prediction",
                "my result",
                "my results",
                "my score",
                "is it good",
                "is it bad",
                "how are my results",
                "explain my prediction",
            ]
        ):
            diabetes = context.get("diabetes_risk", "N/A")
            heart = context.get("heart_disease_risk", "N/A")
            hypertension = context.get("hypertension_risk", "N/A")
            score = context.get("overall_health_score", "N/A")
            bmi = context.get("bmi", "N/A")
            glucose = context.get("blood_glucose_level", "N/A")
            hba1c = context.get("hba1c_level", "N/A")

            numeric_values = [value for value in [diabetes, heart, hypertension] if isinstance(value, (int, float))]
            highest = max(numeric_values) if numeric_values else 0
            if isinstance(score, (int, float)) and score >= 8 and highest < 35:
                verdict = "Your latest prediction looks fairly good overall."
            elif highest >= 70 or (isinstance(score, (int, float)) and score < 5):
                verdict = "Your latest prediction looks concerning overall."
            else:
                verdict = "Your latest prediction looks mixed rather than clearly good or clearly bad."

            return (
                f"{verdict} Your saved results show diabetes risk {diabetes}%, heart disease risk {heart}%, "
                f"hypertension risk {hypertension}%, and a health score of {score}. "
                f"The main things to watch are your BMI ({bmi}), blood glucose ({glucose}), and HbA1c ({hba1c}) because they can push risk upward when they stay elevated. "
                "Precautions: keep monitoring your numbers regularly, focus on food and activity habits that improve glucose and weight control, and discuss persistent high-risk results with a healthcare professional."
            )

        if any(word in ql for word in ["hello", "hi", "hey"]):
            return "Hi! I can help with general questions, app features, healthcare risks, reports, goals, and predictions. Ask me anything."

        if any(word in ql for word in ["who are you", "what can you do", "help me"]):
            return "I’m the assistant for this app. I can answer general questions, explain app features, discuss preventive healthcare topics, and help interpret prediction, monitoring, and insight results."

        if any(word in ql for word in ["report", "pdf", "download"]):
            return "You can download a report after running a prediction. The report summarizes risk levels, explanations, and recommendations from your health data."

        if any(word in ql for word in ["goal", "goals", "task", "tasks"]):
            return "Use Goals to set health targets like weight, sleep, or activity improvements. Use Tasks to track smaller daily actions that support those goals."

        if any(word in ql for word in ["predict", "prediction", "risk score", "diabetes", "heart disease", "hypertension"]):
            extra = ""
            if context:
                extra = (
                    f" Based on your latest saved context, your BMI is {context.get('bmi', 'N/A')} and "
                    f"your overall health score is {context.get('overall_health_score', 'N/A')}."
                )
            return (
                "The app uses your clinical and lifestyle inputs to estimate preventive health risks and explain what factors matter most."
                + extra
            )

        if any(word in ql for word in ["insight", "insights", "monitor", "monitoring", "trend"]):
            return "The Insights and Monitoring features combine prediction history, monitoring signals, and behavior patterns to explain what is changing over time and what actions may help most."

        if any(word in ql for word in ["what is", "why", "how", "explain"]):
            return (
                "I can answer that, but the full AI model response is currently unavailable. "
                f"Here’s the best concise help I can give: your question was '{q}'. "
                "If this is about the app, tell me which feature you mean and I’ll explain it step by step."
            )

        return (
            "I can help with general questions as well as app features like prediction, insights, monitoring, reports, goals, and chat. "
            f"You asked: '{q}'. If you want a more specific answer, send a little more detail and I’ll refine it."
        )

    def generate_insight(self, health_data: Dict[str, Any], trend_data: Dict[str, Any] = None) -> str:
        """Generate summary insights about user's health condition."""
        trend_str = ""
        if trend_data:
            trend_str = f"""
            Health Trends:
            - Risk Trend: {trend_data.get('risk_trend', 'N/A')}
            - BMI Trend: {trend_data.get('bmi_trend', 'N/A')}
            - Glucose Trend: {trend_data.get('glucose_trend', 'N/A')}
            """

        prompt = f"""
        Provide a concise summary and insights about the user's current health condition and any trends.

        Current Health Data:
        - Age: {health_data.get('age', 'N/A')}
        - BMI: {health_data.get('bmi', 'N/A')} ({health_data.get('bmi_status', 'N/A')})
        - Blood Glucose Level: {health_data.get('blood_glucose_level', 'N/A')} mg/dL
        - HbA1c Level: {health_data.get('hba1c_level', 'N/A')}%
        - Diabetes Risk: {health_data.get('diabetes_risk', 'N/A')}%
        - Heart Disease Risk: {health_data.get('heart_disease_risk', 'N/A')}%
        - Overall Health Score: {health_data.get('overall_health_score', 'N/A')}

        {trend_str}

        Generate a 2-3 sentence insight summary highlighting the overall condition, key concerns, and any positive trends.
        """
        return self._call_openai(prompt, max_tokens=250)

    def generate_multisource_insight(
        self,
        prediction_data: Dict[str, Any],
        monitoring_data: Dict[str, Any],
        behavior_data: Dict[str, Any],
        analysis: Dict[str, Any] | None = None,
    ) -> str:
        """Generate structured insight output from prediction, monitoring, and behavior data."""
        prompt = f"""
You are an advanced AI healthcare intelligence assistant.

This module represents the "Insights Feature" of an AI-based preventive healthcare system.

Your task is to generate high-level, explainable, and actionable insights by analyzing multiple sources of user health data.

INPUT DATA:

1. Prediction Results:
{json.dumps(prediction_data, indent=2, default=str)}

2. Monitoring Data (time-series):
{json.dumps(monitoring_data, indent=2, default=str)}

3. Behavioral Data:
{json.dumps(behavior_data, indent=2, default=str)}

OBJECTIVE:

Perform multi-source analysis to explain the user's health condition, identify key risk drivers, detect trends, and provide meaningful insights for decision-making.

TASKS:

1. ROOT CAUSE ANALYSIS
- Identify primary factors contributing to risk
- Explain WHY the risk is high

2. TREND ANALYSIS
- Analyze time-based changes from monitoring data
- Detect:
  • Increasing patterns
  • Decreasing patterns
  • Stable conditions

3. RISK INTERACTION ANALYSIS
- Identify relationships between conditions
- Example:
  Diabetes -> Heart Risk

4. BEHAVIORAL IMPACT ANALYSIS
- Analyze lifestyle factors (activity, sleep, etc.)
- Explain how behavior affects health

5. OVERALL HEALTH INTERPRETATION
- Provide a clear summary of the user's condition
- Combine all inputs into one explanation

6. ACTIONABLE INSIGHTS
- Provide 2–3 clear improvement suggestions

OUTPUT FORMAT:

🔹 Insight Summary:
[High-level explanation of health condition]

🔹 Key Risk Drivers:
- Factor 1 (impact %)
- Factor 2 (impact %)

🔹 Trend Insight:
[Time-based observation]

🔹 Risk Interaction:
[Interdependency explanation]

🔹 Behavioral Insight:
[Impact of habits]

🔹 Actionable Recommendations:
- Suggestion 1
- Suggestion 2
- Suggestion 3

IMPORTANT:

- Keep explanation clear and structured
- Avoid complex medical terminology
- Focus on reasoning and clarity
- Make insights useful for decision-making
        """

        if self.use_mock:
            return self._format_multisource_insight(analysis or {})

        response = self._call_openai(prompt, max_tokens=700)
        if response.startswith("Error generating response:"):
            return self._format_multisource_insight(analysis or {})
        return response

    def _format_multisource_insight(self, analysis: Dict[str, Any]) -> str:
        """Format deterministic fallback output for the insights feature."""
        summary = analysis.get(
            "summary",
            "There is not enough health data yet to generate a full insight summary.",
        )
        drivers = analysis.get("key_risk_drivers") or []
        trend = analysis.get(
            "trend_insight",
            "More monitoring data is needed before clear trends can be described.",
        )
        interaction = analysis.get(
            "risk_interaction",
            "More data is needed to explain how your risk factors interact with each other.",
        )
        behavioral = analysis.get(
            "behavioral_insight",
            "Add a few more behavior logs to connect daily habits with your health trends.",
        )
        recommendations = analysis.get("recommendations") or [
            "Keep logging health and behavior data regularly.",
            "Track the same measurements over time to reveal clearer patterns.",
        ]

        driver_lines = "\n".join(
            f"- {item.get('factor', 'Unknown factor')} ({item.get('impact_percent', 0)}%)"
            for item in drivers[:3]
        ) or "- Limited data (0%)"
        recommendation_lines = "\n".join(f"- {item}" for item in recommendations[:3])

        return (
            "🔹 Insight Summary:\n"
            f"{summary}\n\n"
            "🔹 Key Risk Drivers:\n"
            f"{driver_lines}\n\n"
            "🔹 Trend Insight:\n"
            f"{trend}\n\n"
            "🔹 Risk Interaction:\n"
            f"{interaction}\n\n"
            "🔹 Behavioral Insight:\n"
            f"{behavioral}\n\n"
            "🔹 Actionable Recommendations:\n"
            f"{recommendation_lines}"
        )


# Global instance
ai_service = AIService()
