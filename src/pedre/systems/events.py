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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class Event:
    """Base event class."""


@dataclass
class DialogClosedEvent(Event):
    """Fired when a dialog is closed.

    This event is published by the dialog manager when the player dismisses a dialog
    window. It's commonly used to trigger scripts that should run after a conversation,
    such as advancing the story or showing follow-up actions.

    The event includes both the NPC name and their dialog level at the time the dialog
    was shown, allowing scripts to trigger on specific conversation stages.

    Script trigger example:
        {
            "trigger": {
                "event": "dialog_closed",
                "npc": "martin",
                "dialog_level": 1
            }
        }

    The trigger filters are optional:
    - npc: Only trigger for specific NPC (omit to trigger for any NPC)
    - dialog_level: Only trigger at specific dialog level (omit to trigger at any level)

    Attributes:
        npc_name: Name of the NPC whose dialog was closed.
        dialog_level: Conversation level at the time dialog was shown.
    """

    npc_name: str
    dialog_level: int


@dataclass
class DialogOpenedEvent(Event):
    """Fired when a dialog is opened.

    This event is published by the dialog manager when a dialog window is shown to
    the player. It can be used to track when conversations begin or to coordinate
    other systems with dialog display.

    Note: This event is not currently used for script triggers, but is available
    for programmatic event handling.

    Attributes:
        npc_name: Name of the NPC whose dialog was opened.
        dialog_level: Current conversation level.
    """

    npc_name: str
    dialog_level: int


@dataclass
class InventoryClosedEvent(Event):
    """Fired when the inventory view is closed.

    This event is published when the player closes the inventory screen. It can be
    used to trigger scripts after the player has viewed their items, commonly in
    tutorial sequences or quest chains.

    Script trigger example:
        {
            "trigger": {
                "event": "inventory_closed"
            }
        }

    Attributes:
        has_been_accessed: Whether inventory has been accessed before.
    """

    has_been_accessed: bool


@dataclass
class NPCInteractedEvent(Event):
    """Fired when player interacts with an NPC.

    This event is published when the player presses the interaction key while facing
    an NPC. It triggers before any dialog is shown, making it useful for scripts that
    need to run custom logic at the start of an NPC interaction.

    The event is published even if the NPC has no dialog configured, allowing scripts
    to handle the interaction completely.

    Script trigger example:
        {
            "trigger": {
                "event": "npc_interacted",
                "npc": "martin"
            }
        }

    The npc filter is optional:
    - npc: Only trigger for specific NPC (omit to trigger for any NPC)

    Attributes:
        npc_name: Name of the NPC that was interacted with.
        dialog_level: Current conversation level.
    """

    npc_name: str
    dialog_level: int


@dataclass
class ObjectInteractedEvent(Event):
    """Fired when player interacts with an interactive object.

    This event is published when the player presses the interaction key while facing
    an interactive object in the game world. Objects are tiles or sprites marked as
    interactive in the map data.

    The script manager tracks which objects have been interacted with, allowing
    conditions to check if an object was previously activated.

    Script trigger example:
        {
            "trigger": {
                "event": "object_interacted",
                "object_name": "treasure_chest"
            }
        }

    The object_name filter is optional:
    - object_name: Only trigger for specific object (omit to trigger for any object)

    Attributes:
        object_name: Name of the object that was interacted with.
    """

    object_name: str


@dataclass
class NPCMovementCompleteEvent(Event):
    """Fired when an NPC completes movement to target.

    This event is published by the NPC manager when an NPC finishes pathfinding and
    arrives at their destination. It's useful for chaining actions that should occur
    after an NPC reaches a specific location.

    The event is emitted when both the NPC's path is empty and the is_moving flag
    becomes False, ensuring movement is fully complete.

    Script trigger example:
        {
            "trigger": {
                "event": "npc_movement_complete",
                "npc": "martin"
            }
        }

    The npc filter is optional:
    - npc: Only trigger for specific NPC (omit to trigger for any NPC)

    Attributes:
        npc_name: Name of the NPC that completed movement.
    """

    npc_name: str


@dataclass
class NPCAppearCompleteEvent(Event):
    """Fired when an NPC completes appear animation.

    This event is published by the NPC manager when an AnimatedNPC finishes its appear
    animation. AnimatedNPCs play a special animation when they're revealed, and this
    event signals that the animation has completed.

    This event is typically used internally by wait actions (WaitForNPCsAppearAction)
    rather than as a direct script trigger, but it's available for custom event handling.

    Note: This event is not currently used for script triggers, but is available
    for programmatic event handling.

    Attributes:
        npc_name: Name of the NPC that appeared.
    """

    npc_name: str


@dataclass
class NPCDisappearCompleteEvent(Event):
    """Fired when an NPC completes disappear animation.

    This event is published by the NPC manager when an AnimatedNPC finishes its disappear
    animation. The disappear animation is triggered by the StartDisappearAnimationAction,
    and this event signals when it's safe to perform cleanup or trigger follow-up actions.

    The NPC sprite is automatically hidden after the animation completes, just before
    this event is published.

    Script trigger example:
        {
            "trigger": {
                "event": "npc_disappear_complete",
                "npc": "martin"
            }
        }

    The npc filter is optional:
    - npc: Only trigger for specific NPC (omit to trigger for any NPC)

    Attributes:
        npc_name: Name of the NPC that disappeared.
    """

    npc_name: str


@dataclass
class MapTransitionEvent(Event):
    """Fired when transitioning to a new map.

    This event is published when the player transitions between different maps or scenes
    in the game world. It provides information about both the origin and destination maps.

    This event can be used to trigger cutscenes, initialize map-specific state, or clean
    up resources from the previous map.

    Note: This event is not currently used for script triggers, but is available
    for programmatic event handling.

    Attributes:
        from_map: Name of the map being left.
        to_map: Name of the map being entered.
    """

    from_map: str
    to_map: str


@dataclass
class ScriptCompleteEvent(Event):
    """Fired when a script completes execution.

    This event is published by the script manager when a script's action sequence
    finishes executing. It allows scripts to chain together, where one script waits
    for another to complete before starting.

    This is particularly useful for complex multi-stage sequences where different
    scripts handle different phases of a cutscene or story event.

    Script trigger example:
        {
            "trigger": {
                "event": "script_complete",
                "script": "intro_cutscene"
            }
        }

    The script filter is optional:
    - script: Only trigger when specific script completes (omit to trigger for any script)

    Attributes:
        script_name: Name of the script that completed.
    """

    script_name: str


@dataclass
class GameStartEvent(Event):
    """Fired when a new game starts (not on load).

    This event is published by the game view when a fresh game is initialized
    (not when loading from a save). It's useful for triggering intro sequences,
    initial dialogs, or one-time setup that should only happen on new games.

    The event is only published once per new game, and run_once scripts triggered
    by this event won't fire again when loading a save that already completed them.

    Script trigger example:
        {
            "run_once": true,
            "trigger": {
                "event": "game_start"
            }
        }

    Note: This event has no attributes - it simply signals that a new game has begun.
    """


@dataclass
class SceneStartEvent(Event):
    """Fired when a new scene/map starts loading.

    This event is published by the game view after a map is loaded and all systems
    are initialized. It fires on every map transition and when starting a new game,
    making it useful for scene-specific initialization, cutscenes, or gameplay that
    should trigger each time a particular scene is entered.

    Unlike GameStartEvent which only fires once for new games, SceneStartEvent fires
    every time setup() completes, whether from a new game, loading a save, or
    transitioning through a portal.

    Script trigger example:
        {
            "trigger": {
                "event": "scene_start",
                "scene": "forest"
            }
        }

    The scene filter is optional:
    - scene: Only trigger for specific scene name (omit to trigger for any scene)

    Attributes:
        scene_name: Name of the scene/map that just started (e.g., "casa", "forest").
    """

    scene_name: str


@dataclass
class ItemAcquiredEvent(Event):
    """Fired when player acquires an inventory item.

    This event is published by the inventory manager when an item is added to the
    player's inventory for the first time. It can be used to trigger congratulatory
    messages, unlock new areas, or advance quest chains.

    The event is only published when an item transitions from unacquired to acquired.
    Attempting to acquire an already-owned item will not fire this event.

    Script trigger example:
        {
            "trigger": {
                "event": "item_acquired",
                "item_id": "rusty_key"
            }
        }

    The item_id filter is optional:
    - item_id: Only trigger for specific item (omit to trigger for any item)

    Attributes:
        item_id: Unique identifier of the item that was acquired.
        item_name: Display name of the item (for logging/debugging).
    """

    item_id: str
    item_name: str


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
        self.listeners: dict[type[Event], list[Callable[[Event], None]]] = {}

    def subscribe(self, event_type: type[Event], handler: Callable[[Event], None]) -> None:
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

    def unsubscribe(self, event_type: type[Event], handler: Callable[[Event], None]) -> None:
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
