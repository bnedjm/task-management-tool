"""SQLAlchemy implementation of TaskRepository."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from ....domain.entities.task import Task
from ....domain.repositories.task_repository import TaskRepository
from ....domain.value_objects.deadline import Deadline
from ....domain.value_objects.ids import ProjectId, TaskId
from ..models.task_model import TaskModel


class SQLAlchemyTaskRepository(TaskRepository):
    """SQLAlchemy concrete implementation of TaskRepository.

    Handles conversion between domain entities and ORM models.
    """

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session instance.
        """
        self._session = session

    def save(self, task: Task) -> None:
        """Persist a task entity.

        Args:
            task: The task entity to save.
        """
        orm_model = self._to_orm(task)
        self._session.merge(orm_model)

    def get_by_id(self, task_id: TaskId) -> Optional[Task]:
        """Retrieve a task by its ID.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            Optional[Task]: The task if found, None otherwise.
        """
        orm_model = self._session.query(TaskModel).filter_by(id=str(task_id)).first()
        return self._to_domain(orm_model) if orm_model else None

    def list_all(self) -> List[Task]:
        """Retrieve all tasks.

        Returns:
            List[Task]: List of all tasks.
        """
        orm_models = self._session.query(TaskModel).all()
        return [self._to_domain(model) for model in orm_models]

    def list_by_project(self, project_id: ProjectId) -> List[Task]:
        """Retrieve all tasks for a specific project.

        Args:
            project_id: The ID of the project.

        Returns:
            List[Task]: List of tasks belonging to the project.
        """
        orm_models = self._session.query(TaskModel).filter_by(project_id=str(project_id)).all()
        return [self._to_domain(model) for model in orm_models]

    def list_by_filter(
        self,
        completed: Optional[bool] = None,
        overdue: Optional[bool] = None,
        project_id: Optional[ProjectId] = None,
    ) -> List[Task]:
        """Retrieve tasks matching filter criteria.

        Args:
            completed: Filter by completion status (None for all).
            overdue: Filter for overdue tasks (None for all, True for overdue,
                False for not overdue).
            project_id: Filter by project ID (None for all projects).

        Returns:
            List[Task]: List of tasks matching the criteria.
        """
        query = self._build_filtered_query(completed, overdue, project_id)
        orm_models = query.order_by(TaskModel.created_at.desc(), TaskModel.id.desc()).all()
        return [self._to_domain(model) for model in orm_models]

    def list_by_filter_paginated(
        self,
        completed: Optional[bool],
        overdue: Optional[bool],
        project_id: Optional[ProjectId],
        offset: int,
        limit: int,
    ) -> tuple[List[Task], int]:
        """Retrieve tasks with pagination and total count."""
        base_query = self._build_filtered_query(completed, overdue, project_id)
        total = base_query.count()

        paged_query = base_query.order_by(TaskModel.created_at.desc(), TaskModel.id.desc()).offset(
            offset
        )
        if limit:
            paged_query = paged_query.limit(limit)

        orm_models = paged_query.all()
        return [self._to_domain(model) for model in orm_models], total

    def delete(self, task_id: TaskId) -> None:
        """Delete a task.

        Args:
            task_id: The ID of the task to delete.
        """
        self._session.query(TaskModel).filter_by(id=str(task_id)).delete()

    def get_timestamps(self, task_id: TaskId) -> tuple[datetime, datetime]:
        """Get created_at and updated_at timestamps for a task.

        Args:
            task_id: The ID of the task.

        Returns:
            tuple[datetime, datetime]: (created_at, updated_at) timestamps.
        """
        orm_model = self._session.query(TaskModel).filter_by(id=str(task_id)).first()
        if orm_model:
            return (orm_model.created_at, orm_model.updated_at)
        return (datetime.now(timezone.utc), datetime.now(timezone.utc))

    def _to_domain(self, orm_model: TaskModel) -> Task:
        """Convert ORM model to domain entity.

        Args:
            orm_model: SQLAlchemy ORM model.

        Returns:
            Task: Domain entity.
        """
        project_id = ProjectId.from_string(orm_model.project_id) if orm_model.project_id else None

        return Task(
            id=TaskId.from_string(orm_model.id),
            title=orm_model.title,
            description=orm_model.description,
            deadline=Deadline.from_datetime(orm_model.deadline, validate_past=False),
            completed=orm_model.completed,
            project_id=project_id,
        )

    def _to_orm(self, task: Task) -> TaskModel:
        """Convert domain entity to ORM model.

        Args:
            task: Domain entity.

        Returns:
            TaskModel: SQLAlchemy ORM model.
        """
        return TaskModel(
            id=str(task.id),
            title=task.title,
            description=task.description,
            deadline=task.deadline.value,
            completed=task.is_completed,
            project_id=str(task.project_id) if task.project_id else None,
        )

    def _build_filtered_query(
        self,
        completed: Optional[bool],
        overdue: Optional[bool],
        project_id: Optional[ProjectId],
    ):
        """Create a SQLAlchemy query with common task filters applied."""
        query = self._session.query(TaskModel)

        if project_id is not None:
            query = query.filter_by(project_id=str(project_id))

        if completed is not None:
            query = query.filter_by(completed=completed)

        if overdue is not None:
            if overdue:
                query = query.filter(
                    TaskModel.completed.is_(False), TaskModel.deadline < datetime.now(timezone.utc)
                )
            else:
                query = query.filter(
                    (TaskModel.completed.is_(True))
                    | (TaskModel.deadline >= datetime.now(timezone.utc))
                )

        return query
