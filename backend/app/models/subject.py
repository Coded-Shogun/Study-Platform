from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..utils.database import Base
from .user import StudentLevel

# Association table for many-to-many relationship between subjects and student levels
subject_levels = Table(
    'subject_levels',
    Base.metadata,
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True),
    Column('student_level', String, primary_key=True)
)

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    code = Column(String, nullable=False, unique=True)  # e.g., "CLOUD101", "MATH-P1"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to questions
    questions = relationship("Question", back_populates="subject")

class Category(Base):
    """Categories/Domains within subjects (e.g., 'Security', 'Networking' for Cloud+)"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    subject = relationship("Subject")
    questions = relationship("Question", back_populates="category")
