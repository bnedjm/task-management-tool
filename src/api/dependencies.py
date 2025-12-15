"""Dependency injection for FastAPI endpoints."""

from typing import Generator

from sqlalchemy.orm import Session

from ..application.services.project_service import ProjectService
from ..application.services.task_service import TaskService
from ..infrastructure.config import Config, get_config
from ..infrastructure.events.event_bus import EventBus
from ..infrastructure.persistence.database import get_session
from ..infrastructure.persistence.unit_of_work import UnitOfWork

# Global event bus instance
_event_bus: EventBus | None = None


def get_db_session() -> Generator[Session, None, None]:
    """Provide database session dependency.

    Yields:
        Session: SQLAlchemy session instance.
    """
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def get_event_bus() -> EventBus:
    """Provide event bus singleton.

    Returns:
        EventBus: Event bus instance.
    """
    import logging

    logger = logging.getLogger(__name__)

    global _event_bus
    if _event_bus is None:
        logger.info("🚀 Initializing Event Bus...")
        _event_bus = EventBus()
        # Register event handlers here
        from ..domain.events.project_events import ProjectDeadlineChangedEvent
        from ..domain.events.task_events import (
            TaskCompletedEvent,
            TaskCreatedEvent,
            TaskDeadlineChangedEvent,
            TaskRemovedFromProjectEvent,
        )
        from ..infrastructure.events.handlers import (
            AutoCompleteProjectHandler,
            DeadlineWarningChecker,
            TaskCompletionLogger,
            TaskDeadlineAdjustmentHandler,
        )

        # Get initial config for logging
        initial_config = get_config()
        logger.info(
            f"⚙️  Configuration loaded: AUTO_COMPLETE_PROJECTS={initial_config.AUTO_COMPLETE_PROJECTS}"
        )

        # Register handlers that don't need repositories
        _event_bus.register(TaskCompletedEvent, TaskCompletionLogger().handle)
        logger.info("✅ Registered TaskCompletionLogger")

        # Register DeadlineWarningChecker for both task creation and deadline changes
        def deadline_warning_for_created(event: TaskCreatedEvent):
            """Wrapper for deadline warning on task creation."""
            from ..infrastructure.persistence.repositories.sqlalchemy_task_repository import (
                SQLAlchemyTaskRepository,
            )

            session = get_session()
            try:
                task_repo = SQLAlchemyTaskRepository(session)
                handler = DeadlineWarningChecker(task_repo)
                handler.handle_created(event)
            finally:
                session.close()

        def deadline_warning_for_changed(event: TaskDeadlineChangedEvent):
            """Wrapper for deadline warning on deadline change."""
            from ..infrastructure.persistence.repositories.sqlalchemy_task_repository import (
                SQLAlchemyTaskRepository,
            )

            session = get_session()
            try:
                task_repo = SQLAlchemyTaskRepository(session)
                handler = DeadlineWarningChecker(task_repo)
                handler.handle_deadline_changed(event)
            finally:
                session.close()

        _event_bus.register(TaskCreatedEvent, deadline_warning_for_created)
        logger.info("✅ Registered DeadlineWarningChecker for TaskCreatedEvent")
        _event_bus.register(TaskDeadlineChangedEvent, deadline_warning_for_changed)
        logger.info("✅ Registered DeadlineWarningChecker for TaskDeadlineChangedEvent")

        # Register handlers that need repositories (will get them via UnitOfWork)
        # We create a wrapper that instantiates the handler with fresh repositories per event
        def auto_complete_handler(event: TaskCompletedEvent):
            """Wrapper to handle auto-completion with fresh repositories."""
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"🔔 Auto-complete handler called for task {event.task_id}, "
                f"project {event.project_id}"
            )

            from ..infrastructure.persistence.repositories.sqlalchemy_project_repository import (
                SQLAlchemyProjectRepository,
            )

            # Get config fresh each time to respect runtime changes (e.g., in tests)
            config = get_config()
            session = get_session()
            try:
                project_repo = SQLAlchemyProjectRepository(session)
                handler = AutoCompleteProjectHandler(project_repo, config)
                logger.info(
                    f"📋 Handler created with AUTO_COMPLETE_PROJECTS={config.AUTO_COMPLETE_PROJECTS}"
                )
                handler.handle(event)
                session.commit()
                logger.info("✅ Auto-complete handler completed successfully")
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Error in auto-complete handler: {e}", exc_info=True)
            finally:
                session.close()

        def deadline_adjustment_handler(event: ProjectDeadlineChangedEvent):
            """Wrapper to handle deadline adjustments with fresh repositories."""
            from ..infrastructure.persistence.repositories.sqlalchemy_task_repository import (
                SQLAlchemyTaskRepository,
            )

            session = get_session()
            try:
                task_repo = SQLAlchemyTaskRepository(session)
                handler = TaskDeadlineAdjustmentHandler(task_repo)
                handler.handle(event)
                session.commit()
            except Exception as e:
                session.rollback()
                import logging

                logging.getLogger(__name__).error(
                    f"Error in deadline adjustment handler: {e}", exc_info=True
                )
            finally:
                session.close()

        _event_bus.register(TaskCompletedEvent, auto_complete_handler)
        logger.info("✅ Registered AutoCompleteProjectHandler for TaskCompletedEvent")
        
        # Register handler for task removal events
        def task_removed_handler(event: TaskRemovedFromProjectEvent):
            """Wrapper to handle auto-completion after task removal."""
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"🔔 Task removed handler called for task {event.task_id}, "
                f"project {event.project_id}"
            )

            from ..infrastructure.persistence.repositories.sqlalchemy_project_repository import (
                SQLAlchemyProjectRepository,
            )

            # Get config fresh each time to respect runtime changes (e.g., in tests)
            config = get_config()
            session = get_session()
            try:
                project_repo = SQLAlchemyProjectRepository(session)
                handler = AutoCompleteProjectHandler(project_repo, config)
                handler.handle_task_removed(event)
                session.commit()
                logger.info("✅ Task removed handler completed successfully")
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Error in task removed handler: {e}", exc_info=True)
            finally:
                session.close()

        _event_bus.register(TaskRemovedFromProjectEvent, task_removed_handler)
        logger.info("✅ Registered AutoCompleteProjectHandler for TaskRemovedFromProjectEvent")
        
        _event_bus.register(ProjectDeadlineChangedEvent, deadline_adjustment_handler)
        logger.info("✅ Registered TaskDeadlineAdjustmentHandler")
        logger.info("🎉 Event Bus initialization complete!")

    return _event_bus


def get_unit_of_work() -> UnitOfWork:
    """Provide Unit of Work instance.

    Returns:
        UnitOfWork: Unit of Work instance.
    """
    return UnitOfWork(get_session)


def get_configuration() -> Config:
    """Provide application configuration.

    Returns:
        Config: Application configuration.
    """
    return get_config()


def get_task_service(
    uow: UnitOfWork = None,
    event_bus: EventBus = None,
) -> TaskService:
    """Provide TaskService with dependencies.

    Args:
        uow: Unit of Work (will be created if not provided).
        event_bus: Event bus (will be retrieved if not provided).

    Returns:
        TaskService: Task service instance.
    """
    if uow is None:
        uow = get_unit_of_work()
    if event_bus is None:
        event_bus = get_event_bus()
    return TaskService(uow, event_bus)


def get_project_service(
    uow: UnitOfWork = None,
    event_bus: EventBus = None,
) -> ProjectService:
    """Provide ProjectService with dependencies.

    Args:
        uow: Unit of Work (will be created if not provided).
        event_bus: Event bus (will be retrieved if not provided).

    Returns:
        ProjectService: Project service instance.
    """
    if uow is None:
        uow = get_unit_of_work()
    if event_bus is None:
        event_bus = get_event_bus()
    return ProjectService(uow, event_bus)
