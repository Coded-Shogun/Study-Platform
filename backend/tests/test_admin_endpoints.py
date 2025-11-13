"""
Integration tests for admin endpoints and RBAC
"""
import pytest
from fastapi import status


class TestSubjectEndpoints:
    """Test subject management endpoints"""

    @pytest.mark.integration
    def test_create_subject_as_admin(self, client, admin_headers):
        """Test creating subject as admin"""
        response = client.post("/api/admin/subjects",
            headers=admin_headers,
            json={
                "name": "New Subject",
                "code": "NEW101",
                "description": "A new subject"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Subject"
        assert data["code"] == "NEW101"

    @pytest.mark.integration
    def test_create_subject_as_teacher(self, client, teacher_headers):
        """Test creating subject as teacher"""
        response = client.post("/api/admin/subjects",
            headers=teacher_headers,
            json={
                "name": "Teacher Subject",
                "code": "TEACH101",
                "description": "Subject by teacher"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.integration
    def test_create_subject_as_student_fails(self, client, auth_headers):
        """Test that students cannot create subjects"""
        response = client.post("/api/admin/subjects",
            headers=auth_headers,
            json={
                "name": "Student Subject",
                "code": "STU101",
                "description": "Should fail"
            }
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.integration
    def test_create_subject_no_auth_fails(self, client):
        """Test that unauthenticated users cannot create subjects"""
        response = client.post("/api/admin/subjects", json={
            "name": "Unauth Subject",
            "code": "UNAUTH101",
            "description": "Should fail"
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.integration
    def test_get_subjects(self, client, sample_subject):
        """Test getting all subjects (public endpoint)"""
        response = client.get("/api/admin/subjects")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.integration
    def test_get_subject_by_id(self, client, sample_subject):
        """Test getting specific subject"""
        response = client.get(f"/api/admin/subjects/{sample_subject.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_subject.id
        assert data["name"] == sample_subject.name

    @pytest.mark.integration
    def test_update_subject_as_admin(self, client, sample_subject, admin_headers):
        """Test updating subject as admin"""
        response = client.put(f"/api/admin/subjects/{sample_subject.id}",
            headers=admin_headers,
            json={
                "name": "Updated Subject",
                "code": "UPD101",
                "description": "Updated description"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Subject"

    @pytest.mark.integration
    def test_delete_subject_as_admin(self, client, sample_subject, admin_headers):
        """Test deleting subject as admin"""
        response = client.delete(f"/api/admin/subjects/{sample_subject.id}",
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's deleted
        get_response = client.get(f"/api/admin/subjects/{sample_subject.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestCategoryEndpoints:
    """Test category management endpoints"""

    @pytest.mark.integration
    def test_create_category_as_admin(self, client, sample_subject, admin_headers):
        """Test creating category as admin"""
        response = client.post("/api/admin/categories",
            headers=admin_headers,
            json={
                "subject_id": sample_subject.id,
                "name": "New Category",
                "description": "A new category"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Category"
        assert data["subject_id"] == sample_subject.id

    @pytest.mark.integration
    def test_create_category_invalid_subject(self, client, admin_headers):
        """Test creating category with non-existent subject"""
        response = client.post("/api/admin/categories",
            headers=admin_headers,
            json={
                "subject_id": 99999,  # Non-existent
                "name": "Invalid Category",
                "description": "Should fail"
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.integration
    def test_get_categories_by_subject(self, client, sample_subject, sample_category):
        """Test getting categories filtered by subject"""
        response = client.get(f"/api/admin/categories?subject_id={sample_subject.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert all(cat["subject_id"] == sample_subject.id for cat in data)


class TestQuestionEndpoints:
    """Test question management endpoints"""

    @pytest.mark.integration
    def test_create_question_as_admin(self, client, sample_subject, sample_category, admin_headers):
        """Test creating question as admin"""
        response = client.post("/api/admin/questions",
            headers=admin_headers,
            json={
                "subject_id": sample_subject.id,
                "category_id": sample_category.id,
                "domain": "Test Domain",
                "question_text": "What is the answer?",
                "option_a": "Option A",
                "option_b": "Option B",
                "option_c": "Option C",
                "option_d": "Option D",
                "correct_answer": "A",
                "explanation": "A is correct",
                "difficulty": "easy",
                "student_level": "primary"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["question_text"] == "What is the answer?"
        assert data["difficulty"] == "easy"

    @pytest.mark.integration
    def test_create_question_as_student_fails(self, client, sample_subject, auth_headers):
        """Test that students cannot create questions"""
        response = client.post("/api/admin/questions",
            headers=auth_headers,
            json={
                "subject_id": sample_subject.id,
                "domain": "Test",
                "question_text": "Question?",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_answer": "A",
                "explanation": "Explanation",
                "difficulty": "easy"
            }
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.integration
    def test_get_questions_filtered(self, client, sample_question):
        """Test getting questions with filters"""
        response = client.get("/api/admin/questions?difficulty=easy&student_level=primary")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_update_question(self, client, sample_question, admin_headers):
        """Test updating a question"""
        response = client.put(f"/api/admin/questions/{sample_question.id}",
            headers=admin_headers,
            json={
                "question_text": "Updated question text?"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["question_text"] == "Updated question text?"

    @pytest.mark.integration
    def test_delete_question(self, client, sample_question, admin_headers):
        """Test deleting a question"""
        response = client.delete(f"/api/admin/questions/{sample_question.id}",
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.integration
    def test_bulk_create_questions(self, client, sample_subject, admin_headers):
        """Test bulk question creation"""
        questions = [
            {
                "subject_id": sample_subject.id,
                "domain": "Bulk Test",
                "question_text": f"Question {i}?",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_answer": "A",
                "explanation": "Explanation",
                "difficulty": "medium",
                "student_level": "tertiary"
            }
            for i in range(3)
        ]

        response = client.post("/api/admin/questions/bulk",
            headers=admin_headers,
            json=questions
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["created"] == 3


class TestAdminStatistics:
    """Test admin statistics endpoint"""

    @pytest.mark.integration
    def test_get_statistics_as_admin(self, client, admin_headers, sample_subject, sample_question):
        """Test getting admin statistics"""
        response = client.get("/api/admin/statistics", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have all required fields
        assert "total_subjects" in data
        assert "total_categories" in data
        assert "total_questions" in data
        assert "total_users" in data
        assert "questions_by_level" in data
        assert "users_by_role" in data

        # Values should be numbers
        assert isinstance(data["total_subjects"], int)
        assert isinstance(data["total_questions"], int)

    @pytest.mark.integration
    def test_get_statistics_as_student_fails(self, client, auth_headers):
        """Test that students cannot access statistics"""
        response = client.get("/api/admin/statistics", headers=auth_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRoleBasedAccessControl:
    """Test RBAC across different endpoints"""

    @pytest.mark.integration
    @pytest.mark.security
    def test_admin_can_access_all(self, client, admin_headers, sample_subject):
        """Test that admin can access all admin endpoints"""
        endpoints = [
            ("POST", "/api/admin/subjects", {"name": "Test", "code": "TST"}),
            ("GET", "/api/admin/subjects", None),
            ("GET", "/api/admin/statistics", None),
        ]

        for method, url, json_data in endpoints:
            if method == "POST":
                response = client.post(url, headers=admin_headers, json=json_data)
            else:
                response = client.get(url, headers=admin_headers)

            assert response.status_code in [200, 201], f"Failed on {method} {url}"

    @pytest.mark.integration
    @pytest.mark.security
    def test_teacher_can_manage_content(self, client, teacher_headers, sample_subject):
        """Test that teachers can manage educational content"""
        # Teachers should be able to create subjects
        response = client.post("/api/admin/subjects",
            headers=teacher_headers,
            json={"name": "Teacher Subject", "code": "TCH"}
        )
        assert response.status_code == status.HTTP_201_CREATED

        # Teachers should be able to create questions
        response = client.post("/api/admin/questions",
            headers=teacher_headers,
            json={
                "subject_id": sample_subject.id,
                "domain": "Test",
                "question_text": "Q?",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_answer": "A",
                "explanation": "Exp",
                "difficulty": "easy"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.integration
    @pytest.mark.security
    def test_student_cannot_access_admin_endpoints(self, client, auth_headers, sample_subject):
        """Test that students are blocked from admin endpoints"""
        admin_endpoints = [
            ("POST", "/api/admin/subjects", {"name": "Test", "code": "TST"}),
            ("PUT", f"/api/admin/subjects/{sample_subject.id}", {"name": "Updated", "code": "UPD"}),
            ("DELETE", f"/api/admin/subjects/{sample_subject.id}", None),
            ("POST", "/api/admin/categories", {"subject_id": 1, "name": "Cat"}),
            ("POST", "/api/admin/questions", {"subject_id": 1, "domain": "D", "question_text": "Q?",
                     "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
                     "correct_answer": "A", "explanation": "E", "difficulty": "easy"}),
            ("GET", "/api/admin/statistics", None),
        ]

        for method, url, json_data in admin_endpoints:
            if method == "POST":
                response = client.post(url, headers=auth_headers, json=json_data)
            elif method == "PUT":
                response = client.put(url, headers=auth_headers, json=json_data)
            elif method == "DELETE":
                response = client.delete(url, headers=auth_headers)
            else:
                response = client.get(url, headers=auth_headers)

            assert response.status_code == status.HTTP_403_FORBIDDEN, \
                f"Student should be forbidden from {method} {url}"

    @pytest.mark.integration
    @pytest.mark.security
    def test_unauthenticated_cannot_access_protected_endpoints(self, client, sample_subject):
        """Test that unauthenticated users cannot access protected endpoints"""
        protected_endpoints = [
            ("POST", "/api/admin/subjects", {"name": "Test", "code": "TST"}),
            ("GET", "/api/auth/me", None),
            ("POST", "/api/auth/logout", None),
            ("POST", "/api/auth/change-password", {"current_password": "x", "new_password": "y"}),
        ]

        for method, url, json_data in protected_endpoints:
            if method == "POST":
                response = client.post(url, json=json_data)
            else:
                response = client.get(url)

            assert response.status_code == status.HTTP_403_FORBIDDEN, \
                f"Unauthenticated should be forbidden from {method} {url}"
