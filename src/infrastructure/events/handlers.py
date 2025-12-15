"""Domain event handlers."""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from ...domain.events.project_events import ProjectDeadlineChangedEvent
from ...domain.events.task_events import (
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskDeadlineChangedEvent,
    TaskRemovedFromProjectEvent,
)
from ...domain.value_objects.deadline import Deadline
from ...domain.value_objects.ids import TaskId

if TYPE_CHECKING:
    from ...domain.repositories.project_repository import ProjectRepository
    from ...domain.repositories.task_repository import TaskRepository
    from ..config import Config

logger = logging.getLogger(__name__)


class AutoCompleteProjectHandler:
    """Handles automatic project completion when last task is completed.

    This handler listens to TaskCompletedEvent and checks if all tasks
    in the project are now completed. If so, and if auto-completion is
    enabled, it completes the project.
    """

    def __init__(
        self,
        project_repository: "ProjectRepository",
        config: "Config",
    ):
        """Initialize the handler.

        Args:
            project_repository: Repository for project access.
            config: Application configuration.
        """
        self._project_repository = project_repository
        self._auto_complete_enabled = config.AUTO_COMPLETE_PROJECTS

    def handle(self, event: TaskCompletedEvent) -> None:
        """Handle task completed event.

        Args:
            event: The task completed event.
        """
        if not self._auto_complete_enabled or not event.project_id:
            return

        try:
            project = self._project_repository.get_by_id(event.project_id)
            if not project:
                return

            if project.can_be_completed() and not project.is_completed:
                project.complete()
                self._project_repository.save(project)
                logger.info(
                    f"Auto-completed project {project.id} after task {event.task_id} completion"
                )
        except Exception as e:
            logger.error(f"Error auto-completing project: {e}", exc_info=True)

    def handle_task_removed(self, event: TaskRemovedFromProjectEvent) -> None:
        """Handle task removed from project event.

        When a task is deleted or unlinked, check if all remaining tasks
        are complete and auto-complete the project if so.

        Args:
            event: The task removed from project event.
        """
        if not self._auto_complete_enabled:
            return

        try:
            project = self._project_repository.get_by_id(event.project_id)
            if not project:
                return

            if project.can_be_completed() and not project.is_completed:
                project.complete()
                self._project_repository.save(project)
                logger.info(
                    f"Auto-completed project {project.id} after task {event.task_id} removal"
                )
        except Exception as e:
            logger.error(f"Error auto-completing project after task removal: {e}", exc_info=True)


class TaskDeadlineAdjustmentHandler:
    """Handles automatic task deadline adjustment when project deadline changes.

    When a project's deadline is moved earlier, tasks with deadlines that
    violate the new constraint are automatically adjusted.
    """

    def __init__(self, task_repository: "TaskRepository"):
        """Initialize the handler.

        Args:
            task_repository: Repository for task access.
        """
        self._task_repository = task_repository

    def handle(self, event: ProjectDeadlineChangedEvent) -> None:
        """Handle project deadline changed event.

        Args:
            event: The project deadline changed event.
        """
        if not event.affected_task_ids:
            logger.info(f"Project {event.project_id} deadline changed, " f"no tasks affected")
            return

        try:
            for task_id in event.affected_task_ids:
                task = self._task_repository.get_by_id(task_id)
                if task:
                    # Automatically adjust task deadline to project deadline
                    task.adjust_deadline(event.new_deadline, event.new_deadline)
                    self._task_repository.save(task)
                    logger.info(
                        f"Adjusted task {task_id} deadline to {event.new_deadline} "
                        f"due to project deadline change"
                    )
        except Exception as e:
            logger.error(f"Error adjusting task deadlines: {e}", exc_info=True)


class DeadlineWarningChecker:
    """Checks and logs warnings for approaching deadlines.

    When a task is created or its deadline is updated, checks if the deadline
    is within 24 hours and logs a warning if so.
    """

    def __init__(self, task_repository: "TaskRepository"):
        """Initialize the handler.

        Args:
            task_repository: Repository for task access.
        """
        self._task_repository = task_repository

    def handle_created(self, event: TaskCreatedEvent) -> None:
        """Handle task created event.

        Args:
            event: The task created event.
        """
        logger.info(f"🔔 DeadlineWarningChecker received TaskCreatedEvent for '{event.title}'")
        self._check_deadline(event.task_id, event.title, event.deadline)

    def handle_deadline_changed(self, event: TaskDeadlineChangedEvent) -> None:
        """Handle task deadline changed event.

        Args:
            event: The task deadline changed event.
        """
        logger.info(
            f"🔔 DeadlineWarningChecker received TaskDeadlineChangedEvent for task {event.task_id}"
        )
        # Get task title if we have repository access
        task_title = str(event.task_id)  # Fallback to ID
        if self._task_repository:
            try:
                task = self._task_repository.get_by_id(event.task_id)
                if task:
                    task_title = task.title
            except Exception as e:
                logger.debug(f"Could not fetch task title: {e}")

        self._check_deadline(event.task_id, task_title, event.new_deadline)

    def _check_deadline(self, task_id: TaskId, task_title: str, deadline: Deadline) -> None:
        """Check if deadline is approaching and log warning.

        Args:
            task_id: The task ID.
            task_title: The task title.
            deadline: The deadline to check.
        """
        logger.info(f"   📅 Deadline: {deadline.value}")
        logger.info(f"   ⏰ Current time: {datetime.now(timezone.utc)}")

        try:
            is_within_24h = deadline.is_within_hours(24)
            logger.info(f"   📊 Is within 24 hours? {is_within_24h}")

            if is_within_24h:
                logger.warning(
                    f"⚠️  Task {task_id} '{task_title}' has approaching deadline: "
                    f"{deadline.value}"
                )
        except Exception as e:
            logger.error(f"Error checking deadline warning: {e}", exc_info=True)


class TaskCompletionLogger:
    """Logs task completions for audit purposes."""

    def handle(self, event: TaskCompletedEvent) -> None:
        """Handle task completed event.

        Args:
            event: The task completed event.
        """
        project_info = f" (Project: {event.project_id})" if event.project_id else ""
        logger.info(f"Task {event.task_id} completed at {event.completed_at}{project_info}")
