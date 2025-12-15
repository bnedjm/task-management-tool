"""Pydantic schemas for error responses."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: str = Field(..., description="ISO timestamp of when error occurred")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "TaskNotFoundError",
                "message": "Task with ID 'abc123' not found",
                "timestamp": "2025-12-12T10:30:00",
            }
        }
    }
