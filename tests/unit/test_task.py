"""Unit tests for Task entity."""

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.task import Task
from src.domain.events.task_events import (
    TaskAssignedToProjectEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskDeadlineChangedEvent,
    TaskReopenedEvent,
)
from src.domain.exceptions.project_exceptions import DeadlineConstraintViolation
from src.domain.exceptions.task_exceptions import TaskAlreadyCompletedError
from src.domain.value_objects.deadline import Deadline
from src.domain.value_objects.ids import ProjectId, TaskId


class TestTaskCreation:
    """Test task creation and initialization."""

    def test_create_task_emits_event(self):
        """Creating a task should emit TaskCreatedEvent."""
        task_id = TaskId.generate()
        deadline = Deadline(datetime.now(timezone.utc) + timedelta(days=1))

        task = Task.create(
            id=task_id,
            title="Test Task",
            description="Test Description",
            deadline=deadline,
        )

        events = task.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskCreatedEvent)
        assert events[0].task_id == task_id
        assert events[0].title == "Test Task"

    def test_task_initialization(self, task_id, future_deadline):
        """Task can be initialized with required fields."""
        task = Task(
            id=task_id,
            title="My Task",
            description="Task description",
            deadline=future_deadline,
        )

        assert task.id == task_id
        assert task.title == "My Task"
        assert task.description == "Task description"
        assert task.deadline == future_deadline
        assert task.is_completed is False
        assert task.project_id is None


class TestTaskCompletion:
    """Test task completion business logic."""

    def test_complete_task_marks_as_completed(self, task_factory):
        """Completing a task marks it as completed."""
        task = task_factory()

        task.complete()

        assert task.is_completed is True

    def test_complete_task_emits_event(self, task_factory):
        """Completing a task should emit TaskCompletedEvent."""
        task = task_factory()

        task.complete()

        events = task.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskCompletedEvent)
        assert events[0].task_id == task.id

    def test_complete_already_completed_task_raises_error(self, task_factory):
        """Cannot complete an already completed task."""
        task = task_factory()
        task.complete()
        task.collect_events()  # Clear events

        with pytest.raises(TaskAlreadyCompletedError) as exc_info:
            task.complete()

        assert str(task.id) in str(exc_info.value)

    def test_reopen_task(self, task_factory):
        """Reopening a completed task marks it as incomplete."""
        task = task_factory()
        task.complete()
        task.collect_events()  # Clear events

        task.reopen()

        assert task.is_completed is False

    def test_reopen_task_emits_event(self, task_factory):
        """Reopening a task should emit TaskReopenedEvent."""
        task = task_factory()
        task.complete()
        task.collect_events()  # Clear events

        task.reopen()

        events = task.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskReopenedEvent)
        assert events[0].task_id == task.id


class TestTaskProjectAssignment:
    """Test task-project association constraints."""

    def test_assign_task_with_valid_deadline_succeeds(self, task_factory):
        """Task with deadline before project deadline can be assigned."""
        project_id = ProjectId.generate()
        task_deadline = Deadline(datetime(2025, 1, 1))
        project_deadline = Deadline(datetime(2025, 2, 1))

        task = task_factory(deadline=task_deadline)

        task.assign_to_project(project_id, project_deadline)

        assert task.project_id == project_id

    def test_assign_task_with_later_deadline_than_project_fails(self, task_factory):
        """Task deadline cannot be after project deadline."""
        project_id = ProjectId.generate()
        task_deadline = Deadline(datetime(2025, 2, 1))
        project_deadline = Deadline(datetime(2025, 1, 1))

        task = task_factory(deadline=task_deadline)

        with pytest.raises(DeadlineConstraintViolation) as exc_info:
            task.assign_to_project(project_id, project_deadline)

        assert "cannot be after project deadline" in str(exc_info.value)

    def test_assign_task_emits_event(self, task_factory):
        """Assigning task to project emits event."""
        project_id = ProjectId.generate()
        task_deadline = Deadline(datetime(2025, 1, 1))
        project_deadline = Deadline(datetime(2025, 2, 1))

        task = task_factory(deadline=task_deadline)

        task.assign_to_project(project_id, project_deadline)

        events = task.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskAssignedToProjectEvent)
        assert events[0].task_id == task.id
        assert events[0].project_id == project_id


class TestTaskDeadlineAdjustment:
    """Test task deadline modification."""

    def test_adjust_deadline_without_project(self, task_factory):
        """Can adjust deadline when not assigned to project."""
        task = task_factory()
        new_deadline = Deadline(datetime(2025, 6, 1))

        task.adjust_deadline(new_deadline)

        assert task.deadline == new_deadline

    def test_adjust_deadline_within_project_constraint(self, task_factory):
        """Can adjust deadline within project deadline constraint."""
        task = task_factory()
        new_deadline = Deadline(datetime(2025, 1, 15))
        project_deadline = Deadline(datetime(2025, 2, 1))

        task.adjust_deadline(new_deadline, project_deadline)

        assert task.deadline == new_deadline

    def test_adjust_deadline_violating_project_constraint_fails(self, task_factory):
        """Cannot adjust deadline beyond project deadline."""
        task = task_factory()
        new_deadline = Deadline(datetime(2025, 3, 1))
        project_deadline = Deadline(datetime(2025, 2, 1))

        with pytest.raises(DeadlineConstraintViolation):
            task.adjust_deadline(new_deadline, project_deadline)

    def test_adjust_deadline_emits_event(self, task_factory):
        """Adjusting deadline emits event."""
        task = task_factory()
        old_deadline = task.deadline
        new_deadline = Deadline(datetime(2025, 6, 1))

        task.adjust_deadline(new_deadline)

        events = task.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskDeadlineChangedEvent)
        assert events[0].old_deadline == old_deadline
        assert events[0].new_deadline == new_deadline


class TestTaskOverdue:
    """Test overdue status logic."""

    def test_task_is_overdue_when_deadline_passed(self):
        """Task is overdue when deadline is in the past and not completed."""
        past_deadline = Deadline(datetime.now(timezone.utc) - timedelta(days=1))
        task = Task(
            id=TaskId.generate(),
            title="Overdue Task",
            description="Test",
            deadline=past_deadline,
        )

        assert task.is_overdue is True

    def test_completed_task_is_not_overdue(self):
        """Completed task is not considered overdue."""
        past_deadline = Deadline(datetime.now(timezone.utc) - timedelta(days=1))
        task = Task(
            id=TaskId.generate(),
            title="Completed Task",
            description="Test",
            deadline=past_deadline,
            completed=True,
        )

        assert task.is_overdue is False

    def test_future_task_is_not_overdue(self):
        """Task with future deadline is not overdue."""
        future_deadline = Deadline(datetime.now(timezone.utc) + timedelta(days=1))
        task = Task(
            id=TaskId.generate(),
            title="Future Task",
            description="Test",
            deadline=future_deadline,
        )

        assert task.is_overdue is False


class TestTaskUpdate:
    """Test task detail updates."""

    def test_update_title(self, task_factory):
        """Can update task title."""
        task = task_factory(title="Original Title")

        task.update_details(title="New Title")

        assert task.title == "New Title"

    def test_update_description(self, task_factory):
        """Can update task description."""
        task = task_factory(description="Original Description")

        task.update_details(description="New Description")

        assert task.description == "New Description"

    def test_update_both_title_and_description(self, task_factory):
        """Can update both title and description."""
        task = task_factory(title="Old", description="Old Desc")

        task.update_details(title="New", description="New Desc")

        assert task.title == "New"
        assert task.description == "New Desc"
