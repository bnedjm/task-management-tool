"""Event bus and event handler implementations."""

from .event_bus import EventBus
from .handlers import (
    AutoCompleteProjectHandler,
    DeadlineWarningChecker,
    TaskCompletionLogger,
    TaskDeadlineAdjustmentHandler,
)

__all__ = [
    "EventBus",
    "AutoCompleteProjectHandler",
    "TaskDeadlineAdjustmentHandler",
    "DeadlineWarningChecker",
    "TaskCompletionLogger",
]
