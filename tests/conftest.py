import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from datetime import date  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import app.models  # noqa: E402,F401
from app.db.base import Base  # noqa: E402
from app.models import Department, Employee, Role  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

@pytest.fixture
def client(db):
    """HTTP client whose requests use the rolled-back test session."""
    fastapi_app.dependency_overrides[get_db] = lambda: db
    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()

# Change "change_me" to the POSTGRES_PASSWORD in your .env,
# or set a TEST_DATABASE_URL environment variable.
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:change_me@localhost:5432/employees_test",
)


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DB_URL)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    """Each test runs inside a transaction that is rolled back afterwards."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def dept(db):
    d = Department(name="Engineering")
    db.add(d)
    db.flush()
    return d


@pytest.fixture
def role(db):
    r = Role(title="Developer")
    db.add(r)
    db.flush()
    return r


@pytest.fixture
def make_employee(db, dept, role):
    counter = {"n": 0}

    def _make(**overrides):
        counter["n"] += 1
        data = dict(
            first_name="Test",
            last_name=f"User{counter['n']}",
            email=f"user{counter['n']}@example.com",
            hire_date=date(2024, 1, 1),
            department_id=dept.id,
            role_id=role.id,
        )
        data.update(overrides)
        emp = Employee(**data)
        db.add(emp)
        db.flush()
        return emp

    return _make