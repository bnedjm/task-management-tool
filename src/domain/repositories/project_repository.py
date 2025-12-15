"""Project repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.project import Project
from ..value_objects.ids import ProjectId


class ProjectRepository(ABC):
    """Repository interface for Project aggregate.

    This interface defines the contract for project persistence.
    Concrete implementations will be provided in the infrastructure layer.
    """

    @abstractmethod
    def save(self, project: Project) -> None:
        """Persist a project entity.

        Args:
            project: The project entity to save.
        """
        pass

    @abstractmethod
    def get_by_id(self, project_id: ProjectId) -> Optional[Project]:
        """Retrieve a project by its ID.

        Args:
            project_id: The ID of the project to retrieve.

        Returns:
            Optional[Project]: The project if found, None otherwise.
        """
        pass

    @abstractmethod
    def list_all(self) -> List[Project]:
        """Retrieve all projects.

        Returns:
            List[Project]: List of all projects.
        """
        pass

    @abstractmethod
    def list_by_filter(self, completed: Optional[bool] = None) -> List[Project]:
        """Retrieve projects matching filter criteria.

        Args:
            completed: Filter by completion status (None for all).

        Returns:
            List[Project]: List of projects matching the criteria.
        """
        pass

    @abstractmethod
    def delete(self, project_id: ProjectId) -> None:
        """Delete a project.

        Args:
            project_id: The ID of the project to delete.
        """
        pass
