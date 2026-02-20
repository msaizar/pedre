"""Registry for mapping event names to event classes.

This module provides the EventRegistry class which allows plugins to register
their events by name. This enables the script plugin to discover and subscribe
to events without direct class imports, improving decoupling.
"""

import logging
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pedre.events.base import Event

logger = logging.getLogger(__name__)


class EventParseError(Exception):
    """Raised when an event cannot be parsed."""


class EventRegistry:
    """Central registry for mapping event string names to event classes.

    The EventRegistry allows plugins to register their event types using a
    decorator. Other plugins (like ScriptPlugin) can then retrieve the event
    classes by name to perform dynamic subscriptions.
    """

    _events: ClassVar[dict[str, type[Event]]] = {}

    @classmethod
    def register(cls, event_class: type[Event]) -> type[Event]:
        """Decorator to register an event class."""
        event_name = event_class.name

        if event_name in cls._events:
            msg = f"Event '{event_name}' already registered"
            raise ValueError(msg)

        cls._events[event_name] = event_class
        logger.debug("Registered event: %s", event_name)
        return event_class

    @classmethod
    def create(cls, data: dict[str, Any]) -> Event:
        """Create an event from a dictionary."""
        name = data.get("name")
        if not name:
            msg = "Event missing 'name' field"
            raise EventParseError(msg)

        event_cls = cls._events.get(name)
        if not event_cls:
            msg = f"Unknown event '{name}'"
            raise EventParseError(msg)

        try:
            return event_cls.from_dict(data)
        except Exception as exc:
            msg = f"Failed to parse event '{name}': {exc}"
            raise EventParseError(msg) from exc

    @classmethod
    def get(cls, name: str) -> type[Event] | None:
        """Get an event from a name."""
        return cls._events.get(name)

    @classmethod
    def get_all_names(cls) -> list[str]:
        """Get all registered event names.

        Returns:
            List of event names strings that are registered.
        """
        return list(cls._events.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if an event is registered.

        Args:
            name: The event name to check.

        Returns:
            True if the event name has an event registered, False otherwise.

        """
        return name in cls._events

    @classmethod
    def clear(cls) -> None:
        """Clear the registry.

        Removes all registered actions. This is primarily useful
        for testing to ensure a clean state between tests.
        """
        cls._events.clear()
        logger.debug("Event registry cleared")
