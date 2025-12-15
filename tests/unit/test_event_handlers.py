"""Unit tests for domain event handlers.

These tests verify that event handlers respond correctly to domain events
without touching the database. Repositories and dependencies are mocked.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from src.domain.entities.project import Project
from src.domain.entities.task import Task
from src.domain.events.project_events import ProjectDeadlineChangedEvent
from src.domain.events.task_events import TaskCompletedEvent, TaskCreatedEvent, TaskDeadlineChangedEvent
from src.domain.value_objects.deadline import Deadline
from src.domain.value_objects.ids import ProjectId, TaskId
from src.infrastructure.config import Config
from src.infrastructure.events.handlers import (
    AutoCompleteProjectHandler,
    DeadlineWarningChecker,
    TaskCompletionLogger,
    TaskDeadlineAdjustmentHandler,
)


@pytest.fixture
def mock_project_repository():
    """Create a mock project repository."""
    return Mock()


@pytest.fixture
def mock_task_repository():
    """Create a mock task repository."""
    return Mock()


@pytest.fixture
def mock_config():
    """Create a mock config with auto-completion enabled."""
    config = Mock(spec=Config)
    config.AUTO_COMPLETE_PROJECTS = True
    return config


class TestAutoCompleteProjectHandler:
    """Test automatic project completion logic."""

    def test_auto_complete_when_all_tasks_done(self, mock_project_repository, mock_config):
        """When last task completes and all tasks are done, project auto-completes."""
        handler = AutoCompleteProjectHandler(mock_project_repository, mock_config)

        task_id = TaskId.generate()
        project_id = ProjectId.generate()

        # Create project with one completed task
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        project.add_task(task_id)
        project.mark_task_completed(task_id)

        mock_project_repository.get_by_id.return_value = project

        event = TaskCompletedEvent(
            task_id=task_id,
            project_id=project_id,
            completed_at=datetime.now(timezone.utc),
        )

        handler.handle(event)

        # Verify project was completed and saved
        assert project.is_completed
        mock_project_repository.save.assert_called_once_with(project)

    def test_no_auto_complete_when_tasks_remain(self, mock_project_repository, mock_config):
        """When tasks remain incomplete, project should not auto-complete."""
        handler = AutoCompleteProjectHandler(mock_project_repository, mock_config)

        task1_id = TaskId.generate()
        task2_id = TaskId.generate()
        project_id = ProjectId.generate()

        # Create project with 2 tasks, only 1 completed
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        project.add_task(task1_id)
        project.add_task(task2_id)
        project.mark_task_completed(task1_id)
        # task2 is NOT completed

        mock_project_repository.get_by_id.return_value = project

        event = TaskCompletedEvent(
            task_id=task1_id,
            project_id=project_id,
            completed_at=datetime.now(timezone.utc),
        )

        handler.handle(event)

        # Verify project was NOT completed
        assert not project.is_completed
        # Should not save if no change
        assert not mock_project_repository.save.called

    def test_auto_complete_disabled_does_nothing(self, mock_project_repository):
        """When auto-complete is disabled, handler does nothing."""
        config = Mock(spec=Config)
        config.AUTO_COMPLETE_PROJECTS = False  # Disabled

        handler = AutoCompleteProjectHandler(mock_project_repository, config)

        event = TaskCompletedEvent(
            task_id=TaskId.generate(),
            project_id=ProjectId.generate(),
            completed_at=datetime.now(timezone.utc),
        )

        handler.handle(event)

        # Verify repository was never accessed
        assert not mock_project_repository.get_by_id.called
        assert not mock_project_repository.save.called

    def test_task_without_project_does_nothing(self, mock_project_repository, mock_config):
        """When task has no project, handler does nothing."""
        handler = AutoCompleteProjectHandler(mock_project_repository, mock_config)

        event = TaskCompletedEvent(
            task_id=TaskId.generate(),
            project_id=None,  # No project
            completed_at=datetime.now(timezone.utc),
        )

        handler.handle(event)

        # Verify repository was never accessed
        assert not mock_project_repository.get_by_id.called

    def test_nonexistent_project_handled_gracefully(self, mock_project_repository, mock_config):
        """When project doesn't exist, handler doesn't crash."""
        handler = AutoCompleteProjectHandler(mock_project_repository, mock_config)

        mock_project_repository.get_by_id.return_value = None

        event = TaskCompletedEvent(
            task_id=TaskId.generate(),
            project_id=ProjectId.generate(),
            completed_at=datetime.now(timezone.utc),
        )

        # Should not raise exception
        handler.handle(event)

        # Should not attempt to save
        assert not mock_project_repository.save.called

    def test_already_completed_project_handled(
        self, mock_project_repository, mock_config
    ):
        """When project is already completed, handler still processes event."""
        handler = AutoCompleteProjectHandler(mock_project_repository, mock_config)

        task_id = TaskId.generate()
        project_id = ProjectId.generate()

        # Project already completed
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
            completed=True,
        )
        project.add_task(task_id)
        project.mark_task_completed(task_id)

        mock_project_repository.get_by_id.return_value = project

        event = TaskCompletedEvent(
            task_id=task_id,
            project_id=project_id,
            completed_at=datetime.now(timezone.utc),
        )

        # Should not raise exception
        handler.handle(event)

        # Verify project is still completed
        assert project.is_completed is True


class TestTaskDeadlineAdjustmentHandler:
    """Test automatic task deadline adjustment when project deadline changes."""

    def test_adjust_affected_task_deadlines(self, mock_task_repository):
        """When project deadline changes, affected tasks are adjusted."""
        handler = TaskDeadlineAdjustmentHandler(mock_task_repository)

        task_id = TaskId.generate()
        project_id = ProjectId.generate()
        old_deadline = Deadline(datetime.now(timezone.utc) + timedelta(days=30))
        new_deadline = Deadline(datetime.now(timezone.utc) + timedelta(days=15))

        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=20)),
            project_id=project_id,
        )

        mock_task_repository.get_by_id.return_value = task

        event = ProjectDeadlineChangedEvent(
            project_id=project_id,
            old_deadline=old_deadline,
            new_deadline=new_deadline,
            affected_task_ids=[task_id],
        )

        handler.handle(event)

        # Verify task was saved after adjustment
        mock_task_repository.save.assert_called_once_with(task)
        # Verify task deadline was adjusted to project deadline
        assert task.deadline == new_deadline

    def test_no_affected_tasks_does_nothing(self, mock_task_repository):
        """When no tasks are affected, handler does nothing."""
        handler = TaskDeadlineAdjustmentHandler(mock_task_repository)

        event = ProjectDeadlineChangedEvent(
            project_id=ProjectId.generate(),
            old_deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
            new_deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=15)),
            affected_task_ids=[],  # No affected tasks
        )

        handler.handle(event)

        # Verify repository was never accessed
        assert not mock_task_repository.get_by_id.called
        assert not mock_task_repository.save.called

    def test_multiple_tasks_adjusted(self, mock_task_repository):
        """When multiple tasks are affected, all are adjusted."""
        handler = TaskDeadlineAdjustmentHandler(mock_task_repository)

        task1_id = TaskId.generate()
        task2_id = TaskId.generate()
        project_id = ProjectId.generate()
        new_deadline = Deadline(datetime.now(timezone.utc) + timedelta(days=10))

        task1 = Task(
            id=task1_id,
            title="Task 1",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=20)),
            project_id=project_id,
        )
        task2 = Task(
            id=task2_id,
            title="Task 2",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=15)),
            project_id=project_id,
        )

        mock_task_repository.get_by_id.side_effect = [task1, task2]

        event = ProjectDeadlineChangedEvent(
            project_id=project_id,
            old_deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
            new_deadline=new_deadline,
            affected_task_ids=[task1_id, task2_id],
        )

        handler.handle(event)

        # Verify both tasks were saved
        assert mock_task_repository.save.call_count == 2

    def test_nonexistent_task_handled_gracefully(self, mock_task_repository):
        """When task doesn't exist, handler doesn't crash."""
        handler = TaskDeadlineAdjustmentHandler(mock_task_repository)

        mock_task_repository.get_by_id.return_value = None

        event = ProjectDeadlineChangedEvent(
            project_id=ProjectId.generate(),
            old_deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
            new_deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=15)),
            affected_task_ids=[TaskId.generate()],
        )

        # Should not raise exception
        handler.handle(event)

        # Should not attempt to save
        assert not mock_task_repository.save.called


class TestDeadlineWarningChecker:
    """Test deadline warning checker for approaching deadlines."""

    def test_warn_on_approaching_deadline_created(self, mock_task_repository):
        """When task is created with deadline < 24h, warning is logged."""
        handler = DeadlineWarningChecker(mock_task_repository)

        task_id = TaskId.generate()
        # Deadline in 12 hours
        approaching_deadline = Deadline(datetime.now(timezone.utc) + timedelta(hours=12))

        event = TaskCreatedEvent(
            task_id=task_id,
            title="Urgent Task",
            deadline=approaching_deadline,
            project_id=None,
        )

        # Should not raise exception, just log warning
        with patch("src.infrastructure.events.handlers.logger") as mock_logger:
            handler.handle_created(event)
            # Verify warning was logged
            assert any("approaching deadline" in str(call).lower() 
                      for call in mock_logger.warning.call_args_list)

    def test_no_warn_on_distant_deadline(self, mock_task_repository):
        """When task deadline is far in future, no warning is logged."""
        handler = DeadlineWarningChecker(mock_task_repository)

        task_id = TaskId.generate()
        # Deadline in 7 days
        distant_deadline = Deadline(datetime.now(timezone.utc) + timedelta(days=7))

        event = TaskCreatedEvent(
            task_id=task_id,
            title="Task",
            deadline=distant_deadline,
            project_id=None,
        )

        with patch("src.infrastructure.events.handlers.logger") as mock_logger:
            handler.handle_created(event)
            # Verify no warning was logged (only info)
            assert mock_logger.warning.call_count == 0

    def test_warn_on_deadline_changed_to_approaching(self, mock_task_repository):
        """When task deadline is changed to approaching, warning is logged."""
        handler = DeadlineWarningChecker(mock_task_repository)

        task_id = TaskId.generate()
        approaching_deadline = Deadline(datetime.now(timezone.utc) + timedelta(hours=12))

        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=approaching_deadline,
        )
        mock_task_repository.get_by_id.return_value = task

        event = TaskDeadlineChangedEvent(
            task_id=task_id,
            old_deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            new_deadline=approaching_deadline,
        )

        with patch("src.infrastructure.events.handlers.logger") as mock_logger:
            handler.handle_deadline_changed(event)
            # Verify warning was logged
            assert any("approaching deadline" in str(call).lower() 
                      for call in mock_logger.warning.call_args_list)


class TestTaskCompletionLogger:
    """Test task completion logging."""

    def test_log_task_completion(self):
        """Task completion is logged correctly."""
        handler = TaskCompletionLogger()

        task_id = TaskId.generate()
        event = TaskCompletedEvent(
            task_id=task_id,
            project_id=None,
            completed_at=datetime.now(timezone.utc),
        )

        with patch("src.infrastructure.events.handlers.logger") as mock_logger:
            handler.handle(event)
            # Verify info was logged
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert str(task_id) in log_message
            assert "completed" in log_message.lower()

    def test_log_task_completion_with_project(self):
        """Task completion with project is logged with project info."""
        handler = TaskCompletionLogger()

        task_id = TaskId.generate()
        project_id = ProjectId.generate()
        event = TaskCompletedEvent(
            task_id=task_id,
            project_id=project_id,
            completed_at=datetime.now(timezone.utc),
        )

        with patch("src.infrastructure.events.handlers.logger") as mock_logger:
            handler.handle(event)
            log_message = mock_logger.info.call_args[0][0]
            assert str(task_id) in log_message
            assert str(project_id) in log_message
            assert "Project:" in log_message


class TestEventHandlerErrorHandling:
    """Test that event handlers handle errors gracefully."""

    def test_auto_complete_handler_catches_exceptions(self, mock_project_repository, mock_config):
        """When auto-complete handler encounters error, it logs and doesn't crash."""
        handler = AutoCompleteProjectHandler(mock_project_repository, mock_config)

        # Make repository throw exception
        mock_project_repository.get_by_id.side_effect = Exception("Database error")

        event = TaskCompletedEvent(
            task_id=TaskId.generate(),
            project_id=ProjectId.generate(),
            completed_at=datetime.now(timezone.utc),
        )

        # Should not raise exception, just log error
        with patch("src.infrastructure.events.handlers.logger") as mock_logger:
            handler.handle(event)
            # Verify error was logged
            assert mock_logger.error.called

    def test_deadline_adjustment_handler_catches_exceptions(self, mock_task_repository):
        """When deadline adjustment handler encounters error, it logs and doesn't crash."""
        handler = TaskDeadlineAdjustmentHandler(mock_task_repository)

        # Make repository throw exception
        mock_task_repository.get_by_id.side_effect = Exception("Database error")

        event = ProjectDeadlineChangedEvent(
            project_id=ProjectId.generate(),
            old_deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
            new_deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=15)),
            affected_task_ids=[TaskId.generate()],
        )

        # Should not raise exception, just log error
        with patch("src.infrastructure.events.handlers.logger") as mock_logger:
            handler.handle(event)
            # Verify error was logged
            assert mock_logger.error.called

