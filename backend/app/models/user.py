from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..utils.database import Base
from ..utils.encrypted_types import EncryptedString

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class StudentLevel(str, enum.Enum):
    PRIMARY = "primary"
    HIGH_SCHOOL = "high_school"
    TERTIARY = "tertiary"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(EncryptedString(500), unique=True, index=True, nullable=False)  # Encrypted PII
    hashed_password = Column(String, nullable=False)
    full_name = Column(EncryptedString(500), nullable=True)  # Encrypted PII
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    student_level = Column(Enum(StudentLevel), nullable=True)  # Only for students
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
