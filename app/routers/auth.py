
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.models import User
from app.schemas import RegisterIn, LoginIn, TokenOut, UserOut
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(
    payload: RegisterIn,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(User.email == payload.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user_count = db.scalar(
        select(func.count()).select_from(User)
    )

    if user_count != 0:
        raise HTTPException(
            status_code=403,
            detail="Registration is disabled. Ask an Admin to register users.",
        )

    user = User(
        email=str(payload.email),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role="Admin",
        warehouse_id=None,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@router.post("/login", response_model=TokenOut)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == form_data.username)
    )

    if (
        not user
        or not verify_password(form_data.password, user.password_hash)
        or not user.is_active
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    return TokenOut(
        access_token=create_access_token(str(user.id))
    )

@router.get("/me", response_model=UserOut)
def me(
    user: User = Depends(get_current_user),
):
    return user