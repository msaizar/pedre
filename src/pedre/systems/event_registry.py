"""Registry for pluggable custom events.

This module provides the EventRegistry class which allows users to register
custom event types that integrate with the ScriptManager's trigger system.

Creating Custom Events:
    Custom events allow users to extend the event system with their own game-specific
    events. The process involves:
    1. Creating a new Event subclass
    2. Registering it with EventRegistry
    3. Providing a filter function for script triggers
    4. Publishing the event when appropriate

Example - Creating a Weather Changed Event:

    1. Define the event class:

        from dataclasses import dataclass
        from pedre.systems.events import Event
        from pedre.systems.event_registry import EventRegistry

        @dataclass
        class WeatherChangedEvent(Event):
            '''Fired when weather changes.'''
            weather_type: str  # e.g., "rain", "snow", "clear"
            intensity: float   # 0.0 to 1.0

    2. Register the event with a filter function:

        def weather_filter(event: Event, trigger: dict) -> bool:
            '''Check if event matches trigger filters.'''
            if not isinstance(event, WeatherChangedEvent):
                return False
            weather_type = trigger.get("weather_type")
            if weather_type and event.weather_type != weather_type:
                return False
            return True

        EventRegistry.register(
            "weather_changed",
            WeatherChangedEvent,
            weather_filter
        )

    3. Use in JSON scripts:

        {
            "name": "rain_started",
            "trigger": {
                "event": "weather_changed",
                "weather_type": "rain"
            },
            "actions": [
                {"type": "dialog", "speaker": "martin", "text": ["It's raining!"]}
            ]
        }

    4. Publish from your custom system:

        class WeatherSystem(BaseSystem):
            def set_weather(self, weather_type: str, intensity: float):
                self.current_weather = weather_type
                self.intensity = intensity
                # Publish the event
                context.event_bus.publish(WeatherChangedEvent(weather_type, intensity))
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pedre.systems.events import Event

logger = logging.getLogger(__name__)


# Type alias for filter functions
EventFilterFunc = Callable[["Event", dict[str, Any]], bool]


class EventRegistry:
    """Central registry for custom event types.

    The EventRegistry enables users to extend the ScriptManager's trigger system
    with custom events. Each registered event type needs:
    - A unique trigger name (used in JSON scripts)
    - The Event subclass
    - A filter function that checks if an event matches trigger criteria

    Example:
        # Register a custom event
        EventRegistry.register(
            trigger_name="weather_changed",
            event_class=WeatherChangedEvent,
            filter_func=lambda event, trigger: (
                isinstance(event, WeatherChangedEvent) and
                (not trigger.get("weather") or event.weather == trigger["weather"])
            )
        )

        # Now scripts can use:
        # {"trigger": {"event": "weather_changed", "weather": "rain"}}
    """

    # Mapping from trigger name to event class
    _events: ClassVar[dict[str, type[Event]]] = {}

    # Mapping from trigger name to filter function
    _filters: ClassVar[dict[str, EventFilterFunc]] = {}

    @classmethod
    def register(
        cls,
        trigger_name: str,
        event_class: type[Event],
        filter_func: EventFilterFunc | None = None,
    ) -> None:
        """Register a custom event type for use in script triggers.

        Args:
            trigger_name: The "event" value used in JSON script triggers.
                         Should be snake_case (e.g., "weather_changed").
            event_class: The Event subclass that will be published.
            filter_func: Optional function to check if an event matches trigger
                        criteria. Takes (event, trigger_dict) and returns bool.
                        If not provided, a default filter that only checks the
                        event type is used.

        Example:
            # Simple registration (no filtering)
            EventRegistry.register("game_paused", GamePausedEvent)

            # Registration with custom filter
            def weather_filter(event, trigger):
                if not isinstance(event, WeatherChangedEvent):
                    return False
                weather = trigger.get("weather_type")
                return weather is None or event.weather_type == weather

            EventRegistry.register("weather_changed", WeatherChangedEvent, weather_filter)
        """
        if trigger_name in cls._events:
            logger.warning(
                "Event trigger '%s' is being re-registered (was %s, now %s)",
                trigger_name,
                cls._events[trigger_name].__name__,
                event_class.__name__,
            )

        cls._events[trigger_name] = event_class

        # Use provided filter or create default type-only filter
        if filter_func:
            cls._filters[trigger_name] = filter_func
        else:
            # Default filter just checks the event type
            def default_filter(event: Event, trigger: dict[str, Any]) -> bool:  # noqa: ARG001
                return isinstance(event, event_class)

            cls._filters[trigger_name] = default_filter

        logger.debug("Registered custom event: %s -> %s", trigger_name, event_class.__name__)

    @classmethod
    def get_event_class(cls, trigger_name: str) -> type[Event] | None:
        """Get the Event class for a trigger name.

        Args:
            trigger_name: The trigger name to look up.

        Returns:
            The Event subclass, or None if not registered.
        """
        return cls._events.get(trigger_name)

    @classmethod
    def get_filter(cls, trigger_name: str) -> EventFilterFunc | None:
        """Get the filter function for a trigger name.

        Args:
            trigger_name: The trigger name to look up.

        Returns:
            The filter function, or None if not registered.
        """
        return cls._filters.get(trigger_name)

    @classmethod
    def is_registered(cls, trigger_name: str) -> bool:
        """Check if a trigger name is registered.

        Args:
            trigger_name: The trigger name to check.

        Returns:
            True if the event type is registered, False otherwise.
        """
        return trigger_name in cls._events

    @classmethod
    def get_all_trigger_names(cls) -> list[str]:
        """Get all registered custom event trigger names.

        Returns:
            List of trigger name strings.
        """
        return list(cls._events.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear the registry. Useful for testing.

        Warning:
            This should not be called in production code as it will break
            any code that depends on registered custom events.
        """
        cls._events.clear()
        cls._filters.clear()
        logger.debug("Event registry cleared")
