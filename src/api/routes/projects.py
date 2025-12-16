"""Project API endpoints."""

from typing import Optional

from fastapi import APIRouter, Query, status

from ...application.commands.project_commands import (
    CompleteProjectCommand,
    CreateProjectCommand,
    DeleteProjectCommand,
    LinkTaskToProjectCommand,
    UnlinkTaskFromProjectCommand,
    UpdateProjectCommand,
)
from ...application.dto.project_dto import ProjectDTO
from ...application.dto.task_dto import TaskDTO
from ...application.queries.project_queries import GetProjectByIdQuery, ListProjectsQuery
from ...application.queries.task_queries import ListTasksQuery
from ..dependencies import get_project_service, get_task_service
from ..schemas.project_schemas import (
    PaginatedProjectsResponse,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from ..schemas.task_schemas import PaginatedTasksResponse, TaskResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


def _dto_to_response(dto: ProjectDTO) -> ProjectResponse:
    """Convert DTO to API response.

    Args:
        dto: Project DTO.

    Returns:
        ProjectResponse: API response model.
    """
    return ProjectResponse(
        id=dto.id,
        title=dto.title,
        description=dto.description,
        deadline=dto.deadline,
        completed=dto.completed,
        total_task_count=dto.total_task_count,
        completed_task_count=dto.completed_task_count,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project with title, description, and deadline.",
)
def create_project(request: ProjectCreateRequest) -> ProjectResponse:
    """Create a new project.

    Args:
        request: Project creation request.

    Returns:
        ProjectResponse: Created project data.
    """
    project_service = get_project_service()
    command = CreateProjectCommand(
        title=request.title,
        description=request.description,
        deadline=request.deadline,
    )
    project_id = project_service.create_project(command)

    # Retrieve and return the created project
    query = GetProjectByIdQuery(project_id=project_id)
    project_dto = project_service.get_project_by_id(query)
    return _dto_to_response(project_dto)


@router.get(
    "",
    response_model=PaginatedProjectsResponse,
    summary="List projects",
    description="List all projects with optional filter for completion status.",
)
def list_projects(
    completed: Optional[bool] = None,
    offset: int = Query(0, ge=0, description="Zero-based offset"),
    limit: int = Query(20, gt=0, le=100, description="Maximum items per page"),
) -> PaginatedProjectsResponse:
    """List projects with optional filters.

    Args:
        completed: Filter by completion status (None for all).

    Returns:
        List[ProjectResponse]: List of projects matching criteria.
    """
    project_service = get_project_service()
    query = ListProjectsQuery(completed=completed, offset=offset, limit=limit)
    result = project_service.list_projects(query)
    return PaginatedProjectsResponse(
        items=[_dto_to_response(project) for project in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
        has_more=result.has_more,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Retrieve a specific project by its ID.",
)
def get_project(project_id: str) -> ProjectResponse:
    """Get a project by ID.

    Args:
        project_id: Project ID.

    Returns:
        ProjectResponse: Project data.

    Raises:
        ProjectNotFoundError: If project doesn't exist.
    """
    project_service = get_project_service()
    query = GetProjectByIdQuery(project_id=project_id)
    project_dto = project_service.get_project_by_id(query)
    return _dto_to_response(project_dto)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update project details (title, description, deadline).",
)
def update_project(project_id: str, request: ProjectUpdateRequest) -> ProjectResponse:
    """Update a project.

    Args:
        project_id: Project ID.
        request: Update request with new values.

    Returns:
        ProjectResponse: Updated project data.

    Raises:
        ProjectNotFoundError: If project doesn't exist.
    """
    project_service = get_project_service()
    command = UpdateProjectCommand(
        project_id=project_id,
        title=request.title,
        description=request.description,
        deadline=request.deadline,
    )
    project_dto = project_service.update_project(command)
    return _dto_to_response(project_dto)


@router.patch(
    "/{project_id}/complete",
    response_model=ProjectResponse,
    summary="Complete project",
    description="Mark a project as completed. Only possible if all tasks are completed.",
)
def complete_project(project_id: str) -> ProjectResponse:
    """Mark a project as completed.

    Args:
        project_id: Project ID.

    Returns:
        ProjectResponse: Completed project data.

    Raises:
        ProjectNotFoundError: If project doesn't exist.
        ProjectNotCompletableError: If not all tasks are completed.
    """
    project_service = get_project_service()
    command = CompleteProjectCommand(project_id=project_id)
    project_dto = project_service.complete_project(command)
    return _dto_to_response(project_dto)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project and all its associated tasks permanently.",
)
def delete_project(project_id: str) -> None:
    """Delete a project and its tasks.

    Args:
        project_id: Project ID.

    Raises:
        ProjectNotFoundError: If project doesn't exist.
    """
    project_service = get_project_service()
    command = DeleteProjectCommand(project_id=project_id)
    project_service.delete_project(command)


@router.post(
    "/{project_id}/tasks/{task_id}/link",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Link task to project",
    description="Link an existing task to a project. Validates deadline constraints.",
)
def link_task_to_project(project_id: str, task_id: str) -> None:
    """Link a task to a project.

    Args:
        project_id: Project ID.
        task_id: Task ID.

    Raises:
        ProjectNotFoundError: If project doesn't exist.
        TaskNotFoundError: If task doesn't exist.
        DeadlineConstraintViolation: If task deadline is after project deadline.
    """
    project_service = get_project_service()
    command = LinkTaskToProjectCommand(project_id=project_id, task_id=task_id)
    project_service.link_task_to_project(command)


@router.delete(
    "/{project_id}/tasks/{task_id}/unlink",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink task from project",
    description="Remove the association between a task and a project.",
)
def unlink_task_from_project(project_id: str, task_id: str) -> None:
    """Unlink a task from a project.

    Args:
        project_id: Project ID.
        task_id: Task ID.

    Raises:
        ProjectNotFoundError: If project doesn't exist.
        TaskNotFoundError: If task doesn't exist.
    """
    project_service = get_project_service()
    command = UnlinkTaskFromProjectCommand(project_id=project_id, task_id=task_id)
    project_service.unlink_task_from_project(command)


@router.get(
    "/{project_id}/tasks",
    response_model=PaginatedTasksResponse,
    summary="Get project tasks",
    description="Retrieve all tasks associated with a specific project.",
)
def get_project_tasks(
    project_id: str,
    offset: int = Query(0, ge=0, description="Zero-based offset"),
    limit: int = Query(20, gt=0, le=100, description="Maximum items per page"),
) -> PaginatedTasksResponse:
    """Get all tasks for a project.

    Args:
        project_id: Project ID.

    Returns:
        List[TaskResponse]: List of tasks belonging to the project.

    Raises:
        ProjectNotFoundError: If project doesn't exist.
    """
    from ...domain.exceptions.project_exceptions import ProjectNotFoundError

    # First verify project exists
    project_service = get_project_service()
    query_project = GetProjectByIdQuery(project_id=project_id)
    try:
        project_service.get_project_by_id(query_project)
    except ProjectNotFoundError:
        raise

    # Get tasks for project
    task_service = get_task_service()
    query_tasks = ListTasksQuery(
        project_id=project_id,
        completed=None,
        overdue=False,
        offset=offset,
        limit=limit,
    )
    result = task_service.list_tasks(query_tasks)

    # Convert DTOs to responses
    return PaginatedTasksResponse(
        items=[_dto_to_task_response(task) for task in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
        has_more=result.has_more,
    )


def _dto_to_task_response(dto: TaskDTO) -> TaskResponse:
    """Convert Task DTO to API response.

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
