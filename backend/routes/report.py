from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import PredictionHistory, User
from backend.services.pdf_service import render_preventive_report_pdf
from backend.utils.auth import get_current_user

router = APIRouter()


class EmailReportRequest(BaseModel):
    email: str
    prediction_id: int | None = None


@router.post("/report/email")
def email_report(
    req: EmailReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send report via email (mock implementation)"""
    try:
        user_id = current_user.user_id
        q = db.query(PredictionHistory).filter(PredictionHistory.user_id == user_id)
        if req.prediction_id is not None:
            pred = q.filter(PredictionHistory.id == req.prediction_id).first()
        else:
            pred = q.order_by(PredictionHistory.created_at.desc()).first()

        if not pred:
            raise HTTPException(status_code=404, detail="No prediction found for this user.")

        # In a real implementation, this would send an email with the PDF attachment
        # For now, just log and return success
        print(f"Mock email sent to {req.email} with report for user {user_id}")

        return {"ok": True, "message": f"Report sent to {req.email}"}
    except HTTPException:
        raise


@router.get("/report")
def get_report(
    prediction_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user_id = current_user.user_id
        q = db.query(PredictionHistory).filter(PredictionHistory.user_id == user_id)
        if prediction_id is not None:
            pred = q.filter(PredictionHistory.id == prediction_id).first()
        else:
            pred = q.order_by(PredictionHistory.created_at.desc()).first()

        if not pred:
            raise HTTPException(status_code=404, detail="No prediction found for this user.")

        # Build the PDF input with the same keys the frontend expects.
        prediction_payload = {
            "diabetes_risk_prob": pred.diabetes_risk,
            "risk_level": pred.diabetes_risk_level,
            "heart_risk": pred.heart_risk_level,
            "bmi_status": pred.bmi_status,
            "overall_health_score": pred.overall_health_score,
            "recommendations": pred.recommendations or [],
            "rule_based": pred.risk_breakdown or {},
        }
        pdf_bytes = render_preventive_report_pdf(
            user_id=user_id, generated_at=dt.datetime.utcnow(), prediction=prediction_payload
        )
        headers = {"Content-Disposition": f'attachment; filename="preventive-health-report-{user_id}.pdf"'}
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")

