"""Repository interfaces - Domain layer contracts."""

from .project_repository import ProjectRepository
from .task_repository import TaskRepository

__all__ = ["TaskRepository", "ProjectRepository"]
