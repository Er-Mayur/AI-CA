from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, ActivityHistory
from schemas import UserCreate, UserLogin, UserResponse, Token
from auth import get_password_hash, verify_password, create_access_token
from dependencies import get_current_user
from datetime import datetime

router = APIRouter()

@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.pan_card == user_data.pan_card) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.pan_card == user_data.pan_card:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PAN card already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        pan_card=user_data.pan_card.upper(),
        email=user_data.email,
        gender=user_data.gender,
        date_of_birth=datetime.combine(user_data.date_of_birth, datetime.min.time()),
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log activity
    activity = ActivityHistory(
        user_id=new_user.id,
        financial_year="",
        activity_type="USER_REGISTRATION",
        description=f"User {new_user.name} registered successfully"
    )
    db.add(activity)
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    # Find user by PAN or email
    user = db.query(User).filter(
        (User.pan_card == credentials.identifier.upper()) | 
        (User.email == credentials.identifier)
    ).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Log activity
    activity = ActivityHistory(
        user_id=user.id,
        financial_year="",
        activity_type="USER_LOGIN",
        description=f"User {user.name} logged in"
    )
    db.add(activity)
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

