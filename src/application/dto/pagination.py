"""Shared pagination result DTOs."""

from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """Generic pagination container used across services."""

    items: Sequence[T]
    total: int
    offset: int
    limit: int

    @property
    def has_more(self) -> bool:
        """Whether there are more records beyond the current page."""
        return self.offset + len(self.items) < self.total
