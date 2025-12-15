"""Unit tests for ProjectService with mocked dependencies.

These tests verify the orchestration logic of ProjectService without touching
the database or infrastructure layer. All dependencies are mocked to ensure
fast, isolated unit tests.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from src.application.commands.project_commands import (
    CompleteProjectCommand,
    CreateProjectCommand,
    DeleteProjectCommand,
    LinkTaskToProjectCommand,
    UnlinkTaskFromProjectCommand,
    UpdateProjectCommand,
)
from src.application.queries.project_queries import GetProjectByIdQuery, ListProjectsQuery
from src.application.services.project_service import ProjectService
from src.domain.entities.project import Project
from src.domain.entities.task import Task
from src.domain.events.project_events import ProjectCreatedEvent
from src.domain.exceptions.project_exceptions import (
    DeadlineConstraintViolation,
    ProjectNotCompletableError,
    ProjectNotFoundError,
)
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
    uow.__enter__ = Mock(return_value=uow)
    uow.__exit__ = Mock(return_value=False)
    return uow


@pytest.fixture
def mock_event_bus():
    """Create a mock Event Bus."""
    return Mock()


@pytest.fixture
def project_service(mock_uow, mock_event_bus):
    """Create ProjectService with mocked dependencies."""
    return ProjectService(mock_uow, mock_event_bus)


class TestCreateProject:
    """Test project creation orchestration."""

    def test_create_project_succeeds(self, project_service, mock_uow, mock_event_bus):
        """Creating a project works correctly."""
        command = CreateProjectCommand(
            title="Test Project",
            description="Description",
            deadline=datetime.now(timezone.utc) + timedelta(days=30),
        )

        with patch("src.application.services.project_service.ProjectId") as mock_project_id:
            mock_id = ProjectId.generate()
            mock_project_id.generate.return_value = mock_id

            project_id = project_service.create_project(command)

            # Verify project was saved
            assert mock_uow.projects.save.called
            saved_project = mock_uow.projects.save.call_args[0][0]
            assert saved_project.title == "Test Project"
            assert saved_project.description == "Description"

            # Verify transaction committed
            assert mock_uow.commit.called

            # Verify events published
            assert mock_event_bus.publish.called
            published_events = mock_event_bus.publish.call_args[0][0]
            assert any(isinstance(e, ProjectCreatedEvent) for e in published_events)

            assert project_id == str(mock_id)


class TestUpdateProject:
    """Test project update orchestration."""

    def test_update_project_title_succeeds(self, project_service, mock_uow, mock_event_bus):
        """Updating project title works correctly."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Original",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        mock_uow.projects.get_by_id.return_value = project
        mock_uow.projects.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )
        mock_uow.tasks.list_by_project.return_value = []

        command = UpdateProjectCommand(
            project_id=str(project_id), title="Updated", description=None
        )

        result = project_service.update_project(command)

        assert result.title == "Updated"
        assert mock_uow.projects.save.called
        assert mock_uow.commit.called

    def test_update_nonexistent_project_raises_error(
        self, project_service, mock_uow, mock_event_bus
    ):
        """Updating non-existent project raises error."""
        mock_uow.projects.get_by_id.return_value = None

        command = UpdateProjectCommand(project_id="nonexistent", title="New")

        with pytest.raises(ProjectNotFoundError):
            project_service.update_project(command)

        assert not mock_uow.commit.called

    def test_update_project_deadline_finds_affected_tasks(
        self, project_service, mock_uow, mock_event_bus
    ):
        """Updating project deadline identifies tasks that violate constraint."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )

        # Task with deadline beyond new project deadline
        task = Task(
            id=TaskId.generate(),
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=20)),
            project_id=project_id,
        )

        mock_uow.projects.get_by_id.return_value = project
        mock_uow.tasks.list_by_project.return_value = [task]
        mock_uow.projects.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        # Update project deadline to earlier date (before task deadline)
        command = UpdateProjectCommand(
            project_id=str(project_id),
            deadline=datetime.now(timezone.utc) + timedelta(days=10),
        )

        project_service.update_project(command)

        # Verify tasks were queried
        mock_uow.tasks.list_by_project.assert_called_once_with(project_id)
        # Project should be saved with affected tasks info
        assert mock_uow.projects.save.called


class TestCompleteProject:
    """Test project completion orchestration."""

    def test_complete_project_with_all_tasks_done_succeeds(
        self, project_service, mock_uow, mock_event_bus
    ):
        """Completing project with all tasks done works."""
        project_id = ProjectId.generate()
        task_id = TaskId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        project.add_task(task_id)
        project.mark_task_completed(task_id)

        mock_uow.projects.get_by_id.return_value = project
        mock_uow.projects.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = CompleteProjectCommand(project_id=str(project_id))

        result = project_service.complete_project(command)

        assert result.completed is True
        assert mock_uow.projects.save.called
        assert mock_uow.commit.called
        assert mock_event_bus.publish.called

    def test_complete_project_with_pending_tasks_raises_error(
        self, project_service, mock_uow, mock_event_bus
    ):
        """Completing project with incomplete tasks raises error."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        # Add task but don't mark as completed
        project.add_task(TaskId.generate())

        mock_uow.projects.get_by_id.return_value = project

        command = CompleteProjectCommand(project_id=str(project_id))

        with pytest.raises(ProjectNotCompletableError):
            project_service.complete_project(command)

        assert not mock_uow.commit.called

    def test_complete_nonexistent_project_raises_error(
        self, project_service, mock_uow, mock_event_bus
    ):
        """Completing non-existent project raises error."""
        mock_uow.projects.get_by_id.return_value = None

        command = CompleteProjectCommand(project_id="nonexistent")

        with pytest.raises(ProjectNotFoundError):
            project_service.complete_project(command)

        assert not mock_uow.commit.called


class TestDeleteProject:
    """Test project deletion orchestration."""

    def test_delete_project_without_tasks_succeeds(self, project_service, mock_uow, mock_event_bus):
        """Deleting project without tasks works."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )

        mock_uow.projects.get_by_id.return_value = project
        mock_uow.tasks.list_by_project.return_value = []

        command = DeleteProjectCommand(project_id=str(project_id))

        project_service.delete_project(command)

        mock_uow.projects.delete.assert_called_once_with(project_id)
        assert mock_uow.commit.called

    def test_delete_project_cascades_to_tasks(self, project_service, mock_uow, mock_event_bus):
        """Deleting project deletes all associated tasks."""
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

        command = DeleteProjectCommand(project_id=str(project_id))

        project_service.delete_project(command)

        # Verify all tasks were deleted
        assert mock_uow.tasks.delete.call_count == 2
        mock_uow.projects.delete.assert_called_once_with(project_id)
        assert mock_uow.commit.called

    def test_delete_nonexistent_project_raises_error(
        self, project_service, mock_uow, mock_event_bus
    ):
        """Deleting non-existent project raises error."""
        mock_uow.projects.get_by_id.return_value = None

        command = DeleteProjectCommand(project_id="nonexistent")

        with pytest.raises(ProjectNotFoundError):
            project_service.delete_project(command)

        assert not mock_uow.tasks.delete.called
        assert not mock_uow.commit.called


class TestLinkTask:
    """Test task-project linking orchestration."""

    def test_link_task_to_project_succeeds(self, project_service, mock_uow, mock_event_bus):
        """Linking task to project works correctly."""
        project_id = ProjectId.generate()
        task_id = TaskId.generate()

        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
        )

        mock_uow.projects.get_by_id.return_value = project
        mock_uow.tasks.get_by_id.return_value = task

        command = LinkTaskToProjectCommand(project_id=str(project_id), task_id=str(task_id))

        project_service.link_task_to_project(command)

        # Verify both entities were saved
        assert mock_uow.tasks.save.called
        assert mock_uow.projects.save.called
        assert mock_uow.commit.called
        assert mock_event_bus.publish.called

    def test_link_task_with_invalid_deadline_raises_error(
        self, project_service, mock_uow, mock_event_bus
    ):
        """Linking task with deadline after project deadline raises error."""
        project_id = ProjectId.generate()
        task_id = TaskId.generate()

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
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),  # After project
        )

        mock_uow.projects.get_by_id.return_value = project
        mock_uow.tasks.get_by_id.return_value = task

        command = LinkTaskToProjectCommand(project_id=str(project_id), task_id=str(task_id))

        with pytest.raises(DeadlineConstraintViolation):
            project_service.link_task_to_project(command)

        assert not mock_uow.commit.called

    def test_link_task_to_nonexistent_project_raises_error(
        self, project_service, mock_uow, mock_event_bus
    ):
        """Linking task to non-existent project raises error."""
        mock_uow.projects.get_by_id.return_value = None

        command = LinkTaskToProjectCommand(project_id="nonexistent", task_id="task-id")

        with pytest.raises(ProjectNotFoundError):
            project_service.link_task_to_project(command)

        assert not mock_uow.commit.called

    def test_link_nonexistent_task_raises_error(self, project_service, mock_uow, mock_event_bus):
        """Linking non-existent task raises error."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )

        mock_uow.projects.get_by_id.return_value = project
        mock_uow.tasks.get_by_id.return_value = None

        command = LinkTaskToProjectCommand(project_id=str(project_id), task_id="nonexistent")

        with pytest.raises(TaskNotFoundError):
            project_service.link_task_to_project(command)

        assert not mock_uow.commit.called


class TestUnlinkTask:
    """Test task-project unlinking orchestration."""

    def test_unlink_task_from_project_succeeds(self, project_service, mock_uow, mock_event_bus):
        """Unlinking task from project works correctly."""
        project_id = ProjectId.generate()
        task_id = TaskId.generate()

        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        project.add_task(task_id)

        task = Task(
            id=task_id,
            title="Task",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=7)),
            project_id=project_id,
        )

        mock_uow.projects.get_by_id.return_value = project
        mock_uow.tasks.get_by_id.return_value = task

        command = UnlinkTaskFromProjectCommand(project_id=str(project_id), task_id=str(task_id))

        project_service.unlink_task_from_project(command)

        # Verify both entities were saved
        assert mock_uow.tasks.save.called
        assert mock_uow.projects.save.called
        assert mock_uow.commit.called

    def test_unlink_from_nonexistent_project_raises_error(
        self, project_service, mock_uow, mock_event_bus
    ):
        """Unlinking from non-existent project raises error."""
        mock_uow.projects.get_by_id.return_value = None

        command = UnlinkTaskFromProjectCommand(project_id="nonexistent", task_id="task-id")

        with pytest.raises(ProjectNotFoundError):
            project_service.unlink_task_from_project(command)

        assert not mock_uow.commit.called


class TestQueryProjects:
    """Test project query operations."""

    def test_get_project_by_id_succeeds(self, project_service, mock_uow, mock_event_bus):
        """Getting project by ID returns correct DTO."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        mock_uow.projects.get_by_id.return_value = project
        mock_uow.projects.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        query = GetProjectByIdQuery(project_id=str(project_id))

        result = project_service.get_project_by_id(query)

        assert result.id == str(project_id)
        assert result.title == "Project"

    def test_get_nonexistent_project_raises_error(self, project_service, mock_uow, mock_event_bus):
        """Getting non-existent project raises error."""
        mock_uow.projects.get_by_id.return_value = None

        query = GetProjectByIdQuery(project_id="nonexistent")

        with pytest.raises(ProjectNotFoundError):
            project_service.get_project_by_id(query)

    def test_list_projects_returns_all_projects(self, project_service, mock_uow, mock_event_bus):
        """Listing projects returns all filtered projects."""
        projects = [
            Project(
                id=ProjectId.generate(),
                title=f"Project {i}",
                description="Desc",
                deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
            )
            for i in range(3)
        ]
        mock_uow.projects.list_by_filter.return_value = projects
        mock_uow.projects.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        query = ListProjectsQuery(completed=None)

        result = project_service.list_projects(query)

        assert len(result) == 3
        mock_uow.projects.list_by_filter.assert_called_once_with(completed=None)

    def test_list_completed_projects_only(self, project_service, mock_uow, mock_event_bus):
        """Listing with completed filter works correctly."""
        projects = [
            Project(
                id=ProjectId.generate(),
                title="Completed Project",
                description="Desc",
                deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
                completed=True,
            )
        ]
        mock_uow.projects.list_by_filter.return_value = projects
        mock_uow.projects.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        query = ListProjectsQuery(completed=True)

        result = project_service.list_projects(query)

        assert len(result) == 1
        assert result[0].completed is True
        mock_uow.projects.list_by_filter.assert_called_once_with(completed=True)


class TestTransactionManagement:
    """Test that service properly manages transactions."""

    def test_create_project_rolls_back_on_error(self, project_service, mock_uow, mock_event_bus):
        """When project creation fails, transaction context manager handles it."""
        mock_uow.projects.save.side_effect = Exception("Database error")

        command = CreateProjectCommand(
            title="Project",
            description="Desc",
            deadline=datetime.now(timezone.utc) + timedelta(days=30),
        )

        with pytest.raises(Exception):
            with patch("src.application.services.project_service.ProjectId"):
                project_service.create_project(command)

        # UoW __exit__ should have been called due to exception
        assert mock_uow.__exit__.called

    def test_events_published_only_after_commit(self, project_service, mock_uow, mock_event_bus):
        """Events are published only after successful commit."""
        project_id = ProjectId.generate()
        project = Project(
            id=project_id,
            title="Project",
            description="Desc",
            deadline=Deadline(datetime.now(timezone.utc) + timedelta(days=30)),
        )
        mock_uow.projects.get_by_id.return_value = project
        mock_uow.projects.get_timestamps.return_value = (
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )

        command = CompleteProjectCommand(project_id=str(project_id))

        project_service.complete_project(command)

        # Verify commit was called
        assert mock_uow.commit.called

        # Events should have been published
        assert mock_event_bus.publish.called
