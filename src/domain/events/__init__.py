"""Domain events for event-driven business logic."""

from .base import DomainEvent
from .project_events import (
    ProjectCompletedEvent,
    ProjectCreatedEvent,
    ProjectDeadlineChangedEvent,
    ProjectReopenedEvent,
)
from .task_events import (
    TaskAssignedToProjectEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskDeadlineChangedEvent,
    TaskRemovedFromProjectEvent,
    TaskReopenedEvent,
)

__all__ = [
    "DomainEvent",
    "TaskCompletedEvent",
    "TaskCreatedEvent",
    "TaskAssignedToProjectEvent",
    "TaskDeadlineChangedEvent",
    "TaskRemovedFromProjectEvent",
    "TaskReopenedEvent",
    "ProjectCompletedEvent",
    "ProjectCreatedEvent",
    "ProjectDeadlineChangedEvent",
    "ProjectReopenedEvent",
]
