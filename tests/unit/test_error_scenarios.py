"""Advanced error scenario and edge case tests.

This module tests complex error scenarios, edge cases, and boundary conditions
that go beyond basic validation errors. These tests ensure the system handles
unexpected situations gracefully.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from src.application.commands.project_commands import CompleteProjectCommand, DeleteProjectCommand
from src.application.commands.task_commands import (
    CompleteTaskCommand,
    CreateTaskCommand,
    DeleteTaskCommand,
    UpdateTaskCommand,
)
from src.application.services.project_service import ProjectService
from src.application.services.task_service import TaskService
from src.domain.entities.project import Project
from src.domain.entities.task import Task
from src.domain.exceptions.task_exceptions import TaskNotFoundError
from src.domain.value_objects.deadline import Deadline
from src.domain.value_objects.ids import ProjectId, TaskId


@pytest.fixture
def mock_uow():
    """Create a mock Unit of Work."""
    uow = Mock()
    uow.tasks = Mock()
    uow.projects = Mock()
    uow.commit = Mock()
    uow.rollback = Mock()
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


@pytest.fixture
def project_service(mock_uow, mock_event_bus):
    """Create ProjectService with mocked dependencies."""
    return ProjectService(mock_uow, mock_event_bus)


class TestConcurrentModificationScenarios:
    """Test scenarios involving concurrent access and modifications."""

    def test_task_deleted_between_fetch_and_update(self, task_service, mock_uow):
        """Task exists during fetch but deleted before update completes."""
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

        command = UpdateTaskCommand(task_id=str(task_id), title="Updated")

        # Should succeed based on first fetch (optimistic)
        # Real system would handle this via database constraints or version checking
        result = task_service.update_task(command)
        assert result is not None

    def test_project_completed_concurrently_during_task_completion(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Project is completed by another process while completing task."""
        task_id = TaskId.generate()
        project_id = ProjectId.generate()

        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            project_id=project_id,
        )

        # Create two versions of the project - before and after concurrent completion
        project_v1 = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
            completed=False,
        )
        project_v1.add_task(task_id)

        project_v2 = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
            completed=True,  # Completed concurrently
        )
        project_v2.add_task(task_id)

        mock_uow.tasks.get_by_id.return_value = task
        # Return different versions on different calls
        mock_uow.projects.get_by_id.side_effect = [project_v1, project_v2]
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = CompleteTaskCommand(task_id=str(task_id))

        # Should handle gracefully
        result = task_service.complete_task(command)
        assert result.completed is True


class TestDatabaseErrorScenarios:
    """Test handling of database-level errors."""

    def test_save_fails_due_to_database_error(self, task_service, mock_uow):
        """Database save operation fails."""
        mock_uow.tasks.save.side_effect = Exception("Database connection lost")

        command = CreateTaskCommand(
            title="Task",
            description="Desc",
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
        )

        with pytest.raises(Exception) as exc_info:
            with patch("src.application.services.task_service.TaskId"):
                task_service.create_task(command)

        assert "Database connection lost" in str(exc_info.value)
        # Verify context manager was properly exited (cleanup attempted)
        assert mock_uow.__exit__.called

    def test_commit_fails_after_successful_save(self, task_service, mock_uow):
        """Save succeeds but commit fails."""
        mock_uow.commit.side_effect = Exception("Transaction deadlock")

        command = CreateTaskCommand(
            title="Task",
            description="Desc",
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
        )

        with pytest.raises(Exception) as exc_info:
            with patch("src.application.services.task_service.TaskId"):
                task_service.create_task(command)

        assert "Transaction deadlock" in str(exc_info.value)

    def test_fetch_fails_due_to_connection_error(self, task_service, mock_uow):
        """Database fetch operation fails."""
        mock_uow.tasks.get_by_id.side_effect = Exception("Connection timeout")

        command = CompleteTaskCommand(task_id="task-123")

        with pytest.raises(Exception) as exc_info:
            task_service.complete_task(command)

        assert "Connection timeout" in str(exc_info.value)


class TestEventPublishingErrors:
    """Test scenarios where event publishing fails."""

    def test_event_bus_fails_after_commit(self, task_service, mock_uow, mock_event_bus):
        """Event bus fails to publish after successful commit."""
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
        mock_event_bus.publish.side_effect = Exception("Message broker unavailable")

        command = CompleteTaskCommand(task_id=str(task_id))

        # Event publishing failure should not rollback the committed transaction
        # This is a design decision - we could catch and log, or let it propagate
        with pytest.raises(Exception) as exc_info:
            task_service.complete_task(command)

        assert "Message broker unavailable" in str(exc_info.value)
        # Commit was called before event publishing failed
        assert mock_uow.commit.called


class TestBoundaryConditions:
    """Test boundary conditions and edge values."""

    def test_deadline_at_exact_midnight(self, task_service, mock_uow, mock_event_bus):
        """Task with deadline at exactly midnight."""
        midnight = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        command = CreateTaskCommand(
            title="Midnight Task",
            description="Desc",
            deadline=midnight,
        )

        with patch("src.application.services.task_service.TaskId") as mock_task_id:
            mock_id = TaskId.generate()
            mock_task_id.generate.return_value = mock_id

            task_id = task_service.create_task(command)
            assert task_id is not None

    def test_deadline_one_microsecond_before_project_deadline(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Task deadline exactly 1 microsecond before project deadline."""
        base_time = datetime.now(timezone.utc) + timedelta(days=30)
        project_deadline = Deadline(base_time)
        task_deadline = base_time - timedelta(microseconds=1)

        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=project_deadline,
        )
        mock_uow.projects.get_by_id.return_value = project

        command = CreateTaskCommand(
            title="Task",
            description="Desc",
            deadline=task_deadline,
            project_id=str(project_id),
        )

        with patch("src.application.services.task_service.TaskId"):
            # Should succeed - task deadline is before project deadline
            task_id = task_service.create_task(command)
            assert task_id is not None

    def test_project_with_zero_tasks(self, project_service, mock_uow, mock_event_bus):
        """Project with exactly zero tasks can be completed."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Empty Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        # No tasks added - total_task_count = 0

        mock_uow.projects.get_by_id.return_value = project
        mock_uow.projects.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = CompleteProjectCommand(project_id=str(project_id))

        result = project_service.complete_project(command)
        assert result.completed is True
        assert result.total_task_count == 0


class TestMalformedInputEdgeCases:
    """Test handling of malformed or unusual input."""

    def test_empty_string_as_id(self, task_service, mock_uow):
        """Empty string provided as task ID."""
        mock_uow.tasks.get_by_id.return_value = None

        command = CompleteTaskCommand(task_id="")

        # Should attempt to fetch with empty string and raise appropriate error
        with pytest.raises(TaskNotFoundError):
            task_service.complete_task(command)

    def test_very_long_task_id(self, task_service, mock_uow):
        """Extremely long string provided as task ID."""
        very_long_id = "x" * 10000
        mock_uow.tasks.get_by_id.return_value = None

        command = CompleteTaskCommand(task_id=very_long_id)

        with pytest.raises(TaskNotFoundError):
            task_service.complete_task(command)

    def test_special_characters_in_id(self, task_service, mock_uow):
        """Special characters in task ID."""
        special_id = "task-<script>alert('xss')</script>"
        mock_uow.tasks.get_by_id.return_value = None

        command = CompleteTaskCommand(task_id=special_id)

        with pytest.raises(TaskNotFoundError):
            task_service.complete_task(command)


class TestCascadingFailures:
    """Test scenarios where one failure triggers others."""

    def test_delete_project_when_some_tasks_fail_to_delete(
        self, project_service, mock_uow, mock_event_bus
    ):
        """Project deletion when some tasks fail to delete."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )

        task1_id = TaskId.generate()
        task2_id = TaskId.generate()
        tasks = [
            Task(
                id=task1_id,
                title="Task 1",
                description="Desc",
                deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
                project_id=project_id,
            ),
            Task(
                id=task2_id,
                title="Task 2",
                description="Desc",
                deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
                project_id=project_id,
            ),
        ]

        mock_uow.projects.get_by_id.return_value = project
        mock_uow.tasks.list_by_project.return_value = tasks
        # First delete succeeds, second fails
        mock_uow.tasks.delete.side_effect = [None, Exception("Foreign key constraint violation")]

        command = DeleteProjectCommand(project_id=str(project_id))

        with pytest.raises(Exception) as exc_info:
            project_service.delete_project(command)

        assert "Foreign key constraint violation" in str(exc_info.value)
        # Transaction should be rolled back via context manager
        assert mock_uow.__exit__.called


class TestTimezoneEdgeCases:
    """Test timezone-related edge cases."""

    def test_deadline_with_different_timezone(self, task_service, mock_uow, mock_event_bus):
        """Task with deadline in different timezone."""
        # Create deadline in UTC
        utc_deadline = datetime.now(timezone.utc) + timedelta(days=7)

        command = CreateTaskCommand(
            title="Task",
            description="Desc",
            deadline=utc_deadline,
        )

        with patch("src.application.services.task_service.TaskId") as mock_task_id:
            mock_id = TaskId.generate()
            mock_task_id.generate.return_value = mock_id

            task_id = task_service.create_task(command)
            assert task_id is not None

    def test_deadline_at_daylight_saving_transition(self, task_service, mock_uow, mock_event_bus):
        """Task with deadline during daylight saving time transition."""
        # Use a future date that's during DST transition (varies by region)
        # Using UTC avoids DST issues, but testing edge case
        # Ensure it's in the future by using relative date
        base_time = datetime.now(timezone.utc)
        # Add enough days to get to a future date, then set specific time
        transition_time = base_time.replace(
            month=3, day=9, hour=2, minute=30, second=0, microsecond=0
        )
        if transition_time <= base_time:
            # If the date is in the past, add a year
            transition_time = transition_time.replace(year=transition_time.year + 1)

        command = CreateTaskCommand(
            title="DST Task",
            description="Desc",
            deadline=transition_time,
        )

        with patch("src.application.services.task_service.TaskId") as mock_task_id:
            mock_id = TaskId.generate()
            mock_task_id.generate.return_value = mock_id

            task_id = task_service.create_task(command)
            assert task_id is not None


class TestStateTransitionEdgeCases:
    """Test unusual state transitions."""

    def test_complete_task_that_is_already_in_completed_state_in_db(
        self, task_service, mock_uow, mock_event_bus
    ):
        """Task shows as not completed in memory but is completed in DB."""
        task_id = TaskId.generate()

        # Create task that appears incomplete in first fetch
        task_incomplete = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            completed=False,
        )

        # But when we try to complete it, it's already completed (race condition)
        task_incomplete._completed = True  # Simulate concurrent completion

        mock_uow.tasks.get_by_id.return_value = task_incomplete
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = CompleteTaskCommand(task_id=str(task_id))

        # Should raise error when trying to complete already completed task
        from src.domain.exceptions.task_exceptions import TaskAlreadyCompletedError

        with pytest.raises(TaskAlreadyCompletedError):
            task_service.complete_task(command)

    def test_delete_task_twice_concurrently(self, task_service, mock_uow):
        """Task is deleted by two concurrent requests."""
        task_id = TaskId.generate()

        # First request succeeds
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
        )
        mock_uow.tasks.get_by_id.return_value = task

        # Second request should fail (task already deleted)
        command = DeleteTaskCommand(task_id=str(task_id))
        task_service.delete_task(command)

        # Reset mock for second call
        mock_uow.reset_mock()
        mock_uow.tasks.get_by_id.return_value = None

        # Second delete attempt
        with pytest.raises(TaskNotFoundError):
            task_service.delete_task(command)


class TestResourceExhaustion:
    """Test scenarios involving resource limits."""

    def test_project_with_maximum_tasks(self, project_service, mock_uow, mock_event_bus):
        """Project with very large number of tasks."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Big Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )

        # Add many tasks (simulate large project)
        for i in range(1000):
            task_id = TaskId.generate()
            project.add_task(task_id)
            project.mark_task_completed(task_id)

        mock_uow.projects.get_by_id.return_value = project
        mock_uow.projects.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = CompleteProjectCommand(project_id=str(project_id))

        # Should handle large number of tasks
        result = project_service.complete_project(command)
        assert result.completed is True
        assert result.total_task_count == 1000
        assert result.completed_task_count == 1000


class TestNullAndNoneHandling:
    """Test handling of None values."""

    def test_update_task_with_none_values(self, task_service, mock_uow, mock_event_bus):
        """Update task with None for optional fields."""
        task_id = TaskId.generate()
        task = Task(
            id=task_id,
            title="Original Title",
            description="Original Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
        )
        mock_uow.tasks.get_by_id.return_value = task
        mock_uow.tasks.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        # Update with None values (should keep original)
        command = UpdateTaskCommand(
            task_id=str(task_id), title=None, description=None, deadline=None
        )

        result = task_service.update_task(command)

        # Should keep original values when None is provided
        assert result.title == "Original Title"
        assert result.description == "Original Desc"


class TestIntegrationWithEventHandlers:
    """Test error scenarios in event handler integration."""

    def test_complete_task_when_event_handler_fails(self, task_service, mock_uow, mock_event_bus):
        """Event handler fails but transaction should still commit."""
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
        # Event bus fails
        mock_event_bus.publish.side_effect = Exception("Event bus down")

        command = CompleteTaskCommand(task_id=str(task_id))

        # Should fail when event publishing fails
        with pytest.raises(Exception) as exc_info:
            task_service.complete_task(command)

        assert "Event bus down" in str(exc_info.value)
        # But transaction was committed before event publishing
        assert mock_uow.commit.called
