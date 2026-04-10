"""Shared fixtures for integration tests.

Uses an in-memory SQLite database with StaticPool so all connections
share the same DB and tests run without PostgreSQL.
"""
import os
import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set JWT_SECRET before any app imports
os.environ.setdefault("JWT_SECRET", "test-secret-for-ci")

from app.database import Base, get_db  # noqa: E402
from app.models import User, Project, Task, TaskStatus, TaskPriority  # noqa: E402
from app.auth import hash_password  # noqa: E402
from app.main import app  # noqa: E402

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(setup_database):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient wired to the test database session."""
    from fastapi.testclient import TestClient

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_user(db_session):
    """Create and return a test user."""
    user = User(
        id=uuid.uuid4(),
        name="Test User",
        email="test@example.com",
        password=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_header(client, seed_user):
    """Login as the seed user and return an Authorization header dict."""
    resp = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seed_project(db_session, seed_user):
    """Create a project owned by the seed user."""
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        description="A project for testing",
        owner_id=seed_user.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project
