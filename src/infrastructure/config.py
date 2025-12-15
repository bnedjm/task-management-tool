"""Application configuration management."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration with environment variable support.

    All configuration values can be overridden via environment variables.
    """

    # Database URLs for different environments
    DATABASE_URL: str = "sqlite:///./data/tasks.db"  # Relative path for local dev
    DEV_DATABASE_URL: Optional[str] = None
    PROD_DATABASE_URL: Optional[str] = None

    # Features
    AUTO_COMPLETE_PROJECTS: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    # API
    API_TITLE: str = "Task Management API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = ""

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields from .env
    )

    def get_database_url(self) -> str:
        """Get the appropriate database URL, prioritizing production settings.
        
        Priority:
        1. DATABASE_URL (if set to non-default value, e.g., Railway provides this)
        2. PROD_DATABASE_URL (production override)
        3. DEV_DATABASE_URL (development override)
        4. Default SQLite (local development)
        
        Returns:
            str: Database connection URL to use.
        """
        # If DATABASE_URL is explicitly set to a non-default value, use it
        # This handles Railway and other platforms that set DATABASE_URL directly
        default_sqlite = "sqlite:///./data/tasks.db"
        if self.DATABASE_URL and self.DATABASE_URL != default_sqlite:
            return self.DATABASE_URL
        
        # Otherwise, check for environment-specific overrides
        if self.PROD_DATABASE_URL:
            return self.PROD_DATABASE_URL
        if self.DEV_DATABASE_URL:
            return self.DEV_DATABASE_URL
        
        # Fall back to default SQLite
        return self.DATABASE_URL


_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get application configuration singleton.

    Returns:
        Config: Application configuration instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
