"""SQLAlchemy implementation of ProjectRepository."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from ....domain.entities.project import Project
from ....domain.repositories.project_repository import ProjectRepository
from ....domain.value_objects.deadline import Deadline
from ....domain.value_objects.ids import ProjectId, TaskId
from ..models.project_model import ProjectModel
from ..models.task_model import TaskModel


class SQLAlchemyProjectRepository(ProjectRepository):
    """SQLAlchemy concrete implementation of ProjectRepository.

    Handles conversion between domain entities and ORM models.
    """

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session instance.
        """
        self._session = session

    def save(self, project: Project) -> None:
        """Persist a project entity.

        Args:
            project: The project entity to save.
        """
        orm_model = self._to_orm(project)
        self._session.merge(orm_model)

    def get_by_id(self, project_id: ProjectId) -> Optional[Project]:
        """Retrieve a project by its ID.

        Args:
            project_id: The ID of the project to retrieve.

        Returns:
            Optional[Project]: The project if found, None otherwise.
        """
        orm_model = self._session.query(ProjectModel).filter_by(id=str(project_id)).first()
        return self._to_domain(orm_model) if orm_model else None

    def list_all(self) -> List[Project]:
        """Retrieve all projects.

        Returns:
            List[Project]: List of all projects.
        """
        orm_models = self._session.query(ProjectModel).all()
        return [self._to_domain(model) for model in orm_models]

    def list_by_filter(self, completed: Optional[bool] = None) -> List[Project]:
        """Retrieve projects matching filter criteria.

        Args:
            completed: Filter by completion status (None for all).

        Returns:
            List[Project]: List of projects matching the criteria.
        """
        query = self._build_filtered_query(completed)
        orm_models = query.order_by(ProjectModel.created_at.desc(), ProjectModel.id.desc()).all()
        return [self._to_domain(model) for model in orm_models]

    def list_by_filter_paginated(
        self, completed: Optional[bool], offset: int, limit: int
    ) -> tuple[List[Project], int]:
        """Retrieve projects with pagination and total count."""
        base_query = self._build_filtered_query(completed)
        total = base_query.count()

        paged_query = (
            base_query.order_by(ProjectModel.created_at.desc(), ProjectModel.id.desc())
            .offset(offset)
            .limit(limit)
        )
        orm_models = paged_query.all()
        return [self._to_domain(model) for model in orm_models], total

    def delete(self, project_id: ProjectId) -> None:
        """Delete a project.

        Args:
            project_id: The ID of the project to delete.
        """
        self._session.query(ProjectModel).filter_by(id=str(project_id)).delete()

    def get_timestamps(self, project_id: ProjectId) -> tuple[datetime, datetime]:
        """Get created_at and updated_at timestamps for a project.

        Args:
            project_id: The ID of the project.

        Returns:
            tuple[datetime, datetime]: (created_at, updated_at) timestamps.
        """
        orm_model = self._session.query(ProjectModel).filter_by(id=str(project_id)).first()
        if orm_model:
            return (orm_model.created_at, orm_model.updated_at)
        return (datetime.now(timezone.utc), datetime.now(timezone.utc))

    def _to_domain(self, orm_model: ProjectModel) -> Project:
        """Convert ORM model to domain entity.

        Args:
            orm_model: SQLAlchemy ORM model.

        Returns:
            Project: Domain entity.
        """
        project = Project(
            id=ProjectId.from_string(orm_model.id),
            title=orm_model.title,
            description=orm_model.description,
            deadline=Deadline.from_datetime(orm_model.deadline, validate_past=False),
            completed=orm_model.completed,
        )

        # Load task associations using internal reconstruction method
        # to avoid triggering business logic (like auto-reopening)
        tasks = self._session.query(TaskModel).filter_by(project_id=orm_model.id).all()

        for task_model in tasks:
            task_id = TaskId.from_string(task_model.id)
            project._add_task_for_reconstruction(task_id)  # ← Use reconstruction method
            if task_model.completed:
                project.mark_task_completed(task_id)

        return project

    def _to_orm(self, project: Project) -> ProjectModel:
        """Convert domain entity to ORM model.

        Args:
            project: Domain entity.

        Returns:
            ProjectModel: SQLAlchemy ORM model.
        """
        return ProjectModel(
            id=str(project.id),
            title=project.title,
            description=project.description,
            deadline=project.deadline.value,
            completed=project.is_completed,
        )

    def _build_filtered_query(self, completed: Optional[bool]):
        """Create a SQLAlchemy query with common project filters applied."""
        query = self._session.query(ProjectModel)

        if completed is not None:
            query = query.filter_by(completed=completed)

        return query
