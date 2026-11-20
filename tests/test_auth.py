from app.core.config import REFRESH_COOKIE_NAME
from app.features.auth.service import create_access_token
from app.database.session import get_db


def test_login_returns_access_token_and_http_only_refresh_cookie(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "test-admin", "password": "test-admin-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] == 900

    cookie = response.headers.get("set-cookie", "")
    assert REFRESH_COOKIE_NAME in cookie
    assert "httponly" in cookie.lower()


def test_login_rejects_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "test-admin", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_rejects_unknown_username(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "missing-user", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_protected_endpoint_accepts_admin_access_token(client):
    response = client.get(
        "/api/teachers",
        headers={"Authorization": f"Bearer {create_access_token()}"},
    )
    assert response.status_code == 200


def test_protected_endpoint_rejects_student_access_token(client):
    response = client.get(
        "/api/teachers",
        headers={"Authorization": f"Bearer {create_access_token(user_id=2, role='student', student_id=1)}"},
    )
    assert response.status_code == 403


def test_protected_endpoint_rejects_invalid_token(client):
    response = client.get(
        "/api/teachers",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_refresh_rotates_refresh_cookie(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "test-admin", "password": "test-admin-password"},
    )
    old_cookie = client.cookies.get(REFRESH_COOKIE_NAME)
    assert login.status_code == 200

    refreshed = client.post("/api/auth/refresh")
    new_cookie = client.cookies.get(REFRESH_COOKIE_NAME)

    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    assert new_cookie
    assert new_cookie != old_cookie


def test_logout_revokes_refresh_token(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "test-admin", "password": "test-admin-password"},
    )
    assert login.status_code == 200

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 204

    refresh = client.post("/api/auth/refresh")
    assert refresh.status_code == 401


def test_admin_can_create_student_account(client):
    # Existing test database gets one student through its overridden DB dependency.
    from app.features.students.model import Student

    # Use the request app's dependency override to insert a student in its test DB.
    from app.main import app
    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)
    student = Student(
        first_name="Test", last_name="Student", national_code="1234567891",
        grade="10", field="math", father_name="Parent", phone="09120000000",
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    student_id = student.id
    db.close()
    try:
        response = client.post(
            "/api/auth/users",
            json={"username": "student.one", "password": "student-pass-123", "student_id": student_id},
            headers={"Authorization": f"Bearer {create_access_token()}"},
        )
        assert response.status_code == 201
        assert response.json()["role"] == "student"
        assert response.json()["student_id"] == student_id
        assert "password" not in response.json()
        assert "password_hash" not in response.json()
    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass


def test_student_can_access_only_own_profile_endpoint(client):
    from app.database.session import get_db
    from app.features.students.model import Student
    from app.main import app

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)
    student = Student(
        first_name="Test", last_name="Student", national_code="1234567891",
        grade="10", field="math", father_name="Parent", phone="09120000000",
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    student_id = student.id
    db.close()
    try:
        token = create_access_token(user_id=22, role="student", student_id=student_id)
        response = client.get("/api/students/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["id"] == student_id
    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass
