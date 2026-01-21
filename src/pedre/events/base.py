"""Event system for decoupled game event handling.

This module provides a publish/subscribe event system that allows different parts
of the game to communicate without tight coupling. Components can publish events
when something happens, and other components can subscribe to those events to react.

The event system consists of:
- Event: Base class for all game events
- Concrete event classes: Specific event types for various game occurrences
- EventBus: Central hub for subscribing to and publishing events

Events are used throughout the game to trigger scripts, coordinate systems, and
enable reactive behaviors. Scripts can register event triggers in JSON that will
automatically execute when specific events occur.

Example usage:
    # Create an event bus
    event_bus = EventBus()

    # Subscribe to dialog closed events
    def handle_dialog_closed(event: DialogClosedEvent):
        print(f"Dialog with {event.npc_name} closed at level {event.dialog_level}")

    event_bus.subscribe(DialogClosedEvent, handle_dialog_closed)

    # Publish an event
    event_bus.publish(DialogClosedEvent("martin", 1))

    # Clean up when done
    event_bus.clear()
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

E = TypeVar("E", bound="Event")


@dataclass
class Event:
    """Base event class."""


class EventBus:
    """Central event bus for publish/subscribe event handling.

    The EventBus provides a decoupled communication system where publishers emit events
    without knowing who (if anyone) will handle them, and subscribers can listen for
    events without knowing who publishes them.

    This pattern is essential for the game's script system, allowing different managers
    and systems to react to game events without tight coupling. For example, when a
    dialog closes, the dialog manager publishes a DialogClosedEvent, and the script
    manager (which has subscribed to that event type) can trigger appropriate scripts.

    Thread safety: This implementation is NOT thread-safe. All subscribe, publish, and
    unsubscribe calls should happen on the main game thread.

    Example usage:
        # Create event bus
        bus = EventBus()

        # Subscribe to events
        def on_dialog_closed(event: DialogClosedEvent):
            print(f"Dialog closed: {event.npc_name}")

        bus.subscribe(DialogClosedEvent, on_dialog_closed)

        # Publish events
        bus.publish(DialogClosedEvent("martin", 1))

        # Clean up
        bus.unsubscribe(DialogClosedEvent, on_dialog_closed)
        bus.clear()
    """

    def __init__(self) -> None:
        """Initialize the event bus.

        Creates an empty event bus with no registered listeners.
        """
        self.listeners: dict[type[Event], list[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: type[E], handler: Callable[[E], None]) -> None:
        """Subscribe a handler to an event type.

        Registers a callback function to be invoked whenever an event of the specified
        type is published. Multiple handlers can be subscribed to the same event type,
        and they will be called in the order they were registered.

        The same handler function can be subscribed multiple times, and will be called
        once for each subscription.

        Args:
            event_type: The type of event to listen for (e.g., DialogClosedEvent).
            handler: Callback function that takes the event as parameter.
                    The function should accept one argument of type Event.

        Example:
            def handle_dialog(event: DialogClosedEvent):
                print(f"Dialog closed: {event.npc_name}")

            event_bus.subscribe(DialogClosedEvent, handle_dialog)
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(handler)

    def unsubscribe(self, event_type: type[E], handler: Callable[[E], None]) -> None:
        """Unsubscribe a handler from an event type.

        Removes a previously registered handler from the event type's listener list.
        If the handler was registered multiple times, this removes ALL instances of it.

        If the handler is not currently subscribed, this method does nothing (no error
        is raised).

        Args:
            event_type: The type of event to stop listening for.
            handler: The handler function to remove.

        Example:
            event_bus.unsubscribe(DialogClosedEvent, handle_dialog)
        """
        if event_type in self.listeners:
            self.listeners[event_type] = [h for h in self.listeners[event_type] if h != handler]

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers.

        Dispatches the event to all handlers that have subscribed to this event's type.
        Handlers are called synchronously in the order they were registered.

        If no handlers are subscribed to this event type, the event is silently ignored
        (this is not an error condition).

        If a handler raises an exception, it will propagate up and prevent subsequent
        handlers from being called. Consider using try-except in handlers if you want
        to ensure all handlers run even if one fails.

        Args:
            event: The event instance to publish. The event's type determines which
                  handlers will be called.

        Example:
            event_bus.publish(DialogClosedEvent("martin", 1))
        """
        event_type = type(event)
        if event_type in self.listeners:
            for handler in self.listeners[event_type]:
                handler(event)

    def clear(self) -> None:
        """Clear all event listeners.

        Removes all subscribed handlers for all event types. This is useful for cleanup
        when shutting down the event system or when transitioning between major game states.

        After calling clear(), the event bus will be in the same state as a newly
        constructed EventBus (no listeners registered).

        Warning: This clears ALL listeners for ALL event types. Use with caution in
        production code. Consider unsubscribing specific handlers instead if you only
        need to remove certain listeners.

        Example:
            # Clean shutdown
            event_bus.clear()
        """
        self.listeners.clear()

    def unregister_all(self, subscriber: object) -> None:
        """Unregister all handlers for a specific subscriber.

        This method removes all registered callback functions that belong to the
        specified subscriber instance. It's particularly useful during system
        cleanup to ensure no stale references remain in the event bus.

        Args:
            subscriber: The instance (e.g., manager, system) whose handlers should be removed.
                       Matches handlers by their __self__ attribute if they are bound methods.
        """
        for event_type in self.listeners:
            self.listeners[event_type] = [
                h for h in self.listeners[event_type] if not (hasattr(h, "__self__") and h.__self__ == subscriber)
            ]
