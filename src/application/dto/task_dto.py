"""Task Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TaskDTO:
    """Data Transfer Object for Task entity.

    Used to transfer task data across application boundaries
    without exposing the domain entity directly.
    """

    id: str
    title: str
    description: str
    deadline: datetime
    completed: bool
    project_id: Optional[str]
    is_overdue: bool
    created_at: datetime
    updated_at: datetime
