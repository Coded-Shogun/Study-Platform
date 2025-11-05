# Multi-Level Student Support & Admin Features

This document describes the new multi-level student support and admin course management features added to the Study Platform.

## Overview

The platform now supports three student levels with tailored content:
- **Primary School** - Basic educational content for young learners
- **High School** - Intermediate content for secondary education
- **Tertiary/University** - Advanced content for higher education

Additionally, administrators and teachers can now manage courses, subjects, and question banks through a comprehensive admin interface.

## New Features

### 1. User Roles & Student Levels

Three user roles are now supported:
- **Student** - Can access quizzes and content appropriate for their level
- **Teacher** - Can manage courses and create content
- **Admin** - Full platform access including user and system management

Students must specify their education level during registration:
- Primary
- High School
- Tertiary

### 2. Admin Dashboard

Access via the "Admin" tab in the navigation menu (visible to admins and teachers).

#### Features:
- **Statistics** - View platform-wide metrics
  - Total subjects, categories, questions, and users
  - Breakdown by student level
  - User distribution by role

- **Subject Management**
  - Create, edit, and delete subjects/courses
  - Assign subject codes (e.g., "CLOUD101", "MATH-P1")
  - Add descriptions

- **Category Management**
  - Organize subjects into categories
  - Link categories to specific subjects
  - Manage category descriptions

- **Question Bank Management**
  - Create, edit, and delete questions
  - Assign questions to subjects and categories
  - Set difficulty levels (easy, medium, hard)
  - Specify student level for each question
  - Preview questions before editing
  - Filter questions by subject, level, and difficulty

### 3. Enhanced Registration

The registration flow now includes:
- Account type selection (Student/Teacher/Admin)
- Student level selection (for student accounts)
- Contextual information based on role selection

### 4. Level-Based Content Filtering

Quizzes and content are automatically filtered based on:
- User's student level (for students)
- Subject assignments
- Difficulty preferences

## Database Schema Changes

### User Table Updates
```sql
- role: ENUM ('admin', 'teacher', 'student')
- student_level: ENUM ('primary', 'high_school', 'tertiary') [nullable]
```

### New Tables

**subjects**
- id, name, code, description, created_at, updated_at

**categories**
- id, subject_id (FK), name, description, created_at

**questions** (updated)
- subject_id (FK) - Links to subject
- category_id (FK) - Optional category link
- student_level - Target education level
- [existing fields remain unchanged]

## API Endpoints

### Admin Endpoints (Require admin/teacher role)

#### Subjects
```
GET    /api/admin/subjects
POST   /api/admin/subjects
GET    /api/admin/subjects/{id}
PUT    /api/admin/subjects/{id}
DELETE /api/admin/subjects/{id}
```

#### Categories
```
GET    /api/admin/categories?subject_id={id}
POST   /api/admin/categories
GET    /api/admin/categories/{id}
PUT    /api/admin/categories/{id}
DELETE /api/admin/categories/{id}
```

#### Questions
```
GET    /api/admin/questions?subject_id={id}&student_level={level}&difficulty={diff}
POST   /api/admin/questions
POST   /api/admin/questions/bulk
GET    /api/admin/questions/{id}
PUT    /api/admin/questions/{id}
DELETE /api/admin/questions/{id}
```

#### Statistics
```
GET    /api/admin/statistics
```

### Updated Quiz Endpoints
```
GET /api/quiz/questions?student_level={level}&subject_id={id}&difficulty={diff}
```

### Updated Auth Endpoints

Registration now accepts:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string",
  "role": "student|teacher|admin",
  "student_level": "primary|high_school|tertiary"
}
```

## Getting Started

### 1. Initialize Database with Sample Data

```bash
cd backend
python scripts/init_db.py
```

This creates:
- 3 sample subjects (Cloud+, Basic Math, High School CS)
- 10 categories across subjects
- 7 sample questions for different levels
- 5 sample users (1 admin, 1 teacher, 3 students at different levels)

### 2. Sample User Accounts

| Username | Password | Role | Level |
|----------|----------|------|-------|
| admin | admin123 | Admin | N/A |
| teacher | teacher123 | Teacher | N/A |
| primary_student | student123 | Student | Primary |
| highschool_student | student123 | Student | High School |
| university_student | student123 | Student | Tertiary |

### 3. Start the Application

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Usage Guide

### For Administrators/Teachers

1. **Log in** with admin or teacher credentials
2. **Navigate** to the Admin tab
3. **Create subjects** first (e.g., "Mathematics", "Science")
4. **Add categories** within subjects (e.g., "Algebra", "Geometry")
5. **Create questions** and assign them to subjects/categories with appropriate levels
6. **Review statistics** to monitor platform usage

### For Students

1. **Register** selecting your student level
2. **Log in** to access your personalized dashboard
3. **Take quizzes** filtered to your education level
4. **Track progress** across subjects appropriate for your level

## Architecture Decisions

### Why Three Levels?

The three-tier system (Primary, High School, Tertiary) covers the major education stages:
- **Primary** - Ages 5-11, foundational learning
- **High School** - Ages 12-18, intermediate concepts
- **Tertiary** - University/college, advanced topics

### Subject-Based Organization

Questions are organized by:
1. **Subject** - The main course/topic
2. **Category** - Subcategories within subjects
3. **Level** - Target student level
4. **Difficulty** - Easy, Medium, Hard

This allows fine-grained filtering and personalization.

### Role-Based Access Control (RBAC)

- **Students** - Read-only access to appropriate content
- **Teachers** - Can create and manage educational content
- **Admins** - Full system access including user management

## Future Enhancements

Potential additions:
- [ ] Question import/export (CSV, JSON)
- [ ] Bulk question operations
- [ ] Question versioning and history
- [ ] Content scheduling and publishing
- [ ] Student progress analytics per subject
- [ ] Automated level recommendations
- [ ] Question difficulty auto-adjustment based on performance
- [ ] Multi-language support
- [ ] Question tagging system
- [ ] Collaborative question authoring

## Security Notes

⚠️ **Important**: The current implementation has placeholder security:

1. **Passwords are NOT hashed** - Implement proper bcrypt hashing before production
2. **No JWT authentication** - Token-based auth should be implemented
3. **No rate limiting** - Add rate limiting to prevent abuse
4. **CORS is permissive** - Restrict to specific origins in production

These are marked with TODO comments in the codebase.

## Technical Details

### Models Location
- `/backend/app/models/user.py` - User, UserRole, StudentLevel
- `/backend/app/models/subject.py` - Subject, Category
- `/backend/app/models/quiz.py` - Question (updated)

### API Routes Location
- `/backend/app/api/admin.py` - All admin endpoints
- `/backend/app/api/auth.py` - Updated registration
- `/backend/app/api/quiz.py` - Updated quiz endpoints

### Frontend Components
- `/frontend/src/pages/AdminPage.tsx` - Main admin interface
- `/frontend/src/components/admin/` - Admin components
- `/frontend/src/pages/RegisterPage.tsx` - Registration with level selection

## Support

For issues or questions:
1. Check the API documentation at `/docs` (FastAPI auto-generated)
2. Review the console logs for debugging
3. Verify database initialization completed successfully

## Contributing

When adding new features:
1. Update database models in `/backend/app/models/`
2. Create API endpoints in `/backend/app/api/`
3. Add frontend components in `/frontend/src/`
4. Update this documentation
5. Test with different user roles and levels
