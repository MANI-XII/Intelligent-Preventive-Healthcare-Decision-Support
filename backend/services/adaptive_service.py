from __future__ import annotations

from sqlalchemy.orm import Session

from backend.db.models import PredictionHistory
from backend.utils.risk_scoring import UserHealthInputs


def generate_adaptive_insights(
    user_id: str,
    current_health_index: float,
    inputs: UserHealthInputs,
    db: Session,
) -> dict:
    history = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == user_id)
        .order_by(PredictionHistory.created_at.desc())
        .limit(5)
        .all()
    )

    if not history:
        return {
            "adjustment_factor": 1.0,
            "message": "This is your first prediction in the adaptive learning system.",
            "trend": "Baseline established for future self-learning.",
        }

    prior_scores = [float(p.overall_health_score) for p in history if p.overall_health_score is not None]
    average_prior = sum(prior_scores) / len(prior_scores) if prior_scores else current_health_index
    improvement = current_health_index >= average_prior
    delta = round(current_health_index - average_prior, 2)
    factor = 1.0 + max(-0.1, min(0.1, delta / 200.0))

    return {
        "adjustment_factor": round(factor, 3),
        "message": (
            "Your recent inputs suggest an improving preventive trajectory." if improvement else "Your current health index is trending lower than recent history."
        ),
        "trend": (
            f"Health index change from recent average: {delta:+.2f}."
        ),
        "prior_average": round(average_prior, 2),
    }
