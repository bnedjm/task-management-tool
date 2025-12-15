"""Pydantic schemas for project API endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Request schema for creating a new project."""

    title: str = Field(..., min_length=1, max_length=200, description="Project title")
    description: str = Field(..., description="Project description")
    deadline: datetime = Field(..., description="Project deadline")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "API Development Phase 1",
                "description": "Develop core API endpoints and authentication",
                "deadline": "2025-12-31T23:59:59",
            }
        }
    }


class ProjectUpdateRequest(BaseModel):
    """Request schema for updating a project."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="New project title"
    )
    description: Optional[str] = Field(None, description="New project description")
    deadline: Optional[datetime] = Field(None, description="New project deadline")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "API Development Phase 1 - Extended",
                "deadline": "2026-01-15T23:59:59",
            }
        }
    }


class ProjectResponse(BaseModel):
    """Response schema for project data."""

    id: str = Field(..., description="Project ID")
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Project description")
    deadline: datetime = Field(..., description="Project deadline")
    completed: bool = Field(..., description="Whether project is completed")
    total_task_count: int = Field(..., description="Total number of tasks")
    completed_task_count: int = Field(..., description="Number of completed tasks")
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Project last update timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "title": "API Development Phase 1",
                "description": "Develop core API endpoints and authentication",
                "deadline": "2025-12-31T23:59:59",
                "completed": False,
                "total_task_count": 5,
                "completed_task_count": 3,
                "created_at": "2025-11-01T09:00:00",
                "updated_at": "2025-12-10T14:20:00",
            }
        }
    }
