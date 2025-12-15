"""Task entity - Aggregate root for task management."""

from datetime import datetime, timezone
from typing import List, Optional

from ..events.base import DomainEvent
from ..events.task_events import (
    TaskAssignedToProjectEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskDeadlineChangedEvent,
    TaskReopenedEvent,
)
from ..exceptions.task_exceptions import TaskAlreadyCompletedError
from ..value_objects.deadline import Deadline
from ..value_objects.ids import ProjectId, TaskId


class Task:
    """Task aggregate root.

    Encapsulates all business logic related to task management.
    All business rules are enforced within this entity to maintain
    consistency and domain invariants.
    """

    def __init__(
        self,
        id: TaskId,
        title: str,
        description: str,
        deadline: Deadline,
        completed: bool = False,
        project_id: Optional[ProjectId] = None,
    ):
        """Initialize a Task entity.

        Args:
            id: Unique identifier for the task.
            title: Title of the task.
            description: Detailed description of the task.
            deadline: Deadline for task completion.
            completed: Whether the task is completed.
            project_id: Optional project association.
        """
        self._id = id
        self._title = title
        self._description = description
        self._deadline = deadline
        self._completed = completed
        self._project_id = project_id
        self._events: List[DomainEvent] = []

    @classmethod
    def create(
        cls,
        id: TaskId,
        title: str,
        description: str,
        deadline: Deadline,
        project_id: Optional[ProjectId] = None,
    ) -> "Task":
        """Factory method to create a new task with creation event.

        Args:
            id: Unique identifier for the task.
            title: Title of the task.
            description: Detailed description of the task.
            deadline: Deadline for task completion.
            project_id: Optional project association.

        Returns:
            Task: Newly created task instance.
        """
        task = cls(
            id=id,
            title=title,
            description=description,
            deadline=deadline,
            completed=False,
            project_id=project_id,
        )
        task._add_event(
            TaskCreatedEvent(
                task_id=id,
                title=title,
                deadline=deadline,
                project_id=project_id,
            )
        )
        return task

    def complete(self) -> None:
        """Mark task as completed.

        Raises:
            TaskAlreadyCompletedError: If task is already completed.
        """
        if self._completed:
            raise TaskAlreadyCompletedError(str(self._id))

        self._completed = True
        self._add_event(
            TaskCompletedEvent(
                task_id=self._id,
                completed_at=datetime.now(timezone.utc),
                project_id=self._project_id,
            )
        )

    def reopen(self) -> None:
        """Reopen a completed task.

        This allows a completed task to be marked as incomplete again,
        which may trigger project reopening if the task belongs to a project.
        """
        if not self._completed:
            return

        self._completed = False
        self._add_event(
            TaskReopenedEvent(
                task_id=self._id,
                project_id=self._project_id,
            )
        )

    def assign_to_project(self, project_id: ProjectId, project_deadline: Deadline) -> None:
        """Assign task to a project.

        Args:
            project_id: The ID of the project to assign to.
            project_deadline: The deadline of the project.

        Raises:
            DeadlineConstraintViolation: If task deadline is after project deadline.
        """
        from ..exceptions.project_exceptions import DeadlineConstraintViolation

        if self._deadline.is_after(project_deadline):
            raise DeadlineConstraintViolation(
                f"Task deadline {self._deadline} cannot be after "
                f"project deadline {project_deadline}"
            )

        self._project_id = project_id
        self._add_event(
            TaskAssignedToProjectEvent(
                task_id=self._id,
                project_id=project_id,
            )
        )

    def adjust_deadline(
        self, new_deadline: Deadline, project_deadline: Optional[Deadline] = None
    ) -> None:
        """Update task deadline with validation.

        Args:
            new_deadline: The new deadline for the task.
            project_deadline: Project deadline if task is assigned to a project.

        Raises:
            DeadlineConstraintViolation: If new deadline violates project constraint.
        """
        from ..exceptions.project_exceptions import DeadlineConstraintViolation

        if project_deadline and new_deadline.is_after(project_deadline):
            raise DeadlineConstraintViolation(
                f"Task deadline {new_deadline} cannot be after "
                f"project deadline {project_deadline}"
            )

        old_deadline = self._deadline
        self._deadline = new_deadline
        self._add_event(
            TaskDeadlineChangedEvent(
                task_id=self._id,
                old_deadline=old_deadline,
                new_deadline=new_deadline,
                project_id=self._project_id,
            )
        )

    def update_details(
        self, title: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        """Update task title and/or description.

        Args:
            title: New title for the task (optional).
            description: New description for the task (optional).
        """
        if title is not None:
            self._title = title
        if description is not None:
            self._description = description

    def _add_event(self, event: DomainEvent) -> None:
        """Add a domain event to the event list.

        Args:
            event: The domain event to add.
        """
        self._events.append(event)

    def collect_events(self) -> List[DomainEvent]:
        """Collect and clear all domain events.

        Returns:
            List[DomainEvent]: List of domain events that occurred.
        """
        events = self._events.copy()
        self._events.clear()
        return events

    @property
    def id(self) -> TaskId:
        """Get task ID."""
        return self._id

    @property
    def title(self) -> str:
        """Get task title."""
        return self._title

    @property
    def description(self) -> str:
        """Get task description."""
        return self._description

    @property
    def deadline(self) -> Deadline:
        """Get task deadline."""
        return self._deadline

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self._completed

    @property
    def project_id(self) -> Optional[ProjectId]:
        """Get associated project ID."""
        return self._project_id

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return not self._completed and self._deadline.is_overdue()

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Task):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self._id)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Task(id={self._id}, title='{self._title}', "
            f"completed={self._completed}, deadline={self._deadline})"
        )
