from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import User, UserProfile
from backend.schemas.api import ProfileResponse, ProfileUpdateRequest
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()
    if not row:
        row = UserProfile(user_id=current_user.user_id, created_at=dt.datetime.utcnow())
        db.add(row)
        db.commit()
        db.refresh(row)
    return ProfileResponse(
        user_id=row.user_id,
        full_name=row.full_name,
        date_of_birth=row.date_of_birth,
        height_cm=row.height_cm,
        weight_kg=row.weight_kg,
        locale=row.locale,
        medical_history=row.medical_history or {},
    )


@router.put("", response_model=ProfileResponse)
def update_profile(
    req: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()
    if not row:
        row = UserProfile(user_id=current_user.user_id, created_at=dt.datetime.utcnow())
        db.add(row)
        db.commit()
        db.refresh(row)

    if req.full_name is not None:
        row.full_name = req.full_name
    if req.date_of_birth is not None:
        row.date_of_birth = req.date_of_birth
    if req.height_cm is not None:
        row.height_cm = req.height_cm
    if req.weight_kg is not None:
        row.weight_kg = req.weight_kg
    if req.locale is not None:
        row.locale = req.locale
    if req.medical_history is not None:
        row.medical_history = req.medical_history

    db.add(row)
    db.commit()
    db.refresh(row)

    return ProfileResponse(
        user_id=row.user_id,
        full_name=row.full_name,
        date_of_birth=row.date_of_birth,
        height_cm=row.height_cm,
        weight_kg=row.weight_kg,
        locale=row.locale,
        medical_history=row.medical_history or {},
    )

