from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import PredictionHistory, Task, User
from backend.utils.auth import get_current_user

router = APIRouter()


def _calculate_schedule_metrics(tasks: list[Task], start: dt.date, end: dt.date) -> dict[str, float]:
    overdue_pending = sum(1 for task in tasks if not task.completed and task.task_date < start)
    planning_window_end = end + dt.timedelta(days=7)
    planning_window_tasks = [
        task for task in tasks if start <= task.task_date <= planning_window_end and not task.completed
    ]

    tasks_by_day: dict[str, int] = {}
    for task in planning_window_tasks:
        key = task.task_date.isoformat()
        tasks_by_day[key] = tasks_by_day.get(key, 0) + 1

    active_days = len(tasks_by_day)
    max_tasks_in_day = max(tasks_by_day.values(), default=0)
    total_planned = len(planning_window_tasks)

    spacing_bonus = min(1.5, active_days * 0.2)
    concentration_penalty = max(0.0, (max_tasks_in_day - 2) * 0.45)
    overdue_penalty = min(6.0, overdue_pending * 0.85)

    return {
        "overdue_pending": float(overdue_pending),
        "spacing_bonus": spacing_bonus,
        "concentration_penalty": concentration_penalty,
        "overdue_penalty": overdue_penalty,
        "active_days": float(active_days),
        "total_planned": float(total_planned),
        "max_tasks_in_day": float(max_tasks_in_day),
    }


@router.get("/progress")
def get_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Keep signature compatible with query params:
    # GET /progress?user_id=...
    try:
        user_id = current_user.user_id
        end = dt.date.today()
        start = end - dt.timedelta(days=6)

        preds = (
            db.query(PredictionHistory)
            .filter(PredictionHistory.user_id == user_id)
            .order_by(PredictionHistory.created_at.desc())
            .limit(50)
            .all()
        )

        preds_sorted = sorted(preds, key=lambda x: x.created_at)
        predictions = [
            {
                "prediction_id": p.id,
                "created_at": p.created_at.isoformat(),
                "bmi": p.bmi,
                "diabetes_risk": p.diabetes_risk,
                "diabetes_risk_level": p.diabetes_risk_level,
                "overall_health_score": p.overall_health_score,
                "heart_risk_level": p.heart_risk_level,
                "bmi_status": p.bmi_status,
            }
            for p in preds_sorted
        ]

        all_tasks = (
            db.query(Task)
            .filter(Task.user_id == user_id)
            .order_by(Task.task_date.asc())
            .all()
        )

        tasks_week = [task for task in all_tasks if start <= task.task_date <= end]

        by_day_map: dict[str, dict] = {}
        total = len(tasks_week)
        completed = sum(1 for t in tasks_week if t.completed)

        for offset in range(0, 7):
            d = start + dt.timedelta(days=offset)
            by_day_map[d.isoformat()] = {"date": d.isoformat(), "completed": 0, "total": 0}

        for t in tasks_week:
            key = t.task_date.isoformat()
            by_day_map[key]["total"] += 1
            if t.completed:
                by_day_map[key]["completed"] += 1

        by_day = []
        for day in (start + dt.timedelta(days=i) for i in range(7)):
            key = day.isoformat()
            stats = by_day_map.get(key, {"completed": 0, "total": 0})
            status = "improved" if stats["completed"] > 0 else "stable"
            by_day.append({"date": key, "completed": stats["completed"], "total": stats["total"], "status": status})

        calendar_end = end + dt.timedelta(days=21)
        calendar_tasks = [
            task for task in all_tasks if task.task_date >= start and task.task_date <= calendar_end
        ]

        tasks_list = [
            {
                "id": t.id,
                "task_date": t.task_date.isoformat(),
                "title": t.title,
                "completed": t.completed,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "notes": t.notes,
            }
            for t in calendar_tasks
        ]

        latest_score = predictions[-1]["overall_health_score"] if predictions else 0.0
        latest_diabetes = predictions[-1]["diabetes_risk"] if predictions else 0.0
        risk_factor = 1.0
        if latest_diabetes >= 0.66:
            risk_factor = 0.65
        elif latest_diabetes >= 0.33:
            risk_factor = 0.85

        weekly_completion_rate = (completed / total) if total else 0.0
        schedule_metrics = _calculate_schedule_metrics(all_tasks, start, end)

        projected_score = latest_score + weekly_completion_rate * 4.0 * risk_factor
        projected_score += schedule_metrics["spacing_bonus"]
        projected_score -= schedule_metrics["concentration_penalty"]
        projected_score -= schedule_metrics["overdue_penalty"]
        projected_score = max(0.0, min(100.0, projected_score))

        condition = "Improving" if weekly_completion_rate > 0 else "Stable"
        if schedule_metrics["overdue_pending"] > 0:
            condition = "Needs attention"
        elif latest_diabetes >= 0.66:
            condition = "At risk" if weekly_completion_rate == 0 else condition

        note_parts: list[str] = []
        if weekly_completion_rate > 0:
            note_parts.append("Completing scheduled tasks this week is improving your projected health score.")
        else:
            note_parts.append("No tasks were completed this week, so your projected score is not improving yet.")

        if schedule_metrics["overdue_pending"] > 0:
            note_parts.append(f"{int(schedule_metrics['overdue_pending'])} overdue task(s) are lowering the projection until they are completed or rescheduled.")
        elif schedule_metrics["active_days"] > 0:
            note_parts.append(f"Your upcoming plan is spread across {int(schedule_metrics['active_days'])} day(s), which helps keep the workload manageable.")

        if schedule_metrics["max_tasks_in_day"] > 2:
            note_parts.append("Several tasks land on the same day, so the schedule pressure slightly reduces the projected score.")

        health_condition = {
            "current_score": round(latest_score, 2),
            "projected_score": round(projected_score, 2),
            "condition": condition,
            "note": " ".join(note_parts),
            "diabetes_risk": round(latest_diabetes * 100, 2),
        }

        return {
            "user_id": user_id,
            "date_range": {"start": start.isoformat(), "end": end.isoformat()},
            "task_calendar_range": {"start": start.isoformat(), "end": calendar_end.isoformat()},
            "predictions": predictions,
            "weekly_tasks": {
                "total": total,
                "completed": completed,
                "completion_rate": weekly_completion_rate,
                "by_day": by_day,
                "tasks": tasks_list,
                "health_condition": health_condition,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load progress: {e}")
