"""Scene management system for handling scene transitions and lifecycle.

This module provides the SceneManager class, which manages the high-level state of the game
scenes, including:
- Tracking the current scene information
- Handling visual transitions (fade in/out) between scenes
- Orchestrating the loading of new maps via MapManager
- Coordinating system updates during transitions
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from typing import TYPE_CHECKING, ClassVar, cast

import arcade

from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry
from pedre.systems.scene.events import SceneStartEvent

if TYPE_CHECKING:
    from typing import Any

    from pedre.caches.loader import CacheLoader
    from pedre.config import GameSettings
    from pedre.systems.game_context import GameContext
    from pedre.systems.map import MapManager
    from pedre.systems.npc import NPCManager
    from pedre.systems.portal.events import PortalEnteredEvent
    from pedre.systems.script import ScriptManager

logger = logging.getLogger(__name__)


class TransitionState(Enum):
    """Enum for scene transition states."""

    NONE = auto()  # No transition happening
    FADING_OUT = auto()  # Fading out old scene
    LOADING = auto()  # Loading new scene (internal state)
    FADING_IN = auto()  # Fading in new scene


@SystemRegistry.register
class SceneManager(BaseSystem):
    """Manages scene transitions and lifecycle.

    Responsibilities:
    - Handle request_transition(map_file, waypoint)
    - Manage transition state machine (FADING_OUT -> LOADING -> FADING_IN -> NONE)
    - Render transition overlay
    - Trigger GameView.load_level() when screen is black
    """

    name: ClassVar[str] = "scene"
    dependencies: ClassVar[list[str]] = ["map", "npc", "script"]

    # Class-level cache loader (persists across scene transitions)
    _cache_loader: ClassVar[CacheLoader | None] = None

    @classmethod
    def init_cache_loader(cls, cache_loader: CacheLoader) -> None:
        """Initialize the cache loader.

        Args:
            cache_loader: The CacheLoader instance to use for caching.
        """
        cls._cache_loader = cache_loader

    @classmethod
    def get_cache_loader(cls) -> CacheLoader | None:
        """Get the cache loader instance."""
        return cls._cache_loader

    @classmethod
    def restore_cache_state(cls, cache_states: dict[str, Any]) -> None:
        """Restore the cache state from saved data.

        Args:
            cache_states: Dictionary mapping cache names to their serialized state.
        """
        if cls._cache_loader:
            cls._cache_loader.from_dict(cache_states)

    @classmethod
    def get_cache_state_dict(cls) -> dict[str, Any]:
        """Get the cache state as a dictionary for saving."""
        if cls._cache_loader:
            return cls._cache_loader.to_dict()
        return {}

    def __init__(self) -> None:
        """Initialize the scene manager."""
        self.current_scene: str = "default"

        # Transition state
        self.transition_state: TransitionState = TransitionState.NONE
        self.transition_alpha: float = 0.0  # 0.0 = transparent, 1.0 = opaque
        self.transition_speed: float = 3.0  # Alpha change per second

        # Pending transition data
        self.pending_map_file: str | None = None
        self.pending_spawn_waypoint: str | None = None

        self._settings: GameSettings | None = None

    def setup(self, context: GameContext, settings: GameSettings) -> None:
        """Initialize with context."""
        self._settings = settings
        if context.current_scene:
            self.current_scene = context.current_scene

    def load_level(self, map_file: str, spawn_waypoint: str | None, context: GameContext) -> None:
        """Central orchestration for loading a new map/level.

        Args:
            map_file: The .tmx filename.
            spawn_waypoint: Optional waypoint to spawn at.
            context: Game context.
        """
        if not self._settings:
            logger.error("SceneManager: Settings not initialized, cannot load level")
            return

        # Cache current scene state before transitioning
        if self._cache_loader:
            self._cache_loader.cache_all(self.current_scene, context)

        logger.info("SceneManager: Loading level %s", map_file)
        current_scene = map_file.replace(".tmx", "").lower()
        self.current_scene = current_scene
        context.update_scene(current_scene)

        # Set spawn_waypoint on game_view BEFORE loading map, so PlayerManager.spawn_player()
        # can use it to spawn the player at the correct position directly
        game_view = context.game_view
        if game_view and spawn_waypoint:
            game_view.spawn_waypoint = spawn_waypoint
            logger.debug("SceneManager: Set game_view.spawn_waypoint to '%s'", spawn_waypoint)

        # Load map
        map_manager = cast("MapManager", context.get_system("map"))
        if map_manager and hasattr(map_manager, "load_map"):
            map_manager.load_map(map_file, context, self._settings)

        # Get NPC and script managers for scene loading
        npc_manager = cast("NPCManager | None", context.get_system("npc"))
        script_manager = cast("ScriptManager | None", context.get_system("script"))

        npc_dialogs_data = {}
        if npc_manager and hasattr(npc_manager, "load_scene_dialogs"):
            npc_dialogs_data = npc_manager.load_scene_dialogs(current_scene, self._settings)

        if script_manager and hasattr(script_manager, "load_scene_scripts"):
            script_manager.load_scene_scripts(current_scene, self._settings, npc_dialogs_data)

        # Restore scene state using cache loader
        if self._cache_loader:
            self._cache_loader.restore_all(current_scene, context)

            # Sync wall_list with NPC visibility after restore
            if npc_manager and context.wall_list:
                for npc_state in npc_manager.npcs.values():
                    if not npc_state.sprite.visible and npc_state.sprite in context.wall_list:
                        context.wall_list.remove(npc_state.sprite)
                    elif npc_state.sprite.visible and npc_state.sprite not in context.wall_list:
                        context.wall_list.append(npc_state.sprite)

        # Emit SceneStartEvent
        context.event_bus.publish(SceneStartEvent(current_scene))

    def request_transition(self, map_file: str, spawn_waypoint: str | None = None) -> None:
        """Request a transition to a new map.

        Args:
            map_file: The .tmx filename of the new map.
            spawn_waypoint: Optional waypoint name to spawn at.
        """
        if self.transition_state != TransitionState.NONE:
            logger.warning("Transition already in progress, ignoring request to %s", map_file)
            return

        logger.info("Starting scene transition to %s (waypoint: %s)", map_file, spawn_waypoint)
        self.pending_map_file = map_file
        self.pending_spawn_waypoint = spawn_waypoint
        self.transition_state = TransitionState.FADING_OUT
        self.transition_alpha = 0.0

    def on_draw(self, context: GameContext) -> None:
        """Draw transition overlay."""
        if self.transition_state != TransitionState.NONE:
            self._draw_transition_overlay(context)

    def _draw_transition_overlay(self, context: GameContext) -> None:
        """Draw the black fade overlay."""
        camera_manager = context.get_system("camera")
        if camera_manager:
            pass

        # Ideally we use arcade.camera.Camera2D() (default identity)
        window = arcade.get_window()
        default_cam = arcade.camera.Camera2D()
        default_cam.use()

        alpha = int(self.transition_alpha * 255)
        # alpha clamped 0-255
        alpha = max(0, min(255, alpha))

        arcade.draw_lrbt_rectangle_filled(
            0,
            window.width,
            0,
            window.height,
            (0, 0, 0, alpha),
        )

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update transition state."""
        if self.transition_state == TransitionState.NONE:
            return

        if self.transition_state == TransitionState.FADING_OUT:
            self.transition_alpha += self.transition_speed * delta_time
            if self.transition_alpha >= 1.0:
                self.transition_alpha = 1.0
                self.transition_state = TransitionState.LOADING

                # Perform the map switch
                self._perform_map_switch(context)

                self.transition_state = TransitionState.FADING_IN

        elif self.transition_state == TransitionState.FADING_IN:
            self.transition_alpha -= self.transition_speed * delta_time
            if self.transition_alpha <= 0.0:
                self.transition_alpha = 0.0
                self.transition_state = TransitionState.NONE
                logger.info("Transition complete")

    def _perform_map_switch(self, context: GameContext) -> None:
        """Execute the logic to switch maps while screen is black."""
        if not self.pending_map_file:
            return

        # Use the pending data
        map_file = self.pending_map_file
        waypoint = self.pending_spawn_waypoint

        logger.debug(
            "SceneManager._perform_map_switch: map_file=%s, waypoint=%s",
            map_file,
            waypoint,
        )

        # Clear pending before loading to avoid re-entry issues
        self.pending_map_file = None
        self.pending_spawn_waypoint = None

        # Load the level through our own load_level method
        self.load_level(map_file, waypoint, context)

    def draw_overlay(self) -> None:
        """Draw the transition overlay (called from UI phase)."""
        if self.transition_state == TransitionState.NONE:
            return

        window = arcade.get_window()
        alpha = int(self.transition_alpha * 255)
        arcade.draw_lrbt_rectangle_filled(
            0,
            window.width,
            0,
            window.height,
            (0, 0, 0, alpha),
        )


def event_handler(event: PortalEnteredEvent, context: GameContext) -> None:
    """Handle portal entry events to trigger scene transitions.

    This is a placeholder event handler for portal entry events.
    The actual transition logic is handled by the script system.
    """
