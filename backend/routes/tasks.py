from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import Task, User
from backend.schemas.api import TaskCreateRequest, TaskRescheduleRequest, TaskUpdateRequest
from backend.utils.auth import get_current_user

router = APIRouter()


def _normalize_task_title(title: str) -> str:
    return " ".join(title.split()).strip()


def _future_pending_tasks(db: Session, user_id: str, exclude_ids: set[int] | None = None) -> list[Task]:
    exclude_ids = exclude_ids or set()
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user_id, Task.completed == False, Task.task_date > dt.date.today())
        .order_by(Task.task_date.asc(), Task.id.asc())
        .all()
    )
    return [task for task in tasks if task.id not in exclude_ids]


def _plan_rescheduled_dates(existing_future: list[Task], task_count: int) -> tuple[list[dt.date], str]:
    today = dt.date.today()
    if task_count <= 0:
        return [], "end"

    if len(existing_future) >= 4:
        anchor_index = len(existing_future) // 2
        anchor_date = max(today + dt.timedelta(days=1), existing_future[anchor_index].task_date)
        return [anchor_date + dt.timedelta(days=index) for index in range(task_count)], "middle"

    anchor_date = existing_future[-1].task_date if existing_future else today
    return [anchor_date + dt.timedelta(days=index + 1) for index in range(task_count)], "end"


def _reschedule_options_for_task(db: Session, user_id: str, task_id: int) -> list[dict]:
    today = dt.date.today()
    future_pending = _future_pending_tasks(db, user_id, exclude_ids={task_id})
    future_counts: dict[str, int] = {}
    for item in future_pending:
        key = item.task_date.isoformat()
        future_counts[key] = future_counts.get(key, 0) + 1

    candidate_dates: list[dt.date] = []
    seen_dates: set[dt.date] = set()
    for offset in range(1, 15):
        candidate = today + dt.timedelta(days=offset)
        if candidate not in seen_dates:
            candidate_dates.append(candidate)
            seen_dates.add(candidate)

    for task in future_pending:
        if task.task_date not in seen_dates:
            candidate_dates.append(task.task_date)
            seen_dates.add(task.task_date)

    candidate_dates = sorted(candidate_dates)[:8]
    return [
        {
            "date": candidate.isoformat(),
            "pending_count": future_counts.get(candidate.isoformat(), 0),
            "label": (
                "Available slot"
                if future_counts.get(candidate.isoformat(), 0) == 0
                else f"{future_counts.get(candidate.isoformat(), 0)} task(s) already scheduled"
            ),
        }
        for candidate in candidate_dates
    ]


@router.post("/tasks")
def add_task(
    req: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        normalized_title = _normalize_task_title(req.title)
        existing_task = (
            db.query(Task)
            .filter(
                Task.user_id == current_user.user_id,
                Task.task_date == req.task_date,
                Task.title == normalized_title,
                Task.notes == req.notes,
            )
            .first()
        )
        if existing_task:
            return {
                "id": existing_task.id,
                "user_id": existing_task.user_id,
                "task_date": existing_task.task_date.isoformat(),
                "title": existing_task.title,
                "completed": existing_task.completed,
                "completed_at": existing_task.completed_at.isoformat() if existing_task.completed_at else None,
                "notes": existing_task.notes,
            }

        task = Task(
            user_id=current_user.user_id,
            task_date=req.task_date,
            title=normalized_title,
            completed=req.completed,
            notes=req.notes,
            completed_at=dt.datetime.utcnow() if req.completed else None,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return {
            "id": task.id,
            "user_id": task.user_id,
            "task_date": task.task_date.isoformat(),
            "title": task.title,
            "completed": task.completed,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "notes": task.notes,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add task: {e}")


@router.post("/tasks/update")
def update_task(
    req: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        task = (
            db.query(Task)
            .filter(Task.id == req.task_id, Task.user_id == current_user.user_id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")

        task.completed = req.completed
        task.completed_at = dt.datetime.utcnow() if req.completed else None
        task.notes = req.notes
        db.add(task)
        db.commit()
        db.refresh(task)

        return {
            "id": task.id,
            "user_id": task.user_id,
            "task_date": task.task_date.isoformat(),
            "title": task.title,
            "completed": task.completed,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "notes": task.notes,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {e}")


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.user_id == current_user.user_id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")

        db.delete(task)
        db.commit()
        return {"ok": True, "message": "Task deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {e}")


@router.delete("/tasks")
def delete_all_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        deleted_count = (
            db.query(Task)
            .filter(Task.user_id == current_user.user_id)
            .delete(synchronize_session=False)
        )
        db.commit()
        return {
            "ok": True,
            "deleted_count": deleted_count,
            "message": "All calendar tasks cleared successfully.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear tasks: {e}")


@router.get("/tasks/{task_id}/reschedule-options")
def get_reschedule_options(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == current_user.user_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task.completed:
        raise HTTPException(status_code=400, detail="Completed tasks do not need rescheduling.")
    if task.task_date >= dt.date.today():
        raise HTTPException(status_code=400, detail="Only missed tasks can be rescheduled.")

    return {
        "task_id": task.id,
        "title": task.title,
        "current_date": task.task_date.isoformat(),
        "options": _reschedule_options_for_task(db, current_user.user_id, task.id),
    }


@router.post("/tasks/{task_id}/reschedule")
def reschedule_task(
    task_id: int,
    req: TaskRescheduleRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.user_id == current_user.user_id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")

        today = dt.date.today()
        if task.completed:
            raise HTTPException(status_code=400, detail="Completed tasks cannot be rescheduled.")
        if task.task_date >= today:
            raise HTTPException(status_code=400, detail="Only missed tasks can be rescheduled.")

        options = _reschedule_options_for_task(db, current_user.user_id, task.id)
        available_dates = {item["date"] for item in options}
        target_date = req.target_date.isoformat() if req and req.target_date else None
        if not target_date:
            target_date = options[0]["date"] if options else None
        if not target_date:
            raise HTTPException(status_code=400, detail="No reschedule dates are available.")
        if target_date not in available_dates:
            raise HTTPException(status_code=400, detail="Selected reschedule date is not available.")

        task.task_date = dt.date.fromisoformat(target_date)
        db.add(task)

        db.commit()
        return {
            "ok": True,
            "message": "Task rescheduled. Your existing unfinished future tasks remain in place and the health score has been recalculated.",
            "task_id": task.id,
            "target_date": target_date,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reschedule task: {e}")
