from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from backend.db.models import HealthRecord, PredictionHistory


class MonitoringService:
    def generate_monitoring_report(
        self,
        db: Session,
        user_id: int,
        current_record: Dict[str, Any],
        days_back: int = 30,
    ) -> Dict[str, Any]:
        previous_records = self._get_previous_records(db, user_id, days_back)
        previous_risks = self._get_previous_risks(db, user_id, days_back)

        if not previous_records:
          return self._generate_empty_report(current_record)

        trend_analysis = self._analyze_trends(previous_records, current_record)
        risk_change = self._analyze_risk_changes(previous_risks, current_record)
        anomaly_detection = self._detect_anomalies(previous_records, current_record)
        health_insights = self._generate_health_insights(trend_analysis, risk_change, anomaly_detection)
        overall_status = self._determine_overall_status(trend_analysis, risk_change, anomaly_detection)
        recommendations = self._generate_recommendations(trend_analysis, risk_change, anomaly_detection)

        return {
            "title": "Monitoring Report",
            "trend_analysis": trend_analysis,
            "risk_change": risk_change,
            "anomaly_detection": anomaly_detection,
            "health_insights": health_insights,
            "overall_status": overall_status,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat(),
            "data_points": len(previous_records) + 1,
        }

    def _get_previous_records(self, db: Session, user_id: int, days_back: int) -> List[Dict[str, Any]]:
        cutoff_date = datetime.now() - timedelta(days=days_back)
        rows = (
            db.query(HealthRecord)
            .filter(HealthRecord.user_id == user_id, HealthRecord.recorded_at >= cutoff_date)
            .order_by(HealthRecord.recorded_at.asc(), HealthRecord.id.asc())
            .all()
        )

        records: List[Dict[str, Any]] = []
        for row in rows:
            systolic_bp, diastolic_bp = self._parse_blood_pressure(row.blood_pressure)
            records.append(
                {
                    "id": row.id,
                    "recorded_at": row.recorded_at.isoformat(),
                    "bmi": row.bmi,
                    "blood_glucose_level": row.blood_glucose_level,
                    "hba1c_level": row.hba1c_level,
                    "blood_pressure": row.blood_pressure,
                    "systolic_bp": systolic_bp,
                    "diastolic_bp": diastolic_bp,
                }
            )
        return records

    def _get_previous_risks(self, db: Session, user_id: int, days_back: int) -> List[float]:
        cutoff_date = datetime.now() - timedelta(days=days_back)
        rows = (
            db.query(PredictionHistory)
            .filter(PredictionHistory.user_id == user_id, PredictionHistory.created_at >= cutoff_date)
            .order_by(PredictionHistory.created_at.asc(), PredictionHistory.id.asc())
            .all()
        )
        return [row.overall_health_score for row in rows if row.overall_health_score is not None]

    def _parse_blood_pressure(self, blood_pressure: str | None) -> tuple[float | None, float | None]:
        if not blood_pressure:
            return None, None
        values = [int(v) for v in re.findall(r"\d+", blood_pressure)]
        if len(values) >= 2:
            return float(values[0]), float(values[1])
        return None, None

    def _analyze_trends(self, previous_records: List[Dict[str, Any]], current_record: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        trend_analysis = {
            "bmi": self._calculate_numeric_trend(previous_records, current_record, "bmi", "BMI"),
            "blood_glucose_level": self._calculate_numeric_trend(previous_records, current_record, "blood_glucose_level", "Blood Glucose"),
            "hba1c_level": self._calculate_numeric_trend(previous_records, current_record, "hba1c_level", "HbA1c"),
            "blood_pressure": self._calculate_blood_pressure_trend(previous_records, current_record),
        }
        return trend_analysis

    def _calculate_numeric_trend(
        self,
        previous_records: List[Dict[str, Any]],
        current_record: Dict[str, Any],
        key: str,
        label: str,
    ) -> Dict[str, Any]:
        values = [record[key] for record in previous_records if record.get(key) is not None]
        current_value = current_record.get(key)
        if current_value is None:
            return {"label": label, "trend": "Stable", "assessment": "Stable", "change": None}
        if not values:
            return {"label": label, "trend": "Stable", "assessment": "Stable", "change": 0.0}

        previous_value = values[-1]
        change = current_value - previous_value
        direction = "Increasing" if change > 0.1 else "Decreasing" if change < -0.1 else "Stable"
        assessment = "Improving" if direction == "Decreasing" else "Concerning" if direction == "Increasing" else "Stable"

        return {
            "label": label,
            "trend": direction,
            "assessment": assessment,
            "previous_value": round(previous_value, 2),
            "current_value": round(current_value, 2),
            "change": round(change, 2),
        }

    def _calculate_blood_pressure_trend(self, previous_records: List[Dict[str, Any]], current_record: Dict[str, Any]) -> Dict[str, Any]:
        previous_pairs = [
            (record.get("systolic_bp"), record.get("diastolic_bp"))
            for record in previous_records
            if record.get("systolic_bp") is not None and record.get("diastolic_bp") is not None
        ]
        current_systolic = current_record.get("systolic_bp")
        current_diastolic = current_record.get("diastolic_bp")
        if current_systolic is None or current_diastolic is None:
            current_systolic, current_diastolic = self._parse_blood_pressure(current_record.get("blood_pressure"))

        if current_systolic is None or current_diastolic is None:
            return {"label": "Blood Pressure", "trend": "Stable", "assessment": "Stable", "change": None}
        if not previous_pairs:
            return {
                "label": "Blood Pressure",
                "trend": "Stable",
                "assessment": "Stable",
                "previous_value": None,
                "current_value": f"{int(current_systolic)}/{int(current_diastolic)}",
                "change": None,
            }

        previous_systolic, previous_diastolic = previous_pairs[-1]
        systolic_change = current_systolic - previous_systolic
        diastolic_change = current_diastolic - previous_diastolic

        direction = "Stable"
        if systolic_change > 3 or diastolic_change > 3:
            direction = "Increasing"
        elif systolic_change < -3 or diastolic_change < -3:
            direction = "Decreasing"

        assessment = "Improving" if direction == "Decreasing" else "Concerning" if direction == "Increasing" else "Stable"

        return {
            "label": "Blood Pressure",
            "trend": direction,
            "assessment": assessment,
            "previous_value": f"{int(previous_systolic)}/{int(previous_diastolic)}",
            "current_value": f"{int(current_systolic)}/{int(current_diastolic)}",
            "change": f"{int(round(systolic_change))}/{int(round(diastolic_change))}",
        }

    def _analyze_risk_changes(self, previous_risks: List[float], current_record: Dict[str, Any]) -> Dict[str, Any]:
        current_risk = current_record.get("overall_risk_score")
        if current_risk is None:
            current_risk = current_record.get("overall_health_score")

        if current_risk is None:
            return {
                "previous_risk": None,
                "current_risk": None,
                "change": None,
                "status": "Stable",
            }

        previous_risk = previous_risks[-1] if previous_risks else None
        if previous_risk is None:
            return {
                "previous_risk": None,
                "current_risk": round(current_risk, 1),
                "change": None,
                "status": "Stable",
            }

        change = current_risk - previous_risk
        if abs(change) < 1:
            status = "Stable"
        elif change < 0:
            status = "Improving"
        else:
            status = "Worsening"

        return {
            "previous_risk": round(previous_risk, 1),
            "current_risk": round(current_risk, 1),
            "change": round(change, 1),
            "change_percent": round(change, 1),
            "status": status,
        }

    def _detect_anomalies(self, previous_records: List[Dict[str, Any]], current_record: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not previous_records:
            return []

        latest_previous = previous_records[-1]
        anomalies: List[Dict[str, Any]] = []
        checks = [
            ("blood_glucose_level", "Blood Glucose", 30, 180),
            ("hba1c_level", "HbA1c", 0.5, 7.0),
            ("bmi", "BMI", 2.0, 35.0),
        ]

        for key, label, spike_threshold, critical_high in checks:
            previous_value = latest_previous.get(key)
            current_value = current_record.get(key)
            if previous_value is None or current_value is None:
                continue
            change = current_value - previous_value
            if abs(change) >= spike_threshold or current_value >= critical_high:
                severity = self._classify_anomaly_severity(abs(change), spike_threshold, current_value >= critical_high)
                anomalies.append(
                    {
                        "parameter": label,
                        "description": f"Sudden {label.lower()} {'spike' if change > 0 else 'drop'} detected ({previous_value} → {current_value})",
                        "severity": severity,
                    }
                )

        previous_systolic, previous_diastolic = latest_previous.get("systolic_bp"), latest_previous.get("diastolic_bp")
        current_systolic = current_record.get("systolic_bp")
        current_diastolic = current_record.get("diastolic_bp")
        if current_systolic is None or current_diastolic is None:
            current_systolic, current_diastolic = self._parse_blood_pressure(current_record.get("blood_pressure"))

        if (
            previous_systolic is not None
            and previous_diastolic is not None
            and current_systolic is not None
            and current_diastolic is not None
        ):
            systolic_change = abs(current_systolic - previous_systolic)
            diastolic_change = abs(current_diastolic - previous_diastolic)
            if systolic_change >= 20 or diastolic_change >= 15 or current_systolic >= 180 or current_diastolic >= 120:
                severity = self._classify_anomaly_severity(max(systolic_change / 20, diastolic_change / 15), 1.0, current_systolic >= 180 or current_diastolic >= 120)
                anomalies.append(
                    {
                        "parameter": "Blood Pressure",
                        "description": f"Sudden blood pressure spike detected ({int(previous_systolic)}/{int(previous_diastolic)} → {int(current_systolic)}/{int(current_diastolic)})",
                        "severity": severity,
                    }
                )

        return anomalies

    def _classify_anomaly_severity(self, change: float, threshold: float, is_critical: bool) -> str:
        if is_critical or change >= threshold * 2:
            return "High"
        if change >= threshold * 1.25:
            return "Medium"
        return "Low"

    def _generate_health_insights(
        self,
        trends: Dict[str, Dict[str, Any]],
        risk_change: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
    ) -> str:
        improving = [trend["label"] for trend in trends.values() if trend.get("assessment") == "Improving"]
        concerning = [trend["label"] for trend in trends.values() if trend.get("assessment") == "Concerning"]

        parts: List[str] = []
        if improving:
            parts.append(f"{', '.join(improving)} shows positive movement over time.")
        if concerning:
            parts.append(f"{', '.join(concerning)} needs closer attention because it is moving in the wrong direction.")
        if risk_change.get("status") == "Improving":
            parts.append("Your overall risk is lower than before, which suggests the recent changes are helping.")
        elif risk_change.get("status") == "Worsening":
            parts.append("Your overall risk is higher than before, so preventive action is important now.")
        if anomalies:
            parts.append("A sudden change was detected, so more frequent monitoring is recommended.")

        if not parts:
            return "Your health values are mostly stable right now, with no major warning signs in the recent data."
        return " ".join(parts)

    def _determine_overall_status(
        self,
        trends: Dict[str, Dict[str, Any]],
        risk_change: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
    ) -> str:
        improving = sum(1 for trend in trends.values() if trend.get("assessment") == "Improving")
        concerning = sum(1 for trend in trends.values() if trend.get("assessment") == "Concerning")

        if anomalies and any(item["severity"] == "High" for item in anomalies):
            return "Worsening"
        if improving > 0 and concerning > 0:
            return "Mixed Progress"
        if risk_change.get("status") == "Improving" and concerning == 0:
            return "Improving"
        if risk_change.get("status") == "Worsening" or concerning > improving:
            return "Worsening"
        return "Stable"

    def _generate_recommendations(
        self,
        trends: Dict[str, Dict[str, Any]],
        risk_change: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
    ) -> List[str]:
        recommendations: List[str] = []

        if trends["blood_glucose_level"].get("assessment") == "Concerning" or trends["hba1c_level"].get("assessment") == "Concerning":
            recommendations.append("Reduce sugar and refined carbohydrate intake and keep checking glucose regularly.")
        if trends["bmi"].get("assessment") == "Concerning":
            recommendations.append("Increase regular physical activity and keep meals balanced to support healthy weight control.")
        if trends["blood_pressure"].get("assessment") == "Concerning":
            recommendations.append("Reduce sodium intake and monitor blood pressure more frequently.")
        if risk_change.get("status") == "Worsening":
            recommendations.append("Book a follow-up health review if the higher risk trend continues.")
        if anomalies:
            recommendations.append("Repeat the abnormal measurement soon to confirm whether the change is temporary or persistent.")

        if not recommendations:
            recommendations = [
                "Maintain regular physical activity.",
                "Keep following balanced meals and hydration habits.",
                "Continue routine monitoring to track progress.",
            ]

        return recommendations[:3]

    def _generate_empty_report(self, current_record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": "Monitoring Report",
            "trend_analysis": {
                "bmi": {"label": "BMI", "trend": "Stable", "assessment": "Stable", "change": None},
                "blood_glucose_level": {"label": "Blood Glucose", "trend": "Stable", "assessment": "Stable", "change": None},
                "hba1c_level": {"label": "HbA1c", "trend": "Stable", "assessment": "Stable", "change": None},
                "blood_pressure": {"label": "Blood Pressure", "trend": "Stable", "assessment": "Stable", "change": None},
            },
            "risk_change": {
                "previous_risk": None,
                "current_risk": current_record.get("overall_risk_score") or current_record.get("overall_health_score"),
                "change": None,
                "status": "Stable",
            },
            "anomaly_detection": [],
            "health_insights": "This is your first health record. Continue monitoring to build a useful health trend over time.",
            "overall_status": "Stable",
            "recommendations": [
                "Keep logging health records regularly.",
                "Stay active and follow balanced meals.",
                "Repeat measurements on a routine schedule.",
            ],
            "generated_at": datetime.now().isoformat(),
            "data_points": 1,
        }


monitoring_service = MonitoringService()
