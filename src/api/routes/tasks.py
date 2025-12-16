"""Task API endpoints."""

from typing import Optional

from fastapi import APIRouter, Query, status

from ...application.commands.task_commands import (
    CompleteTaskCommand,
    CreateTaskCommand,
    DeleteTaskCommand,
    ReopenTaskCommand,
    UpdateTaskCommand,
)
from ...application.dto.task_dto import TaskDTO
from ...application.queries.task_queries import GetTaskByIdQuery, ListTasksQuery
from ..dependencies import get_task_service
from ..schemas.task_schemas import (
    PaginatedTasksResponse,
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _dto_to_response(dto: TaskDTO) -> TaskResponse:
    """Convert DTO to API response.

    Args:
        dto: Task DTO.

    Returns:
        TaskResponse: API response model.
    """
    return TaskResponse(
        id=dto.id,
        title=dto.title,
        description=dto.description,
        deadline=dto.deadline,
        completed=dto.completed,
        project_id=dto.project_id,
        is_overdue=dto.is_overdue,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description=(
        "Create a new task with title, description, and deadline. "
        "Optionally assign to a project."
    ),
)
def create_task(request: TaskCreateRequest) -> TaskResponse:
    """Create a new task.

    Args:
        request: Task creation request.

    Returns:
        TaskResponse: Created task data.

    Raises:
        ProjectNotFoundError: If specified project doesn't exist.
        DeadlineConstraintViolation: If task deadline is after project deadline.
    """
    task_service = get_task_service()
    command = CreateTaskCommand(
        title=request.title,
        description=request.description,
        deadline=request.deadline,
        project_id=request.project_id,
    )
    task_id = task_service.create_task(command)

    # Retrieve and return the created task
    query = GetTaskByIdQuery(task_id=task_id)
    task_dto = task_service.get_task_by_id(query)
    return _dto_to_response(task_dto)


@router.get(
    "",
    response_model=PaginatedTasksResponse,
    summary="List tasks",
    description="List all tasks with optional filters for completion status, overdue, and project.",
)
def list_tasks(
    completed: Optional[bool] = None,
    overdue: Optional[bool] = None,
    project_id: Optional[str] = None,
    offset: int = Query(0, ge=0, description="Zero-based offset"),
    limit: int = Query(20, gt=0, le=100, description="Maximum items per page"),
) -> PaginatedTasksResponse:
    """List tasks with optional filters.

    Args:
        completed: Filter by completion status (None for all,
            True for completed, False for not completed).
        overdue: Filter for overdue tasks only (None for all,
            True for overdue, False for not overdue).
        project_id: Filter by project ID.

    Returns:
        List[TaskResponse]: List of tasks matching criteria.
    """
    task_service = get_task_service()
    query = ListTasksQuery(
        completed=completed,
        overdue=overdue,
        project_id=project_id,
        offset=offset,
        limit=limit,
    )
    result = task_service.list_tasks(query)
    return PaginatedTasksResponse(
        items=[_dto_to_response(task) for task in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
        has_more=result.has_more,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID",
    description="Retrieve a specific task by its ID.",
)
def get_task(task_id: str) -> TaskResponse:
    """Get a task by ID.

    Args:
        task_id: Task ID.

    Returns:
        TaskResponse: Task data.

    Raises:
        TaskNotFoundError: If task doesn't exist.
    """
    task_service = get_task_service()
    query = GetTaskByIdQuery(task_id=task_id)
    task_dto = task_service.get_task_by_id(query)
    return _dto_to_response(task_dto)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update task details (title, description, deadline).",
)
def update_task(task_id: str, request: TaskUpdateRequest) -> TaskResponse:
    """Update a task.

    Args:
        task_id: Task ID.
        request: Update request with new values.

    Returns:
        TaskResponse: Updated task data.

    Raises:
        TaskNotFoundError: If task doesn't exist.
        DeadlineConstraintViolation: If new deadline violates project deadline.
    """
    task_service = get_task_service()
    command = UpdateTaskCommand(
        task_id=task_id,
        title=request.title,
        description=request.description,
        deadline=request.deadline,
    )
    task_dto = task_service.update_task(command)
    return _dto_to_response(task_dto)


@router.patch(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Complete task",
    description="Mark a task as completed. May trigger automatic project completion.",
)
def complete_task(task_id: str) -> TaskResponse:
    """Mark a task as completed.

    Args:
        task_id: Task ID.

    Returns:
        TaskResponse: Completed task data.

    Raises:
        TaskNotFoundError: If task doesn't exist.
        TaskAlreadyCompletedError: If task is already completed.
    """
    task_service = get_task_service()
    command = CompleteTaskCommand(task_id=task_id)
    task_dto = task_service.complete_task(command)
    return _dto_to_response(task_dto)


@router.patch(
    "/{task_id}/reopen",
    response_model=TaskResponse,
    summary="Reopen task",
    description="Reopen a completed task. May trigger project reopening if it was auto-completed.",
)
def reopen_task(task_id: str) -> TaskResponse:
    """Reopen a completed task.

    Args:
        task_id: Task ID.

    Returns:
        TaskResponse: Reopened task data.

    Raises:
        TaskNotFoundError: If task doesn't exist.
    """
    task_service = get_task_service()
    command = ReopenTaskCommand(task_id=task_id)
    task_dto = task_service.reopen_task(command)
    return _dto_to_response(task_dto)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Delete a task permanently.",
)
def delete_task(task_id: str) -> None:
    """Delete a task.

    Args:
        task_id: Task ID.

    Raises:
        TaskNotFoundError: If task doesn't exist.
    """
    task_service = get_task_service()
    command = DeleteTaskCommand(task_id=task_id)
    task_service.delete_task(command)
