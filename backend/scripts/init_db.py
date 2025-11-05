"""
Database initialization script for the Study Platform
Creates sample subjects, categories, and questions for all student levels
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.utils.database import SessionLocal, engine, Base
from app.models import User, Subject, Category, Question, UserRole, StudentLevel

def init_database():
    """Initialize database with sample data"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_subjects = db.query(Subject).count()
        if existing_subjects > 0:
            print(f"Database already initialized with {existing_subjects} subjects")
            return

        print("\nCreating sample subjects...")

        # Create Subjects
        subjects = [
            Subject(
                name="CompTIA Cloud+",
                code="CLOUD101",
                description="Cloud architecture, security, deployment, and troubleshooting"
            ),
            Subject(
                name="Basic Mathematics",
                code="MATH-P1",
                description="Primary level mathematics - numbers, addition, subtraction"
            ),
            Subject(
                name="High School Computer Science",
                code="CS-HS1",
                description="Introduction to programming and computer concepts"
            ),
        ]

        for subject in subjects:
            db.add(subject)
        db.commit()
        print(f"✓ Created {len(subjects)} subjects")

        # Refresh subjects to get IDs
        for subject in subjects:
            db.refresh(subject)

        print("\nCreating categories...")

        # Create Categories
        categories = [
            # CompTIA Cloud+ Categories
            Category(subject_id=subjects[0].id, name="Cloud Architecture & Design", description="Cloud concepts and architecture"),
            Category(subject_id=subjects[0].id, name="Security", description="Cloud security best practices"),
            Category(subject_id=subjects[0].id, name="Deployment", description="Cloud deployment strategies"),
            Category(subject_id=subjects[0].id, name="Operations & Support", description="Cloud operations and maintenance"),
            Category(subject_id=subjects[0].id, name="Troubleshooting", description="Cloud troubleshooting techniques"),

            # Math Categories
            Category(subject_id=subjects[1].id, name="Numbers", description="Understanding numbers"),
            Category(subject_id=subjects[1].id, name="Addition", description="Basic addition"),
            Category(subject_id=subjects[1].id, name="Subtraction", description="Basic subtraction"),

            # Computer Science Categories
            Category(subject_id=subjects[2].id, name="Programming Basics", description="Introduction to programming"),
            Category(subject_id=subjects[2].id, name="Data Structures", description="Basic data structures"),
        ]

        for category in categories:
            db.add(category)
        db.commit()
        print(f"✓ Created {len(categories)} categories")

        # Refresh categories to get IDs
        for category in categories:
            db.refresh(category)

        print("\nCreating sample questions...")

        # Create Sample Questions
        questions = [
            # PRIMARY LEVEL - Mathematics
            Question(
                subject_id=subjects[1].id,
                category_id=categories[5].id,  # Numbers
                domain="Numbers",
                question_text="What number comes after 5?",
                option_a="4",
                option_b="6",
                option_c="7",
                option_d="3",
                correct_answer="B",
                explanation="The number after 5 is 6. When counting, we go 1, 2, 3, 4, 5, 6...",
                difficulty="easy",
                student_level="primary"
            ),
            Question(
                subject_id=subjects[1].id,
                category_id=categories[6].id,  # Addition
                domain="Addition",
                question_text="What is 2 + 3?",
                option_a="4",
                option_b="5",
                option_c="6",
                option_d="7",
                correct_answer="B",
                explanation="When we add 2 and 3 together, we get 5. You can count: 1, 2 (that's 2) then 3, 4, 5 (that's 3 more).",
                difficulty="easy",
                student_level="primary"
            ),

            # HIGH SCHOOL LEVEL - Computer Science
            Question(
                subject_id=subjects[2].id,
                category_id=categories[8].id,  # Programming Basics
                domain="Programming Basics",
                question_text="What is a variable in programming?",
                option_a="A constant value that never changes",
                option_b="A container that stores data values",
                option_c="A type of loop",
                option_d="A programming language",
                correct_answer="B",
                explanation="A variable is a container that stores data values. It has a name and can hold different types of data like numbers, text, or boolean values.",
                difficulty="easy",
                student_level="high_school"
            ),
            Question(
                subject_id=subjects[2].id,
                category_id=categories[9].id,  # Data Structures
                domain="Data Structures",
                question_text="Which data structure uses First-In-First-Out (FIFO) principle?",
                option_a="Stack",
                option_b="Queue",
                option_c="Tree",
                option_d="Graph",
                correct_answer="B",
                explanation="A Queue follows the First-In-First-Out (FIFO) principle, meaning the first element added is the first one to be removed, like a line of people waiting.",
                difficulty="medium",
                student_level="high_school"
            ),

            # TERTIARY LEVEL - CompTIA Cloud+
            Question(
                subject_id=subjects[0].id,
                category_id=categories[0].id,  # Cloud Architecture
                domain="Cloud Architecture & Design",
                question_text="Which cloud service model provides the most control over the underlying infrastructure?",
                option_a="Software as a Service (SaaS)",
                option_b="Platform as a Service (PaaS)",
                option_c="Infrastructure as a Service (IaaS)",
                option_d="Function as a Service (FaaS)",
                correct_answer="C",
                explanation="IaaS provides the most control as it offers virtualized computing resources over the internet, allowing users to manage operating systems, storage, and deployed applications.",
                difficulty="medium",
                student_level="tertiary"
            ),
            Question(
                subject_id=subjects[0].id,
                category_id=categories[1].id,  # Security
                domain="Security",
                question_text="What is the primary purpose of encryption in cloud computing?",
                option_a="To improve application performance",
                option_b="To reduce storage costs",
                option_c="To protect data confidentiality",
                option_d="To increase network speed",
                correct_answer="C",
                explanation="The primary purpose of encryption is to protect data confidentiality by converting it into a code to prevent unauthorized access, especially important for data in transit and at rest in the cloud.",
                difficulty="medium",
                student_level="tertiary"
            ),
            Question(
                subject_id=subjects[0].id,
                category_id=categories[2].id,  # Deployment
                domain="Deployment",
                question_text="What is a containerization technology commonly used in cloud deployments?",
                option_a="VMware",
                option_b="Docker",
                option_c="VirtualBox",
                option_d="Hyper-V",
                correct_answer="B",
                explanation="Docker is a popular containerization platform that packages applications and their dependencies into containers, making them portable and consistent across different environments.",
                difficulty="medium",
                student_level="tertiary"
            ),
        ]

        for question in questions:
            db.add(question)
        db.commit()
        print(f"✓ Created {len(questions)} sample questions")

        # Create sample users
        print("\nCreating sample users...")
        users = [
            User(
                username="admin",
                email="admin@studyplatform.com",
                hashed_password="admin123",  # TODO: Hash in production
                full_name="System Administrator",
                role=UserRole.ADMIN,
                student_level=None
            ),
            User(
                username="teacher",
                email="teacher@studyplatform.com",
                hashed_password="teacher123",  # TODO: Hash in production
                full_name="Jane Teacher",
                role=UserRole.TEACHER,
                student_level=None
            ),
            User(
                username="primary_student",
                email="primary@student.com",
                hashed_password="student123",  # TODO: Hash in production
                full_name="Tommy Primary",
                role=UserRole.STUDENT,
                student_level=StudentLevel.PRIMARY
            ),
            User(
                username="highschool_student",
                email="highschool@student.com",
                hashed_password="student123",  # TODO: Hash in production
                full_name="Sarah Highschool",
                role=UserRole.STUDENT,
                student_level=StudentLevel.HIGH_SCHOOL
            ),
            User(
                username="university_student",
                email="university@student.com",
                hashed_password="student123",  # TODO: Hash in production
                full_name="Mike University",
                role=UserRole.STUDENT,
                student_level=StudentLevel.TERTIARY
            ),
        ]

        for user in users:
            db.add(user)
        db.commit()
        print(f"✓ Created {len(users)} sample users")

        print("\n" + "="*50)
        print("Database initialization complete!")
        print("="*50)
        print("\nSample User Credentials:")
        print("-" * 50)
        print("Admin:              admin / admin123")
        print("Teacher:            teacher / teacher123")
        print("Primary Student:    primary_student / student123")
        print("High School:        highschool_student / student123")
        print("University:         university_student / student123")
        print("-" * 50)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Study Platform - Database Initialization")
    print("="*50)
    init_database()
