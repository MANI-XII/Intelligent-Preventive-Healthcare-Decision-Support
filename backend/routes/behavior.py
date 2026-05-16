from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import BehaviorLog, User
from backend.schemas.api import BehaviorLogCreateRequest
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/behavior", tags=["behavior"])


@router.post("")
def add_behavior_log(
    req: BehaviorLogCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = BehaviorLog(user_id=current_user.user_id, category=req.category, value=req.value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "data": {"id": row.id}}


@router.get("")
def list_behavior_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(BehaviorLog)
        .filter(BehaviorLog.user_id == current_user.user_id)
        .order_by(BehaviorLog.created_at.desc())
        .limit(200)
        .all()
    )
    return {
        "ok": True,
        "data": [
            {"id": r.id, "created_at": r.created_at, "category": r.category, "value": r.value}
            for r in rows
        ],
    }

