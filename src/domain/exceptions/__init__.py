"""Domain-specific exceptions."""

from .base import DomainException
from .project_exceptions import (
    DeadlineConstraintViolation,
    ProjectNotCompletableError,
    ProjectNotFoundError,
)
from .task_exceptions import TaskAlreadyCompletedError, TaskNotFoundError

__all__ = [
    "DomainException",
    "TaskAlreadyCompletedError",
    "TaskNotFoundError",
    "DeadlineConstraintViolation",
    "ProjectNotCompletableError",
    "ProjectNotFoundError",
]
