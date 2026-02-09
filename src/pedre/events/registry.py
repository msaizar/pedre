"""Registry for mapping event names to event classes.

This module provides the EventRegistry class which allows plugins to register
their events by name. This enables the script plugin to discover and subscribe
to events without direct class imports, improving decoupling.
"""

import logging
from typing import TYPE_CHECKING, ClassVar, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=type)


class EventRegistry:
    """Central registry for mapping event string names to event classes.

    The EventRegistry allows plugins to register their event types using a
    decorator. Other plugins (like ScriptPlugin) can then retrieve the event
    classes by name to perform dynamic subscriptions.
    """

    _events: ClassVar[dict[str, type]] = {}
    _names: ClassVar[dict[type, str]] = {}
    _trigger_keys: ClassVar[dict[str, frozenset[str]]] = {}

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

            # Auto-register trigger keys if event class has them
            if hasattr(event_class, "trigger_keys"):
                cls._trigger_keys[name] = event_class.trigger_keys  # type: ignore[attr-defined]
                logger.debug("Registered trigger keys for event: %s", name)

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
    def is_registered(cls, name: str) -> bool:
        """Check if an event type is registered.

        Args:
            name: The event type name to check.

        Returns:
            True if the event type is registered, False otherwise.
        """
        return name in cls._events

    @classmethod
    def get_all_types(cls) -> list[str]:
        """Get all registered event type names.

        Returns:
            List of event type strings that are registered.
        """
        return list(cls._events.keys())

    @classmethod
    def get_trigger_keys(cls, name: str) -> frozenset[str] | None:
        """Get valid trigger filter keys for an event type.

        Args:
            name: The event type name.

        Returns:
            Frozenset of valid filter key names, or None if not declared.

        Example:
            Getting trigger keys for an event::

                keys = EventRegistry.get_trigger_keys("item_consumed")
                # Returns: frozenset({"item_id", "category"})

                # Check if a filter key is valid
                if "category" in keys:
                    # Valid filter key
                    pass
        """
        return cls._trigger_keys.get(name)

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (primarily for testing)."""
        cls._events.clear()
        cls._names.clear()
        cls._trigger_keys.clear()
