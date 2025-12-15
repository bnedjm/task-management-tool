"""Error handling middleware for domain exceptions."""

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ...domain.exceptions import (
    DeadlineConstraintViolation,
    DomainException,
    ProjectNotCompletableError,
    ProjectNotFoundError,
    TaskAlreadyCompletedError,
    TaskNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for domain exceptions.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(TaskNotFoundError)
    async def task_not_found_handler(request: Request, exc: TaskNotFoundError):
        """Handle TaskNotFoundError."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "TaskNotFoundError",
                "message": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(ProjectNotFoundError)
    async def project_not_found_handler(request: Request, exc: ProjectNotFoundError):
        """Handle ProjectNotFoundError."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "ProjectNotFoundError",
                "message": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(TaskAlreadyCompletedError)
    async def task_already_completed_handler(request: Request, exc: TaskAlreadyCompletedError):
        """Handle TaskAlreadyCompletedError."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "TaskAlreadyCompletedError",
                "message": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(DeadlineConstraintViolation)
    async def deadline_constraint_handler(request: Request, exc: DeadlineConstraintViolation):
        """Handle DeadlineConstraintViolation."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "DeadlineConstraintViolation",
                "message": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(ProjectNotCompletableError)
    async def project_not_completable_handler(request: Request, exc: ProjectNotCompletableError):
        """Handle ProjectNotCompletableError."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "ProjectNotCompletableError",
                "message": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        """Handle generic DomainException."""
        return JSONResponse(
            status_code=500,
            content={
                "error": exc.__class__.__name__,
                "message": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
