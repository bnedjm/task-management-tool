"""Unit of Work pattern implementation."""

from typing import Callable, Optional

from sqlalchemy.orm import Session

from ...domain.repositories.project_repository import ProjectRepository
from ...domain.repositories.task_repository import TaskRepository
from .repositories.sqlalchemy_project_repository import SQLAlchemyProjectRepository
from .repositories.sqlalchemy_task_repository import SQLAlchemyTaskRepository


class UnitOfWork:
    """Unit of Work pattern for managing database transactions.

    Provides transaction boundaries and coordinates repository access.
    Ensures all operations within a transaction succeed or fail together.
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """Initialize Unit of Work.

        Args:
            session_factory: Callable that returns a new database session.
        """
        self._session_factory = session_factory
        self._session: Optional[Session] = None
        self._tasks: Optional[TaskRepository] = None
        self._projects: Optional[ProjectRepository] = None

    def __enter__(self) -> "UnitOfWork":
        """Enter transaction context.

        Returns:
            UnitOfWork: Self for context manager usage.
        """
        self._session = self._session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit transaction context.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        if exc_type is not None:
            self.rollback()
        self._session.close()

    def commit(self) -> None:
        """Commit the current transaction."""
        if self._session:
            self._session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session:
            self._session.rollback()

    @property
    def tasks(self) -> TaskRepository:
        """Get task repository.

        Returns:
            TaskRepository: Task repository instance.
        """
        if self._tasks is None:
            self._tasks = SQLAlchemyTaskRepository(self._session)
        return self._tasks

    @property
    def projects(self) -> ProjectRepository:
        """Get project repository.

        Returns:
            ProjectRepository: Project repository instance.
        """
        if self._projects is None:
            self._projects = SQLAlchemyProjectRepository(self._session)
        return self._projects
