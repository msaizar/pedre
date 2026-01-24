"""NPC management system for tracking state, movement, and interactions.

This module provides the NPCManager class, which serves as the central hub for all
NPC-related functionality in the game. It manages NPC registration, pathfinding-based
movement, dialog system with conditional branching, and animation state tracking.

The NPC system supports:
- Dynamic registration and tracking of multiple NPCs per scene
- Scene-aware dialog system with conversation progression
- Conditional dialog branching based on game state
- Pathfinding-based movement with automatic obstacle avoidance
- Animation state management (appear, disappear, walk cycles)
- Event emission for NPC lifecycle (movement complete, animations finished)
- Interaction distance checking for player-NPC communication

Key features:
- **Dialog System**: Multi-level conversations with conditional branching. NPCs can have
  different dialog at each conversation level, with conditions that check inventory state,
  interaction history, or other NPC dialog levels.
- **Movement**: NPCs navigate using A* pathfinding, automatically avoiding walls and other
  NPCs. Movement is smooth and frame-rate independent.
- **Animations**: Integration with AnimatedNPC sprites for appear/disappear effects and
  walking animations that sync with movement direction.
- **Scene Awareness**: Dialog can vary by scene/map, allowing NPCs to have location-specific
  conversations.

The manager uses an event-driven architecture where NPC actions (movement complete,
animations finished) publish events that scripts can listen for to create complex
scripted sequences.

Example usage:
    # Get the NPC manager from context
    npc_mgr = context.get_system("npc")

    # Load dialog from JSON files
    npc_mgr.load_dialogs_from_json("assets/dialogs/")

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

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, cast

import arcade

from pedre.conditions.registry import ConditionRegistry
from pedre.conf import settings
from pedre.constants import asset_path
from pedre.sprites import AnimatedNPC
from pedre.systems.inventory import InventoryManager
from pedre.systems.npc.base import NPCBaseManager, NPCState
from pedre.systems.npc.events import (
    NPCAppearCompleteEvent,
    NPCDisappearCompleteEvent,
    NPCMovementCompleteEvent,
)
from pedre.systems.pathfinding import PathfindingManager
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.events import EventBus
    from pedre.systems.dialog.base import DialogBaseManager
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@dataclass
class NPCDialogConfig:
    """Configuration for NPC dialog at a specific conversation level.

    NPCDialogConfig defines what an NPC says at a particular point in their conversation
    progression, along with optional conditions that must be met for this dialog to appear.
    This is static data typically loaded from JSON files that doesn't change during gameplay.

    The dialog system supports conditional branching where different text can be shown based
    on game state (inventory accessed, objects interacted with, other NPC dialog levels).
    If conditions aren't met, optional fallback actions can be executed instead.

    Attributes:
        text: List of dialog text pages to display. Each string is one page that the player
             advances through. Example: ["Hello there!", "Welcome to my shop."]
        name: Optional display name for the speaker. If provided, this name is shown in the
             dialog box instead of the NPC's key name. Useful for proper capitalization or
             titles (e.g., "Merchant" instead of "merchant").
        conditions: Optional list of condition dictionaries that must ALL be true for this
                   dialog to display. Each condition has a "check" type and expected values.
                   Common checks: "npc_dialog_level", "inventory_accessed", "object_interacted".
                   If None or empty, dialog always shows.
        on_condition_fail: Optional list of action dictionaries to execute if conditions fail.
                          Allows fallback behavior like showing reminder text or triggering
                          alternative sequences. If None, condition failure silently falls back
                          to other available dialog options.

    Example JSON:
        {
            "merchant": {
                "0": {
                    "name": "Merchant",
                    "text": ["Welcome to my shop!"]
                },
                "1": {
                    "name": "Merchant",
                    "text": ["You're back! Did you check your inventory?"],
                    "conditions": [{"check": "inventory_accessed", "equals": true}],
                    "on_condition_fail": [
                        {"type": "dialog", "speaker": "Merchant", "text": ["Please check your inventory first!"]}
                    ]
                }
            }
        }
    """

    text: list[str]
    name: str | None = None
    conditions: list[dict[str, Any]] | None = None
    on_condition_fail: list[dict[str, Any]] | None = None  # List of actions to execute if conditions fail


@SystemRegistry.register
class NPCManager(NPCBaseManager):
    """Manages NPC state, movement, and interactions.

    The NPCManager is the central controller for all NPC-related systems. It coordinates
    NPC registration, dialog management, pathfinding movement, animation tracking, and
    event emission for NPC lifecycle events.

    Key responsibilities:
    - **Registration**: Track all NPCs in the current scene by name
    - **Dialog**: Load and serve scene-aware dialog with conditional branching
    - **Movement**: Calculate and execute pathfinding-based movement
    - **Interaction**: Determine which NPCs are within interaction range
    - **Animation**: Track animation state for appear/disappear effects
    - **Events**: Publish events when NPCs complete movements or animations

    The manager uses a scene-based dialog system where conversations are organized by
    map/scene name, allowing NPCs to have different dialog depending on location. Dialog
    progression is tracked per-NPC via dialog_level, supporting multi-stage conversations.

    Movement is handled via A* pathfinding with smooth interpolation between waypoints.
    NPCs automatically avoid walls and other moving NPCs. Movement completes when the
    NPC reaches their final waypoint, triggering an event that scripts can respond to.

    Attributes:
        npcs: Dictionary mapping NPC names to their NPCState instances. Contains all
             registered NPCs and their current runtime state.
        dialogs: Nested dictionary structure: scene -> npc_name -> dialog_level -> config.
                Stores all loaded dialog configurations organized by scene and progression.
        pathfinding: PathfindingManager instance used for calculating NPC movement paths.
        interaction_distance: Maximum distance in pixels for player to interact with NPCs.
        waypoint_threshold: Distance in pixels to consider an NPC has reached a waypoint.
        npc_speed: Movement speed in pixels per second. Applied to all NPCs uniformly.
        inventory_manager: Optional reference for checking inventory conditions in dialog.
        event_bus: Optional EventBus for publishing NPC lifecycle events.
        interacted_objects: Set tracking which interactive objects have been used, for
                           dialog condition checking.
        interacted_npcs: Set tracking which NPCs have been interacted with, for
                        dialog and script condition checking.
    """

    name: ClassVar[str] = "npc"
    dependencies: ClassVar[list[str]] = ["pathfinding"]

    # Class-level cache for per-scene dialog data (lazy loaded).
    # Maps scene name to dialog data: scene_name -> npc_name -> dialog_level -> dialog_data
    _dialog_cache: ClassVar[dict[str, dict[str, dict[int | str, NPCDialogConfig]]]] = {}

    def __init__(self) -> None:
        """Initialize the NPC manager with default values.

        Creates an NPC manager with empty registries and default configuration.
        Actual initialization with dependencies happens in setup().
        """
        self.npcs: dict[str, NPCState] = {}
        # Changed to scene -> npc -> level structure for scene-aware dialogs
        self.dialogs: dict[str, dict[str, dict[int | str, NPCDialogConfig]]] = {}
        self.pathfinding: PathfindingManager | None = None
        self.interaction_distance = 50
        self.waypoint_threshold = 2
        self.npc_speed = 80.0
        self.inventory_manager: InventoryManager | None = None
        self.event_bus: EventBus | None = None
        self.interacted_objects: set[str] = set()
        self.interacted_npcs: set[str] = set()

    def setup(self, context: GameContext) -> None:
        """Initialize the NPC system with game context and settings.

        This method is called by the SystemLoader after all systems have been
        instantiated. It configures the manager with references to required
        systems and settings.

        Args:
            context: Game context providing access to other systems.
            settings: Game configuration containing NPC-related settings.
        """
        # Get required dependencies from context
        pathfinding_system = context.get_system("pathfinding")
        if pathfinding_system and isinstance(pathfinding_system, PathfindingManager):
            self.pathfinding = pathfinding_system

        inventory_system = context.get_system("inventory")
        if inventory_system and isinstance(inventory_system, InventoryManager):
            self.inventory_manager = inventory_system
        self.event_bus = context.event_bus
        self.interacted_objects = context.interacted_objects
        # Use a separate set for NPCs if desired, or share context.interacted_objects
        # For now, let's keep it consistent with ScriptManager's potential view.
        # ScriptManager used has_npc_been_interacted_with(npc_name) which checked npc_manager.
        # Wait, let's check NPCManager.has_npc_been_interacted_with.

        # Apply settings if available
        if hasattr(settings, "NPC_INTERACTION_DISTANCE"):
            self.interaction_distance = settings.NPC_INTERACTION_DISTANCE
        if hasattr(settings, "NPC_SPEED"):
            self.npc_speed = settings.NPC_SPEED

        logger.debug("NPCManager setup complete")

    def load_from_tiled(
        self,
        tile_map: arcade.TileMap,
        arcade_scene: arcade.Scene,
        context: GameContext,
    ) -> None:
        """Load NPCs from Tiled object layer."""
        npc_layer = tile_map.object_lists.get("NPCs")
        if not npc_layer:
            logger.debug("No NPCs layer found in map")
            return

        # Use existing method
        self.load_npcs_from_objects(
            npc_layer,
            arcade_scene,
            context.wall_list,
        )

    def cleanup(self) -> None:
        """Clean up NPC resources when the scene unloads.

        Clears all registered NPCs and resets state.
        """
        self.npcs.clear()
        self.dialogs.clear()
        logger.debug("NPCManager cleanup complete")

    def reset(self) -> None:
        """Reset NPC system for new game."""
        self.npcs.clear()
        self.dialogs.clear()
        self.interacted_npcs.clear()
        logger.debug("NPCManager reset complete")

    def load_dialogs(self, dialogs: dict[str, dict[str, dict[int | str, NPCDialogConfig]]]) -> None:
        """Load NPC dialog configurations.

        Args:
            dialogs: Dictionary mapping scenes to NPC names to dialog configs by conversation level.
        """
        self.dialogs = dialogs

    def load_scene_dialogs(self, scene_name: str) -> dict[str, Any]:
        """Load and cache dialogs for a specific scene.

        Args:
            scene_name: Name of the scene (map file without extension).
            settings: Game settings for resolving asset paths.

        Returns:
            The loaded dialog data for the scene.
        """
        if scene_name in self._dialog_cache:
            self.dialogs[scene_name] = self._dialog_cache[scene_name]
        else:
            try:
                scene_dialog_file = asset_path(f"dialogs/{scene_name}_dialogs.json", settings.ASSETS_HANDLE)
                if self.load_dialogs_from_json(scene_dialog_file) and scene_name in self.dialogs:
                    self._dialog_cache[scene_name] = self.dialogs[scene_name]
                else:
                    logger.debug("No dialogs found for scene %s", scene_name)
            except Exception:  # noqa: BLE001
                # No dialogs found or failed to load
                logger.debug("No dialogs found for scene %s", scene_name)

        return self.dialogs.get(scene_name, {})

    def load_dialogs_from_json(self, json_path: Path | str) -> bool:
        """Load NPC dialog configurations from a JSON file or directory.

        Args:
            json_path: Path to JSON file or directory containing dialog files.

        Returns:
            True if dialogs loaded successfully, False otherwise.
        """
        json_path = Path(json_path)

        if json_path.is_dir():
            # Load all JSON files in the directory
            dialog_files = list(json_path.glob("*.json"))
            if not dialog_files:
                logger.warning("No dialog files found in directory: %s", json_path)
                return False

            for dialog_file in dialog_files:
                self._load_dialog_file(dialog_file)
            return True

        if json_path.is_file():
            # Load single file
            return self._load_dialog_file(json_path)

        logger.warning("Dialog path not found: %s", json_path)
        return False

    def _load_dialog_file(self, json_path: Path) -> bool:
        """Load dialogs from a single JSON file.

        Extracts scene name from filename (e.g., casa_dialogs.json -> casa).

        Args:
            json_path: Path to the JSON file containing dialog data.

        Returns:
            True if dialogs loaded successfully, False otherwise.
        """
        try:
            with json_path.open() as f:
                data = json.load(f)

            # Extract scene from filename (e.g., casa_dialogs.json -> casa)
            # For backwards compatibility, files without scene prefix use "default"
            filename = json_path.stem  # filename without extension
            if "_dialogs" in filename:
                scene = filename.replace("_dialogs", "")
            elif "_dialog" in filename:
                scene = filename.replace("_dialog", "")
            else:
                # No scene in filename, use default
                scene = "default"

            # Initialize scene in dialogs dict if not exists
            if scene not in self.dialogs:
                self.dialogs[scene] = {}

            # Convert JSON structure to NPCDialogConfig objects
            npc_count = 0

            for npc_name, npc_dialogs in data.items():
                # Initialize NPC dialogs dict if not exists
                if npc_name not in self.dialogs[scene]:
                    self.dialogs[scene][npc_name] = {}

                for level_str, dialog_data in npc_dialogs.items():
                    # Try to convert to int, but keep as string if it fails
                    # String keys can be used for conditional dialogs (e.g., "1_reminder")
                    try:
                        level: int | str = int(level_str)
                    except ValueError:
                        level = level_str

                    # Create dialog config
                    self.dialogs[scene][npc_name][level] = NPCDialogConfig(
                        text=dialog_data["text"],
                        name=dialog_data.get("name"),
                        conditions=dialog_data.get("conditions"),
                        on_condition_fail=dialog_data.get("on_condition_fail"),
                    )

                npc_count += 1

            logger.info("Loaded dialogs for %d NPCs from %s (scene: %s)", npc_count, json_path.name, scene)
        except FileNotFoundError:
            logger.warning("Dialog file not found: %s", json_path)
            return False
        except json.JSONDecodeError:
            logger.exception("Failed to parse dialog JSON from %s", json_path)
            return False
        except OSError:
            logger.warning("Failed to access dialog file: %s", json_path)
            return False
        except Exception:
            logger.exception("Unexpected error loading dialogs from %s", json_path)
            return False
        else:
            return True

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

    def on_key_press(self, symbol: int, modifiers: int, context: GameContext) -> bool:
        """Handle interaction input for NPCs.

        Args:
            symbol: Arcade key constant.
            modifiers: Modifier key bitfield.
            context: Game context.

        Returns:
            True if interaction occurred.
        """
        if symbol == arcade.key.SPACE:
            player_sprite = context.player_sprite

            if player_sprite:
                nearby = self.get_nearby_npc(player_sprite)
                logger.debug(
                    "NPCManager: SPACE pressed, player at (%.1f, %.1f), npcs=%d, nearby=%s",
                    player_sprite.center_x,
                    player_sprite.center_y,
                    len(self.npcs),
                    nearby[1] if nearby else None,
                )
                if nearby:
                    _sprite, name, _dialog_level = nearby
                    if self.interact_with_npc(name, context):
                        return True
        return False

    def interact_with_npc(self, name: str, context: GameContext) -> bool:
        """Trigger interaction with a specific NPC.

        Args:
            name: Name of the NPC to interact with.
            context: GameContext for access to other systems.

        Returns:
            True if interaction started (dialog shown).
        """
        # Get NPC state
        npc = self.get_npc_by_name(name)
        if not npc:
            return False

        dialog_manager = cast("DialogBaseManager", context.get_system("dialog"))

        # Get dialog
        current_scene = context.current_scene or "default"

        dialog_data = self.get_dialog(name, npc.dialog_level, current_scene, context)
        if not dialog_data:
            return False

        dialog_config, on_condition_fail = dialog_data

        if dialog_manager:
            # If conditions failed, execute on_condition_fail actions
            if on_condition_fail:
                for action in on_condition_fail:
                    if action.get("type") == "dialog":
                        fail_text = action.get("text", [])
                        speaker = action.get("speaker", name)
                        dialog_manager.show_dialog(speaker, fail_text, dialog_level=npc.dialog_level)
                        return True
                return False

            # Show dialog - use display name from config if available, otherwise use NPC key name
            if dialog_config:
                display_name = dialog_config.name or name
                dialog_manager.show_dialog(
                    display_name, dialog_config.text, dialog_level=npc.dialog_level, npc_key=name
                )
                self.mark_npc_as_interacted(name)
                return True

        return False

    def mark_npc_as_interacted(self, npc_name: str) -> None:
        """Mark an NPC as interacted with.

        Args:
            npc_name: Name of the NPC.
        """
        self.interacted_npcs.add(npc_name)
        logger.debug("NPCManager: NPC '%s' marked as interacted", npc_name)

    def has_npc_been_interacted_with(self, npc_name: str) -> bool:
        """Check if an NPC has been interacted with.

        Args:
            npc_name: Name of the NPC to check.

        Returns:
            True if the NPC has been interacted with, False otherwise.
        """
        return npc_name in self.interacted_npcs

    def _check_dialog_conditions(self, conditions: list[dict[str, Any]], context: GameContext) -> bool:
        """Check if all dialog conditions are met using ConditionRegistry.

        Args:
            conditions: List of condition dictionaries.
            context: Game context for accessing systems.

        Returns:
            True if all conditions are met.
        """
        for condition in conditions:
            check_type = condition.get("check")
            if not check_type:
                logger.warning("NPCManager: Condition missing 'check' field")
                return False

            # Delegate to ConditionRegistry
            if not ConditionRegistry.check(check_type, condition, context):
                return False

        return True

    def get_dialog(
        self, npc_name: str, dialog_level: int, scene: str = "default", context: GameContext | None = None
    ) -> tuple[NPCDialogConfig | None, list[dict[str, Any]] | None]:
        """Get dialog for an NPC at a specific conversation level in a scene.

        Args:
            npc_name: The NPC name.
            dialog_level: The conversation level.
            scene: The current scene name (defaults to "default" for backwards compatibility).
            context: Game context for checking conditions. If None, conditions are not checked.

        Returns:
            Tuple of (dialog_config, on_condition_fail_actions):
            - dialog_config: NPCDialogConfig if conditions met, None if no dialog found
            - on_condition_fail_actions: List of actions to execute if conditions failed, None otherwise
        """
        # Try to get dialogs for the specified scene first, fall back to default
        scene_dialogs = self.dialogs.get(scene)
        if not scene_dialogs:
            scene_dialogs = self.dialogs.get("default")

        if not scene_dialogs or npc_name not in scene_dialogs:
            return None, None

        # Get all available dialog states for this NPC
        available_dialogs = scene_dialogs[npc_name]

        # First check for exact conversation level match
        if dialog_level in available_dialogs:
            exact_match = available_dialogs[dialog_level]
            if exact_match.conditions:
                if context and self._check_dialog_conditions(exact_match.conditions, context):
                    # Conditions met, return the dialog
                    return exact_match, None
                # Conditions failed or no context, return on_condition_fail actions
                logger.debug("Dialog condition failed for %s level %d", npc_name, dialog_level)
                return None, exact_match.on_condition_fail
            # No conditions, return the dialog
            return exact_match, None

        # No exact match found, look for fallback dialogs
        candidates: list[tuple[int | str, NPCDialogConfig]] = []

        for state, dialog_config in available_dialogs.items():
            # Skip the exact level we already checked
            if state == dialog_level:
                continue

            # Check if this dialog's conditions are met
            if dialog_config.conditions:
                if context and self._check_dialog_conditions(dialog_config.conditions, context):
                    candidates.append((state, dialog_config))
            else:
                # No conditions means always available
                candidates.append((state, dialog_config))

        if not candidates:
            # No dialogs with met conditions
            logger.debug("No dialogs with met conditions for %s at level %d", npc_name, dialog_level)
            return None, None

        # Prefer string keys (like "1_reminder") over numeric progression
        string_candidates = [(s, d) for s, d in candidates if isinstance(s, str)]
        if string_candidates:
            return string_candidates[0][1], None

        # Fall back to numeric progression - highest level <= dialog_level
        numeric_candidates = [(s, d) for s, d in candidates if isinstance(s, int)]
        if numeric_candidates:
            numeric_candidates.sort(key=lambda x: x[0], reverse=True)
            for state, dialog_config in numeric_candidates:
                if state <= dialog_level:
                    return dialog_config, None

        # Last resort: return first candidate
        return candidates[0][1], None

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

    def move_npc_to_tile(self, npc_name: str, tile_x: int, tile_y: int) -> None:
        """Start moving an NPC to a target tile position.

        Args:
            npc_name: The NPC name.
            tile_x: Target tile x coordinate.
            tile_y: Target tile y coordinate.
        """
        npc = self.npcs.get(npc_name)
        if not npc:
            logger.warning("Cannot move unknown NPC: %s", npc_name)
            return

        if not self.pathfinding:
            logger.warning("Cannot move NPC %s: pathfinding not available", npc_name)
            return

        logger.info("Starting pathfinding for %s", npc_name)
        logger.debug("  From: (%.1f, %.1f)", npc.sprite.center_x, npc.sprite.center_y)
        logger.debug("  To tile: (%d, %d)", tile_x, tile_y)

        # Collect all moving NPCs to exclude from pathfinding obstacles
        moving_npc_sprites = [other_npc.sprite for other_npc in self.npcs.values() if other_npc.is_moving]

        path = self.pathfinding.find_path(
            npc.sprite.center_x,
            npc.sprite.center_y,
            tile_x,
            tile_y,
            exclude_sprite=npc.sprite,
            exclude_sprites=moving_npc_sprites,
        )

        logger.info("  Path length: %d waypoints", len(path))
        if path:
            logger.debug("  First waypoint: %s", path[0])

        npc.path = path
        npc.is_moving = bool(path)

    def show_npcs(self, npc_names: list[str], wall_list: arcade.SpriteList | None = None) -> None:
        """Make hidden NPCs visible and add them to collision.

        Args:
            npc_names: List of NPC names to reveal.
            wall_list: Optional wall list to add visible NPCs to for collision.
        """
        for npc_name in npc_names:
            npc = self.npcs.get(npc_name)
            if npc and not npc.sprite.visible:
                npc.sprite.visible = True

                # Start appear animation for animated NPCs
                if isinstance(npc.sprite, AnimatedNPC):
                    npc.sprite.start_appear_animation()

                if wall_list is not None and npc.sprite not in wall_list:
                    wall_list.append(npc.sprite)
                logger.info("Showing hidden NPC: %s", npc_name)

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update NPC movements along their paths.

        Args:
            delta_time: Time since last update in seconds.
            context: Game context (provides access to wall_list if needed).
        """
        for npc in self.npcs.values():
            # Update animation for animated NPCs
            if isinstance(npc.sprite, AnimatedNPC):
                npc.sprite.update_animation(delta_time, moving=npc.is_moving)

                # Check if appear animation just completed
                if npc.sprite.appear_complete and not npc.appear_event_emitted:
                    if self.event_bus:
                        self.event_bus.publish(NPCAppearCompleteEvent(npc_name=npc.name))
                        logger.info("%s appear animation complete, event emitted", npc.name)
                    npc.appear_event_emitted = True

                # Check if disappear animation just completed
                if npc.sprite.disappear_complete and not npc.disappear_event_emitted:
                    if self.event_bus:
                        self.event_bus.publish(NPCDisappearCompleteEvent(npc_name=npc.name))
                        logger.info("%s disappear animation complete, event emitted", npc.name)
                    npc.disappear_event_emitted = True

            if not npc.is_moving or not npc.path:
                continue

            # Get next waypoint
            target_x, target_y = npc.path[0]

            # Calculate direction to target
            dx = target_x - npc.sprite.center_x
            dy = target_y - npc.sprite.center_y
            distance = (dx**2 + dy**2) ** 0.5

            # Update direction for animated NPCs based on horizontal movement
            if isinstance(npc.sprite, AnimatedNPC):
                if dx > 0 and npc.sprite.current_direction != "right":
                    npc.sprite.set_direction("right")
                elif dx < 0 and npc.sprite.current_direction != "left":
                    npc.sprite.set_direction("left")

            # Move towards target
            if distance < self.waypoint_threshold:
                # Close enough to waypoint, move to next
                npc.path.popleft()
                if not npc.path:
                    # Path completed
                    npc.sprite.center_x = target_x
                    npc.sprite.center_y = target_y
                    npc.is_moving = False

                    # Emit movement complete event
                    if self.event_bus:
                        self.event_bus.publish(NPCMovementCompleteEvent(npc_name=npc.name))
                        logger.info("%s movement complete, event emitted", npc.name)

            # Move NPC (only if distance > 0 to avoid division by zero)
            elif distance > 0:
                move_distance = self.npc_speed * delta_time
                move_distance = min(move_distance, distance)
                npc.sprite.center_x += (dx / distance) * move_distance
                npc.sprite.center_y += (dy / distance) * move_distance

    def get_npc_positions(self) -> dict[str, dict[str, float | bool]]:
        """Get current positions and visibility for all NPCs.

        Exports the position and visibility state of all registered NPCs for save data.
        This allows the save system to preserve NPC locations after scripted movements
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
            npc_positions = npc_manager.get_npc_positions()
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
            save_data = save_manager.load_game(slot=1)
            if save_data and save_data.npc_positions:
                npc_manager._restore_positions(save_data.npc_positions)
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
            if npc_manager.has_moving_npcs():
                logger.debug("Cannot pause: NPCs are moving")
                return
        """
        return any(npc.is_moving for npc in self.npcs.values())

    def load_npcs_from_objects(
        self,
        npc_objects: list,
        scene: arcade.Scene | None,
        wall_list: arcade.SpriteList | None = None,
    ) -> None:
        """Load NPCs from Tiled object layer (like Player, Portals, etc.).

        Creates AnimatedNPC instances from object layer data and adds them to the scene.

        Args:
            npc_objects: List of Tiled objects from tile_map.object_lists["NPCs"].
            scene: The arcade Scene to add NPC sprites to.
            settings: Game settings for asset paths.
            wall_list: Optional wall list to add visible NPCs to for collision.
        """
        # Create NPCs sprite list for the scene if needed
        npc_sprite_list = arcade.SpriteList()

        for npc_obj in npc_objects:
            if not npc_obj.properties:
                continue

            npc_name = npc_obj.properties.get("name")
            if not npc_name:
                continue

            npc_name = npc_name.lower()

            # Get position from object shape
            spawn_x = float(npc_obj.shape[0])
            spawn_y = float(npc_obj.shape[1])

            # Get sprite sheet properties
            sprite_sheet = npc_obj.properties.get("sprite_sheet")
            tile_size = npc_obj.properties.get("tile_size", 32)

            if not sprite_sheet:
                logger.warning("NPC %s missing 'sprite_sheet' property", npc_name)
                continue

            sprite_sheet_path = asset_path(sprite_sheet, settings.ASSETS_HANDLE)

            # Extract animation props
            anim_props = {
                key: val
                for key, val in npc_obj.properties.items()
                if key.startswith(("idle_", "walk_")) and isinstance(val, int)
            }

            try:
                animated_npc = AnimatedNPC(
                    sprite_sheet_path,
                    tile_size=tile_size,
                    columns=12,
                    scale=1.0,
                    center_x=spawn_x,
                    center_y=spawn_y,
                    **anim_props,
                )

                # Store properties for later use
                animated_npc.properties = npc_obj.properties

                # Handle initial visibility
                if npc_obj.properties.get("initially_hidden", False):
                    animated_npc.visible = False

                # Register with manager
                self.register_npc(animated_npc, npc_name)

                # Add to sprite list
                npc_sprite_list.append(animated_npc)

                # Add to wall list if visible
                if wall_list is not None and animated_npc.visible:
                    wall_list.append(animated_npc)

                logger.debug("Loaded NPC %s at (%.1f, %.1f)", npc_name, spawn_x, spawn_y)

            except Exception:
                logger.exception("Failed to create AnimatedNPC for %s", npc_name)

        # Add NPCs layer to scene
        if scene is not None and len(npc_sprite_list) > 0:
            if "NPCs" in scene:
                scene.remove_sprite_list_by_name("NPCs")
            scene.add_sprite_list("NPCs", sprite_list=npc_sprite_list)
            logger.info("Added %d NPCs to scene", len(npc_sprite_list))

    def get_save_state(self) -> dict[str, Any]:
        """Return serializable state for saving NPC data.

        Saves NPC positions, visibility, dialog levels, and animation flags.

        Returns:
            Dictionary mapping NPC names to their state dictionaries.
        """
        state: dict[str, Any] = {}
        for npc_name, npc in self.npcs.items():
            npc_state: dict[str, Any] = {
                "x": npc.sprite.center_x,
                "y": npc.sprite.center_y,
                "visible": npc.sprite.visible,
                "dialog_level": npc.dialog_level,
            }

            # Save animation flags for AnimatedNPC sprites
            if isinstance(npc.sprite, AnimatedNPC):
                npc_state["appear_complete"] = npc.sprite.appear_complete
                npc_state["disappear_complete"] = npc.sprite.disappear_complete
                npc_state["interact_complete"] = npc.sprite.interact_complete

            state[npc_name] = npc_state

        return state

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Restore NPC state from save data.

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

            # Restore animation flags for AnimatedNPC sprites
            if isinstance(npc.sprite, AnimatedNPC):
                npc.sprite.appear_complete = npc_state.get("appear_complete", False)
                npc.sprite.disappear_complete = npc_state.get("disappear_complete", False)
                npc.sprite.interact_complete = npc_state.get("interact_complete", False)

        logger.info("Restored state for %d NPCs", len(state))
