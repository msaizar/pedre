"""Registry for mapping event names to event classes.

This module provides the EventRegistry class which allows systems to register
their events by name. This enables the script system to discover and subscribe
to events without direct class imports, improving decoupling.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=type)


class EventRegistry:
    """Central registry for mapping event string names to event classes.

    The EventRegistry allows systems to register their event types using a
    decorator. Other systems (like ScriptManager) can then retrieve the event
    classes by name to perform dynamic subscriptions.
    """

    _events: ClassVar[dict[str, type]] = {}
    _names: ClassVar[dict[type, str]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[T]], type[T]]:
        """Decorator to register an event class with a unique string name.

        Args:
            name: The string name to associate with the event class
                 (e.g., "dialog_closed").

        Returns:
            The decorator function.
        """

        def decorator(event_class: type[T]) -> type[T]:
            if name in cls._events:
                logger.warning(
                    "Event '%s' is being re-registered (was %s, now %s)",
                    name,
                    cls._events[name].__name__,
                    event_class.__name__,
                )
            cls._events[name] = event_class
            cls._names[event_class] = name
            logger.debug("Registered event: %s -> %s", name, event_class.__name__)
            return event_class

        return decorator

    @classmethod
    def get(cls, name: str) -> type | None:
        """Get a registered event class by its name."""
        return cls._events.get(name)

    @classmethod
    def get_name(cls, event_class: type) -> str | None:
        """Get the registered name for an event class."""
        return cls._names.get(event_class)

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (primarily for testing)."""
        cls._events.clear()
        cls._names.clear()
