"""Project-related domain events."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ..value_objects.deadline import Deadline
from ..value_objects.ids import ProjectId, TaskId
from .base import DomainEvent


@dataclass
class ProjectCreatedEvent(DomainEvent):
    """Event raised when a new project is created."""

    project_id: ProjectId
    title: str
    deadline: Deadline

    def __post_init__(self):
        """Initialize base class."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "project_id": str(self.project_id),
                "title": self.title,
                "deadline": self.deadline.to_string(),
            }
        )
        return base


@dataclass
class ProjectCompletedEvent(DomainEvent):
    """Event raised when a project is marked as completed."""

    project_id: ProjectId

    def __post_init__(self):
        """Initialize base class."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "project_id": str(self.project_id),
            }
        )
        return base


@dataclass
class ProjectReopenedEvent(DomainEvent):
    """Event raised when a completed project is reopened."""

    project_id: ProjectId
    triggering_task_id: TaskId

    def __post_init__(self):
        """Initialize base class."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "project_id": str(self.project_id),
                "triggering_task_id": str(self.triggering_task_id),
            }
        )
        return base


@dataclass
class ProjectDeadlineChangedEvent(DomainEvent):
    """Event raised when a project's deadline is updated.

    This event is particularly important as it may trigger
    cascading updates to task deadlines that violate the new constraint.
    """

    project_id: ProjectId
    old_deadline: Deadline
    new_deadline: Deadline
    affected_task_ids: List[TaskId]

    def __post_init__(self):
        """Initialize base class."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "project_id": str(self.project_id),
                "old_deadline": self.old_deadline.to_string(),
                "new_deadline": self.new_deadline.to_string(),
                "affected_task_ids": [str(tid) for tid in self.affected_task_ids],
            }
        )
        return base
