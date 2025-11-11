# Test Suite Documentation

This directory contains comprehensive tests for the Study Platform backend.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_security.py         # Unit tests for security utilities
├── test_auth_endpoints.py   # Integration tests for authentication
├── test_admin_endpoints.py  # Integration tests for admin endpoints
└── README.md               # This file
```

## Running Tests

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests

```bash
cd backend
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

This generates:
- Terminal coverage report
- HTML coverage report in `htmlcov/`

### Run Specific Test Categories

**Unit Tests Only**:
```bash
pytest -m unit
```

**Integration Tests Only**:
```bash
pytest -m integration
```

**Security Tests Only**:
```bash
pytest -m security
```

**Specific Test File**:
```bash
pytest tests/test_security.py
```

**Specific Test Class**:
```bash
pytest tests/test_security.py::TestPasswordHashing
```

**Specific Test Function**:
```bash
pytest tests/test_security.py::TestPasswordHashing::test_password_hashing
```

### Run Tests in Parallel

```bash
pytest -n auto
```

Requires: `pip install pytest-xdist`

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Tests and Stop on First Failure

```bash
pytest -x
```

## Test Categories

Tests are marked with the following categories:

- `@pytest.mark.unit` - Fast unit tests (no database/network)
- `@pytest.mark.integration` - Integration tests (with database)
- `@pytest.mark.security` - Security-specific tests
- `@pytest.mark.slow` - Slow-running tests

## Test Coverage Goals

- **Overall Coverage**: > 80%
- **Security Module**: > 95%
- **API Endpoints**: > 85%
- **Critical Paths**: 100%

## Current Test Statistics

- **Total Tests**: 70+
- **Unit Tests**: 30+
- **Integration Tests**: 40+
- **Security Tests**: 15+

## Fixtures Available

### Database Fixtures
- `db_session` - Fresh database session for each test
- `client` - FastAPI test client with DB override

### User Fixtures
- `sample_user` - Student user (tertiary level)
- `admin_user` - Admin user
- `teacher_user` - Teacher user
- `inactive_user` - Inactive user

### Auth Fixtures
- `auth_token` - JWT token for sample user
- `admin_token` - JWT token for admin
- `teacher_token` - JWT token for teacher
- `auth_headers` - Authorization headers with bearer token
- `admin_headers` - Authorization headers for admin
- `teacher_headers` - Authorization headers for teacher

### Content Fixtures
- `sample_subject` - Test subject
- `sample_category` - Test category
- `sample_question` - Test question

## Writing New Tests

### Example Unit Test

```python
import pytest
from app.utils.security import get_password_hash, verify_password

class TestMyFeature:
    @pytest.mark.unit
    def test_something(self):
        # Arrange
        password = "Test123!"

        # Act
        hashed = get_password_hash(password)

        # Assert
        assert verify_password(password, hashed)
```

### Example Integration Test

```python
import pytest
from fastapi import status

class TestMyEndpoint:
    @pytest.mark.integration
    def test_endpoint(self, client, auth_headers):
        # Act
        response = client.get("/api/my-endpoint", headers=auth_headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "expected_field" in data
```

## Test Best Practices

1. **Follow AAA Pattern**
   - Arrange: Set up test data
   - Act: Execute the code being tested
   - Assert: Verify the results

2. **One Assertion Focus Per Test**
   - Each test should verify one specific behavior
   - Multiple assertions are OK if they verify the same behavior

3. **Use Descriptive Test Names**
   - `test_login_success` ✅
   - `test_login_wrong_password` ✅
   - `test_1` ❌

4. **Clean Up After Tests**
   - Database is automatically cleaned between tests
   - Use fixtures for setup/teardown

5. **Test Edge Cases**
   - Empty inputs
   - Very long inputs
   - Special characters
   - Null values
   - Boundary conditions

6. **Test Security Scenarios**
   - Unauthorized access attempts
   - Invalid tokens
   - SQL injection attempts
   - XSS attempts

## Continuous Integration

Tests run automatically on:
- Every push to main/develop branches
- Every pull request
- Nightly builds (if configured)

See `.github/workflows/ci.yml` for CI configuration.

## Troubleshooting

### Tests Fail with Database Errors

The test suite uses an in-memory SQLite database. If you see database errors:
```bash
# Clear any existing test databases
rm -f test_*.db

# Re-run tests
pytest
```

### Import Errors

Make sure you're in the backend directory:
```bash
cd backend
pytest
```

Or set PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Slow Tests

Skip slow tests during development:
```bash
pytest -m "not slow"
```

### Coverage Not Generated

Ensure pytest-cov is installed:
```bash
pip install pytest-cov
```

## Viewing Coverage Reports

### Terminal Report
```bash
pytest --cov=app --cov-report=term-missing
```

### HTML Report
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### XML Report (for CI)
```bash
pytest --cov=app --cov-report=xml
```

## Adding New Tests

1. Create test file: `test_feature_name.py`
2. Import pytest and required modules
3. Create test classes for logical grouping
4. Add pytest markers (@pytest.mark.unit, etc.)
5. Use fixtures from conftest.py
6. Run tests locally before committing
7. Ensure coverage stays above 80%

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
