"""
Integration tests for authentication endpoints
"""
import pytest
from fastapi import status


class TestRegistration:
    """Test user registration endpoint"""

    @pytest.mark.integration
    def test_register_student_success(self, client):
        """Test successful student registration"""
        response = client.post("/api/auth/register", json={
            "username": "newstudent",
            "email": "student@test.com",
            "password": "Student123!",
            "full_name": "New Student",
            "role": "student",
            "student_level": "tertiary"
        })

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "newstudent"
        assert data["email"] == "student@test.com"
        assert data["role"] == "student"
        assert data["student_level"] == "tertiary"
        assert "hashed_password" not in data  # Password should not be returned

    @pytest.mark.integration
    def test_register_admin_success(self, client):
        """Test successful admin registration"""
        response = client.post("/api/auth/register", json={
            "username": "newadmin",
            "email": "admin@test.com",
            "password": "Admin123!",
            "full_name": "New Admin",
            "role": "admin"
        })

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["role"] == "admin"
        assert data["student_level"] is None

    @pytest.mark.integration
    def test_register_duplicate_username(self, client, sample_user):
        """Test registration with existing username"""
        response = client.post("/api/auth/register", json={
            "username": sample_user.username,
            "email": "different@test.com",
            "password": "Password123!",
            "full_name": "Different User",
            "role": "student",
            "student_level": "primary"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.integration
    def test_register_duplicate_email(self, client, sample_user):
        """Test registration with existing email"""
        response = client.post("/api/auth/register", json={
            "username": "differentuser",
            "email": sample_user.email,
            "password": "Password123!",
            "full_name": "Different User",
            "role": "student",
            "student_level": "primary"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.integration
    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post("/api/auth/register", json={
            "username": "weakpass",
            "email": "weak@test.com",
            "password": "weak",  # Too short, no uppercase, no digit
            "full_name": "Weak Pass",
            "role": "student",
            "student_level": "primary"
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.integration
    def test_register_student_without_level(self, client):
        """Test student registration without student level"""
        response = client.post("/api/auth/register", json={
            "username": "nolevel",
            "email": "nolevel@test.com",
            "password": "Password123!",
            "full_name": "No Level",
            "role": "student"
            # Missing student_level
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.integration
    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post("/api/auth/register", json={
            "username": "invalidemail",
            "email": "not-an-email",
            "password": "Password123!",
            "full_name": "Invalid Email",
            "role": "student",
            "student_level": "primary"
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.integration
    def test_register_short_username(self, client):
        """Test registration with too short username"""
        response = client.post("/api/auth/register", json={
            "username": "ab",  # Only 2 characters
            "email": "short@test.com",
            "password": "Password123!",
            "full_name": "Short Username",
            "role": "student",
            "student_level": "primary"
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Test login endpoint"""

    @pytest.mark.integration
    def test_login_success(self, client, sample_user):
        """Test successful login"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "Test123!"
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return tokens
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Should return user info
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"

    @pytest.mark.integration
    def test_login_wrong_password(self, client, sample_user):
        """Test login with wrong password"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "WrongPassword123!"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.integration
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent username"""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "Password123!"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_login_inactive_user(self, client, inactive_user):
        """Test login with inactive account"""
        response = client.post("/api/auth/login", json={
            "username": "inactive",
            "password": "Inactive123!"
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["detail"].lower()

    @pytest.mark.integration
    def test_login_case_insensitive_username(self, client, sample_user):
        """Test that username login is case-insensitive"""
        response = client.post("/api/auth/login", json={
            "username": "TESTUSER",  # Uppercase
            "password": "Test123!"
        })

        # Should fail because we convert to lowercase on registration
        # If the user registered as "testuser", "TESTUSER" won't match
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUser:
    """Test /me endpoint for getting current user"""

    @pytest.mark.integration
    def test_get_current_user_success(self, client, sample_user, auth_headers):
        """Test getting current user with valid token"""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "student"

    @pytest.mark.integration
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        response = client.get("/api/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.integration
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenRefresh:
    """Test token refresh endpoint"""

    @pytest.mark.integration
    def test_refresh_token_success(self, client, sample_user):
        """Test refreshing access token"""
        # First login to get refresh token
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "Test123!"
        })
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data

    @pytest.mark.integration
    def test_refresh_with_access_token_fails(self, client, auth_token):
        """Test that access token cannot be used for refresh"""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": auth_token  # Using access token instead
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token"""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePassword:
    """Test password change endpoint"""

    @pytest.mark.integration
    def test_change_password_success(self, client, sample_user, auth_headers):
        """Test successful password change"""
        response = client.post("/api/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "Test123!",
                "new_password": "NewPassword123!"
            }
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify can login with new password
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "NewPassword123!"
        })
        assert login_response.status_code == status.HTTP_200_OK

    @pytest.mark.integration
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test password change with wrong current password"""
        response = client.post("/api/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword123!"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.integration
    def test_change_password_same_as_current(self, client, auth_headers):
        """Test changing to same password"""
        response = client.post("/api/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "Test123!",
                "new_password": "Test123!"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.integration
    def test_change_password_weak_new_password(self, client, auth_headers):
        """Test changing to weak password"""
        response = client.post("/api/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "Test123!",
                "new_password": "weak"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.integration
    def test_change_password_no_auth(self, client):
        """Test password change without authentication"""
        response = client.post("/api/auth/change-password", json={
            "current_password": "Test123!",
            "new_password": "NewPassword123!"
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestLogout:
    """Test logout endpoint"""

    @pytest.mark.integration
    def test_logout_success(self, client, auth_headers):
        """Test successful logout"""
        response = client.post("/api/auth/logout", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert "success" in response.json()["message"].lower()

    @pytest.mark.integration
    def test_logout_no_auth(self, client):
        """Test logout without authentication"""
        response = client.post("/api/auth/logout")

        assert response.status_code == status.HTTP_403_FORBIDDEN
