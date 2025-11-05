from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from ..utils.database import Base

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    domain = Column(String, nullable=False, index=True)
    questions_attempted = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_date = Column(DateTime(timezone=True), server_default=func.now())
    duration_minutes = Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    topics_covered = Column(String, nullable=True)  # JSON string of topics
