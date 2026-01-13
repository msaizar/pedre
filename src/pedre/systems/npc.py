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
    # Initialize manager
    npc_mgr = NPCManager(
        pathfinding_manager=pathfinding_mgr,
        interaction_distance=50,
        npc_speed=80.0,
        event_bus=event_bus
    )

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
    npc_mgr.update(delta_time)
"""

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import arcade

from pedre.sprites import AnimatedNPC
from pedre.systems.events import (
    NPCAppearCompleteEvent,
    NPCDisappearCompleteEvent,
    NPCMovementCompleteEvent,
)

if TYPE_CHECKING:
    from pedre.systems.events import EventBus
    from pedre.systems.inventory import InventoryManager
    from pedre.systems.pathfinding import PathfindingManager

logger = logging.getLogger(__name__)


@dataclass
class NPCState:
    """Runtime state tracking for a single NPC.

    NPCState holds all mutable state for an NPC during gameplay, including their current
    position (via sprite), conversation progress, pathfinding data, and animation status.
    This state persists throughout the game session and is updated as the NPC moves,
    interacts with players, and performs animations.

    The state is stored separately from dialog configuration (NPCDialogConfig) to separate
    what the NPC says (static data) from what the NPC is currently doing (runtime state).

    Attributes:
        sprite: The arcade Sprite representing this NPC visually. Can be a regular Sprite
               or an AnimatedNPC with animation capabilities. Position is tracked via
               sprite.center_x and sprite.center_y.
        name: Unique identifier for this NPC (e.g., "martin", "shopkeeper"). Used for
             lookups, dialog assignment, and event tracking.
        dialog_level: Current conversation progression level (0-based). Increments as
                     player has conversations, determining which dialog text is shown.
                     Default starts at 0 for first conversation.
        path: Queue of (x, y) pixel coordinates representing the NPC's pathfinding route.
             Waypoints are popped from the front as the NPC reaches them. Empty deque
             means no active path.
        is_moving: Whether the NPC is currently traversing a path. True during movement,
                  False when stationary. NPCs cannot be interacted with while moving.
        appear_event_emitted: Tracks if NPCAppearCompleteEvent has been published for this
                            NPC. Reset when starting a new appear animation. Prevents
                            duplicate event emissions.
        disappear_event_emitted: Tracks if NPCDisappearCompleteEvent has been published.
                               Reset when starting a new disappear animation. Prevents
                               duplicate event emissions.
    """

    sprite: arcade.Sprite
    name: str
    dialog_level: int = 0
    path: deque[tuple[float, float]] = field(default_factory=deque)
    is_moving: bool = False
    appear_event_emitted: bool = False
    disappear_event_emitted: bool = False


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
            "martin": {
                "1": {
                    "text": ["You're back! Did you check your inventory?"],
                    "conditions": [{"check": "inventory_accessed", "equals": true}],
                    "on_condition_fail": [
                        {"type": "dialog", "speaker": "martin", "text": ["Please check your inventory first!"]}
                    ]
                }
            }
        }
    """

    text: list[str]
    conditions: list[dict[str, Any]] | None = None
    on_condition_fail: list[dict[str, Any]] | None = None  # List of actions to execute if conditions fail


class NPCManager:
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
    """

    def __init__(
        self,
        pathfinding_manager: PathfindingManager,
        interaction_distance: int = 50,
        waypoint_threshold: int = 2,
        npc_speed: float = 80.0,
        inventory_manager: InventoryManager | None = None,
        event_bus: EventBus | None = None,
        interacted_objects: set[str] | None = None,
    ) -> None:
        """Initialize the NPC manager with pathfinding and configuration parameters.

        Creates a new NPCManager with empty NPC and dialog registries. The pathfinding
        manager is required for movement calculations. Other parameters configure interaction
        ranges, movement speeds, and optional integrations with other systems.

        Args:
            pathfinding_manager: PathfindingManager instance for A* path calculation.
                               Required for move_npc_to_tile() functionality.
            interaction_distance: Maximum distance in pixels from player to NPC for
                                interaction to be possible. Typical values: 40-60 pixels.
                                Default 50 allows comfortable interaction range.
            waypoint_threshold: Distance in pixels to consider a waypoint "reached" during
                              pathfinding. Lower values require more precision, higher values
                              allow cutting corners. Default 2 pixels provides good balance.
            npc_speed: Movement speed in pixels per second for all NPCs. Frame-rate
                      independent. Typical values: 60-100 pixels/second. Default 80 gives
                      moderate walking speed.
            inventory_manager: Optional InventoryManager for dialog conditions that check
                             if inventory has been accessed. Pass None if not using
                             inventory-conditional dialog.
            event_bus: Optional EventBus for publishing NPC events (movement complete,
                      animations finished). Pass None if not using event-driven scripts.
            interacted_objects: Optional set tracking object interaction history for dialog
                              conditions. Shared with GameContext.interacted_objects for
                              consistency.
        """
        self.npcs: dict[str, NPCState] = {}
        # Changed to scene -> npc -> level structure for scene-aware dialogs
        self.dialogs: dict[str, dict[str, dict[int | str, NPCDialogConfig]]] = {}
        self.pathfinding = pathfinding_manager
        self.interaction_distance = interaction_distance
        self.waypoint_threshold = waypoint_threshold
        self.npc_speed = npc_speed
        self.inventory_manager = inventory_manager
        self.event_bus = event_bus
        self.interacted_objects = interacted_objects if interacted_objects is not None else set()

    def load_dialogs(self, dialogs: dict[str, dict[str, dict[int | str, NPCDialogConfig]]]) -> None:
        """Load NPC dialog configurations.

        Args:
            dialogs: Dictionary mapping scenes to NPC names to dialog configs by conversation level.
        """
        self.dialogs = dialogs

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
                        conditions=dialog_data.get("conditions"),
                        on_condition_fail=dialog_data.get("on_condition_fail"),
                    )

                npc_count += 1

            logger.info("Loaded dialogs for %d NPCs from %s (scene: %s)", npc_count, json_path.name, scene)
        except Exception:
            logger.exception("Failed to load dialogs from %s", json_path)
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
        closest_distance = self.interaction_distance

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

    def _check_dialog_conditions(self, conditions: list[dict[str, Any]], npc_name: str) -> bool:
        """Check if all dialog conditions are met.

        Args:
            conditions: List of condition dictionaries.
            npc_name: Name of the NPC for level checks.

        Returns:
            True if all conditions are met.
        """
        for condition in conditions:
            check_type = condition.get("check")

            if check_type == "npc_dialog_level":
                expected_level = condition.get("equals")
                npc_state = self.npcs.get(npc_name)
                if not npc_state or npc_state.dialog_level != expected_level:
                    return False

            elif check_type == "inventory_accessed":
                expected = condition.get("equals", True)
                if not self.inventory_manager or self.inventory_manager.has_been_accessed != expected:
                    return False

            elif check_type == "object_interacted":
                object_name = condition.get("object", "")
                expected = condition.get("equals", True)
                was_interacted = object_name in self.interacted_objects
                logger.debug(
                    "Checking object_interacted: object=%s, expected=%s, was_interacted=%s, interacted_objects=%s",
                    object_name,
                    expected,
                    was_interacted,
                    self.interacted_objects,
                )
                if was_interacted != expected:
                    return False

            else:
                logger.warning("Unknown condition type: %s", check_type)
                return False

        return True

    def get_dialog(
        self, npc_name: str, dialog_level: int, scene: str = "default"
    ) -> tuple[NPCDialogConfig | None, list[dict[str, Any]] | None]:
        """Get dialog for an NPC at a specific conversation level in a scene.

        Args:
            npc_name: The NPC name.
            dialog_level: The conversation level.
            scene: The current scene name (defaults to "default" for backwards compatibility).

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
                if self._check_dialog_conditions(exact_match.conditions, npc_name):
                    # Conditions met, return the dialog
                    return exact_match, None
                # Conditions failed, return on_condition_fail actions
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
                if self._check_dialog_conditions(dialog_config.conditions, npc_name):
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
                if state <= dialog_level:  # type: ignore[operator]
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

    def update(self, delta_time: float, wall_list: arcade.SpriteList | None = None) -> None:
        """Update NPC movements along their paths.

        Args:
            delta_time: Time since last update in seconds.
            wall_list: Optional sprite list containing wall sprites (unused, kept for compatibility).
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

            # Move NPC
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

    def restore_state(self, npc_dialog_levels: dict[str, int]) -> None:
        """Restore NPC dialog levels from save data.

        Updates the dialog_level for each NPC based on saved state. This is called
        when loading a save file to restore conversation progression. NPCs not present
        in the save data retain their current dialog level (typically 0 for new NPCs).

        Args:
            npc_dialog_levels: Dictionary mapping NPC names to their saved dialog levels.
                Example: {"martin": 2, "shopkeeper": 1, "guard": 0}

        Example:
            # After loading save data
            save_data = save_manager.load_game(slot=1)
            if save_data:
                npc_manager.restore_state(save_data.npc_dialog_levels)
                # All NPCs now have their conversation progress restored
        """
        for npc_name, dialog_level in npc_dialog_levels.items():
            npc = self.npcs.get(npc_name)
            if npc:
                npc.dialog_level = dialog_level
                logger.debug("Restored %s dialog level to %d", npc_name, dialog_level)
            else:
                logger.warning("Cannot restore dialog level for unknown NPC: %s", npc_name)

    def restore_positions(self, npc_positions: dict[str, dict[str, float | bool]]) -> None:
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
                npc_manager.restore_positions(save_data.npc_positions)
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
