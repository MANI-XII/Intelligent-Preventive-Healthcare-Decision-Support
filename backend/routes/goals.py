from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import HealthGoal, Task, User
from backend.schemas.api import GoalCreateRequest, GoalUpdateRequest
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("")
def list_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(HealthGoal)
        .filter(HealthGoal.user_id == current_user.user_id)
        .order_by(HealthGoal.created_at.desc())
        .limit(200)
        .all()
    )
    return {
        "ok": True,
        "data": [
            {
                "id": r.id,
                "created_at": r.created_at,
                "goal_type": r.goal_type,
                "target_value": r.target_value,
                "deadline": r.deadline,
                "status": r.status,
                "progress_value": r.progress_value,
                "notes": r.notes,
            }
            for r in rows
        ],
    }


@router.post("")
def create_goal(
    req: GoalCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = HealthGoal(
        user_id=current_user.user_id,
        goal_type=req.goal_type,
        target_value=req.target_value,
        deadline=req.deadline,
        notes=req.notes,
        status="active",
        progress_value=0.0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "data": {"id": row.id}}


@router.patch("")
def update_goal(
    req: GoalUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(HealthGoal)
        .filter(HealthGoal.user_id == current_user.user_id, HealthGoal.id == req.goal_id)
        .first()
    )
    if not row:
        return {"ok": False, "detail": "Goal not found"}
    if req.target_value is not None:
        row.target_value = req.target_value
    if req.deadline is not None:
        row.deadline = req.deadline
    if req.status is not None:
        row.status = req.status
    if req.progress_value is not None:
        row.progress_value = req.progress_value
    if req.notes is not None:
        row.notes = req.notes
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "data": {"id": row.id}}


@router.delete("/{goal_id}")
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(HealthGoal)
        .filter(HealthGoal.user_id == current_user.user_id, HealthGoal.id == goal_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Goal not found")

    linked_tasks = (
        db.query(Task)
        .filter(Task.user_id == current_user.user_id, Task.notes.is_not(None))
        .all()
    )
    deleted_task_count = 0
    goal_marker = f"\"goal_id\": {goal_id}"
    compact_goal_marker = f"\"goal_id\":{goal_id}"
    for task in linked_tasks:
        notes = task.notes or ""
        if goal_marker in notes or compact_goal_marker in notes:
            db.delete(task)
            deleted_task_count += 1

    db.delete(row)
    db.commit()
    return {
        "ok": True,
        "deleted_goal_id": goal_id,
        "deleted_task_count": deleted_task_count,
    }
