"""Project-related domain exceptions."""

from .base import DomainException


class ProjectNotFoundError(DomainException):
    """Raised when a project cannot be found."""

    def __init__(self, project_id: str):
        """Initialize the exception.

        Args:
            project_id: The ID of the project that was not found.
        """
        self.project_id = project_id
        super().__init__(f"Project with ID '{project_id}' not found")


class DeadlineConstraintViolation(DomainException):
    """Raised when a deadline constraint is violated.

    For example, when a task's deadline would be after its project's deadline.
    """

    def __init__(self, message: str):
        """Initialize the exception.

        Args:
            message: Description of the constraint violation.
        """
        super().__init__(message)


class ProjectNotCompletableError(DomainException):
    """Raised when attempting to complete a project with incomplete tasks."""

    def __init__(self, project_id: str, incomplete_count: int):
        """Initialize the exception.

        Args:
            project_id: The ID of the project that cannot be completed.
            incomplete_count: Number of incomplete tasks remaining.
        """
        self.project_id = project_id
        self.incomplete_count = incomplete_count
        super().__init__(
            f"Cannot complete project '{project_id}': " f"{incomplete_count} task(s) still pending"
        )


class PastDateError(DomainException):
    """Raised when attempting to set a deadline in the past."""

    def __init__(self, deadline: str):
        """Initialize the exception.

        Args:
            deadline: The deadline that was in the past.
        """
        self.deadline = deadline
        super().__init__(f"Deadline cannot be in the past: {deadline}")
