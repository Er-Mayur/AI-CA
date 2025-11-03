# backend/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User
from schemas.auth_schemas import RegisterIn, LoginIn, TokenOut, UserOut
from core.security import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

# --------------------------------------------------------------------
# 1️ Register API (Full Profile Required)
# --------------------------------------------------------------------
@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    """Register a new user with PAN, Email, and complete profile details."""

    # Check if user already exists by email or PAN
    existing_user = (
        db.query(User)
        .filter((User.email == payload.email.lower()) | (User.pan_number == payload.pan_number.upper()))
        .first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or PAN already registered")

    # Hash password securely
    hashed_pw = hash_password(payload.password)

    # Create a new user entry
    new_user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        pan_number=payload.pan_number.upper(),
        password_hash=hashed_pw,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        employment_type=payload.employment_type,
        residential_status=payload.residential_status,
        state=payload.state,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate JWT token
    token = create_token(new_user.id, new_user.email, new_user.pan_number)

    return TokenOut(access_token=token)


# --------------------------------------------------------------------
# 2️ Login API (Email or PAN)
# --------------------------------------------------------------------
@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    """Login using PAN or Email."""

    identifier = payload.identifier.strip().upper()
    user = None

    if "@" in identifier:
        user = db.query(User).filter(User.email == identifier.lower()).first()
    else:
        user = db.query(User).filter(User.pan_number == identifier).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    token = create_token(user.id, user.email, user.pan_number)
    return TokenOut(access_token=token)


# --------------------------------------------------------------------
# 3️ Get current user details (for dashboard)
# --------------------------------------------------------------------
@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """Return profile of the logged-in user."""
    # 'current_user' will be provided later using get_current_user()
    return current_user
