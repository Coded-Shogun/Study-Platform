"""
Pytest fixtures and configuration for tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.utils.database import Base, get_db
from app.utils.security import get_password_hash, create_access_token
from app.models import User, Subject, Category, Question, UserRole, StudentLevel

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session):
    """Create a sample student user"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("Test123!"),
        full_name="Test User",
        role=UserRole.STUDENT,
        student_level=StudentLevel.TERTIARY,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create a sample admin user"""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("Admin123!"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        student_level=None,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def teacher_user(db_session):
    """Create a sample teacher user"""
    user = User(
        username="teacher",
        email="teacher@example.com",
        hashed_password=get_password_hash("Teacher123!"),
        full_name="Teacher User",
        role=UserRole.TEACHER,
        student_level=None,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session):
    """Create an inactive user"""
    user = User(
        username="inactive",
        email="inactive@example.com",
        hashed_password=get_password_hash("Inactive123!"),
        full_name="Inactive User",
        role=UserRole.STUDENT,
        student_level=StudentLevel.PRIMARY,
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_subject(db_session):
    """Create a sample subject"""
    subject = Subject(
        name="Test Subject",
        code="TEST101",
        description="A test subject"
    )
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject


@pytest.fixture
def sample_category(db_session, sample_subject):
    """Create a sample category"""
    category = Category(
        subject_id=sample_subject.id,
        name="Test Category",
        description="A test category"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def sample_question(db_session, sample_subject, sample_category):
    """Create a sample question"""
    question = Question(
        subject_id=sample_subject.id,
        category_id=sample_category.id,
        domain="Testing",
        question_text="What is 2 + 2?",
        option_a="3",
        option_b="4",
        option_c="5",
        option_d="6",
        correct_answer="B",
        explanation="2 + 2 equals 4",
        difficulty="easy",
        student_level="primary"
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


@pytest.fixture
def auth_token(sample_user):
    """Generate authentication token for sample user"""
    return create_access_token(data={"sub": sample_user.id, "role": sample_user.role})


@pytest.fixture
def admin_token(admin_user):
    """Generate authentication token for admin user"""
    return create_access_token(data={"sub": admin_user.id, "role": admin_user.role})


@pytest.fixture
def teacher_token(teacher_user):
    """Generate authentication token for teacher user"""
    return create_access_token(data={"sub": teacher_user.id, "role": teacher_user.role})


@pytest.fixture
def auth_headers(auth_token):
    """Generate authorization headers with bearer token"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Generate authorization headers with admin bearer token"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def teacher_headers(teacher_token):
    """Generate authorization headers with teacher bearer token"""
    return {"Authorization": f"Bearer {teacher_token}"}
