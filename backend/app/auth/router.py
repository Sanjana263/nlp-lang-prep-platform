from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.schemas import (
    LoginRequest, ProfileUpdate, RegisterRequest, TokenResponse, UserPublic,
)
from app.core.security import (
    DUMMY_HASH, create_access_token, hash_password, verify_password,
)
from app.db.session import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.user_id, user.role),
        user=UserPublic.model_validate(user),
    )


def _login(db: Session, body: LoginRequest, required_role: str) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    # Always run one bcrypt check, and return one generic error (FR-1.5).
    ok = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not ok or user.role != required_role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _token_response(user)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """FR-1.1, FR-1.2, FR-1.3, FR-1.7 (created_at is set by the DB)."""
    email = body.email.lower()
    if db.scalar(select(User.user_id).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        full_name=body.full_name,
        email=email,
        password_hash=hash_password(body.password),
        target_exam=body.target_exam,
        role="student",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two simultaneous registrations with the same email
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    db.refresh(user)
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """FR-1.4, FR-1.5 (student login)."""
    return _login(db, body, required_role="student")


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(body: LoginRequest, db: Session = Depends(get_db)):
    """FR-1.8: separate admin login."""
    return _login(db, body, required_role="admin")


@users_router.get("/me", response_model=UserPublic)
def read_me(user: User = Depends(get_current_user)):
    return user


@users_router.put("/me", response_model=UserPublic)
def update_me(body: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """FR-1.6."""
    if body.full_name is not None:
        user.full_name = body.full_name.strip()
    if body.target_exam is not None:
        user.target_exam = body.target_exam
    db.commit()
    db.refresh(user)
    return user
