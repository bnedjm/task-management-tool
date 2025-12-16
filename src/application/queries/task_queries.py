"""Task-related query objects."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetTaskByIdQuery:
    """Query to get a task by its ID."""

    task_id: str


@dataclass
class ListTasksQuery:
    """Query to list tasks with optional filters."""

    completed: Optional[bool] = None
    overdue: Optional[bool] = None
    project_id: Optional[str] = None
    offset: int = 0
    limit: int = 20
