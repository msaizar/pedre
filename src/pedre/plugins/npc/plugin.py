"""NPC management plugin for tracking state, movement, and interactions.

This module provides the NPCPlugin class, which serves as the central hub for all
NPC-related functionality in the game. It manages NPC registration, pathfinding-based
movement, dialog with conditional branching, and animation state tracking.

The NPC plugin supports:
- Dynamic registration and tracking of multiple NPCs per scene
- Scene-aware dialog with conversation progression via DialogRegistry
- Conditional dialog branching based on game state
- Pathfinding-based movement with automatic obstacle avoidance
- Animation state management (appear, disappear, walk cycles)
- Event emission for NPC lifecycle (movement complete, animations finished)
- Interaction distance checking for player-NPC communication

Key features:
- **Dialog**: Multi-level conversations with conditional branching. NPCs can have
  different dialog at each conversation level, with conditions that check inventory state,
  interaction history, or other NPC dialog levels. Dialog definitions are loaded via
  DialogRegistry (content registry) from ``*_dialogs.json`` files in CONTENT_DIRECTORY.
- **Movement**: NPCs navigate using A* pathfinding, automatically avoiding walls and other
  NPCs. Movement is smooth and frame-rate independent.
- **Animations**: Integration with AnimatedNPC sprites for appear/disappear effects and
  walking animations that sync with movement direction.
- **Scene Awareness**: Dialog can vary by scene/map, allowing NPCs to have location-specific
  conversations.

The plugin uses an event-driven architecture where NPC actions (movement complete,
animations finished) publish events that scripts can listen for to create complex
scripted sequences.

Example usage:
    # Get the NPC plugin from context
    npc_mgr = context.npc_plugin

    # Register NPCs from map
    for npc_sprite in npc_layer:
        npc_mgr.register_npc(npc_sprite, name=npc_sprite.properties["name"])

    # Check for nearby NPC interaction
    nearby = npc_mgr.get_nearby_npc(player_sprite)
    if nearby:
        sprite, name, dialog_level = nearby
        dialog_config, _ = npc_mgr.get_dialog(name, dialog_level, current_scene)
        if dialog_config:
            show_dialog(name, dialog_config.text)

    # Move NPC to location
    npc_mgr.move_npc_to_tile("martin", tile_x=10, tile_y=15)

    # Update movement each frame
    npc_mgr.update(delta_time, context)
"""

import logging
from typing import TYPE_CHECKING, Any, ClassVar, cast

import arcade

from pedre.actions.registry import ActionParseError, ActionRegistry
from pedre.conditions.registry import ConditionParseError, ConditionRegistry
from pedre.conf import settings
from pedre.content.registries.dialog import DialogRegistry
from pedre.helpers import asset_path, matches_key
from pedre.plugins.npc.base import NPCBasePlugin, NPCDialogConfig, NPCState
from pedre.plugins.npc.events import (
    NPCAppearCompleteEvent,
    NPCDisappearCompleteEvent,
    NPCMovementCompleteEvent,
)
from pedre.plugins.registry import PluginRegistry
from pedre.sprites import AnimatedSprite

if TYPE_CHECKING:
    from pedre.actions.base import Action
    from pedre.conditions.base import Condition
    from pedre.content.registry import ContentRegistry

logger = logging.getLogger(__name__)


@PluginRegistry.register
class NPCPlugin(NPCBasePlugin):
    """Manages NPC state, movement, and interactions.

    The NPCPlugin is the central controller for all NPC-related plugins. It coordinates
    NPC registration, dialog management, pathfinding movement, animation tracking, and
    event emission for NPC lifecycle events.

    Key responsibilities:
    - **Registration**: Track all NPCs in the current scene by name
    - **Dialog**: Serve scene-aware dialog with conditional branching via DialogRegistry
    - **Movement**: Calculate and execute pathfinding-based movement
    - **Interaction**: Determine which NPCs are within interaction range
    - **Animation**: Track animation state for appear/disappear effects
    - **Events**: Publish events when NPCs complete movements or animations

    Dialog definitions live in the content registry (DialogRegistry). Dialog progression
    is tracked per-NPC via dialog_level, supporting multi-stage conversations.

    Movement is handled via A* pathfinding with smooth interpolation between waypoints.
    NPCs automatically avoid walls and other moving NPCs. Movement completes when the
    NPC reaches their final waypoint, triggering an event that scripts can respond to.

    Attributes:
        npcs: Dictionary mapping NPC names to their NPCState instances. Contains all
             registered NPCs and their current runtime state.
        pathfinding: PathfindingPlugin instance used for calculating NPC movement paths.
        interaction_distance: Maximum distance in pixels for player to interact with NPCs.
        waypoint_threshold: Distance in pixels to consider an NPC has reached a waypoint.
        movement_speed: Movement speed in pixels per second. Applied to all NPCs uniformly.
        interacted_npcs: Dictionary mapping scene names to sets of NPC names that have
                        been interacted with in that scene. Allows scene-specific interaction tracking.
    """

    name: ClassVar[str] = "npc"
    dependencies: ClassVar[list[str]] = ["pathfinding"]

    def __init__(self) -> None:
        """Initialize the NPC plugin with default values.

        Creates an NPC plugin with empty registries and default configuration.
        Actual initialization with dependencies happens in setup().
        """
        self.npcs: dict[str, NPCState] = {}
        self._parsed_dialog_cache: dict[str, NPCDialogConfig] = {}
        self.interaction_distance = settings.NPC_INTERACTION_DISTANCE
        self.waypoint_threshold = settings.NPC_WAYPOINT_THRESHOLD
        self.movement_speed = settings.NPC_MOVEMENT_SPEED
        self.interacted_npcs: dict[str, set[str]] = {}

    def load_from_tiled(self, tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None:
        """Load NPCs from Tiled object layer."""
        npc_layer = tile_map.object_lists.get("NPCs")
        if not npc_layer:
            logger.debug("No NPCs layer found in map")
            return

        # Use existing method
        self.load_npcs_from_objects(npc_layer, arcade_scene)

    def cleanup(self) -> None:
        """Clean up NPC resources when the scene unloads.

        Clears all registered NPCs and resets state.
        """
        self.npcs.clear()
        logger.debug("NPCPlugin cleanup complete")

    def reset(self) -> None:
        """Reset NPC plugin for new game."""
        self.npcs.clear()
        self._parsed_dialog_cache.clear()
        self.interacted_npcs.clear()
        logger.debug("NPCPlugin reset complete")

    def get_npcs(self) -> dict[str, NPCState]:
        """Get NPCs."""
        return self.npcs

    def _parse_dialog_entry(self, npc_name: str, level_str: str, dialog_data: dict[str, Any]) -> NPCDialogConfig:
        """Parse a raw dialog definition dict into an NPCDialogConfig.

        Args:
            npc_name: NPC name (used for log messages).
            level_str: Dialog level string (used for log messages).
            dialog_data: Raw dialog definition from the registry.

        Returns:
            Parsed NPCDialogConfig.
        """
        parsed_conditions = None
        if condition_defs := dialog_data.get("conditions"):
            parsed_conditions = []
            for condition_def in condition_defs:
                try:
                    parsed_conditions.append(ConditionRegistry.create(condition_def))
                except ConditionParseError as e:
                    logger.warning(
                        "Failed to parse condition for NPC '%s' level %s: %s",
                        npc_name,
                        level_str,
                        e,
                    )

        parsed_fail_actions = None
        if fail_action_defs := dialog_data.get("on_condition_fail"):
            parsed_fail_actions = []
            for action_def in fail_action_defs:
                try:
                    parsed_fail_actions.append(ActionRegistry.create(action_def))
                except ActionParseError as e:
                    logger.warning(
                        "Failed to parse on_condition_fail action for NPC '%s' level %s: %s",
                        npc_name,
                        level_str,
                        e,
                    )

        return NPCDialogConfig(
            text=dialog_data["text"],
            name=dialog_data.get("name"),
            conditions=parsed_conditions,
            on_condition_fail=parsed_fail_actions,
        )

    def register_npc(self, sprite: arcade.Sprite, name: str) -> None:
        """Register an NPC sprite for management.

        Args:
            sprite: The NPC sprite.
            name: The NPC's unique name identifier.
        """
        self.npcs[name] = NPCState(sprite=sprite, name=name)

    def get_npc_by_name(self, name: str) -> NPCState | None:
        """Get NPC state by name.

        Args:
            name: The NPC name.

        Returns:
            NPCState or None if not found.
        """
        return self.npcs.get(name)

    def get_nearby_npc(self, player_sprite: arcade.Sprite) -> tuple[arcade.Sprite, str, int] | None:
        """Find the nearest NPC within interaction distance.

        Args:
            player_sprite: The player sprite.

        Returns:
            Tuple of (sprite, name, dialog_level) or None.
        """
        closest_npc: NPCState | None = None
        closest_distance: float = self.interaction_distance

        for npc_state in self.npcs.values():
            if not npc_state.sprite.visible:
                continue

            # Skip NPCs that are currently moving
            if npc_state.is_moving:
                continue

            distance = arcade.get_distance_between_sprites(player_sprite, npc_state.sprite)

            if distance < closest_distance:
                closest_distance = distance
                closest_npc = npc_state

        if closest_npc:
            return (
                closest_npc.sprite,
                closest_npc.name,
                closest_npc.dialog_level,
            )

        return None

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle interaction input for NPCs.

        Args:
            symbol: Arcade key constant.
            modifiers: Modifier key bitfield.
            context: Game context.

        Returns:
            True if interaction occurred.
        """
        if matches_key(symbol, settings.NPC_INTERACTION_KEY):
            player_sprite = self.context.player_plugin.get_player_sprite()

            if player_sprite:
                nearby = self.get_nearby_npc(player_sprite)
                logger.debug(
                    "NPCPlugin: Interaction, player at (%.1f, %.1f), npcs=%d, nearby=%s",
                    player_sprite.center_x,
                    player_sprite.center_y,
                    len(self.npcs),
                    nearby[1] if nearby else None,
                )
                if nearby:
                    _sprite, name, _dialog_level = nearby
                    if self.interact_with_npc(name):
                        return True
        return False

    def interact_with_npc(self, name: str) -> bool:
        """Trigger interaction with a specific NPC.

        Args:
            name: Name of the NPC to interact with.

        Returns:
            True if interaction started (dialog shown).
        """
        # Get NPC state
        npc = self.get_npc_by_name(name)
        if not npc:
            return False

        dialog_plugin = self.context.dialog_plugin

        # Get dialog
        current_scene = self.context.scene_plugin.get_current_scene()

        dialog_config, on_condition_fail = self.get_dialog(name, npc.dialog_level, current_scene)

        if dialog_plugin:
            # If conditions failed, execute on_condition_fail actions via ScriptPlugin
            if on_condition_fail:
                self.context.script_plugin.run_actions(f"npc_{name}_condition_fail", on_condition_fail)
                return True

            # Show dialog - use display name from config if available, otherwise use NPC key name
            if dialog_config:
                display_name = dialog_config.name or name
                dialog_plugin.show_dialog(display_name, dialog_config.text, dialog_level=npc.dialog_level, npc_key=name)
                self.mark_npc_as_interacted(name)
                return True

        return False

    def mark_npc_as_interacted(self, npc_name: str, scene_name: str | None = None) -> None:
        """Mark an NPC as interacted with in a specific scene.

        Args:
            npc_name: Name of the NPC.
            scene_name: Scene name (defaults to current scene if not provided).
        """
        if scene_name is None:
            scene_name = self.context.scene_plugin.get_current_scene()

        if scene_name not in self.interacted_npcs:
            self.interacted_npcs[scene_name] = set()

        self.interacted_npcs[scene_name].add(npc_name)
        logger.debug("NPCPlugin: NPC '%s' marked as interacted in scene '%s'", npc_name, scene_name)

    def has_npc_been_interacted_with(self, npc_name: str, scene_name: str | None = None) -> bool:
        """Check if an NPC has been interacted with in a specific scene.

        Args:
            npc_name: Name of the NPC to check.
            scene_name: Scene name (defaults to current scene if not provided).

        Returns:
            True if the NPC has been interacted with in the specified scene, False otherwise.
        """
        if scene_name is None:
            scene_name = self.context.scene_plugin.get_current_scene()

        return npc_name in self.interacted_npcs.get(scene_name, set())

    def _check_dialog_conditions(self, conditions: list[Condition]) -> bool:
        """Check if all dialog conditions are met.

        Args:
            conditions: List of parsed Condition objects.

        Returns:
            True if all conditions are met.
        """
        return all(condition.check(self.context) for condition in conditions)

    def get_dialog(
        self, npc_name: str, dialog_level: int, scene: str = "default"
    ) -> tuple[NPCDialogConfig | None, list[Action] | None]:
        """Get dialog for an NPC at a specific conversation level in a scene.

        Args:
            npc_name: The NPC name.
            dialog_level: The conversation level.
            scene: The current scene name (defaults to "default").

        Returns:
            Tuple of (dialog_config, on_condition_fail_actions):
            - dialog_config: NPCDialogConfig if conditions met, None if no dialog found
            - on_condition_fail_actions: List of actions to execute if conditions failed, None otherwise
        """
        dialog_registry = cast("DialogRegistry", self.context.content_registry.get_sub_registry("dialogs"))
        level_str = str(dialog_level)

        # Try scene-specific entry first, fall back to "default"
        raw = dialog_registry.get_dialog(scene, npc_name, level_str)
        effective_scene = scene
        if raw is None and scene != "default":
            raw = dialog_registry.get_dialog("default", npc_name, level_str)
            effective_scene = "default"

        if raw is None:
            return None, None

        cache_key = f"{effective_scene}/{npc_name}/{level_str}"
        if cache_key not in self._parsed_dialog_cache:
            self._parsed_dialog_cache[cache_key] = self._parse_dialog_entry(npc_name, level_str, raw)

        config = self._parsed_dialog_cache[cache_key]

        if config.conditions:
            if self._check_dialog_conditions(config.conditions):
                return config, None
            logger.debug("Dialog condition failed for %s level %s", npc_name, level_str)
            return None, config.on_condition_fail

        return config, None

    def advance_dialog(self, npc_name: str) -> int:
        """Advance the dialog level for an NPC.

        Args:
            npc_name: The NPC name.

        Returns:
            The new dialog level.
        """
        npc = self.npcs.get(npc_name)
        if npc:
            npc.dialog_level += 1
            logger.debug(
                "Advanced dialog for %s: %d -> %d",
                npc_name,
                npc.dialog_level - 1,
                npc.dialog_level,
            )
            return npc.dialog_level
        return 0

    def move_npc_to_position(self, npc_name: str, x: float, y: float) -> None:
        """Start moving an NPC to a target position.

        Args:
            npc_name: The NPC name.
            x: Target x coordinate in pixels.
            y: Target y coordinate in pixels.
        """
        npc = self.npcs.get(npc_name)
        if not npc:
            logger.warning("Cannot move unknown NPC: %s", npc_name)
            return
        pathfinding = self.context.pathfinding_plugin
        if not pathfinding:
            logger.warning("Cannot move NPC %s: pathfinding not available", npc_name)
            return

        logger.info("Starting pathfinding for %s", npc_name)
        logger.debug("  From: (%.1f, %.1f)", npc.sprite.center_x, npc.sprite.center_y)
        logger.debug("  To position: (%.1f, %.1f)", x, y)

        # Collect all moving NPCs to exclude from pathfinding obstacles
        moving_npc_sprites = [other_npc.sprite for other_npc in self.npcs.values() if other_npc.is_moving]

        path = pathfinding.find_path(
            npc.sprite.center_x,
            npc.sprite.center_y,
            x,
            y,
            exclude_sprite=npc.sprite,
            exclude_sprites=moving_npc_sprites,
        )

        logger.info("  Path length: %d waypoints", len(path))
        if path:
            logger.debug("  First waypoint: %s", path[0])

        npc.path = path
        npc.is_moving = bool(path)

    def show_npcs(self, npc_names: list[str]) -> None:
        """Make hidden NPCs visible and add them to collision.

        Args:
            npc_names: List of NPC names to reveal.
        """
        for npc_name in npc_names:
            npc = self.npcs.get(npc_name)
            if npc and not npc.sprite.visible:
                npc.sprite.visible = True

                # Start appear animation for sprites that support it
                if isinstance(npc.sprite, AnimatedSprite) and npc.sprite.has_state("appear"):
                    npc.sprite.request_state("appear")
                scene_plugin = self.context.scene_plugin
                if scene_plugin:
                    scene_plugin.add_to_wall_list(npc.sprite)
                logger.info("Showing hidden NPC: %s", npc_name)

    def update(self, delta_time: float) -> None:
        """Update NPC movements along their paths.

        Args:
            delta_time: Time since last update in seconds.
            context: Game context (provides access to wall_list if needed).
        """
        for npc in self.npcs.values():
            # Process pathfinding movement first
            moving = False  # Track if NPC is actually moving this frame

            if npc.is_moving and npc.path:
                # Get next waypoint
                target_x, target_y = npc.path[0]

                # Calculate direction to target
                dx = target_x - npc.sprite.center_x
                dy = target_y - npc.sprite.center_y
                distance = (dx**2 + dy**2) ** 0.5

                # Update direction based on movement vector (prioritize horizontal)
                if isinstance(npc.sprite, AnimatedSprite):
                    # Determine new direction from movement vector
                    if dx > 0:
                        new_direction = "right"
                    elif dx < 0:
                        new_direction = "left"
                    elif dy > 0:
                        new_direction = "up"
                    elif dy < 0:
                        new_direction = "down"
                    else:
                        new_direction = npc.sprite.current_direction

                    # Only update if direction changed (prevents unnecessary animation resets)
                    if new_direction != npc.sprite.current_direction:
                        npc.sprite.set_direction(new_direction)

                # Move towards target
                if distance < self.waypoint_threshold:
                    # Close enough to waypoint, move to next
                    npc.path.popleft()
                    if not npc.path:
                        # Path completed
                        npc.sprite.center_x = target_x
                        npc.sprite.center_y = target_y
                        npc.is_moving = False
                        moving = False

                        # Emit movement complete event
                        if self.context.event_bus:
                            self.context.event_bus.publish(NPCMovementCompleteEvent(npc_name=npc.name))
                            logger.info("%s movement complete, event emitted", npc.name)
                    else:
                        # More waypoints remaining, NPC is still moving
                        moving = True

                # Move NPC towards target
                else:
                    move_distance = self.movement_speed * delta_time
                    move_distance = min(move_distance, distance)
                    npc.sprite.center_x += (dx / distance) * move_distance
                    npc.sprite.center_y += (dy / distance) * move_distance
                    moving = True  # NPC is actively moving

            # Update animation (after movement logic)
            if isinstance(npc.sprite, AnimatedSprite):
                if moving:
                    npc.sprite.request_state("walk")
                else:
                    npc.sprite.release_state("walk")
                npc.sprite.update_animation(delta_time)

                # Check if appear animation just completed
                if npc.sprite.is_state_complete("appear") and not npc.appear_event_emitted:
                    if self.context.event_bus:
                        self.context.event_bus.publish(NPCAppearCompleteEvent(npc_name=npc.name))
                        logger.info("%s appear animation complete, event emitted", npc.name)
                    npc.appear_event_emitted = True

                # Check if disappear animation just completed
                if npc.sprite.is_state_complete("disappear") and not npc.disappear_event_emitted:
                    if self.context.event_bus:
                        self.context.event_bus.publish(NPCDisappearCompleteEvent(npc_name=npc.name))
                        logger.info("%s disappear animation complete, event emitted", npc.name)
                    npc.disappear_event_emitted = True

    def get_npc_positions(self) -> dict[str, dict[str, float | bool]]:
        """Get current positions and visibility for all NPCs.

        Exports the position and visibility state of all registered NPCs for save data.
        This allows the save plugin to preserve NPC locations after scripted movements
        or appearance/disappearance animations.

        Returns:
            Dictionary mapping NPC names to their position/visibility state.
            Each NPC entry contains: {"x": float, "y": float, "visible": bool}.
            Example: {
                "martin": {"x": 320.0, "y": 240.0, "visible": True},
                "shopkeeper": {"x": 640.0, "y": 480.0, "visible": False}
            }

        Example:
            # Save NPC positions
            npc_positions = npc_plugin.get_npc_positions()
            save_data["npc_positions"] = npc_positions
        """
        positions = {}
        for npc_name, npc_state in self.npcs.items():
            positions[npc_name] = {
                "x": npc_state.sprite.center_x,
                "y": npc_state.sprite.center_y,
                "visible": npc_state.sprite.visible,
            }
        return positions

    def _restore_positions(self, npc_positions: dict[str, dict[str, float | bool]]) -> None:
        """Restore NPC positions and visibility from save data.

        Updates NPC sprite positions and visibility based on saved state. This is called
        when loading a save file to restore NPC locations after scripted movements or
        appearance/disappearance sequences.

        NPCs that were moved by scripts or made invisible will be restored to their
        saved state. NPCs not present in the save data retain their current position
        and visibility (typically from map defaults).

        Args:
            npc_positions: Dictionary mapping NPC names to position and visibility.
                Each entry should contain: {"x": float, "y": float, "visible": bool}.
                Example: {
                    "martin": {"x": 320.0, "y": 240.0, "visible": True},
                    "guard": {"x": 640.0, "y": 480.0, "visible": False}
                }

        Example:
            # After loading save data
            save_data = save_plugin.load_game(slot=1)
            if save_data and save_data.npc_positions:
                npc_plugin._restore_positions(save_data.npc_positions)
                # All NPCs now at their saved positions with correct visibility
        """
        for npc_name, position_data in npc_positions.items():
            npc = self.npcs.get(npc_name)
            if npc:
                npc.sprite.center_x = float(position_data["x"])
                npc.sprite.center_y = float(position_data["y"])
                npc.sprite.visible = bool(position_data["visible"])
                logger.debug(
                    "Restored %s position to (%.1f, %.1f), visible=%s",
                    npc_name,
                    npc.sprite.center_x,
                    npc.sprite.center_y,
                    npc.sprite.visible,
                )
            else:
                logger.warning("Cannot restore position for unknown NPC: %s", npc_name)

    def has_moving_npcs(self) -> bool:
        """Check if any NPCs are currently moving.

        Returns True if any NPC has an active movement path in progress. This is
        useful for determining if the game is in a state where pausing/saving
        should be blocked (e.g., during scripted NPC movements).

        Returns:
            True if at least one NPC is currently moving, False if all NPCs are stationary.

        Example:
            # Check before allowing pause
            if npc_plugin.has_moving_npcs():
                logger.debug("Cannot pause: NPCs are moving")
                return
        """
        return any(npc.is_moving for npc in self.npcs.values())

    def load_npcs_from_objects(self, npc_objects: list, scene: arcade.Scene | None) -> None:
        """Load NPCs from Tiled object layer.

        For each NPC object the method looks up the NPC definition in the content
        registry (via ``sprite_id`` or ``npc_name``), resolves the sprite definition,
        and builds an AnimatedSprite using the factory.

        Tiled object properties used:
            name (required): NPC identifier (lowercased).

        Args:
            npc_objects: List of Tiled objects from tile_map.object_lists["NPCs"].
            scene: The arcade Scene to add NPC sprites to.
        """
        npc_sprite_list = arcade.SpriteList()
        content_registry = self.context.content_registry

        for npc_obj in npc_objects:
            npc_name = npc_obj.name
            if not npc_name:
                continue

            npc_name = npc_name.lower()

            # Get position from object shape
            spawn_x = float(npc_obj.shape[0])
            spawn_y = float(npc_obj.shape[1])

            try:
                animated_sprite = self._create_npc_sprite(
                    npc_name=npc_name,
                    npc_obj=npc_obj,
                    spawn_x=spawn_x,
                    spawn_y=spawn_y,
                    content_registry=content_registry,
                )
            except Exception:
                logger.exception("Failed to create sprite for NPC '%s'", npc_name)
                continue

            if animated_sprite is None:
                continue

            self.register_npc(animated_sprite, npc_name)
            npc_sprite_list.append(animated_sprite)

            scene_plugin = self.context.scene_plugin
            if scene_plugin and animated_sprite.visible:
                scene_plugin.add_to_wall_list(animated_sprite)

            logger.debug("Loaded NPC '%s' at (%.1f, %.1f)", npc_name, spawn_x, spawn_y)

        # Add NPCs layer to scene
        if scene is not None and len(npc_sprite_list) > 0:
            if "NPCs" in scene:
                scene.remove_sprite_list_by_name("NPCs")
            scene.add_sprite_list("NPCs", sprite_list=npc_sprite_list)
            logger.info("Added %d NPCs to scene", len(npc_sprite_list))

    def _create_npc_sprite(
        self,
        *,
        npc_name: str,
        npc_obj: object,
        spawn_x: float,
        spawn_y: float,
        content_registry: ContentRegistry,
    ) -> AnimatedSprite | None:
        """Resolve sprite definition and create an AnimatedSprite for an NPC.

        Looks up the NPC in the content registry and builds a sprite from the
        matching sprite definition.  Scale, tile_size, and initially_hidden are
        read from the NPC registry definition (npcs.json).

        Args:
            npc_name: NPC identifier.
            npc_obj: Tiled object with properties dict.
            spawn_x: World X position.
            spawn_y: World Y position.
            content_registry: ContentRegistry instance.

        Returns:
            AnimatedSprite instance, or None if the sprite could not be created.
        """
        npc_def: dict = {}
        npcs = content_registry.get_sub_registry("npcs")
        sprites = content_registry.get_sub_registry("sprites")
        sprite_id = None
        if npcs.has(npc_name):
            npc_def = npcs.get(npc_name)
            sprite_id = npc_def.get("sprite_id")

        if sprite_id and sprites.has(sprite_id):
            sprite_def = sprites.get(sprite_id)
            # Resolve sprite_sheet path via asset_path helper
            sprite_def = dict(sprite_def)
            sprite_def["sprite_sheet"] = asset_path(sprite_def["sprite_sheet"])
            sprite = AnimatedSprite.from_definition(
                sprite_def,
                center_x=spawn_x,
                center_y=spawn_y,
                scale=npc_def.get("scale"),
                tile_size=npc_def.get("tile_size"),
            )
            if npc_def.get("initially_hidden", False):
                sprite.visible = False
            return sprite

        logger.warning(
            "NPC '%s': no registry definition found. Skipping.",
            npc_name,
        )
        return None

    def get_save_state(self) -> dict[str, Any]:
        """Return serializable state for saving NPC data.

        Saves NPC positions, visibility, dialog levels, animation flags, and interaction history.

        Returns:
            Dictionary containing NPC states and interaction history.
        """
        npc_states: dict[str, Any] = {}
        for npc_name, npc in self.npcs.items():
            npc_state: dict[str, Any] = {
                "x": npc.sprite.center_x,
                "y": npc.sprite.center_y,
                "visible": npc.sprite.visible,
                "dialog_level": npc.dialog_level,
            }

            # Save animation completion flags for animated sprites
            if isinstance(npc.sprite, AnimatedSprite):
                npc_state["appear_complete"] = npc.sprite.is_state_complete("appear")
                npc_state["disappear_complete"] = npc.sprite.is_state_complete("disappear")
                npc_state["interact_complete"] = npc.sprite.is_state_complete("interact")

            npc_states[npc_name] = npc_state

        # Convert interacted_npcs sets to lists for JSON serialization
        interacted_npcs_serialized = {scene: list(npcs) for scene, npcs in self.interacted_npcs.items()}

        return {
            "npcs": npc_states,
            "interacted_npcs": interacted_npcs_serialized,
        }

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Phase 1: No metadata to restore for NPCs (sprites don't exist yet)."""

    def apply_entity_state(self, state: dict[str, Any]) -> None:
        """Phase 2: Apply saved NPC state after sprites exist."""
        self._apply_npc_state(state["npcs"])
        # Restore interacted NPCs
        if "interacted_npcs" in state:
            self.interacted_npcs = {scene: set(npcs) for scene, npcs in state["interacted_npcs"].items()}
            logger.debug("Restored interacted NPCs for %d scenes", len(self.interacted_npcs))

    def _apply_npc_state(self, state: dict[str, Any]) -> None:
        """Apply NPC state from save data or scene cache.

        Restores NPC positions, visibility, dialog levels, and animation flags.

        Args:
            state: Previously saved state from get_save_state().
        """
        for npc_name, npc_state in state.items():
            npc = self.npcs.get(npc_name)
            if not npc:
                continue

            # Restore position and visibility
            npc.sprite.center_x = npc_state.get("x", npc.sprite.center_x)
            npc.sprite.center_y = npc_state.get("y", npc.sprite.center_y)
            npc.sprite.visible = npc_state.get("visible", True)
            npc.dialog_level = npc_state.get("dialog_level", 0)

            # Restore animation completion flags for animated sprites
            if isinstance(npc.sprite, AnimatedSprite):
                if npc_state.get("appear_complete", False):
                    npc.sprite.mark_state_complete("appear")
                if npc_state.get("disappear_complete", False):
                    npc.sprite.mark_state_complete("disappear")
                if npc_state.get("interact_complete", False):
                    npc.sprite.mark_state_complete("interact")

        logger.info("Applied state for %d NPCs", len(state))

    def cache_scene_state(self, scene_name: str) -> dict[str, Any]:
        """Return state to cache during scene transitions.

        Note: Only caches NPC entity state (positions, visibility, dialog levels).
        Interaction history is global across all scenes and saved separately.
        """
        npc_states: dict[str, Any] = {}
        for npc_name, npc in self.npcs.items():
            npc_state: dict[str, Any] = {
                "x": npc.sprite.center_x,
                "y": npc.sprite.center_y,
                "visible": npc.sprite.visible,
                "dialog_level": npc.dialog_level,
            }

            # Save animation completion flags for animated sprites
            if isinstance(npc.sprite, AnimatedSprite):
                npc_state["appear_complete"] = npc.sprite.is_state_complete("appear")
                npc_state["disappear_complete"] = npc.sprite.is_state_complete("disappear")
                npc_state["interact_complete"] = npc.sprite.is_state_complete("interact")

            npc_states[npc_name] = npc_state

        return npc_states

    def restore_scene_state(self, scene_name: str, state: dict[str, Any]) -> None:
        """Restore cached state when returning to a scene."""
        self._apply_npc_state(state)
