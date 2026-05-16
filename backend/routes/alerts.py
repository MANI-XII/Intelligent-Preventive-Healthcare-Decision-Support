from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import Alert, User
from backend.schemas.api import AlertAckRequest
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Alert)
        .filter(Alert.user_id == current_user.user_id)
        .order_by(Alert.created_at.desc())
        .limit(200)
        .all()
    )
    return {
        "ok": True,
        "data": [
            {
                "id": r.id,
                "created_at": r.created_at,
                "severity": r.severity,
                "category": r.category,
                "title": r.title,
                "message": r.message,
                "acknowledged": r.acknowledged,
                "meta": r.meta or {},
            }
            for r in rows
        ],
    }


@router.post("/ack")
def ack_alert(
    req: AlertAckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(Alert)
        .filter(Alert.user_id == current_user.user_id, Alert.id == req.alert_id)
        .first()
    )
    if not row:
        return {"ok": False, "detail": "Alert not found"}
    row.acknowledged = bool(req.acknowledged)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "data": {"id": row.id, "acknowledged": row.acknowledged}}

