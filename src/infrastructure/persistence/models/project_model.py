"""SQLAlchemy ORM model for Project."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


def get_utc_now():
    """Get current UTC time (Python 3.13 compatible)."""
    return datetime.now(timezone.utc)


class ProjectModel(Base):
    """ORM model for Project entity.

    This is separate from the domain entity to maintain clean separation
    between domain and infrastructure layers.
    """

    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationship (optional, for ORM queries)
    tasks = relationship("TaskModel", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ProjectModel(id={self.id}, title={self.title})>"
