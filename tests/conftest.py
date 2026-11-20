import os
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")
os.environ.setdefault("BOOTSTRAP_ADMIN_USERNAME", "test-admin")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-key-change-me-123456789")

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app as fastapi_app
from app.database.base import Base
from app.database.session import get_db
from app.features.auth.model import User
from app.features.auth.service import hash_password
import app.database.models


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    db = TestingSessionLocal()
    db.add(User(
        username="test-admin",
        password_hash=hash_password("test-admin-password"),
        role="admin",
        is_active=True,
    ))
    db.commit()
    db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
