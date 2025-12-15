"""Pytest fixtures for integration tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.infrastructure.config import Config
from src.infrastructure.persistence.database import Base, init_database


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine)

    yield session_factory

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def client(test_db):
    """Provide a test client with test database."""
    # Initialize with test database
    init_database("sqlite:///:memory:")

    # Import here to avoid circular dependencies
    from src.infrastructure.persistence.database import create_tables

    create_tables()

    # Reset event bus before each test to ensure clean state
    from src.api import dependencies
    dependencies._event_bus = None

    with TestClient(app) as test_client:
        yield test_client

    # Reset event bus after test
    dependencies._event_bus = None


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return Config(
        DATABASE_URL="sqlite:///:memory:",
        AUTO_COMPLETE_PROJECTS=True,
        LOG_LEVEL="DEBUG",
    )
