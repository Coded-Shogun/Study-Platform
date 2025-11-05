# API Documentation

Complete API reference for the CompTIA Cloud+ Study Platform backend.

**Base URL:** `http://localhost:8000`

**API Documentation UI:** `http://localhost:8000/docs` (Swagger)

## Table of Contents
- [Authentication](#authentication)
- [Quiz Endpoints](#quiz-endpoints)
- [Progress Endpoints](#progress-endpoints)
- [Labs Endpoints](#labs-endpoints)
- [Error Responses](#error-responses)

---

## Authentication

### Register User
Create a new user account.

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "full_name": "string" (optional)
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### Login
Authenticate a user.

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:** `200 OK`
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

---

## Quiz Endpoints

### Get Questions
Retrieve quiz questions with optional filtering.

**Endpoint:** `GET /api/quiz/questions`

**Query Parameters:**
- `domain` (optional): Filter by domain name
- `limit` (optional): Number of questions to return (default: 10)

**Example:**
```
GET /api/quiz/questions?domain=Security&limit=5
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "domain": "Security",
    "question_text": "What is the principle of least privilege?",
    "option_a": "Give users maximum access",
    "option_b": "Grant minimum access needed",
    "option_c": "Remove all restrictions",
    "option_d": "Provide admin access"
  }
]
```

---

### Get Single Question
Retrieve a specific question with correct answer.

**Endpoint:** `GET /api/quiz/questions/{question_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "domain": "Security",
  "question_text": "What is the principle of least privilege?",
  "option_a": "Give users maximum access",
  "option_b": "Grant minimum access needed",
  "option_c": "Remove all restrictions",
  "option_d": "Provide admin access",
  "correct_answer": "Grant minimum access needed",
  "explanation": "The principle of least privilege states..."
}
```

---

### Create Quiz Session
Start a new quiz session.

**Endpoint:** `POST /api/quiz/sessions`

**Response:** `200 OK`
```json
{
  "id": 1,
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": null,
  "total_questions": 0,
  "correct_answers": 0,
  "score_percentage": 0.0
}
```

---

### Submit Answer
Submit an answer for a question.

**Endpoint:** `POST /api/quiz/submit-answer`

**Request Body:**
```json
{
  "session_id": 1,
  "question_id": 1,
  "user_answer": "Grant minimum access needed"
}
```

**Response:** `200 OK`
```json
{
  "is_correct": true,
  "correct_answer": "Grant minimum access needed",
  "explanation": "The principle of least privilege states..."
}
```

---

### Get Quiz Session
Retrieve quiz session details.

**Endpoint:** `GET /api/quiz/sessions/{session_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:30:00Z",
  "total_questions": 10,
  "correct_answers": 8,
  "score_percentage": 80.0
}
```

---

### Get Domains
Get all available quiz domains.

**Endpoint:** `GET /api/quiz/domains`

**Response:** `200 OK`
```json
[
  "Cloud Architecture & Design",
  "Security",
  "Deployment",
  "Operations & Support",
  "Troubleshooting"
]
```

---

## Progress Endpoints

### Get Progress Summary
Retrieve overall progress summary.

**Endpoint:** `GET /api/progress/summary`

**Response:** `200 OK`
```json
{
  "total_questions": 57,
  "total_correct": 45,
  "overall_average": 78.95,
  "study_streak": 3,
  "total_study_time": 285
}
```

---

### Get Domain Progress
Get progress breakdown by domain.

**Endpoint:** `GET /api/progress/domains`

**Response:** `200 OK`
```json
[
  {
    "domain": "Security",
    "questions_attempted": 12,
    "questions_correct": 10,
    "average_score": 83.33,
    "last_activity": "2024-01-01T12:00:00Z"
  }
]
```

---

### Get Study Sessions
Retrieve recent study sessions.

**Endpoint:** `GET /api/progress/sessions`

**Query Parameters:**
- `limit` (optional): Number of sessions to return (default: 10)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "session_date": "2024-01-01T12:00:00Z",
    "duration_minutes": 45,
    "questions_answered": 10
  }
]
```

---

### Create Study Session
Record a new study session.

**Endpoint:** `POST /api/progress/sessions`

**Request Body:**
```json
{
  "duration_minutes": 45,
  "questions_answered": 10,
  "topics_covered": "Security, Deployment"
}
```

**Response:** `200 OK`
```json
{
  "message": "Study session recorded",
  "session_id": 1
}
```

---

### Get Weekly Analytics
Retrieve weekly activity data.

**Endpoint:** `GET /api/progress/analytics/weekly`

**Response:** `200 OK`
```json
{
  "Mon": {
    "questions": 5,
    "time": 30
  },
  "Tue": {
    "questions": 8,
    "time": 45
  }
}
```

---

### Get Achievements
Get user achievements.

**Endpoint:** `GET /api/progress/achievements`

**Response:** `200 OK`
```json
[
  {
    "title": "First Steps",
    "description": "Complete your first quiz",
    "earned": true,
    "icon": "🎯"
  },
  {
    "title": "Week Warrior",
    "description": "Study 7 days in a row",
    "earned": false,
    "icon": "🔥"
  }
]
```

---

## Labs Endpoints

### Get All Labs
Retrieve all available labs.

**Endpoint:** `GET /api/labs/`

**Response:** `200 OK`
```json
[
  {
    "id": "1",
    "title": "Cloud Architecture Basics",
    "description": "Learn fundamental cloud architecture concepts...",
    "difficulty": "beginner",
    "duration": "30 min",
    "status": "not-started",
    "topics": ["Docker", "Containers", "Networking"]
  }
]
```

---

### Get Lab Details
Get specific lab information.

**Endpoint:** `GET /api/labs/{lab_id}`

**Response:** `200 OK`
```json
{
  "id": "1",
  "title": "Cloud Architecture Basics",
  "description": "Learn fundamental cloud architecture concepts...",
  "difficulty": "beginner",
  "duration": "30 min",
  "status": "not-started",
  "topics": ["Docker", "Containers", "Networking"]
}
```

---

### Start Lab
Start a lab environment.

**Endpoint:** `POST /api/labs/{lab_id}/start`

**Response:** `200 OK`
```json
{
  "message": "Lab 1 started",
  "status": "in-progress",
  "container_id": "lab-1-container",
  "access_url": "http://localhost:8080/lab-1"
}
```

---

### Stop Lab
Stop a running lab.

**Endpoint:** `POST /api/labs/{lab_id}/stop`

**Response:** `200 OK`
```json
{
  "message": "Lab 1 stopped",
  "status": "stopped"
}
```

---

### Get Lab Status
Check lab environment status.

**Endpoint:** `GET /api/labs/{lab_id}/status`

**Response:** `200 OK`
```json
{
  "lab_id": "1",
  "status": "in-progress",
  "progress_percentage": 45.0,
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": null
}
```

---

### Complete Lab
Mark a lab as completed.

**Endpoint:** `POST /api/labs/{lab_id}/complete`

**Response:** `200 OK`
```json
{
  "message": "Lab 1 marked as completed",
  "status": "completed",
  "completed_at": "2024-01-01T12:45:00Z"
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
Invalid request data.

```json
{
  "detail": "Username or email already registered"
}
```

### 401 Unauthorized
Authentication failed.

```json
{
  "detail": "Incorrect username or password"
}
```

### 404 Not Found
Resource not found.

```json
{
  "detail": "Question not found"
}
```

### 422 Validation Error
Request validation failed.

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### 500 Internal Server Error
Server error.

```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently, there are no rate limits implemented. In production, consider implementing rate limiting for:
- Authentication endpoints: 5 requests per minute
- Quiz submissions: 30 requests per minute
- General API: 100 requests per minute

---

## Authentication Flow

1. **Register:** `POST /api/auth/register`
2. **Login:** `POST /api/auth/login` → Receive token
3. **Use Token:** Include in `Authorization: Bearer <token>` header
4. **Access Protected Routes:** All subsequent requests

Note: Full JWT authentication is not yet implemented in this version.

---

## Best Practices

1. **Always handle errors** - Check response status codes
2. **Use sessions** - Create a quiz session before submitting answers
3. **Track progress** - Record study sessions after each study period
4. **Batch requests** - Use filters to reduce API calls
5. **Check status** - Verify lab status before starting/stopping

---

For interactive API testing, visit: **http://localhost:8000/docs**
