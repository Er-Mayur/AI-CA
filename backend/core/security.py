# backend/core/security.py
import os
import jwt
from datetime import date, datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.hash import bcrypt
from db.database import SessionLocal
from db import models

# --------------------------------------------------------------------
# 1️ Configuration
# --------------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_DAYS = 7

auth_scheme = HTTPBearer()


# --------------------------------------------------------------------
# 2️ Password Hashing
# --------------------------------------------------------------------
def hash_password(password: str) -> str:
    """bcrypt automatically limits to 72 bytes internally"""
    return bcrypt.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.verify(plain, hashed)


# --------------------------------------------------------------------
# 3️ JWT Token Creation & Decoding
# --------------------------------------------------------------------
def create_token(user_id: int, email: str, pan_number: str) -> str:
    """Generate JWT token."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "pan": pan_number,
        "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str):
    """Decode a JWT token and validate expiry."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# --------------------------------------------------------------------
# 4️ Get current user from token
# --------------------------------------------------------------------
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """Return current user (DB object) based on provided token."""
    token = credentials.credentials
    data = decode_token(token)
    user_id = int(data.get("sub"))

    db = SessionLocal()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# --------------------------------------------------------------------
# 5️ Calculate user age based on current year
# --------------------------------------------------------------------
def calculate_age(dob: date) -> int:
    """Return accurate age (in years) from a given date of birth."""
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age
