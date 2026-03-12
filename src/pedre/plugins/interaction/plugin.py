"""Interaction plugin for handling interactive objects in the game world.

This module provides the InteractionPlugin class, which manages interactive objects
that the player can activate by pressing an interaction key. Interactive objects are
typically defined in Tiled maps as objects with special properties that determine their
behavior when interacted with.

The interaction plugin supports:
- Distance-based interaction (objects must be within range)
- Multiple interaction types (messages, toggles, custom behaviors)
- Property-driven configuration from Tiled
- Automatic nearest-object selection

Interactive objects are commonly used for:
- Environmental storytelling (reading signs, examining objects)
- Puzzle elements (switches, levers, buttons)
- Item pickups and loot containers
- Quest triggers and progression markers

The plugin uses a simple distance check to determine which objects are within
interaction range, automatically selecting the nearest one when multiple objects
are nearby. This provides intuitive player interaction without requiring precise
positioning or targeting.

Example usage in a map:
    # In Tiled, create an object with properties:
    # - name: "town_sign"

    # In game code:
    interaction_mgr = context.get_plugin("interaction")

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
            interaction_mgr.handle_interaction(obj)
"""

import logging
from typing import Any, ClassVar

import arcade

from pedre.conf import settings
from pedre.helpers import matches_key
from pedre.plugins.interaction.base import InteractionBasePlugin, InteractiveObject
from pedre.plugins.interaction.events import ObjectInteractedEvent
from pedre.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


@PluginRegistry.register
class InteractionPlugin(InteractionBasePlugin):
    """Manages interactive objects and their behaviors.

    The InteractionPlugin acts as a registry and handler for all interactive objects
    in the game world. It maintains a collection of registered objects, determines which
    objects are within interaction range of the player.

    This plugin provides a flexible, data-driven approach to game interactions where
    designers can configure interactive elements in Tiled without requiring code changes.
    The plugin handles the common patterns (distance checking, nearest object selection)
    while allowing custom interaction types to be added through handler methods.

    Key responsibilities:
    - Registering interactive objects from map data
    - Finding nearby objects within interaction distance
    - Routing interactions to type-specific handlers

    The distance-based interaction plugin uses Euclidean distance to determine if an
    object is within range. When multiple objects are nearby, the nearest one is selected
    automatically, providing intuitive interaction behavior without explicit targeting.

    Attributes:
        interaction_distance: Maximum distance in pixels for interaction (default 64.0,
                            which is about 2 tiles at 32x32 tile size).
        interactive_objects: Dictionary mapping object names to InteractiveObject instances.
                           Used for O(1) lookups by name and iteration for distance checks.
    """

    name: ClassVar[str] = "interaction"
    dependencies: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """Initialize the interaction plugin with configurable interaction distance.

        Creates a new InteractionPlugin with an empty registry of interactive objects.
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
        self.interaction_distance = settings.INTERACTION_PLUGIN_DISTANCE
        self.interactive_objects: dict[str, InteractiveObject] = {}
        self.interacted_objects: set[str] = set()

    def load_from_tiled(self, tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None:
        """Load interactive objects from Tiled scene layer."""
        self.clear()
        interactive_layer = tile_map.object_lists.get("Interactive")
        if not interactive_layer:
            logger.debug("No Interactive layer found in map")
            return

        for obj in interactive_layer:
            if not obj.name:
                logger.warning("Interactive object missing 'name', skipping")
                continue

            # Extract shape geometry
            xs: list[float] = []
            ys: list[float] = []

            if isinstance(obj.shape, (list, tuple)) and len(obj.shape) > 0:
                first_elem = obj.shape[0]
                if isinstance(first_elem, (tuple, list)):
                    for p in obj.shape:
                        if isinstance(p, (tuple, list)) and len(p) >= 2:
                            xs.append(float(p[0]))
                            ys.append(float(p[1]))
                else:
                    second_elem = obj.shape[1]
                    if not isinstance(second_elem, (int, float)):
                        logger.warning("Interactive object '%s' has invalid shape, skipping", obj.name)
                        continue
                    xs.append(float(first_elem))
                    ys.append(float(second_elem))
            else:
                logger.warning("Interactive object '%s' has invalid shape, skipping", obj.name)
                continue

            # Create sprite for interaction zone
            sprite = arcade.Sprite()
            sprite.center_x = (min(xs) + max(xs)) / 2
            sprite.center_y = (min(ys) + max(ys)) / 2
            sprite.width = max(xs) - min(xs)
            sprite.height = max(ys) - min(ys)

            properties = obj.properties if hasattr(obj, "properties") and obj.properties else {}
            self.register_object(sprite, obj.name.lower(), properties)

    def get_interactive_objects(self) -> dict[str, InteractiveObject]:
        """Get interactive objects."""
        return self.interactive_objects

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle interaction input.

        Args:
            symbol: Arcade key constant.
            modifiers: Modifier key bitfield.
            context: Game context.

        Returns:
            True if interaction occurred.
        """
        if matches_key(symbol, settings.INTERACTION_KEY):
            player_sprite = self.context.player_plugin.get_player_sprite()
            if player_sprite:
                logger.debug(
                    "InteractionPlugin: %s pressed, player at (%.1f, %.1f)",
                    settings.INTERACTION_KEY,
                    player_sprite.center_x,
                    player_sprite.center_y,
                )

                # Check for nearby objects
                obj = self.get_nearby_object(player_sprite)
                if obj:
                    return self.handle_interaction(obj)

        return False

    def cleanup(self) -> None:
        """Clean up interaction resources when the scene unloads."""
        self.clear()
        logger.debug("InteractionPlugin cleanup complete")

    def register_object(self, sprite: arcade.Sprite, name: str, properties: dict) -> None:
        """Register an interactive object in the plugin.

        Adds a new interactive object to the plugin's registry, making it available for
        interaction queries and handling. This method is typically called during map
        loading when processing Tiled object layers that contain interactive elements.

        Objects are stored by name, so each name must be unique within the plugin.
        Registering an object with an existing name will overwrite the previous object.

        Args:
            sprite: The arcade Sprite representing this object visually. The sprite's
                   position (center_x, center_y) is used for distance calculations.
            name: Unique identifier for this object. Used for lookups and tracking.
                 Should match the object's name in Tiled for consistency.
            properties: Dictionary of custom properties from Tiled. The entire
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
        obj = InteractiveObject(
            sprite=sprite,
            name=name,
            properties=properties,
        )

        self.interactive_objects[name] = obj
        logger.info("Registered interactive object: %s", name)

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
                    self.interaction_mgr.handle_interaction(nearby_obj)
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

    def handle_interaction(self, obj: InteractiveObject) -> bool:
        """Handle interaction with an object by dispatching to type-specific handler.

        This is the main entry point for processing interactions.


        Args:
            obj: The InteractiveObject to interact with.

        Returns:
            True when the interaction is handled.

        Example:
            obj = interaction_mgr.get_nearby_object(player_sprite)
            if obj:
                success = interaction_mgr.handle_interaction(obj)
                if success:
                    audio_mgr.play_sfx("interact.wav")
        """
        self.mark_as_interacted(obj.name)
        self.context.event_bus.publish(ObjectInteractedEvent(object_name=obj.name))
        logger.debug("Published ObjectInteractedEvent for %s", obj.name)
        return True

    def mark_as_interacted(self, object_name: str) -> None:
        """Mark an object as interacted with.

        Args:
            object_name: Name of the object.
        """
        self.interacted_objects.add(object_name)
        logger.debug("InteractionPlugin: Object '%s' marked as interacted", object_name)

    def has_interacted_with(self, object_name: str) -> bool:
        """Check if an object has been interacted with.

        Args:
            object_name: Name of the object to check.

        Returns:
            True if the object has been interacted with, False otherwise.
        """
        return object_name in self.interacted_objects

    def reset(self) -> None:
        """Reset interactive and interacted objects."""
        self.interactive_objects.clear()
        self.interacted_objects.clear()

    def clear(self) -> None:
        """Clear all registered interactive objects from the plugin.

        Removes all interactive objects from the registry, effectively resetting the
        plugin to its initial empty state. This method is typically called when
        transitioning between maps or scenes to clean up objects from the previous map.

        After calling clear(), get_nearby_object() will always return None until new
        objects are registered. Any references to InteractiveObject instances remain
        valid (the objects themselves aren't destroyed), but they are no longer tracked
        by this plugin.

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

    def get_save_state(self) -> dict[str, Any]:
        """Return serializable state for saving (BasePlugin interface)."""
        return self.to_dict()

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Phase 1: Restore interacted objects set (doesn't need sprites)."""
        if "interacted_objects" in state:
            self.from_dict(state)

    def to_dict(self) -> dict[str, Any]:
        """Convert interaction state to dictionary for save data serialization."""
        return {"interacted_objects": list(self.interacted_objects)}

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore interaction state from dictionary (deserialize save data)."""
        self.interacted_objects = set(data["interacted_objects"])
