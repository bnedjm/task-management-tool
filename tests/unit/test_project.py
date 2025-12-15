"""Unit tests for Project entity."""

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.project import Project
from src.domain.events.project_events import (
    ProjectCompletedEvent,
    ProjectCreatedEvent,
    ProjectDeadlineChangedEvent,
    ProjectReopenedEvent,
)
from src.domain.exceptions.project_exceptions import ProjectNotCompletableError
from src.domain.value_objects.deadline import Deadline
from src.domain.value_objects.ids import ProjectId, TaskId


class TestProjectCreation:
    """Test project creation and initialization."""

    def test_create_project_emits_event(self):
        """Creating a project should emit ProjectCreatedEvent."""
        project_id = ProjectId.generate()
        deadline = Deadline(datetime.now(timezone.utc) + timedelta(days=30))

        project = Project.create(
            id=project_id,
            title="Test Project",
            description="Test Description",
            deadline=deadline,
        )

        events = project.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectCreatedEvent)
        assert events[0].project_id == project_id
        assert events[0].title == "Test Project"

    def test_project_initialization(self, project_id, future_deadline):
        """Project can be initialized with required fields."""
        project = Project(
            id=project_id,
            title="My Project",
            description="Project description",
            deadline=future_deadline,
        )

        assert project.id == project_id
        assert project.title == "My Project"
        assert project.description == "Project description"
        assert project.deadline == future_deadline
        assert project.is_completed is False
        assert project.total_task_count == 0


class TestProjectTaskManagement:
    """Test project task association management."""

    def test_add_task_to_project(self, project_factory):
        """Can add task to project."""
        project = project_factory()
        task_id = TaskId.generate()

        project.add_task(task_id)

        assert task_id in project.task_ids
        assert project.total_task_count == 1

    def test_remove_task_from_project(self, project_factory):
        """Can remove task from project."""
        project = project_factory()
        task_id = TaskId.generate()
        project.add_task(task_id)

        project.remove_task(task_id)

        assert task_id not in project.task_ids
        assert project.total_task_count == 0

    def test_mark_task_completed(self, project_factory):
        """Can mark task as completed in project."""
        project = project_factory()
        task_id = TaskId.generate()
        project.add_task(task_id)

        project.mark_task_completed(task_id)

        assert project.completed_task_count == 1

    def test_mark_task_reopened(self, project_factory):
        """Can mark task as reopened in project."""
        project = project_factory()
        task_id = TaskId.generate()
        project.add_task(task_id)
        project.mark_task_completed(task_id)

        project.mark_task_reopened(task_id)

        assert project.completed_task_count == 0


class TestProjectCompletion:
    """Test project completion lifecycle."""

    def test_complete_project_with_all_tasks_completed(self, project_factory):
        """Can complete project when all tasks are completed."""
        project = project_factory()
        task1_id = TaskId.generate()
        task2_id = TaskId.generate()

        project.add_task(task1_id)
        project.add_task(task2_id)
        project.mark_task_completed(task1_id)
        project.mark_task_completed(task2_id)

        project.complete()

        assert project.is_completed is True

    def test_complete_project_with_no_tasks(self, project_factory):
        """Can complete project with no tasks."""
        project = project_factory()

        project.complete()

        assert project.is_completed is True

    def test_complete_project_with_incomplete_tasks_fails(self, project_factory):
        """Cannot complete project with pending tasks."""
        project = project_factory()
        task1_id = TaskId.generate()
        task2_id = TaskId.generate()

        project.add_task(task1_id)
        project.add_task(task2_id)
        project.mark_task_completed(task1_id)
        # task2 still incomplete

        with pytest.raises(ProjectNotCompletableError) as exc_info:
            project.complete()

        assert "1 task(s) still pending" in str(exc_info.value)

    def test_complete_project_emits_event(self, project_factory):
        """Completing project emits event."""
        project = project_factory()

        project.complete()

        events = project.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectCompletedEvent)
        assert events[0].project_id == project.id

    def test_can_be_completed_with_all_tasks_done(self, project_factory):
        """can_be_completed returns True when all tasks completed."""
        project = project_factory()
        task_id = TaskId.generate()
        project.add_task(task_id)
        project.mark_task_completed(task_id)

        assert project.can_be_completed() is True

    def test_can_be_completed_with_incomplete_tasks(self, project_factory):
        """can_be_completed returns False with incomplete tasks."""
        project = project_factory()
        task_id = TaskId.generate()
        project.add_task(task_id)

        assert project.can_be_completed() is False


class TestProjectReopening:
    """Test project reopening when tasks are reopened."""

    def test_reopen_completed_project_due_to_task(self, project_factory):
        """Reopening a task reopens the completed project."""
        project = project_factory()
        task_id = TaskId.generate()

        project.add_task(task_id)
        project.mark_task_completed(task_id)
        project.complete()
        project.collect_events()  # Clear events

        assert project.is_completed is True

        project.reopen_due_to_task(task_id)

        assert project.is_completed is False

    def test_reopen_project_emits_event(self, project_factory):
        """Reopening project emits event."""
        project = project_factory()
        task_id = TaskId.generate()

        project.add_task(task_id)
        project.mark_task_completed(task_id)
        project.complete()
        project.collect_events()  # Clear events

        project.reopen_due_to_task(task_id)

        events = project.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectReopenedEvent)
        assert events[0].project_id == project.id
        assert events[0].triggering_task_id == task_id

    def test_reopen_does_not_affect_incomplete_project(self, project_factory):
        """Reopening doesn't affect already incomplete project."""
        project = project_factory()
        task_id = TaskId.generate()
        project.add_task(task_id)

        project.reopen_due_to_task(task_id)

        # Should not emit event as project wasn't completed
        events = project.collect_events()
        assert len(events) == 0


class TestProjectDeadlineUpdate:
    """Test event-driven deadline update logic."""

    def test_update_deadline_emits_event(self, project_factory):
        """Updating deadline emits event."""
        project = project_factory()
        old_deadline = project.deadline
        new_deadline = Deadline(datetime(2025, 6, 1))

        project.update_deadline(new_deadline, [])

        events = project.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectDeadlineChangedEvent)
        assert events[0].old_deadline == old_deadline
        assert events[0].new_deadline == new_deadline

    def test_update_deadline_with_affected_tasks(self, project_factory):
        """Updating deadline includes affected task IDs in event."""
        project = project_factory()
        task1_id = TaskId.generate()
        task2_id = TaskId.generate()

        new_deadline = Deadline(datetime(2025, 2, 1))

        project.update_deadline(new_deadline, [task1_id, task2_id])

        events = project.collect_events()
        deadline_event = events[0]

        assert task1_id in deadline_event.affected_task_ids
        assert task2_id in deadline_event.affected_task_ids

    def test_update_deadline_updates_value(self, project_factory):
        """Updating deadline changes the deadline value."""
        project = project_factory()
        new_deadline = Deadline(datetime(2025, 6, 1))

        project.update_deadline(new_deadline, [])

        assert project.deadline == new_deadline


class TestProjectUpdate:
    """Test project detail updates."""

    def test_update_title(self, project_factory):
        """Can update project title."""
        project = project_factory(title="Original Title")

        project.update_details(title="New Title")

        assert project.title == "New Title"

    def test_update_description(self, project_factory):
        """Can update project description."""
        project = project_factory(description="Original Description")

        project.update_details(description="New Description")

        assert project.description == "New Description"

    def test_update_both_title_and_description(self, project_factory):
        """Can update both title and description."""
        project = project_factory(title="Old", description="Old Desc")

        project.update_details(title="New", description="New Desc")

        assert project.title == "New"
        assert project.description == "New Desc"
