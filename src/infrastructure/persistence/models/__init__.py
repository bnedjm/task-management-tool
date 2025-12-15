"""ORM models - Separate from domain entities."""

from .project_model import ProjectModel
from .task_model import TaskModel

__all__ = ["TaskModel", "ProjectModel"]
