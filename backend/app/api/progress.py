from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from ..utils.database import get_db
from ..models.progress import UserProgress, StudySession
from ..models.quiz import QuizSession, UserAnswer

router = APIRouter()

class ProgressResponse(BaseModel):
    domain: str
    questions_attempted: int
    questions_correct: int
    average_score: float
    last_activity: datetime

    class Config:
        from_attributes = True

class StudySessionResponse(BaseModel):
    id: int
    session_date: datetime
    duration_minutes: int
    questions_answered: int

    class Config:
        from_attributes = True

class ProgressSummary(BaseModel):
    total_questions: int
    total_correct: int
    overall_average: float
    study_streak: int
    total_study_time: int

@router.get("/summary", response_model=ProgressSummary)
async def get_progress_summary(db: Session = Depends(get_db)):
    """Get overall progress summary"""
    # Get all quiz sessions
    sessions = db.query(QuizSession).all()

    total_questions = sum(s.total_questions for s in sessions)
    total_correct = sum(s.correct_answers for s in sessions)
    overall_average = (total_correct / total_questions * 100) if total_questions > 0 else 0

    # Calculate study streak (simplified)
    study_sessions = db.query(StudySession).order_by(StudySession.session_date.desc()).all()
    study_streak = len(study_sessions) if study_sessions else 0

    # Calculate total study time
    total_study_time = sum(s.duration_minutes for s in study_sessions)

    return {
        "total_questions": total_questions,
        "total_correct": total_correct,
        "overall_average": round(overall_average, 2),
        "study_streak": study_streak,
        "total_study_time": total_study_time
    }

@router.get("/domains", response_model=List[ProgressResponse])
async def get_domain_progress(db: Session = Depends(get_db)):
    """Get progress breakdown by domain"""
    progress = db.query(UserProgress).all()

    if not progress:
        # Return empty list if no progress yet
        return []

    return progress

@router.get("/sessions", response_model=List[StudySessionResponse])
async def get_study_sessions(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent study sessions"""
    sessions = db.query(StudySession).order_by(
        StudySession.session_date.desc()
    ).limit(limit).all()

    return sessions

@router.post("/sessions")
async def create_study_session(
    duration_minutes: int,
    questions_answered: int,
    topics_covered: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Record a new study session"""
    session = StudySession(
        user_id=None,  # TODO: Get from authenticated user
        duration_minutes=duration_minutes,
        questions_answered=questions_answered,
        topics_covered=topics_covered
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return {"message": "Study session recorded", "session_id": session.id}

@router.get("/analytics/weekly")
async def get_weekly_analytics(db: Session = Depends(get_db)):
    """Get weekly activity analytics"""
    # Get sessions from the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    sessions = db.query(StudySession).filter(
        StudySession.session_date >= seven_days_ago
    ).all()

    # Group by day
    daily_stats = {}
    for session in sessions:
        day = session.session_date.strftime('%a')
        if day not in daily_stats:
            daily_stats[day] = {
                'questions': 0,
                'time': 0
            }
        daily_stats[day]['questions'] += session.questions_answered
        daily_stats[day]['time'] += session.duration_minutes

    return daily_stats

@router.get("/achievements")
async def get_achievements(db: Session = Depends(get_db)):
    """Get user achievements"""
    # Calculate achievements based on progress
    sessions = db.query(QuizSession).all()
    study_sessions = db.query(StudySession).all()

    total_questions = sum(s.total_questions for s in sessions)
    perfect_scores = sum(1 for s in sessions if s.score_percentage == 100)
    total_study_time = sum(s.duration_minutes for s in study_sessions)

    achievements = [
        {
            "title": "First Steps",
            "description": "Complete your first quiz",
            "earned": len(sessions) > 0,
            "icon": "🎯"
        },
        {
            "title": "Week Warrior",
            "description": "Study 7 days in a row",
            "earned": len(study_sessions) >= 7,
            "icon": "🔥"
        },
        {
            "title": "Lab Master",
            "description": "Complete 5 practice labs",
            "earned": False,
            "icon": "🧪"
        },
        {
            "title": "Perfect Score",
            "description": "Get 100% on any quiz",
            "earned": perfect_scores > 0,
            "icon": "💯"
        },
        {
            "title": "Dedicated Learner",
            "description": "Study for 10 hours total",
            "earned": total_study_time >= 600,
            "icon": "📚"
        },
        {
            "title": "Question Master",
            "description": "Answer 100 questions",
            "earned": total_questions >= 100,
            "icon": "👑"
        }
    ]

    return achievements
