"""Task-related domain events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from ..value_objects.deadline import Deadline
from ..value_objects.ids import ProjectId, TaskId
from .base import DomainEvent


@dataclass
class TaskCreatedEvent(DomainEvent):
    """Event raised when a new task is created."""

    task_id: TaskId
    title: str
    deadline: Deadline
    project_id: Optional[ProjectId] = None

    def __post_init__(self):
        """Initialize base class."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "task_id": str(self.task_id),
                "title": self.title,
                "deadline": self.deadline.to_string(),
                "project_id": str(self.project_id) if self.project_id else None,
            }
        )
        return base


@dataclass
class TaskCompletedEvent(DomainEvent):
    """Event raised when a task is marked as completed."""

    task_id: TaskId
    completed_at: datetime
    project_id: Optional[ProjectId] = None

    def __post_init__(self):
        """Initialize base class."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "task_id": str(self.task_id),
                "completed_at": self.completed_at.isoformat(),
                "project_id": str(self.project_id) if self.project_id else None,
            }
        )
        return base


@dataclass
class TaskReopenedEvent(DomainEvent):
    """Event raised when a completed task is reopened."""

    task_id: TaskId
    project_id: Optional[ProjectId] = None

    def __post_init__(self):
        """Initialize base class."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "task_id": str(self.task_id),
                "project_id": str(self.project_id) if self.project_id else None,
            }
        )
        return base


@dataclass
class TaskAssignedToProjectEvent(DomainEvent):
    """Event raised when a task is assigned to a project."""

    task_id: TaskId
    project_id: ProjectId

    def __post_init__(self):
        """Initialize base class."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "task_id": str(self.task_id),
                "project_id": str(self.project_id),
            }
        )
        return base


@dataclass
class TaskDeadlineChangedEvent(DomainEvent):
    """Event raised when a task's deadline is changed."""

    task_id: TaskId
    old_deadline: Deadline
    new_deadline: Deadline
    project_id: Optional[ProjectId] = None

    def __post_init__(self):
        """Initialize base class."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "task_id": str(self.task_id),
                "old_deadline": self.old_deadline.to_string(),
                "new_deadline": self.new_deadline.to_string(),
                "project_id": str(self.project_id) if self.project_id else None,
            }
        )
        return base


@dataclass
class TaskRemovedFromProjectEvent(DomainEvent):
    """Event raised when a task is removed from a project (deleted or unlinked)."""

    task_id: TaskId
    project_id: ProjectId

    def __post_init__(self):
        """Initialize base class."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "task_id": str(self.task_id),
                "project_id": str(self.project_id),
            }
        )
        return base
