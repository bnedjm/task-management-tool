"""Pydantic schemas for task API endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    """Request schema for creating a new task."""

    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: str = Field(..., description="Task description")
    deadline: datetime = Field(..., description="Task deadline")
    project_id: Optional[str] = Field(None, description="Optional project ID to assign task to")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Implement user authentication",
                "description": "Add JWT-based authentication to the API",
                "deadline": "2025-12-31T23:59:59",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    }


class TaskUpdateRequest(BaseModel):
    """Request schema for updating a task."""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="New task title")
    description: Optional[str] = Field(None, description="New task description")
    deadline: Optional[datetime] = Field(None, description="New task deadline")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Implement OAuth authentication",
                "description": "Add OAuth2 support in addition to JWT",
                "deadline": "2025-12-25T23:59:59",
            }
        }
    }


class TaskResponse(BaseModel):
    """Response schema for task data."""

    id: str = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    deadline: datetime = Field(..., description="Task deadline")
    completed: bool = Field(..., description="Whether task is completed")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    is_overdue: bool = Field(..., description="Whether task is overdue")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Task last update timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Implement user authentication",
                "description": "Add JWT-based authentication to the API",
                "deadline": "2025-12-31T23:59:59",
                "completed": False,
                "project_id": "660e8400-e29b-41d4-a716-446655440000",
                "is_overdue": False,
                "created_at": "2025-12-01T10:00:00",
                "updated_at": "2025-12-10T15:30:00",
            }
        }
    }


class PaginatedTasksResponse(BaseModel):
    """Paginated response schema for tasks."""

    items: List[TaskResponse] = Field(..., description="List of tasks in the current page")
    total: int = Field(..., description="Total number of tasks matching filters")
    offset: int = Field(..., description="Zero-based offset of the current page")
    limit: int = Field(..., description="Maximum items per page")
    has_more: bool = Field(..., description="Whether more items are available")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Implement user authentication",
                        "description": "Add JWT-based authentication to the API",
                        "deadline": "2025-12-31T23:59:59",
                        "completed": False,
                        "project_id": "660e8400-e29b-41d4-a716-446655440000",
                        "is_overdue": False,
                        "created_at": "2025-12-01T10:00:00",
                        "updated_at": "2025-12-10T15:30:00",
                    }
                ],
                "total": 42,
                "offset": 0,
                "limit": 20,
                "has_more": True,
            }
        }
    }
