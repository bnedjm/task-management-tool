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
        """Ensure the datetime is timezone-aware (UTC) and validate it's not in the past."""
        if self.value.tzinfo is None:
            # If naive datetime, assume UTC and make it aware
            object.__setattr__(self, "value", self.value.replace(tzinfo=timezone.utc))

        # Validate that the deadline is not in the past
        now = datetime.now(timezone.utc)
        if self.value < now:
            from ..exceptions.project_exceptions import PastDateError

            raise PastDateError(self.value.isoformat())

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

    @classmethod
    def from_datetime(cls, dt: datetime, validate_past: bool = True) -> "Deadline":
        """Create Deadline from datetime, optionally skipping past date validation.

        This method is useful when loading deadlines from persistence where
        past dates may exist in the database.

        Args:
            dt: Datetime value for the deadline.
            validate_past: If False, skip past date validation (default: True).

        Returns:
            Deadline: Deadline instance.
        """
        instance = cls.__new__(cls)
        # Set the value directly without going through __post_init__ validation
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        object.__setattr__(instance, "value", dt)

        # Only validate if requested
        if validate_past:
            now = datetime.now(timezone.utc)
            if instance.value < now:
                from ..exceptions.project_exceptions import PastDateError

                raise PastDateError(instance.value.isoformat())

        return instance

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
