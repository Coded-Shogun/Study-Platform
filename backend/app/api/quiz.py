from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..utils.database import get_db
from ..models.quiz import Question, QuizSession, UserAnswer

router = APIRouter()

class QuestionResponse(BaseModel):
    id: int
    domain: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    class Config:
        from_attributes = True

class QuestionWithAnswer(QuestionResponse):
    correct_answer: str
    explanation: str

class SubmitAnswerRequest(BaseModel):
    session_id: int
    question_id: int
    user_answer: str

class QuizSessionResponse(BaseModel):
    id: int
    started_at: datetime
    completed_at: Optional[datetime]
    total_questions: int
    correct_answers: int
    score_percentage: float

    class Config:
        from_attributes = True

@router.get("/questions", response_model=List[QuestionResponse])
async def get_questions(
    domain: Optional[str] = None,
    student_level: Optional[str] = None,
    subject_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get quiz questions, optionally filtered by domain, student level, subject, or difficulty"""
    query = db.query(Question)

    if domain:
        query = query.filter(Question.domain == domain)

    if student_level:
        query = query.filter(Question.student_level == student_level)

    if subject_id:
        query = query.filter(Question.subject_id == subject_id)

    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    questions = query.limit(limit).all()
    return questions

@router.get("/questions/{question_id}", response_model=QuestionWithAnswer)
async def get_question(question_id: int, db: Session = Depends(get_db)):
    """Get a specific question with answer"""
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return question

@router.post("/sessions", response_model=QuizSessionResponse)
async def create_quiz_session(db: Session = Depends(get_db)):
    """Start a new quiz session"""
    session = QuizSession(
        user_id=None,  # TODO: Get from authenticated user
        total_questions=0,
        correct_answers=0,
        score_percentage=0.0
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session

@router.post("/submit-answer")
async def submit_answer(
    answer: SubmitAnswerRequest,
    db: Session = Depends(get_db)
):
    """Submit an answer for a question"""
    # Get the question
    question = db.query(Question).filter(Question.id == answer.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if answer is correct
    is_correct = question.correct_answer == answer.user_answer

    # Save the answer
    user_answer = UserAnswer(
        session_id=answer.session_id,
        question_id=answer.question_id,
        user_answer=answer.user_answer,
        is_correct=is_correct
    )
    db.add(user_answer)

    # Update session statistics
    session = db.query(QuizSession).filter(QuizSession.id == answer.session_id).first()
    if session:
        session.total_questions += 1
        if is_correct:
            session.correct_answers += 1
        session.score_percentage = (session.correct_answers / session.total_questions) * 100

    db.commit()

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation
    }

@router.get("/sessions/{session_id}", response_model=QuizSessionResponse)
async def get_quiz_session(session_id: int, db: Session = Depends(get_db)):
    """Get quiz session details"""
    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session

@router.get("/domains")
async def get_domains(db: Session = Depends(get_db)):
    """Get all available domains"""
    domains = db.query(Question.domain).distinct().all()
    return [domain[0] for domain in domains]
