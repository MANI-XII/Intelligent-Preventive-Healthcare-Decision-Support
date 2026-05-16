from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import User
from backend.schemas.api import AuthTokenResponse, LoginRequest, MeResponse, SignupRequest
from backend.utils.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)

router = APIRouter()


@router.post("/auth/signup", response_model=AuthTokenResponse)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.user_id == req.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    user = User(
        user_id=req.user_id.strip(),
        password_hash=get_password_hash(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.user_id)
    return AuthTokenResponse(access_token=token, user_id=user.user_id)


@router.post("/auth/login", response_model=AuthTokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.user_id.strip(), req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(subject=user.user_id)
    return AuthTokenResponse(access_token=token, user_id=user.user_id)


@router.get("/auth/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(user_id=current_user.user_id)
