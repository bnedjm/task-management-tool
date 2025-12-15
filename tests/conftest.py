"""Pytest configuration and shared fixtures."""

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.project import Project
from src.domain.entities.task import Task
from src.domain.value_objects.deadline import Deadline
from src.domain.value_objects.ids import ProjectId, TaskId


@pytest.fixture
def task_id():
    """Provide a task ID for testing."""
    return TaskId.generate()


@pytest.fixture
def project_id():
    """Provide a project ID for testing."""
    return ProjectId.generate()


@pytest.fixture
def future_deadline():
    """Provide a future deadline."""
    return Deadline(datetime.now(timezone.utc) + timedelta(days=7))


@pytest.fixture
def task_factory():
    """Factory for creating test tasks."""

    def _create_task(**kwargs):
        defaults = {
            "id": TaskId.generate(),
            "title": "Test Task",
            "description": "Test Description",
            "deadline": Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            "completed": False,
            "project_id": None,
        }
        return Task(**{**defaults, **kwargs})

    return _create_task


@pytest.fixture
def project_factory():
    """Factory for creating test projects."""

    def _create_project(**kwargs):
        defaults = {
            "id": ProjectId.generate(),
            "title": "Test Project",
            "description": "Test Project Description",
            "deadline": Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
            "completed": False,
        }
        return Project(**{**defaults, **kwargs})

    return _create_project
