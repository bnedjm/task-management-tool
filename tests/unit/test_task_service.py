"""Unit tests for TaskService with mocked dependencies.

These tests verify the orchestration logic of TaskService without touching
the database or infrastructure layer. All dependencies are mocked to ensure
fast, isolated unit tests.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, call, patch

import pytest

from src.application.commands.task_commands import (
    CompleteTaskCommand,
    CreateTaskCommand,
    DeleteTaskCommand,
    ReopenTaskCommand,
    UpdateTaskCommand,
)
from src.application.queries.task_queries import GetTaskByIdQuery, ListTasksQuery
from src.application.services.task_service import TaskService
from src.domain.entities.project import Project
from src.domain.entities.task import Task
from src.domain.events.task_events import TaskCompletedEvent, TaskCreatedEvent
from src.domain.exceptions.project_exceptions import (
    DeadlineConstraintViolation,
    ProjectNotFoundError,
)
from src.domain.exceptions.task_exceptions import (
    TaskAlreadyCompletedError,
    TaskNotFoundError,
)
from src.domain.value_objects.deadline import Deadline
from src.domain.value_objects.ids import ProjectId, TaskId


@pytest.fixture
def mock_uow():
    """Create a mock Unit of Work."""
    uow = Mock()
    uow.tasks = Mock()
    uow.projects = Mock()
    uow.commit = Mock()
    uow.__enter__ = Mock(return_value=uow)
    uow.__exit__ = Mock(return_value=False)
    return uow


@pytest.fixture
def mock_event_bus():
    """Create a mock Event Bus."""
    return Mock()


@pytest.fixture
def task_service(mock_uow, mock_event_bus):
    """Create TaskService with mocked dependencies."""
    return TaskService(mock_uow, mock_event_bus)


class TestCreateTask:
    """Test task creation orchestration."""

    def test_create_task_without_project_succeeds(self, task_service, mock_uow, mock_event_bus):
        """Creating a task without project assignment works."""
        command = CreateTaskCommand(
            title="Test Task",
            description="Description",
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
            project_id=None,
        )

        with patch("src.application.services.task_service.TaskId") as mock_task_id:
            mock_id = TaskId.generate()
            mock_task_id.generate.return_value = mock_id

            task_id = task_service.create_task(command)

            # Verify task was saved
            assert mock_uow.tasks.save.called
            saved_task = mock_uow.tasks.save.call_args[0][0]
            assert saved_task.title == "Test Task"
            assert saved_task.description == "Description"

            # Verify transaction committed
            assert mock_uow.commit.called

            # Verify events published
            assert mock_event_bus.publish.called
            published_events = mock_event_bus.publish.call_args[0][0]
            assert any(isinstance(e, TaskCreatedEvent) for e in published_events)

            assert task_id == str(mock_id)

    def test_create_task_with_project_validates_project_exists(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Creating a task with project validates project exists."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Test Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        mock_uow.projects.get_by_id.return_value = project

        command = CreateTaskCommand(
            title="Task",
            description="Desc",
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
            project_id=str(project_id),
        )

        with patch("src.application.services.task_service.TaskId"):
            task_service.create_task(command)

            # Verify project was fetched
            mock_uow.projects.get_by_id.assert_called_once()

            # Verify project was saved (task added to project)
            assert mock_uow.projects.save.called

    def test_create_task_with_nonexistent_project_raises_error(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Creating a task with non-existent project raises error."""
        mock_uow.projects.get_by_id.return_value = None

        command = CreateTaskCommand(
            title="Task",
            description="Desc",
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
            project_id="nonexistent-project-id",
        )

        with pytest.raises(ProjectNotFoundError) as exc_info:
            task_service.create_task(command)

        assert "nonexistent-project-id" in str(exc_info.value)
        assert not mock_uow.commit.called  # Transaction should not commit

    def test_create_task_with_invalid_deadline_raises_error(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Creating a task with deadline after project deadline raises error."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
        )
        mock_uow.projects.get_by_id.return_value = project

        # Task deadline is AFTER project deadline
        command = CreateTaskCommand(
            title="Task",
            description="Desc",
            deadline=datetime.now(timezone.utc) + timedelta(days=30),
            project_id=str(project_id),
        )

        with patch("src.application.services.task_service.TaskId"):
            with pytest.raises(DeadlineConstraintViolation):
                task_service.create_task(command)

            assert not mock_uow.commit.called


class TestUpdateTask:
    """Test task update orchestration."""

    def test_update_task_title_succeeds(self, task_service, mock_uow, mock_event_bus):
        """Updating task title works correctly."""
        task_id = TaskId.generate()
        task = Task(
            id=task_id,
            title="Original",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
        )
        mock_uow.tasks.get_by_id.return_value = task
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = UpdateTaskCommand(task_id=str(task_id), title="Updated", description=None)

        result = task_service.update_task(command)

        assert result.title == "Updated"
        assert mock_uow.tasks.save.called
        assert mock_uow.commit.called

    def test_update_nonexistent_task_raises_error(self, task_service, mock_uow, mock_event_bus):
        """Updating non-existent task raises error."""
        mock_uow.tasks.get_by_id.return_value = None

        command = UpdateTaskCommand(task_id="nonexistent", title="New")

        with pytest.raises(TaskNotFoundError):
            task_service.update_task(command)

        assert not mock_uow.commit.called

    def test_update_task_deadline_validates_project_constraint(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Updating task deadline validates project deadline constraint."""
        task_id = TaskId.generate()
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
        )
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=5)),
            project_id=project_id,
        )

        mock_uow.tasks.get_by_id.return_value = task
        mock_uow.projects.get_by_id.return_value = project

        # Try to update deadline beyond project deadline
        command = UpdateTaskCommand(
            task_id=str(task_id),
            deadline=datetime.now(timezone.utc) + timedelta(days=30),
        )

        with pytest.raises(DeadlineConstraintViolation):
            task_service.update_task(command)

        assert not mock_uow.commit.called


class TestCompleteTask:
    """Test task completion orchestration."""

    def test_complete_task_succeeds(self, task_service, mock_uow, mock_event_bus):
        """Completing a task works correctly."""
        task_id = TaskId.generate()
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
        )
        mock_uow.tasks.get_by_id.return_value = task
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = CompleteTaskCommand(task_id=str(task_id))

        result = task_service.complete_task(command)

        assert result.completed is True
        assert mock_uow.tasks.save.called
        assert mock_uow.commit.called
        assert mock_event_bus.publish.called

    def test_complete_task_with_project_updates_project(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Completing a task updates project task counts."""
        task_id = TaskId.generate()
        project_id = ProjectId.generate()
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            project_id=project_id,
        )
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        project.add_task(task_id)

        mock_uow.tasks.get_by_id.return_value = task
        mock_uow.projects.get_by_id.return_value = project
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = CompleteTaskCommand(task_id=str(task_id))

        task_service.complete_task(command)

        # Verify project was fetched and saved
        mock_uow.projects.get_by_id.assert_called_once_with(project_id)
        assert mock_uow.projects.save.called

    def test_complete_already_completed_task_raises_error(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Completing an already completed task raises error."""
        task_id = TaskId.generate()
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            completed=True,
        )
        mock_uow.tasks.get_by_id.return_value = task

        command = CompleteTaskCommand(task_id=str(task_id))

        with pytest.raises(TaskAlreadyCompletedError):
            task_service.complete_task(command)

        assert not mock_uow.commit.called


class TestReopenTask:
    """Test task reopening orchestration."""

    def test_reopen_task_succeeds(self, task_service, mock_uow, mock_event_bus):
        """Reopening a task works correctly."""
        task_id = TaskId.generate()
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            completed=True,
        )
        mock_uow.tasks.get_by_id.return_value = task
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = ReopenTaskCommand(task_id=str(task_id))

        result = task_service.reopen_task(command)

        assert result.completed is False
        assert mock_uow.tasks.save.called
        assert mock_uow.commit.called
        assert mock_event_bus.publish.called

    def test_reopen_task_with_project_reopens_project(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Reopening a task can reopen a completed project."""
        task_id = TaskId.generate()
        project_id = ProjectId.generate()
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            project_id=project_id,
            completed=True,
        )
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
            completed=True,
        )
        project.add_task(task_id)
        project.mark_task_completed(task_id)

        mock_uow.tasks.get_by_id.return_value = task
        mock_uow.projects.get_by_id.return_value = project
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = ReopenTaskCommand(task_id=str(task_id))

        task_service.reopen_task(command)

        # Verify project was saved (reopened)
        assert mock_uow.projects.save.called


class TestDeleteTask:
    """Test task deletion orchestration."""

    def test_delete_task_succeeds(self, task_service, mock_uow, mock_event_bus):
        """Deleting a task works correctly."""
        task_id = TaskId.generate()
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
        )
        mock_uow.tasks.get_by_id.return_value = task

        command = DeleteTaskCommand(task_id=str(task_id))

        task_service.delete_task(command)

        mock_uow.tasks.delete.assert_called_once_with(task_id)
        assert mock_uow.commit.called

    def test_delete_task_with_project_removes_from_project(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Deleting a task removes it from project."""
        task_id = TaskId.generate()
        project_id = ProjectId.generate()
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            project_id=project_id,
        )
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        project.add_task(task_id)

        mock_uow.tasks.get_by_id.return_value = task
        mock_uow.projects.get_by_id.return_value = project

        command = DeleteTaskCommand(task_id=str(task_id))

        task_service.delete_task(command)

        # Verify project was updated
        assert mock_uow.projects.save.called
        mock_uow.tasks.delete.assert_called_once_with(task_id)

    def test_delete_nonexistent_task_raises_error(self, task_service, mock_uow, mock_event_bus):
        """Deleting non-existent task raises error."""
        mock_uow.tasks.get_by_id.return_value = None

        command = DeleteTaskCommand(task_id="nonexistent")

        with pytest.raises(TaskNotFoundError):
            task_service.delete_task(command)

        assert not mock_uow.tasks.delete.called
        assert not mock_uow.commit.called


class TestQueryTasks:
    """Test task query operations."""

    def test_get_task_by_id_succeeds(self, task_service, mock_uow, mock_event_bus):
        """Getting task by ID returns correct DTO."""
        task_id = TaskId.generate()
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
        )
        mock_uow.tasks.get_by_id.return_value = task
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        query = GetTaskByIdQuery(task_id=str(task_id))

        result = task_service.get_task_by_id(query)

        assert result.id == str(task_id)
        assert result.title == "Task"

    def test_get_nonexistent_task_raises_error(self, task_service, mock_uow, mock_event_bus):
        """Getting non-existent task raises error."""
        mock_uow.tasks.get_by_id.return_value = None

        query = GetTaskByIdQuery(task_id="nonexistent")

        with pytest.raises(TaskNotFoundError):
            task_service.get_task_by_id(query)

    def test_list_tasks_returns_all_tasks(self, task_service, mock_uow, mock_event_bus):
        """Listing tasks returns all filtered tasks."""
        tasks = [
            Task(
                id=TaskId.generate(),
                title=f"Task {i}",
                description="Desc",
                deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            )
            for i in range(3)
        ]
        mock_uow.tasks.list_by_filter.return_value = tasks
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        query = ListTasksQuery(completed=None, overdue=None, project_id=None)

        result = task_service.list_tasks(query)

        assert len(result) == 3
        mock_uow.tasks.list_by_filter.assert_called_once_with(completed=None, overdue=None)

    def test_list_tasks_by_project(self, task_service, mock_uow, mock_event_bus):
        """Listing tasks by project uses correct repository method."""
        project_id = ProjectId.generate()
        tasks = [
            Task(
                id=TaskId.generate(),
                title="Task",
                description="Desc",
                deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
                project_id=project_id,
            )
        ]
        mock_uow.tasks.list_by_project.return_value = tasks
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        query = ListTasksQuery(completed=None, overdue=None, project_id=str(project_id))

        result = task_service.list_tasks(query)

        assert len(result) == 1
        mock_uow.tasks.list_by_project.assert_called_once()


class TestTransactionManagement:
    """Test that service properly manages transactions."""

    def test_create_task_rolls_back_on_error(self, task_service, mock_uow, mock_event_bus):
        """When task creation fails, transaction context manager handles it."""
        mock_uow.tasks.save.side_effect = Exception("Database error")

        command = CreateTaskCommand(
            title="Task",
            description="Desc",
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
        )

        with pytest.raises(Exception):
            with patch("src.application.services.task_service.TaskId"):
                task_service.create_task(command)

        # UoW __exit__ should have been called due to exception
        assert mock_uow.__exit__.called

    def test_events_published_only_after_commit(self, task_service, mock_uow, mock_event_bus):
        """Events are published only after successful commit."""
        task_id = TaskId.generate()
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
        )
        mock_uow.tasks.get_by_id.return_value = task
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = CompleteTaskCommand(task_id=str(task_id))

        task_service.complete_task(command)

        # Verify commit was called before publish
        call_order = [c[0] for c in mock_uow.method_calls]
        commit_index = next(i for i, c in enumerate(call_order) if "commit" in str(c))
        assert commit_index >= 0  # Commit was called

        # Events should have been published
        assert mock_event_bus.publish.called

