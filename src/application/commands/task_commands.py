"""Task-related command objects."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CreateTaskCommand:
    """Command to create a new task."""

    title: str
    description: str
    deadline: datetime
    project_id: Optional[str] = None


@dataclass
class UpdateTaskCommand:
    """Command to update task details."""

    task_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None


@dataclass
class CompleteTaskCommand:
    """Command to mark a task as completed."""

    task_id: str


@dataclass
class ReopenTaskCommand:
    """Command to reopen a completed task."""

    task_id: str


@dataclass
class DeleteTaskCommand:
    """Command to delete a task."""

    task_id: str
