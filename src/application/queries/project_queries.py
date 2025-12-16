"""Project-related query objects."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetProjectByIdQuery:
    """Query to get a project by its ID."""

    project_id: str


@dataclass
class ListProjectsQuery:
    """Query to list projects with optional filters."""

    completed: Optional[bool] = None
    offset: int = 0
    limit: int = 20
