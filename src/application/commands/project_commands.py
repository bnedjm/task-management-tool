"""Project-related command objects."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CreateProjectCommand:
    """Command to create a new project."""

    title: str
    description: str
    deadline: datetime


@dataclass
class UpdateProjectCommand:
    """Command to update project details."""

    project_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None


@dataclass
class CompleteProjectCommand:
    """Command to mark a project as completed."""

    project_id: str


@dataclass
class DeleteProjectCommand:
    """Command to delete a project."""

    project_id: str


@dataclass
class LinkTaskToProjectCommand:
    """Command to link a task to a project."""

    project_id: str
    task_id: str


@dataclass
class UnlinkTaskFromProjectCommand:
    """Command to unlink a task from a project."""

    project_id: str
    task_id: str
