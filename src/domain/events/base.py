"""Base domain event class."""

from datetime import datetime, timezone
from typing import Any, Dict


class DomainEvent:
    """Base class for all domain events.

    Domain events represent something that happened in the domain
    that domain experts care about. They are immutable and should
    carry all information needed by event handlers.
    """

    def __init__(self):
        """Initialize domain event with timestamp."""
        self.occurred_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of the event.
        """
        return {
            "event_type": self.__class__.__name__,
            "occurred_at": self.occurred_at.isoformat(),
        }
