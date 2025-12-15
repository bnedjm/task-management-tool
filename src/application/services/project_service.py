"""Project application service."""

from typing import TYPE_CHECKING, List

from ...domain.entities.project import Project
from ...domain.exceptions.project_exceptions import ProjectNotFoundError
from ...domain.value_objects.deadline import Deadline
from ...domain.value_objects.ids import ProjectId, TaskId
from ..commands.project_commands import (
    CompleteProjectCommand,
    CreateProjectCommand,
    DeleteProjectCommand,
    LinkTaskToProjectCommand,
    UnlinkTaskFromProjectCommand,
    UpdateProjectCommand,
)
from ..dto.project_dto import ProjectDTO
from ..queries.project_queries import GetProjectByIdQuery, ListProjectsQuery

if TYPE_CHECKING:
    from ...infrastructure.events.event_bus import EventBus
    from ...infrastructure.persistence.unit_of_work import UnitOfWork


class ProjectService:
    """Application service for project-related use cases.

    Orchestrates project operations, manages transactions via Unit of Work,
    and publishes domain events.
    """

    def __init__(self, uow: "UnitOfWork", event_bus: "EventBus"):
        """Initialize the project service.

        Args:
            uow: Unit of Work for transaction management.
            event_bus: Event bus for publishing domain events.
        """
        self._uow = uow
        self._event_bus = event_bus

    def create_project(self, command: CreateProjectCommand) -> str:
        """Create a new project.

        Args:
            command: Command containing project creation data.

        Returns:
            str: ID of the created project.
        """
        with self._uow:
            project_id = ProjectId.generate()
            deadline = Deadline(command.deadline)

            project = Project.create(
                id=project_id,
                title=command.title,
                description=command.description,
                deadline=deadline,
            )

            self._uow.projects.save(project)
            self._uow.commit()

            # Publish domain events
            self._event_bus.publish(project.collect_events())

            return str(project_id)

    def update_project(self, command: UpdateProjectCommand) -> ProjectDTO:
        """Update project details.

        Args:
            command: Command containing update data.

        Returns:
            ProjectDTO: Updated project data.

        Raises:
            ProjectNotFoundError: If project doesn't exist.
        """
        with self._uow:
            project_id = ProjectId.from_string(command.project_id)
            project = self._uow.projects.get_by_id(project_id)
            if not project:
                raise ProjectNotFoundError(command.project_id)

            # Update basic details
            if command.title or command.description:
                project.update_details(command.title, command.description)

            # Update deadline if provided
            if command.deadline:
                new_deadline = Deadline(command.deadline)
                # Find tasks that would violate the new deadline
                tasks = self._uow.tasks.list_by_project(project_id)
                violating_task_ids = [
                    task.id for task in tasks if task.deadline.is_after(new_deadline)
                ]
                project.update_deadline(new_deadline, violating_task_ids)

            self._uow.projects.save(project)
            self._uow.commit()

            # Publish domain events (may trigger task deadline adjustments)
            self._event_bus.publish(project.collect_events())

            return self._to_dto(project)

    def complete_project(self, command: CompleteProjectCommand) -> ProjectDTO:
        """Mark a project as completed.

        Args:
            command: Command containing project ID.

        Returns:
            ProjectDTO: Completed project data.

        Raises:
            ProjectNotFoundError: If project doesn't exist.
            ProjectNotCompletableError: If not all tasks are completed.
        """
        with self._uow:
            project_id = ProjectId.from_string(command.project_id)
            project = self._uow.projects.get_by_id(project_id)
            if not project:
                raise ProjectNotFoundError(command.project_id)

            project.complete()
            self._uow.projects.save(project)
            self._uow.commit()

            # Publish domain events
            self._event_bus.publish(project.collect_events())

            return self._to_dto(project)

    def delete_project(self, command: DeleteProjectCommand) -> None:
        """Delete a project and its tasks.

        Args:
            command: Command containing project ID.

        Raises:
            ProjectNotFoundError: If project doesn't exist.
        """
        with self._uow:
            project_id = ProjectId.from_string(command.project_id)
            project = self._uow.projects.get_by_id(project_id)
            if not project:
                raise ProjectNotFoundError(command.project_id)

            # Delete all associated tasks
            tasks = self._uow.tasks.list_by_project(project_id)
            for task in tasks:
                self._uow.tasks.delete(task.id)

            self._uow.projects.delete(project_id)
            self._uow.commit()

    def get_project_by_id(self, query: GetProjectByIdQuery) -> ProjectDTO:
        """Get a project by ID.

        Args:
            query: Query containing project ID.

        Returns:
            ProjectDTO: Project data.

        Raises:
            ProjectNotFoundError: If project doesn't exist.
        """
        with self._uow:
            project_id = ProjectId.from_string(query.project_id)
            project = self._uow.projects.get_by_id(project_id)
            if not project:
                raise ProjectNotFoundError(query.project_id)
            return self._to_dto(project)

    def list_projects(self, query: ListProjectsQuery) -> List[ProjectDTO]:
        """List projects with optional filters.

        Args:
            query: Query containing filter criteria.

        Returns:
            List[ProjectDTO]: List of project data.
        """
        with self._uow:
            projects = self._uow.projects.list_by_filter(completed=query.completed)
            return [self._to_dto(project) for project in projects]

    def link_task_to_project(self, command: LinkTaskToProjectCommand) -> None:
        """Link a task to a project.

        Args:
            command: Command containing project and task IDs.

        Raises:
            ProjectNotFoundError: If project doesn't exist.
            TaskNotFoundError: If task doesn't exist.
            DeadlineConstraintViolation: If task deadline violates project deadline.
        """
        from ...domain.exceptions.task_exceptions import TaskNotFoundError

        with self._uow:
            project_id = ProjectId.from_string(command.project_id)
            task_id = TaskId.from_string(command.task_id)

            # Validate project exists
            project = self._uow.projects.get_by_id(project_id)
            if not project:
                raise ProjectNotFoundError(command.project_id)

            # Validate task exists
            task = self._uow.tasks.get_by_id(task_id)
            if not task:
                raise TaskNotFoundError(command.task_id)

            # Assign task to project (validates deadline constraint)
            task.assign_to_project(project_id, project.deadline)
            # Pass is_completed to prevent reopening if task is already completed
            project.add_task(task_id, is_completed=task.is_completed)

            # If task is already completed, mark it in project
            if task.is_completed:
                project.mark_task_completed(task_id)

            self._uow.tasks.save(task)
            self._uow.projects.save(project)
            self._uow.commit()

            # Publish domain events from both task and project
            events = task.collect_events()
            events.extend(project.collect_events())
            self._event_bus.publish(events)

    def unlink_task_from_project(self, command: UnlinkTaskFromProjectCommand) -> None:
        """Unlink a task from a project.

        Args:
            command: Command containing project and task IDs.

        Raises:
            ProjectNotFoundError: If project doesn't exist.
            TaskNotFoundError: If task doesn't exist.
        """
        from ...domain.events.task_events import TaskRemovedFromProjectEvent
        from ...domain.exceptions.task_exceptions import TaskNotFoundError

        with self._uow:
            project_id = ProjectId.from_string(command.project_id)
            task_id = TaskId.from_string(command.task_id)

            # Validate project exists
            project = self._uow.projects.get_by_id(project_id)
            if not project:
                raise ProjectNotFoundError(command.project_id)

            # Validate task exists
            task = self._uow.tasks.get_by_id(task_id)
            if not task:
                raise TaskNotFoundError(command.task_id)

            # Remove task from project
            project.remove_task(task_id)

            # Update task to remove project association
            task._project_id = None

            self._uow.tasks.save(task)
            self._uow.projects.save(project)
            self._uow.commit()

            # Emit event for task removal
            events = [
                TaskRemovedFromProjectEvent(
                    task_id=task_id,
                    project_id=project_id,
                )
            ]
            self._event_bus.publish(events)

    def _to_dto(self, project: Project) -> ProjectDTO:
        """Convert Project entity to DTO.

        Args:
            project: Project entity.

        Returns:
            ProjectDTO: Project data transfer object.
        """
        # Get timestamps from repository (infrastructure concern)
        created_at, updated_at = self._uow.projects.get_timestamps(project.id)

        return ProjectDTO(
            id=str(project.id),
            title=project.title,
            description=project.description,
            deadline=project.deadline.value,
            completed=project.is_completed,
            total_task_count=project.total_task_count,
            completed_task_count=project.completed_task_count,
            created_at=created_at,
            updated_at=updated_at,
        )
