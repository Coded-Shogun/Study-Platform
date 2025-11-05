from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..utils.database import get_db
from ..models import Subject, Category, Question, User, UserRole, StudentLevel

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ==================== Pydantic Schemas ====================

class SubjectCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class SubjectResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryCreate(BaseModel):
    subject_id: int
    name: str
    description: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    subject_id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    subject_id: int
    category_id: Optional[int] = None
    domain: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: str
    difficulty: str = "medium"
    student_level: Optional[str] = None

class QuestionUpdate(BaseModel):
    subject_id: Optional[int] = None
    category_id: Optional[int] = None
    domain: Optional[str] = None
    question_text: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    student_level: Optional[str] = None

class QuestionResponse(BaseModel):
    id: int
    subject_id: int
    category_id: Optional[int]
    domain: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: str
    difficulty: str
    student_level: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ==================== Dependency: Admin Check ====================

def get_current_admin_user(user_id: int = 1, db: Session = Depends(get_db)) -> User:
    """
    TODO: Implement proper JWT authentication
    For now, accepts user_id as parameter
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin or Teacher role required."
        )

    return user

# ==================== Subject Endpoints ====================

@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new subject/course"""
    # Check if subject with same code already exists
    existing = db.query(Subject).filter(Subject.code == subject.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject with code '{subject.code}' already exists"
        )

    db_subject = Subject(**subject.dict())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

@router.get("/subjects", response_model=List[SubjectResponse])
def get_subjects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all subjects"""
    subjects = db.query(Subject).offset(skip).limit(limit).all()
    return subjects

@router.get("/subjects/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    """Get a specific subject"""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@router.put("/subjects/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    subject: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a subject"""
    db_subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    for key, value in subject.dict().items():
        setattr(db_subject, key, value)

    db.commit()
    db.refresh(db_subject)
    return db_subject

@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a subject"""
    db_subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    db.delete(db_subject)
    db.commit()
    return None

# ==================== Category Endpoints ====================

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new category within a subject"""
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == category.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    subject_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all categories, optionally filtered by subject"""
    query = db.query(Category)
    if subject_id:
        query = query.filter(Category.subject_id == subject_id)
    categories = query.offset(skip).limit(limit).all()
    return categories

@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get a specific category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a category"""
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    for key, value in category.dict().items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a category"""
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(db_category)
    db.commit()
    return None

# ==================== Question Management Endpoints ====================

@router.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new question"""
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == question.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Verify category exists if provided
    if question.category_id:
        category = db.query(Category).filter(Category.id == question.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    db_question = Question(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@router.get("/questions", response_model=List[QuestionResponse])
def get_all_questions(
    subject_id: Optional[int] = None,
    category_id: Optional[int] = None,
    student_level: Optional[str] = None,
    difficulty: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all questions with optional filters"""
    query = db.query(Question)

    if subject_id:
        query = query.filter(Question.subject_id == subject_id)
    if category_id:
        query = query.filter(Question.category_id == category_id)
    if student_level:
        query = query.filter(Question.student_level == student_level)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    questions = query.offset(skip).limit(limit).all()
    return questions

@router.get("/questions/{question_id}", response_model=QuestionResponse)
def get_question_by_id(question_id: int, db: Session = Depends(get_db)):
    """Get a specific question"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    question: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a question"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Update only provided fields
    for key, value in question.dict(exclude_unset=True).items():
        setattr(db_question, key, value)

    db.commit()
    db.refresh(db_question)
    return db_question

@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a question"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(db_question)
    db.commit()
    return None

# ==================== Bulk Operations ====================

@router.post("/questions/bulk", status_code=status.HTTP_201_CREATED)
def bulk_create_questions(
    questions: List[QuestionCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Bulk create questions"""
    created_questions = []
    for question_data in questions:
        db_question = Question(**question_data.dict())
        db.add(db_question)
        created_questions.append(db_question)

    db.commit()
    for q in created_questions:
        db.refresh(q)

    return {"created": len(created_questions), "questions": created_questions}

# ==================== Statistics ====================

@router.get("/statistics")
def get_admin_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get administrative statistics"""
    total_subjects = db.query(Subject).count()
    total_categories = db.query(Category).count()
    total_questions = db.query(Question).count()
    total_users = db.query(User).count()

    # Questions by level
    questions_by_level = {
        "primary": db.query(Question).filter(Question.student_level == "primary").count(),
        "high_school": db.query(Question).filter(Question.student_level == "high_school").count(),
        "tertiary": db.query(Question).filter(Question.student_level == "tertiary").count(),
    }

    # Users by role
    users_by_role = {
        "admin": db.query(User).filter(User.role == UserRole.ADMIN).count(),
        "teacher": db.query(User).filter(User.role == UserRole.TEACHER).count(),
        "student": db.query(User).filter(User.role == UserRole.STUDENT).count(),
    }

    return {
        "total_subjects": total_subjects,
        "total_categories": total_categories,
        "total_questions": total_questions,
        "total_users": total_users,
        "questions_by_level": questions_by_level,
        "users_by_role": users_by_role
    }
