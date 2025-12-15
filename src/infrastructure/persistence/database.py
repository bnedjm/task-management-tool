"""Database connection and session management."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ..config import get_config

# Base class for ORM models
Base = declarative_base()

# Global engine and session factory
_engine = None
_session_factory = None


def init_database(database_url: str | None = None) -> None:
    """Initialize database engine and session factory.

    Args:
        database_url: Database connection URL (uses config if not provided).
    """
    global _engine, _session_factory

    if database_url is None:
        config = get_config()
        # Use the prioritized database URL method
        database_url = config.get_database_url()

    # For SQLite, ensure the directory exists before creating the database
    if database_url.startswith("sqlite"):
        # Extract path from SQLite URL
        # sqlite:///./data/tasks.db -> ./data/tasks.db
        # sqlite:////data/tasks.db -> /data/tasks.db
        if database_url.startswith("sqlite:////"):
            # Absolute path: sqlite:////data/tasks.db
            db_path = database_url.replace("sqlite:////", "/", 1)
        elif database_url.startswith("sqlite:///"):
            # Relative path: sqlite:///./data/tasks.db
            db_path = database_url.replace("sqlite:///", "", 1)
        else:
            # Fallback: sqlite://data/tasks.db
            db_path = database_url.replace("sqlite://", "", 1)

        # Create parent directory if it doesn't exist
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert postgresql:// to postgresql+psycopg:// for psycopg3 driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Configure engine with appropriate parameters
    if database_url.startswith("sqlite"):
        engine_kwargs = {
            "connect_args": {"check_same_thread": False},
            "echo": False,
        }
    else:
        # PostgreSQL/MySQL configuration with connection pooling
        engine_kwargs = {
            "echo": False,
            "pool_pre_ping": True,  # Verify connections before using them
            "pool_size": 5,  # Number of connections to maintain
            "max_overflow": 10,  # Additional connections allowed
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "pool_timeout": 30,  # Timeout for getting connection from pool
        }

    _engine = create_engine(database_url, **engine_kwargs)
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)


def create_tables() -> None:
    """Create all database tables."""
    if _engine is None:
        init_database()
    Base.metadata.create_all(_engine)


def get_session() -> Session:
    """Get a new database session.

    Returns:
        Session: SQLAlchemy session instance.
    """
    if _session_factory is None:
        init_database()
    return _session_factory()


def get_engine():
    """Get the database engine.

    Returns:
        Engine: SQLAlchemy engine instance.
    """
    if _engine is None:
        init_database()
    return _engine
