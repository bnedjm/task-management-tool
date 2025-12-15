"""Event bus implementation for domain event handling."""

import logging
from typing import Callable, Dict, List, Type

from ...domain.events.base import DomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    """Simple in-memory event bus with handler registration.

    Allows decoupled communication between components via domain events.
    Handlers can be registered for specific event types and will be
    invoked when those events are published.
    """

    def __init__(self):
        """Initialize the event bus."""
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = {}

    def register(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        """Register an event handler for a specific event type.

        Args:
            event_type: The type of event to handle.
            handler: Callable that handles the event.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler {handler.__name__} for {event_type.__name__}")

    def unregister(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        """Unregister an event handler.

        Args:
            event_type: The type of event.
            handler: The handler to unregister.
        """
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    def publish(self, events: List[DomainEvent]) -> None:
        """Publish a list of domain events to registered handlers.

        Args:
            events: List of domain events to publish.
        """
        for event in events:
            event_type = type(event)
            handlers = self._handlers.get(event_type, [])

            logger.debug(f"Publishing {event_type.__name__} to {len(handlers)} handler(s)")

            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(
                        f"Error in handler {handler.__name__} "
                        f"for event {event_type.__name__}: {e}",
                        exc_info=True,
                    )

    def clear_handlers(self) -> None:
        """Clear all registered handlers (useful for testing)."""
        self._handlers.clear()
