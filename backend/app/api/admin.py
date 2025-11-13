from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..utils.database import get_db
from ..utils.auth import get_admin_or_teacher
from ..utils.audit import log_admin_action, get_model_changes
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

# ==================== Subject Endpoints ====================

@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject: SubjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
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

    # Log admin action
    log_admin_action(
        db=db,
        request=request,
        current_user=current_user,
        action=f"Created subject '{db_subject.name}'",
        resource_type="SUBJECT",
        resource_id=db_subject.id,
        resource_name=db_subject.name,
        new_values=subject.dict(),
        description=f"Admin created new subject: {db_subject.name} ({db_subject.code})"
    )

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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """Update a subject"""
    db_subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Capture old values before update
    old_values = {
        "name": db_subject.name,
        "code": db_subject.code,
        "description": db_subject.description
    }

    for key, value in subject.dict().items():
        setattr(db_subject, key, value)

    db.commit()
    db.refresh(db_subject)

    # Log admin action
    log_admin_action(
        db=db,
        request=request,
        current_user=current_user,
        action=f"Updated subject '{db_subject.name}'",
        resource_type="SUBJECT",
        resource_id=db_subject.id,
        resource_name=db_subject.name,
        old_values=old_values,
        new_values=subject.dict(),
        description=f"Admin updated subject: {db_subject.name}"
    )

    return db_subject

@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """Delete a subject"""
    db_subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Capture data before deletion
    subject_data = {
        "name": db_subject.name,
        "code": db_subject.code,
        "description": db_subject.description
    }

    db.delete(db_subject)
    db.commit()

    # Log admin action
    log_admin_action(
        db=db,
        request=request,
        current_user=current_user,
        action=f"Deleted subject '{subject_data['name']}'",
        resource_type="SUBJECT",
        resource_id=subject_id,
        resource_name=subject_data["name"],
        old_values=subject_data,
        description=f"Admin deleted subject: {subject_data['name']} ({subject_data['code']})"
    )

    return None

# ==================== Category Endpoints ====================

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
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

    # Log admin action
    log_admin_action(
        db=db,
        request=request,
        current_user=current_user,
        action=f"Created category '{db_category.name}' in subject '{subject.name}'",
        resource_type="CATEGORY",
        resource_id=db_category.id,
        resource_name=db_category.name,
        new_values=category.dict(),
        description=f"Admin created new category: {db_category.name}"
    )

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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """Update a category"""
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Capture old values
    old_values = {
        "subject_id": db_category.subject_id,
        "name": db_category.name,
        "description": db_category.description
    }

    for key, value in category.dict().items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)

    # Log admin action
    log_admin_action(
        db=db,
        request=request,
        current_user=current_user,
        action=f"Updated category '{db_category.name}'",
        resource_type="CATEGORY",
        resource_id=db_category.id,
        resource_name=db_category.name,
        old_values=old_values,
        new_values=category.dict(),
        description=f"Admin updated category: {db_category.name}"
    )

    return db_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """Delete a category"""
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Capture data before deletion
    category_data = {
        "subject_id": db_category.subject_id,
        "name": db_category.name,
        "description": db_category.description
    }

    db.delete(db_category)
    db.commit()

    # Log admin action
    log_admin_action(
        db=db,
        request=request,
        current_user=current_user,
        action=f"Deleted category '{category_data['name']}'",
        resource_type="CATEGORY",
        resource_id=category_id,
        resource_name=category_data["name"],
        old_values=category_data,
        description=f"Admin deleted category: {category_data['name']}"
    )

    return None

# ==================== Question Management Endpoints ====================

@router.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    question: QuestionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
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

    # Log admin action
    log_admin_action(
        db=db,
        request=request,
        current_user=current_user,
        action=f"Created question in domain '{db_question.domain}'",
        resource_type="QUESTION",
        resource_id=db_question.id,
        resource_name=f"Q{db_question.id}: {db_question.question_text[:50]}...",
        new_values={"domain": db_question.domain, "difficulty": db_question.difficulty, "student_level": db_question.student_level},
        description=f"Admin created new question for {subject.name}"
    )

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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """Update a question"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Capture old values
    old_values = {}
    update_dict = question.dict(exclude_unset=True)
    for key in update_dict.keys():
        old_values[key] = str(getattr(db_question, key, None))

    # Update only provided fields
    for key, value in update_dict.items():
        setattr(db_question, key, value)

    db.commit()
    db.refresh(db_question)

    # Log admin action
    log_admin_action(
        db=db,
        request=request,
        current_user=current_user,
        action=f"Updated question Q{db_question.id}",
        resource_type="QUESTION",
        resource_id=db_question.id,
        resource_name=f"Q{db_question.id}: {db_question.question_text[:50]}...",
        old_values=old_values,
        new_values=update_dict,
        description=f"Admin updated question in domain: {db_question.domain}"
    )

    return db_question

@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """Delete a question"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Capture data before deletion
    question_data = {
        "domain": db_question.domain,
        "difficulty": db_question.difficulty,
        "student_level": db_question.student_level,
        "question_text_preview": db_question.question_text[:50]
    }

    db.delete(db_question)
    db.commit()

    # Log admin action
    log_admin_action(
        db=db,
        request=request,
        current_user=current_user,
        action=f"Deleted question Q{question_id}",
        resource_type="QUESTION",
        resource_id=question_id,
        resource_name=f"Q{question_id}",
        old_values=question_data,
        description=f"Admin deleted question from domain: {question_data['domain']}"
    )

    return None

# ==================== Bulk Operations ====================

@router.post("/questions/bulk", status_code=status.HTTP_201_CREATED)
def bulk_create_questions(
    questions: List[QuestionCreate],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
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

    # Log bulk admin action
    log_admin_action(
        db=db,
        request=request,
        current_user=current_user,
        action=f"Bulk created {len(created_questions)} questions",
        resource_type="QUESTION",
        resource_name=f"Bulk creation of {len(created_questions)} questions",
        new_values={"count": len(created_questions)},
        description=f"Admin bulk created {len(created_questions)} questions"
    )

    return {"created": len(created_questions), "questions": created_questions}

# ==================== Statistics ====================

@router.get("/statistics")
def get_admin_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
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
