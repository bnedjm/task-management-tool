"""Task-related domain exceptions."""

from .base import DomainException


class TaskNotFoundError(DomainException):
    """Raised when a task cannot be found."""

    def __init__(self, task_id: str):
        """Initialize the exception.

        Args:
            task_id: The ID of the task that was not found.
        """
        self.task_id = task_id
        super().__init__(f"Task with ID '{task_id}' not found")


class TaskAlreadyCompletedError(DomainException):
    """Raised when attempting to complete an already completed task."""

    def __init__(self, task_id: str):
        """Initialize the exception.

        Args:
            task_id: The ID of the task that is already completed.
        """
        self.task_id = task_id
        super().__init__(f"Task '{task_id}' is already completed")
