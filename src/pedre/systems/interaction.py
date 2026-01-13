"""Interaction manager for handling interactive objects in the game world.

This module provides the InteractionManager class, which manages interactive objects
that the player can activate by pressing an interaction key. Interactive objects are
typically defined in Tiled maps as objects with special properties that determine their
behavior when interacted with.

The interaction system supports:
- Distance-based interaction (objects must be within range)
- Multiple interaction types (messages, toggles, custom behaviors)
- Property-driven configuration from Tiled
- Automatic nearest-object selection

Interactive objects are commonly used for:
- Environmental storytelling (reading signs, examining objects)
- Puzzle elements (switches, levers, buttons)
- Item pickups and loot containers
- Quest triggers and progression markers

The manager uses a simple distance check to determine which objects are within
interaction range, automatically selecting the nearest one when multiple objects
are nearby. This provides intuitive player interaction without requiring precise
positioning or targeting.

Example usage in a map:
    # In Tiled, create an object with properties:
    # - name: "town_sign"
    # - interaction_type: "message"
    # - title: "Welcome"
    # - message: "Welcome to Townsville!"

    # In game code:
    interaction_mgr = InteractionManager(interaction_distance=64.0)

    # Register objects from map
    for obj_sprite in interactive_layer:
        interaction_mgr.register_object(
            sprite=obj_sprite,
            name=obj_sprite.properties["name"],
            properties=obj_sprite.properties
        )

    # In game loop, check for interaction
    if input_mgr.is_key_pressed(arcade.key.E):
        obj = interaction_mgr.get_nearby_object(player_sprite)
        if obj:
            interaction_mgr.handle_interaction(obj, dialog_manager)
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import arcade

    from pedre.systems.dialog import DialogManager

logger = logging.getLogger(__name__)


@dataclass
class InteractiveObject:
    """Represents an interactive object in the game world.

    An InteractiveObject wraps an arcade Sprite with metadata that defines how the
    object behaves when the player interacts with it. These objects are typically
    created from Tiled map data where designers define interactive elements with
    custom properties.

    The interaction_type determines what happens when the object is activated:
    - "message": Shows a dialog box with text (requires title and message properties)
    - "toggle": Changes the object's state (on/off, useful for switches)
    - Custom types can be added by extending the InteractionManager

    The properties dictionary contains all custom properties from the Tiled object,
    allowing designers to configure behavior without code changes. Common properties
    include message text, interaction effects, state values, and trigger flags.

    Attributes:
        sprite: The arcade Sprite representing this object in the game world.
               Used for position, rendering, and distance calculations.
        name: Unique identifier for this object. Used to track interaction state
             and reference the object in scripts or events.
        interaction_type: Type of interaction behavior (e.g., "message", "toggle").
                        Determines which handler method is called.
        properties: Dictionary of custom properties from Tiled or code. Contains
                   configuration like message text, state values, and behavior flags.

    Example from Tiled:
        Object properties:
        - name: "mysterious_lever"
        - interaction_type: "toggle"
        - state: "off"
        - description: "An old lever covered in dust"
    """

    sprite: arcade.Sprite
    name: str
    interaction_type: str
    properties: dict


class InteractionManager:
    """Manages interactive objects and their behaviors.

    The InteractionManager acts as a registry and handler for all interactive objects
    in the game world. It maintains a collection of registered objects, determines which
    objects are within interaction range of the player, and dispatches interaction events
    to the appropriate handler based on the object's type.

    This manager provides a flexible, data-driven approach to game interactions where
    designers can configure interactive elements in Tiled without requiring code changes.
    The manager handles the common patterns (distance checking, nearest object selection)
    while allowing custom interaction types to be added through handler methods.

    Key responsibilities:
    - Registering interactive objects from map data
    - Finding nearby objects within interaction distance
    - Routing interactions to type-specific handlers
    - Managing object state changes (toggles, flags, etc.)

    The distance-based interaction system uses Euclidean distance to determine if an
    object is within range. When multiple objects are nearby, the nearest one is selected
    automatically, providing intuitive interaction behavior without explicit targeting.

    Attributes:
        interaction_distance: Maximum distance in pixels for interaction (default 64.0,
                            which is about 2 tiles at 32x32 tile size).
        interactive_objects: Dictionary mapping object names to InteractiveObject instances.
                           Used for O(1) lookups by name and iteration for distance checks.
    """

    def __init__(self, interaction_distance: float = 64.0) -> None:
        """Initialize the interaction manager with configurable interaction distance.

        Creates a new InteractionManager with an empty registry of interactive objects.
        The interaction distance determines how close the player must be to an object
        to interact with it.

        The default distance of 64 pixels (2 tiles at 32x32 tile size) provides a
        comfortable interaction range that feels natural - close enough to require
        deliberate positioning but not so close as to be frustrating. Adjust this
        value based on your game's tile size and desired interaction feel.

        Args:
            interaction_distance: Maximum distance in pixels from the player's center
                                to an object's center for interaction to be possible.
                                Typical values: 32.0 (1 tile), 64.0 (2 tiles), 96.0 (3 tiles).
                                Default is 64.0 for comfortable interaction range.
        """
        self.interaction_distance = interaction_distance
        self.interactive_objects: dict[str, InteractiveObject] = {}

    def register_object(self, sprite: arcade.Sprite, name: str, properties: dict) -> None:
        """Register an interactive object in the manager.

        Adds a new interactive object to the manager's registry, making it available for
        interaction queries and handling. This method is typically called during map
        loading when processing Tiled object layers that contain interactive elements.

        The properties dictionary should contain at minimum an "interaction_type" key
        that determines the object's behavior. If not provided, defaults to "generic".
        Additional properties depend on the interaction type:
        - "message": Requires "title" and "message" properties
        - "toggle": Can include "state" property (defaults to "off")

        Objects are stored by name, so each name must be unique within the manager.
        Registering an object with an existing name will overwrite the previous object.

        Args:
            sprite: The arcade Sprite representing this object visually. The sprite's
                   position (center_x, center_y) is used for distance calculations.
            name: Unique identifier for this object. Used for lookups and tracking.
                 Should match the object's name in Tiled for consistency.
            properties: Dictionary of custom properties from Tiled. Should include
                       "interaction_type" and any type-specific properties. The entire
                       dictionary is stored with the object for flexible configuration.

        Example:
            # From map loading code
            for obj in tiled_map.object_lists["Interactive"]:
                interaction_mgr.register_object(
                    sprite=obj.sprite,
                    name=obj.name,
                    properties=obj.properties
                )
        """
        interaction_type = properties.get("interaction_type", "generic")

        obj = InteractiveObject(
            sprite=sprite,
            name=name,
            interaction_type=interaction_type,
            properties=properties,
        )

        self.interactive_objects[name] = obj
        logger.info("Registered interactive object: %s (type: %s)", name, interaction_type)

    def get_nearby_object(self, player_sprite: arcade.Sprite) -> InteractiveObject | None:
        """Get the nearest interactive object within interaction distance.

        Searches all registered interactive objects and returns the one closest to the
        player that is within the interaction distance threshold. This method uses
        Euclidean distance (straight-line distance) to determine proximity.

        When multiple objects are within range, the nearest one is selected. This provides
        intuitive behavior where the player interacts with the closest object without
        needing to explicitly target it. If no objects are within range, returns None.

        The distance calculation uses the center points of both the player sprite and
        object sprites, so the effective interaction range depends on sprite sizes.
        Larger sprites may feel like they have a shorter interaction range since their
        edges are further from their centers.

        This method is typically called in the game's update loop when the player presses
        the interaction key, to determine what (if anything) should be interacted with.

        Args:
            player_sprite: The player's arcade Sprite. The sprite's center_x and center_y
                         are used as the player's position for distance calculations.

        Returns:
            The nearest InteractiveObject within interaction_distance, or None if no
            objects are in range. When multiple objects are equidistant (rare), returns
            whichever was checked first (non-deterministic due to dict iteration).

        Example:
            # In game update loop
            if input_mgr.is_key_pressed(arcade.key.E):
                nearby_obj = interaction_mgr.get_nearby_object(self.player_sprite)
                if nearby_obj:
                    self.interaction_mgr.handle_interaction(nearby_obj, self.dialog_mgr)
                else:
                    # Optional: Show "nothing to interact with" message
                    pass
        """
        nearest_obj = None
        nearest_distance = float("inf")

        for obj in self.interactive_objects.values():
            dx = player_sprite.center_x - obj.sprite.center_x
            dy = player_sprite.center_y - obj.sprite.center_y
            distance = (dx**2 + dy**2) ** 0.5

            if distance < self.interaction_distance and distance < nearest_distance:
                nearest_obj = obj
                nearest_distance = distance

        return nearest_obj

    def handle_interaction(
        self,
        obj: InteractiveObject,
        dialog_manager: DialogManager | None = None,
    ) -> bool:
        """Handle interaction with an object by dispatching to type-specific handler.

        This is the main entry point for processing interactions. It examines the object's
        interaction_type and routes to the appropriate handler method. This pattern allows
        for easy extension with new interaction types by adding new handler methods.

        Currently supported interaction types:
        - "message": Shows a dialog box with title and message text
        - "toggle": Toggles the object's state between "on" and "off"

        If an unknown interaction type is encountered, a warning is logged and False is
        returned. This allows the game to continue running even if there are configuration
        errors in the map data.

        The dialog_manager parameter is optional but required for "message" type interactions.
        If a message interaction is triggered without a dialog_manager, the interaction will
        fail gracefully.

        Args:
            obj: The InteractiveObject to interact with. The object's interaction_type
                determines which handler method is called.
            dialog_manager: Optional DialogManager for displaying message interactions.
                          Required for "message" type, unused for other types. Pass None
                          if dialog is not available or not needed.

        Returns:
            True if the interaction was successfully handled, False if the interaction
            failed (unknown type, missing dependencies, etc.). The return value can be
            used to provide feedback to the player or trigger follow-up actions.

        Example:
            obj = interaction_mgr.get_nearby_object(player_sprite)
            if obj:
                success = interaction_mgr.handle_interaction(obj, dialog_mgr)
                if success:
                    audio_mgr.play_sfx("interact.wav")
                    context.interacted_objects.add(obj.name)
        """
        if obj.interaction_type == "message":
            return self._handle_message(obj, dialog_manager)
        if obj.interaction_type == "toggle":
            return self._handle_toggle(obj)
        logger.warning("Unknown interaction type: %s", obj.interaction_type)
        return False

    def _handle_message(self, obj: InteractiveObject, dialog_manager: DialogManager | None) -> bool:
        """Handle showing a message dialog to the player.

        This handler displays a dialog box with text when the player interacts with an
        object. It's commonly used for signs, books, notes, and environmental storytelling
        elements that provide information to the player.

        The message is extracted from the object's properties dictionary. Expected properties:
        - "message": The text to display (defaults to "..." if missing)
        - "title": The dialog box title/speaker name (defaults to "Info" if missing)

        If no dialog_manager is provided, the interaction fails gracefully and returns False.
        This prevents crashes when the system is called without proper setup.

        Args:
            obj: The InteractiveObject containing message properties. Should have "message"
                and optionally "title" in its properties dictionary.
            dialog_manager: DialogManager for displaying the message. If None, the interaction
                          fails and returns False.

        Returns:
            True if the message was successfully shown (dialog_manager was available),
            False if dialog_manager was None.

        Example Tiled properties:
            - interaction_type: "message"
            - title: "Town Sign"
            - message: "Welcome to Adventureville! Population: 42"
        """
        if not dialog_manager:
            return False

        message = obj.properties.get("message", "...")
        title = obj.properties.get("title", "Info")
        dialog_manager.show_dialog(title, [message])
        return True

    def _handle_toggle(self, obj: InteractiveObject) -> bool:
        """Handle toggling an object's state between on and off.

        This handler switches the object's state property between "on" and "off" each
        time it's interacted with. It's commonly used for switches, levers, buttons,
        and other interactive elements that have two states.

        The state is stored in the object's properties dictionary under the "state" key.
        If no state exists, it defaults to "off" before toggling. The new state is stored
        back in the properties dictionary, making it persistent for the game session.

        This handler always succeeds and returns True. The state change is logged for
        debugging purposes. Game code can query the object's state via its properties
        to trigger visual changes (sprite swaps) or game logic (opening doors, etc.).

        Args:
            obj: The InteractiveObject to toggle. The object's properties["state"] will
                be switched from "off" to "on" or vice versa.

        Returns:
            True (always succeeds). The toggle operation cannot fail.

        Example usage:
            # In Tiled:
            - interaction_type: "toggle"
            - state: "off"
            - linked_door: "secret_passage"

            # In game code after interaction:
            if obj.properties["state"] == "on":
                open_door(obj.properties["linked_door"])
                obj.sprite.texture = lever_on_texture
            else:
                close_door(obj.properties["linked_door"])
                obj.sprite.texture = lever_off_texture
        """
        # Toggle visibility or other state
        current_state = obj.properties.get("state", "off")
        new_state = "on" if current_state == "off" else "off"
        obj.properties["state"] = new_state

        logger.info("Toggled object %s to state: %s", obj.name, new_state)
        return True

    def clear(self) -> None:
        """Clear all registered interactive objects from the manager.

        Removes all interactive objects from the registry, effectively resetting the
        manager to its initial empty state. This method is typically called when
        transitioning between maps or scenes to clean up objects from the previous map.

        After calling clear(), get_nearby_object() will always return None until new
        objects are registered. Any references to InteractiveObject instances remain
        valid (the objects themselves aren't destroyed), but they are no longer tracked
        by this manager.

        This is an important cleanup step to prevent memory leaks and ensure that
        objects from previous maps don't interfere with the current map's interactions.

        Example usage:
            # When loading a new map
            interaction_mgr.clear()  # Remove old map's objects

            # Load new map
            new_map = load_tiled_map("new_level.tmx")

            # Register new map's interactive objects
            for obj in new_map.object_lists.get("Interactive", []):
                interaction_mgr.register_object(obj.sprite, obj.name, obj.properties)
        """
        self.interactive_objects.clear()
