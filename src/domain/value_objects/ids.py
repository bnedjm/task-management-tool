"""Value objects for entity identifiers."""

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskId:
    """Unique identifier for a Task entity."""

    value: str

    @classmethod
    def generate(cls) -> "TaskId":
        """Generate a new unique task identifier.

        Returns:
            TaskId: A new unique task identifier.
        """
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls, id_str: str) -> "TaskId":
        """Create TaskId from string representation.

        Args:
            id_str: String representation of the task ID.

        Returns:
            TaskId: Task identifier instance.
        """
        return cls(value=id_str)

    def __str__(self) -> str:
        """String representation of the task ID."""
        return self.value

    def __eq__(self, other: Any) -> bool:
        """Check equality with another TaskId."""
        if not isinstance(other, TaskId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """Hash implementation for TaskId."""
        return hash(self.value)


@dataclass(frozen=True)
class ProjectId:
    """Unique identifier for a Project entity."""

    value: str

    @classmethod
    def generate(cls) -> "ProjectId":
        """Generate a new unique project identifier.

        Returns:
            ProjectId: A new unique project identifier.
        """
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls, id_str: str) -> "ProjectId":
        """Create ProjectId from string representation.

        Args:
            id_str: String representation of the project ID.

        Returns:
            ProjectId: Project identifier instance.
        """
        return cls(value=id_str)

    def __str__(self) -> str:
        """String representation of the project ID."""
        return self.value

    def __eq__(self, other: Any) -> bool:
        """Check equality with another ProjectId."""
        if not isinstance(other, ProjectId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """Hash implementation for ProjectId."""
        return hash(self.value)
