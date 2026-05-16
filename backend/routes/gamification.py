from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import GamificationState, User
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/gamification", tags=["gamification"])


def _get_or_create(db: Session, user_id: str) -> GamificationState:
    row = db.query(GamificationState).filter(GamificationState.user_id == user_id).first()
    if row:
        return row
    row = GamificationState(user_id=user_id, points=0, streak_days=0, badges=[], updated_at=dt.datetime.utcnow())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("")
def get_state(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = _get_or_create(db, current_user.user_id)
    return {
        "ok": True,
        "data": {
            "points": row.points,
            "streak_days": row.streak_days,
            "badges": row.badges or [],
            "updated_at": row.updated_at,
        },
    }

