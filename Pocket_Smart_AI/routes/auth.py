from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    UserOut,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):

    email = payload.email.lower()

    existing = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    user = User(
        name=payload.name,
        email=email,
        password_hash=hash_password(
            payload.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        user.id
    )

    settings = get_settings()

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=(
            settings.access_token_expire_minutes
            * 60
        ),
    )

    return user


@router.post(
    "/login",
    response_model=UserOut,
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):

    user = db.scalar(
        select(User).where(
            User.email
            == payload.email.lower()
        )
    )

    if not user or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        user.id
    )

    settings = get_settings()

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=(
            settings.access_token_expire_minutes
            * 60
        ),
    )

    return user


@router.post("/logout")
def logout(response: Response):

    response.delete_cookie(
        "access_token"
    )

    return {
        "message": "Logged out successfully."
    }


@router.get(
    "/me",
    response_model=UserOut,
)
def me(
    user: User = Depends(
        get_current_user
    ),
):
    return user