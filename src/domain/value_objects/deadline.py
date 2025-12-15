"""Deadline value object with comparison logic."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Deadline:
    """Value object representing a deadline with comparison capabilities.

    This is an immutable value object that encapsulates deadline logic
    and provides comparison methods for business rule validation.
    """

    value: datetime

    def __post_init__(self):
        """Ensure the datetime is timezone-aware (UTC)."""
        if self.value.tzinfo is None:
            # If naive datetime, assume UTC and make it aware
            object.__setattr__(self, "value", self.value.replace(tzinfo=timezone.utc))

    def is_after(self, other: "Deadline") -> bool:
        """Check if this deadline is after another deadline.

        Args:
            other: The deadline to compare against.

        Returns:
            bool: True if this deadline is after the other deadline.
        """
        return self.value > other.value

    def is_before(self, other: "Deadline") -> bool:
        """Check if this deadline is before another deadline.

        Args:
            other: The deadline to compare against.

        Returns:
            bool: True if this deadline is before the other deadline.
        """
        return self.value < other.value

    def is_within_hours(self, hours: int) -> bool:
        """Check if deadline is within specified hours from now.

        Args:
            hours: Number of hours to check against.

        Returns:
            bool: True if deadline is within the specified hours.
        """
        time_diff = (self.value - datetime.now(timezone.utc)).total_seconds()
        return 0 <= time_diff <= hours * 3600

    def is_overdue(self) -> bool:
        """Check if the deadline has passed.

        Returns:
            bool: True if the deadline is in the past.
        """
        return self.value < datetime.now(timezone.utc)

    @classmethod
    def from_string(cls, date_str: str) -> "Deadline":
        """Create Deadline from ISO format string.

        Args:
            date_str: ISO format datetime string.

        Returns:
            Deadline: Deadline instance.
        """
        return cls(value=datetime.fromisoformat(date_str))

    def to_string(self) -> str:
        """Convert deadline to ISO format string.

        Returns:
            str: ISO format datetime string.
        """
        return self.value.isoformat()

    def __str__(self) -> str:
        """String representation of the deadline."""
        return self.value.isoformat()

    def __eq__(self, other: Any) -> bool:
        """Check equality with another Deadline."""
        if not isinstance(other, Deadline):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """Hash implementation for Deadline."""
        return hash(self.value)
