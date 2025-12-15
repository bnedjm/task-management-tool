"""Project entity - Aggregate root for project management."""

from typing import List, Set

from ..events.base import DomainEvent
from ..events.project_events import (
    ProjectCompletedEvent,
    ProjectCreatedEvent,
    ProjectDeadlineChangedEvent,
    ProjectReopenedEvent,
)
from ..exceptions.project_exceptions import ProjectNotCompletableError
from ..value_objects.deadline import Deadline
from ..value_objects.ids import ProjectId, TaskId


class Project:
    """Project aggregate root.

    Manages task associations and enforces project-level business rules.
    A project can only be completed when all its tasks are completed.
    """

    def __init__(
        self,
        id: ProjectId,
        title: str,
        description: str,
        deadline: Deadline,
        completed: bool = False,
    ):
        """Initialize a Project entity.

        Args:
            id: Unique identifier for the project.
            title: Title of the project.
            description: Detailed description of the project.
            deadline: Deadline for project completion.
            completed: Whether the project is completed.
        """
        self._id = id
        self._title = title
        self._description = description
        self._deadline = deadline
        self._completed = completed
        self._task_ids: Set[TaskId] = set()
        self._completed_task_ids: Set[TaskId] = set()
        self._events: List[DomainEvent] = []

    @classmethod
    def create(
        cls,
        id: ProjectId,
        title: str,
        description: str,
        deadline: Deadline,
    ) -> "Project":
        """Factory method to create a new project with creation event.

        Args:
            id: Unique identifier for the project.
            title: Title of the project.
            description: Detailed description of the project.
            deadline: Deadline for project completion.

        Returns:
            Project: Newly created project instance.
        """
        project = cls(
            id=id,
            title=title,
            description=description,
            deadline=deadline,
            completed=False,
        )
        project._add_event(
            ProjectCreatedEvent(
                project_id=id,
                title=title,
                deadline=deadline,
            )
        )
        return project

    def add_task(self, task_id: TaskId, is_completed: bool = False) -> None:
        """Add a task to this project.

        If the project is completed and the task being added is incomplete,
        the project will be automatically reopened since there's incomplete work.

        Args:
            task_id: ID of the task to add.
            is_completed: Whether the task is already completed. If True,
                the project won't be reopened even if it's currently completed.
        """
        self._task_ids.add(task_id)

        # If project is completed and we're adding an incomplete task, reopen it
        # If the task is already completed, don't reopen the project
        if self._completed and not is_completed:
            self._completed = False
            self._add_event(
                ProjectReopenedEvent(
                    project_id=self._id,
                    triggering_task_id=task_id,
                )
            )

    def _add_task_for_reconstruction(self, task_id: TaskId) -> None:
        """Add a task without side effects (for repository reconstruction).

        This method is used internally by repositories when reconstructing
        a project from the database. It doesn't trigger reopening logic.

        Args:
            task_id: ID of the task to add.
        """
        self._task_ids.add(task_id)

    def remove_task(self, task_id: TaskId) -> None:
        """Remove a task from this project.

        Args:
            task_id: ID of the task to remove.
        """
        self._task_ids.discard(task_id)
        self._completed_task_ids.discard(task_id)

    def mark_task_completed(self, task_id: TaskId) -> None:
        """Mark a task as completed.

        Args:
            task_id: ID of the completed task.
        """
        if task_id in self._task_ids:
            self._completed_task_ids.add(task_id)

    def mark_task_reopened(self, task_id: TaskId) -> None:
        """Mark a task as reopened (no longer completed).

        Args:
            task_id: ID of the reopened task.
        """
        self._completed_task_ids.discard(task_id)

    def update_deadline(self, new_deadline: Deadline, violating_task_ids: List[TaskId]) -> None:
        """Update project deadline.

        This emits an event with affected tasks that violate the new deadline.

        Args:
            new_deadline: The new deadline for the project.
            violating_task_ids: List of task IDs that violate the new deadline.
        """
        old_deadline = self._deadline
        self._deadline = new_deadline
        self._add_event(
            ProjectDeadlineChangedEvent(
                project_id=self._id,
                old_deadline=old_deadline,
                new_deadline=new_deadline,
                affected_task_ids=violating_task_ids,
            )
        )

    def complete(self) -> None:
        """Mark project as completed.

        Can only be completed when all tasks are completed.

        Raises:
            ProjectNotCompletableError: If not all tasks are completed.
        """
        if not self.can_be_completed():
            incomplete_count = len(self._task_ids) - len(self._completed_task_ids)
            raise ProjectNotCompletableError(str(self._id), incomplete_count)

        self._completed = True
        self._add_event(ProjectCompletedEvent(project_id=self._id))

    def reopen_due_to_task(self, task_id: TaskId) -> None:
        """Reopen project when a completed task is reopened.

        Args:
            task_id: ID of the task that triggered the reopening.
        """
        if self._completed and task_id in self._task_ids:
            self._completed = False
            self._add_event(
                ProjectReopenedEvent(
                    project_id=self._id,
                    triggering_task_id=task_id,
                )
            )

    def can_be_completed(self) -> bool:
        """Check if project can be completed.

        Returns:
            bool: True if all tasks are completed, False otherwise.
        """
        if not self._task_ids:
            return True
        return len(self._completed_task_ids) == len(self._task_ids)

    def update_details(self, title: str | None = None, description: str | None = None) -> None:
        """Update project title and/or description.

        Args:
            title: New title for the project (optional).
            description: New description for the project (optional).
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
    def id(self) -> ProjectId:
        """Get project ID."""
        return self._id

    @property
    def title(self) -> str:
        """Get project title."""
        return self._title

    @property
    def description(self) -> str:
        """Get project description."""
        return self._description

    @property
    def deadline(self) -> Deadline:
        """Get project deadline."""
        return self._deadline

    @property
    def is_completed(self) -> bool:
        """Check if project is completed."""
        return self._completed

    @property
    def task_ids(self) -> Set[TaskId]:
        """Get set of task IDs associated with this project."""
        return self._task_ids.copy()

    @property
    def completed_task_count(self) -> int:
        """Get count of completed tasks."""
        return len(self._completed_task_ids)

    @property
    def total_task_count(self) -> int:
        """Get total count of tasks."""
        return len(self._task_ids)

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Project):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self._id)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Project(id={self._id}, title='{self._title}', "
            f"completed={self._completed}, tasks={len(self._task_ids)})"
        )
