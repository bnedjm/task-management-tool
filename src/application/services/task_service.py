"""Task application service."""

from typing import TYPE_CHECKING, List

from ...domain.entities.task import Task
from ...domain.exceptions.project_exceptions import ProjectNotFoundError
from ...domain.exceptions.task_exceptions import TaskNotFoundError
from ...domain.value_objects.deadline import Deadline
from ...domain.value_objects.ids import ProjectId, TaskId
from ..commands.task_commands import (
    CompleteTaskCommand,
    CreateTaskCommand,
    DeleteTaskCommand,
    ReopenTaskCommand,
    UpdateTaskCommand,
)
from ..dto.task_dto import TaskDTO
from ..queries.task_queries import GetTaskByIdQuery, ListTasksQuery

if TYPE_CHECKING:
    from ...infrastructure.events.event_bus import EventBus
    from ...infrastructure.persistence.unit_of_work import UnitOfWork


class TaskService:
    """Application service for task-related use cases.

    Orchestrates task operations, manages transactions via Unit of Work,
    and publishes domain events.
    """

    def __init__(self, uow: "UnitOfWork", event_bus: "EventBus"):
        """Initialize the task service.

        Args:
            uow: Unit of Work for transaction management.
            event_bus: Event bus for publishing domain events.
        """
        self._uow = uow
        self._event_bus = event_bus

    def create_task(self, command: CreateTaskCommand) -> str:
        """Create a new task.

        Args:
            command: Command containing task creation data.

        Returns:
            str: ID of the created task.

        Raises:
            ProjectNotFoundError: If specified project doesn't exist.
            DeadlineConstraintViolation: If task deadline violates project deadline.
        """
        with self._uow:
            task_id = TaskId.generate()
            deadline = Deadline(command.deadline)

            # If project specified, validate it exists and deadline constraint
            project_id = None
            if command.project_id:
                project_id = ProjectId.from_string(command.project_id)
                project = self._uow.projects.get_by_id(project_id)
                if not project:
                    raise ProjectNotFoundError(command.project_id)

            task = Task.create(
                id=task_id,
                title=command.title,
                description=command.description,
                deadline=deadline,
                project_id=project_id,
            )

            # If assigning to project, validate deadline constraint
            if project_id:
                task.assign_to_project(project_id, project.deadline)
                # Newly created tasks are always incomplete, so project will reopen if completed
                project.add_task(task_id, is_completed=False)
                self._uow.projects.save(project)

            self._uow.tasks.save(task)
            self._uow.commit()

            # Publish domain events from both task and project
            events = task.collect_events()
            if project_id:
                events.extend(project.collect_events())

            import logging

            logger = logging.getLogger(__name__)
            logger.info(f"📤 Publishing {len(events)} event(s) from task creation")
            for event in events:
                logger.info(f"   📨 Event: {type(event).__name__}")

            self._event_bus.publish(events)

            return str(task_id)

    def update_task(self, command: UpdateTaskCommand) -> TaskDTO:
        """Update task details.

        Args:
            command: Command containing update data.

        Returns:
            TaskDTO: Updated task data.

        Raises:
            TaskNotFoundError: If task doesn't exist.
            DeadlineConstraintViolation: If new deadline violates project deadline.
        """
        with self._uow:
            task_id = TaskId.from_string(command.task_id)
            task = self._uow.tasks.get_by_id(task_id)
            if not task:
                raise TaskNotFoundError(command.task_id)

            # Update basic details
            if command.title or command.description:
                task.update_details(command.title, command.description)

            # Update deadline if provided
            if command.deadline:
                new_deadline = Deadline(command.deadline)
                project_deadline = None
                if task.project_id:
                    project = self._uow.projects.get_by_id(task.project_id)
                    project_deadline = project.deadline if project else None
                task.adjust_deadline(new_deadline, project_deadline)

            self._uow.tasks.save(task)
            self._uow.commit()

            # Publish domain events
            self._event_bus.publish(task.collect_events())

            return self._to_dto(task)

    def complete_task(self, command: CompleteTaskCommand) -> TaskDTO:
        """Mark a task as completed.

        Args:
            command: Command containing task ID.

        Returns:
            TaskDTO: Completed task data.

        Raises:
            TaskNotFoundError: If task doesn't exist.
            TaskAlreadyCompletedError: If task is already completed.
        """
        with self._uow:
            task_id = TaskId.from_string(command.task_id)
            task = self._uow.tasks.get_by_id(task_id)
            if not task:
                raise TaskNotFoundError(command.task_id)

            task.complete()

            # Update project task completion tracking
            if task.project_id:
                project = self._uow.projects.get_by_id(task.project_id)
                if project:
                    project.mark_task_completed(task_id)
                    self._uow.projects.save(project)

            self._uow.tasks.save(task)
            self._uow.commit()

            # Publish domain events (may trigger auto-complete)
            events = task.collect_events()

            import logging

            logger = logging.getLogger(__name__)
            logger.info(f"📤 Publishing {len(events)} event(s) from task completion")
            for event in events:
                logger.info(f"   📨 Event: {type(event).__name__}")

            self._event_bus.publish(events)

            return self._to_dto(task)

    def reopen_task(self, command: ReopenTaskCommand) -> TaskDTO:
        """Reopen a completed task.

        Args:
            command: Command containing task ID.

        Returns:
            TaskDTO: Reopened task data.

        Raises:
            TaskNotFoundError: If task doesn't exist.
        """
        with self._uow:
            task_id = TaskId.from_string(command.task_id)
            task = self._uow.tasks.get_by_id(task_id)
            if not task:
                raise TaskNotFoundError(command.task_id)

            task.reopen()

            # Update project and potentially reopen it
            if task.project_id:
                project = self._uow.projects.get_by_id(task.project_id)
                if project:
                    project.mark_task_reopened(task_id)
                    project.reopen_due_to_task(task_id)
                    self._uow.projects.save(project)

            self._uow.tasks.save(task)
            self._uow.commit()

            # Publish domain events
            events = task.collect_events()
            if task.project_id:
                project = self._uow.projects.get_by_id(task.project_id)
                if project:
                    events.extend(project.collect_events())
            self._event_bus.publish(events)

            return self._to_dto(task)

    def delete_task(self, command: DeleteTaskCommand) -> None:
        """Delete a task.

        Args:
            command: Command containing task ID.

        Raises:
            TaskNotFoundError: If task doesn't exist.
        """
        from ...domain.events.task_events import TaskRemovedFromProjectEvent

        with self._uow:
            task_id = TaskId.from_string(command.task_id)
            task = self._uow.tasks.get_by_id(task_id)
            if not task:
                raise TaskNotFoundError(command.task_id)

            # Remove from project if assigned
            project_id = None
            if task.project_id:
                project_id = task.project_id
                project = self._uow.projects.get_by_id(project_id)
                if project:
                    project.remove_task(task_id)
                    self._uow.projects.save(project)

            self._uow.tasks.delete(task_id)
            self._uow.commit()

            # Emit event if task was removed from a project
            if project_id:
                events = [
                    TaskRemovedFromProjectEvent(
                        task_id=task_id,
                        project_id=project_id,
                    )
                ]
                self._event_bus.publish(events)

    def get_task_by_id(self, query: GetTaskByIdQuery) -> TaskDTO:
        """Get a task by ID.

        Args:
            query: Query containing task ID.

        Returns:
            TaskDTO: Task data.

        Raises:
            TaskNotFoundError: If task doesn't exist.
        """
        with self._uow:
            task_id = TaskId.from_string(query.task_id)
            task = self._uow.tasks.get_by_id(task_id)
            if not task:
                raise TaskNotFoundError(query.task_id)
            return self._to_dto(task)

    def list_tasks(self, query: ListTasksQuery) -> List[TaskDTO]:
        """List tasks with optional filters.

        Args:
            query: Query containing filter criteria.

        Returns:
            List[TaskDTO]: List of task data.
        """
        with self._uow:
            if query.project_id:
                project_id = ProjectId.from_string(query.project_id)
                tasks = self._uow.tasks.list_by_project(project_id)
            else:
                tasks = self._uow.tasks.list_by_filter(
                    completed=query.completed,
                    overdue=query.overdue,
                )
            return [self._to_dto(task) for task in tasks]

    def _to_dto(self, task: Task) -> TaskDTO:
        """Convert Task entity to DTO.

        Args:
            task: Task entity.

        Returns:
            TaskDTO: Task data transfer object.
        """
        # Get timestamps from repository (infrastructure concern)
        created_at, updated_at = self._uow.tasks.get_timestamps(task.id)

        return TaskDTO(
            id=str(task.id),
            title=task.title,
            description=task.description,
            deadline=task.deadline.value,
            completed=task.is_completed,
            project_id=str(task.project_id) if task.project_id else None,
            is_overdue=task.is_overdue,
            created_at=created_at,
            updated_at=updated_at,
        )
