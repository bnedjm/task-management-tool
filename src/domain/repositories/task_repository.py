"""Task repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.task import Task
from ..value_objects.ids import ProjectId, TaskId


class TaskRepository(ABC):
    """Repository interface for Task aggregate.

    This interface defines the contract for task persistence.
    Concrete implementations will be provided in the infrastructure layer.
    """

    @abstractmethod
    def save(self, task: Task) -> None:
        """Persist a task entity.

        Args:
            task: The task entity to save.
        """
        pass

    @abstractmethod
    def get_by_id(self, task_id: TaskId) -> Optional[Task]:
        """Retrieve a task by its ID.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            Optional[Task]: The task if found, None otherwise.
        """
        pass

    @abstractmethod
    def list_all(self) -> List[Task]:
        """Retrieve all tasks.

        Returns:
            List[Task]: List of all tasks.
        """
        pass

    @abstractmethod
    def list_by_project(self, project_id: ProjectId) -> List[Task]:
        """Retrieve all tasks for a specific project.

        Args:
            project_id: The ID of the project.

        Returns:
            List[Task]: List of tasks belonging to the project.
        """
        pass

    @abstractmethod
    def list_by_filter(
        self,
        completed: Optional[bool] = None,
        overdue: bool = False,
    ) -> List[Task]:
        """Retrieve tasks matching filter criteria.

        Args:
            completed: Filter by completion status (None for all).
            overdue: Filter for overdue tasks only.

        Returns:
            List[Task]: List of tasks matching the criteria.
        """
        pass

    @abstractmethod
    def delete(self, task_id: TaskId) -> None:
        """Delete a task.

        Args:
            task_id: The ID of the task to delete.
        """
        pass
