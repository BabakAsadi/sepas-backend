import os

os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-key-change-me-123456789")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database.models  # noqa: F401
from app.database.base import Base
from app.shared.dependencies import get_db
from app.features.teachers.router import router as teachers_router
from app.features.lessons.router import router as lessons_router
from app.features.classrooms.router import router as classrooms_router
from app.features.sessions.router import router as sessions_router
from app.features.students.router import router as students_router
from app.features.courses.router import router as courses_router
from app.features.course_schedules.router import router as schedules_router
from app.features.course_occurrences.router import router as occurrences_router
from app.features.course_enrollments.router import router as enrollments_router
from app.features.wallets.router import router as wallets_router
from app.features.reports.router import router as reports_router
from app.features.auth.router import router as auth_router
from app.features.auth.service import create_access_token, hash_password
from app.features.auth.model import User


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    setup_db = TestingSession()
    setup_db.add(User(username="test-admin", password_hash=hash_password("test-admin-password"), role="admin", is_active=True))
    setup_db.commit()
    setup_db.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    for router in (
        teachers_router,
        lessons_router,
        classrooms_router,
        sessions_router,
        students_router,
        courses_router,
        schedules_router,
        occurrences_router,
        enrollments_router,
        wallets_router,
        reports_router,
        auth_router,
    ):
        app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


PROTECTED_READ_ENDPOINTS = [
    "/api/teachers",
    "/api/teachers/1",
    "/api/lessons",
    "/api/lessons/1",
    "/api/classrooms",
    "/api/classrooms/1",
    "/api/sessions",
    "/api/sessions/1",
    "/api/courses",
    "/api/courses/1",
    "/api/course-schedules",
    "/api/course-schedules/1",
    "/api/course-occurrences",
    "/api/course-occurrences/1",
]


@pytest.mark.parametrize("path", PROTECTED_READ_ENDPOINTS)
def test_management_read_endpoints_require_access_token(client, path):
    response = client.get(path)
    assert response.status_code == 401


@pytest.mark.parametrize("path", PROTECTED_READ_ENDPOINTS)
def test_management_read_endpoints_accept_access_token(client, path):
    response = client.get(path, headers={"Authorization": f"Bearer {create_access_token()}"})
    assert response.status_code in (200, 404)


def test_enrollment_list_rejects_non_positive_student_filter(client):
    response = client.get(
        "/api/course-enrollments?student_id=0",
        headers={"Authorization": f"Bearer {create_access_token()}"},
    )
    assert response.status_code == 422


def test_enrollment_list_rejects_non_positive_course_filter(client):
    response = client.get(
        "/api/course-enrollments?course_id=-1",
        headers={"Authorization": f"Bearer {create_access_token()}"},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("path", [
    "/api/wallets/0",
    "/api/wallets/-1/top-ups",
    "/api/wallets/0/allocations",
])
def test_wallet_endpoints_reject_non_positive_student_id(client, path):
    response = client.get(path, headers={"Authorization": f"Bearer {create_access_token()}"}) if path.endswith(('/0', '/-1')) else client.post(
        path,
        json={"enrollment_id": 1, "amount": 1},
        headers={"Authorization": f"Bearer {create_access_token()}"},
    )
    assert response.status_code == 422


def test_wallet_top_up_rejects_zero_amount(client):
    response = client.post(
        "/api/wallets/1/top-ups",
        json={"amount": 0},
        headers={"Authorization": f"Bearer {create_access_token()}"},
    )
    assert response.status_code == 422


def test_wallet_allocation_rejects_zero_amount(client):
    response = client.post(
        "/api/wallets/1/allocations",
        json={"enrollment_id": 1, "amount": 0},
        headers={"Authorization": f"Bearer {create_access_token()}"},
    )
    assert response.status_code == 422


def test_management_read_endpoint_rejects_invalid_access_token(client):
    response = client.get(
        "/api/courses",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
