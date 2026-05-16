from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import User
from backend.services.monitoring_service import monitoring_service
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/monitor", tags=["monitoring"])


@router.post("/report", response_model=dict)
def generate_monitoring_report(
    current_record: dict = Body(...),
    days_back: int = Query(30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate comprehensive health monitoring report.

    Analyzes trends, detects anomalies, and provides insights based on
    historical health data compared to current measurements.
    """
    try:
        report = monitoring_service.generate_monitoring_report(
            db=db,
            user_id=current_user.user_id,
            current_record=current_record,
            days_back=days_back
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate monitoring report: {str(e)}"
        )


@router.get("/trends", response_model=dict)
def get_health_trends(
    days_back: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get simplified trend analysis for key health parameters.
    """
    try:
        # Get recent records
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days_back)

        from backend.db.models import HealthRecord
        records = db.query(HealthRecord).filter(
            HealthRecord.user_id == current_user.user_id,
            HealthRecord.created_at >= cutoff_date
        ).order_by(HealthRecord.created_at.desc()).all()

        if not records:
            return {"trends": {}, "message": "No historical data available"}

        # Calculate simple trends
        trends = {}
        parameters = ["bmi", "blood_glucose_level", "hba1c_level", "systolic_bp", "diastolic_bp"]

        for param in parameters:
            values = [getattr(record, param) for record in records if getattr(record, param) is not None]
            if len(values) >= 2:
                # Simple trend calculation
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]

                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)

                if second_avg > first_avg * 1.05:  # 5% increase
                    trends[param] = "Increasing"
                elif second_avg < first_avg * 0.95:  # 5% decrease
                    trends[param] = "Decreasing"
                else:
                    trends[param] = "Stable"
            else:
                trends[param] = "Insufficient data"

        return {"trends": trends, "data_points": len(records)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get health trends: {str(e)}"
        )


@router.get("/alerts", response_model=dict)
def get_monitoring_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get active health monitoring alerts and warnings.
    """
    try:
        # Get latest health record
        from backend.db.models import HealthRecord
        latest_record = db.query(HealthRecord).filter(
            HealthRecord.user_id == current_user.user_id
        ).order_by(HealthRecord.created_at.desc()).first()

        if not latest_record:
            return {"alerts": [], "message": "No health records found"}

        # Simple alert generation based on current values
        alerts = []

        # BMI alerts
        if latest_record.bmi >= 30:
            alerts.append({
                "type": "warning",
                "parameter": "BMI",
                "message": "BMI indicates obesity. Consider weight management plan.",
                "severity": "high"
            })
        elif latest_record.bmi >= 25:
            alerts.append({
                "type": "info",
                "parameter": "BMI",
                "message": "BMI indicates overweight. Monitor weight trends.",
                "severity": "medium"
            })

        # Glucose alerts
        if latest_record.blood_glucose_level >= 200:
            alerts.append({
                "type": "critical",
                "parameter": "Blood Glucose",
                "message": "Blood glucose is critically high. Seek medical attention.",
                "severity": "high"
            })
        elif latest_record.blood_glucose_level >= 140:
            alerts.append({
                "type": "warning",
                "parameter": "Blood Glucose",
                "message": "Blood glucose is elevated. Monitor closely.",
                "severity": "medium"
            })

        # HbA1c alerts
        if latest_record.hba1c_level >= 7.0:
            alerts.append({
                "type": "warning",
                "parameter": "HbA1c",
                "message": "HbA1c indicates poor glucose control. Consult healthcare provider.",
                "severity": "high"
            })

        # Blood pressure alerts
        if latest_record.systolic_bp >= 180 or latest_record.diastolic_bp >= 120:
            alerts.append({
                "type": "critical",
                "parameter": "Blood Pressure",
                "message": "Blood pressure is critically high. Seek immediate medical attention.",
                "severity": "high"
            })
        elif latest_record.systolic_bp >= 140 or latest_record.diastolic_bp >= 90:
            alerts.append({
                "type": "warning",
                "parameter": "Blood Pressure",
                "message": "Blood pressure is elevated. Monitor and consult healthcare provider.",
                "severity": "medium"
            })

        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "last_checked": latest_record.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monitoring alerts: {str(e)}"
        )
