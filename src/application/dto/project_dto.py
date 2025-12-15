"""Project Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProjectDTO:
    """Data Transfer Object for Project entity.

    Used to transfer project data across application boundaries
    without exposing the domain entity directly.
    """

    id: str
    title: str
    description: str
    deadline: datetime
    completed: bool
    total_task_count: int
    completed_task_count: int
    created_at: datetime
    updated_at: datetime
