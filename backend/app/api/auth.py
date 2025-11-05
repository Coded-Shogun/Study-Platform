from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from ..utils.database import get_db
from ..models.user import User, UserRole, StudentLevel

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "student"  # admin, teacher, student
    student_level: Optional[str] = None  # primary, high_school, tertiary (required for students)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    student_level: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Validate student_level is provided for students
    if user.role == "student" and not user.student_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student level is required for student accounts (primary, high_school, or tertiary)"
        )

    # Validate role value
    valid_roles = ["admin", "teacher", "student"]
    if user.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    # Validate student_level value if provided
    if user.student_level:
        valid_levels = ["primary", "high_school", "tertiary"]
        if user.student_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid student level. Must be one of: {', '.join(valid_levels)}"
            )

    # Create new user (in production, hash the password!)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=user.password,  # TODO: Hash password in production
        full_name=user.full_name,
        role=user.role,
        student_level=user.student_level
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post("/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or user.hashed_password != login_data.password:  # TODO: Verify hashed password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # TODO: Create and return JWT token
    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "student_level": user.student_level
        }
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user(db: Session = Depends(get_db)):
    """Get current user info"""
    # TODO: Get user from JWT token
    # For now, return mock data
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not fully implemented yet"
    )
