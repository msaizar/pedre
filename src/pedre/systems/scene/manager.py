"""Scene management system for handling scene transitions, lifecycle, and map loading.

This module provides the SceneManager class, which manages the high-level state of the game
scenes, including:
- Loading and processing Tiled map files
- Tracking the current scene information
- Handling visual transitions (fade in/out) between scenes
- Coordinating system updates during transitions
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import arcade

from pedre.conf import settings
from pedre.constants import asset_path
from pedre.systems.registry import SystemRegistry
from pedre.systems.scene.base import SceneBaseManager, TransitionState
from pedre.systems.scene.events import SceneStartEvent

if TYPE_CHECKING:
    from typing import Any

    from pedre.systems.cache_manager import CacheManager
    from pedre.systems.camera.base import CameraBaseManager
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@SystemRegistry.register
class SceneManager(SceneBaseManager):
    """Manages scene transitions, lifecycle, and map loading.

    Responsibilities:
    - Load Tiled map files (.tmx)
    - Extract collision layers (walls, objects) to sprite lists
    - Extract and manage waypoints
    - Handle request_transition(map_file, waypoint)
    - Manage transition state machine (FADING_OUT -> LOADING -> FADING_IN -> NONE)
    - Render transition overlay
    - Orchestrate loading of map-dependent data for other systems:
        - Portals (PortalManager)
        - Interactive objects (InteractionManager)
        - NPCs (NPCManager)

    Attributes:
        tile_map: The loaded arcade.TileMap instance.
        arcade_scene: The arcade.Scene created from the tile map.
        waypoints: Dictionary of waypoints {name: (x, y)} from map object layer.
        current_map: The filename of the currently loaded map.
        current_scene: The name of the current scene (derived from map filename).
    """

    name: ClassVar[str] = "scene"
    dependencies: ClassVar[list[str]] = ["waypoint", "npc", "portal", "interaction", "player", "script"]

    # Class-level cache manager (persists across scene transitions)
    _cache_manager: ClassVar[CacheManager | None] = None

    @classmethod
    def init_cache_manager(cls, cache_manager: CacheManager) -> None:
        """Initialize the cache manager.

        Args:
            cache_manager: The CacheManager instance to use for caching.
        """
        cls._cache_manager = cache_manager

    @classmethod
    def get_cache_manager(cls) -> CacheManager | None:
        """Get the cache manager instance."""
        return cls._cache_manager

    @classmethod
    def restore_cache_state(cls, cache_states: dict[str, Any]) -> None:
        """Restore the cache state from saved data.

        Args:
            cache_states: Dictionary mapping cache names to their serialized state.
        """
        if cls._cache_manager:
            cls._cache_manager.from_dict(cache_states)

    @classmethod
    def get_cache_state_dict(cls) -> dict[str, Any]:
        """Get the cache state as a dictionary for saving."""
        if cls._cache_manager:
            return cls._cache_manager.to_dict()
        return {}

    def get_current_map(self) -> str:
        """Get current map."""
        return self.current_map

    def get_transition_state(self) -> TransitionState:
        """Get transition state."""
        return self.transition_state

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

        # Map data (merged from MapManager)
        self.tile_map: arcade.TileMap | None = None
        self.arcade_scene: arcade.Scene | None = None
        self.waypoints: dict[str, tuple[float, float]] = {}
        self.current_map: str = ""

    def setup(self, context: GameContext) -> None:
        """Initialize with context."""
        if context.current_scene:
            self.current_scene = context.current_scene

    def reset(self) -> None:
        """Reset scene manager state for new game."""
        self.current_scene = "default"
        self.current_map = ""
        self.transition_state = TransitionState.NONE
        self.transition_alpha = 0.0
        self.pending_map_file = None
        self.pending_spawn_waypoint = None
        logger.debug("SceneManager reset complete")

    def get_arcade_scene(self) -> arcade.Scene | None:
        """Get arcade scene."""
        return self.arcade_scene

    def get_tile_map(self) -> arcade.TileMap | None:
        """Get tile map."""
        return self.tile_map

    def load_level(self, map_file: str, spawn_waypoint: str | None, context: GameContext) -> None:
        """Central orchestration for loading a new map/level.

        Args:
            map_file: The .tmx filename.
            spawn_waypoint: Optional waypoint to spawn at.
            context: Game context.
        """
        # Cache current scene state before transitioning
        if self._cache_manager:
            self._cache_manager.cache_scene(self.current_scene, context)

        logger.info("SceneManager: Loading level %s", map_file)
        current_scene = map_file.replace(".tmx", "").lower()
        self.current_scene = current_scene
        context.update_scene(current_scene)

        # Set next_spawn_waypoint in context BEFORE loading map, so PlayerManager.spawn_player()
        # can use it to spawn the player at the correct position directly
        if spawn_waypoint:
            context.next_spawn_waypoint = spawn_waypoint
            logger.debug("SceneManager: Set context.next_spawn_waypoint to '%s'", spawn_waypoint)

        # Load map
        self._load_map(map_file, context)

        # Get NPC and script managers for scene loading
        npc_manager = context.npc_manager
        script_manager = context.script_manager

        npc_dialogs_data = {}
        if npc_manager:
            npc_dialogs_data = npc_manager.load_scene_dialogs(current_scene)

        if script_manager:
            script_manager.load_scene_scripts(current_scene, npc_dialogs_data)

        # Restore scene state using cache manager
        if self._cache_manager:
            self._cache_manager.restore_scene(current_scene, context)

            # Sync wall_list with NPC visibility after restore
            if npc_manager and context.wall_list:
                for npc_state in npc_manager.npcs.values():
                    if not npc_state.sprite.visible and npc_state.sprite in context.wall_list:
                        context.wall_list.remove(npc_state.sprite)
                    elif npc_state.sprite.visible and npc_state.sprite not in context.wall_list:
                        context.wall_list.append(npc_state.sprite)

        # Emit SceneStartEvent
        context.event_bus.publish(SceneStartEvent(current_scene))

    def _load_map(self, map_file: str, context: GameContext) -> None:
        """Load a Tiled map and populate game context and systems.

        Args:
            map_file: Filename of the .tmx map to load (e.g. "map.tmx").
            context: GameContext for updating shared state (wall_list, waypoints).
        """
        map_path = asset_path(f"maps/{map_file}", settings.ASSETS_HANDLE)
        logger.info("Loading map: %s", map_path)
        self.current_map = map_file

        # 1. Load TileMap and Scene
        self.tile_map = arcade.load_tilemap(map_path, scaling=1.0)
        self.arcade_scene = arcade.Scene.from_tilemap(self.tile_map)

        # 2. Extract collision layers (foundation for other systems)
        wall_list = self._extract_collision_layers(self.arcade_scene)
        context.wall_list = wall_list

        # 3. Let systems load their Tiled data (in dependency order)
        # This includes waypoints, portals, interactions, player, NPCs
        self._load_systems_from_tiled(context)

        # 4. Invalidate physics engine (needs new player/walls)
        physics_manager = context.physics_manager
        physics_manager.invalidate()

        # 5. Update pathfinding (needs new wall list)
        pathfinding = context.pathfinding_manager
        pathfinding.set_wall_list(wall_list)

        # 6. Setup camera with map bounds
        self._setup_camera(context)

    def _extract_collision_layers(self, arcade_scene: arcade.Scene | None) -> arcade.SpriteList:
        """Extract collision layers into a wall list."""
        wall_list = arcade.SpriteList()
        collision_layer_names = ["Walls", "Collision", "Objects", "Buildings"]
        if arcade_scene:
            for layer_name in collision_layer_names:
                if layer_name in arcade_scene:
                    for sprite in arcade_scene[layer_name]:
                        wall_list.append(sprite)
        return wall_list

    def _load_systems_from_tiled(self, context: GameContext) -> None:
        """Call load_from_tiled() on all systems that implement it."""
        # Iterate through all systems (already in dependency order)
        for system in context.get_systems().values():
            # Only call if system has load_from_tiled and both tile_map and arcade_scene are loaded
            if hasattr(system, "load_from_tiled") and self.tile_map is not None and self.arcade_scene is not None:
                system.load_from_tiled(
                    self.tile_map,
                    self.arcade_scene,
                    context,
                )
                logger.debug("Loaded Tiled data for system: %s", system.name)

    def _setup_camera(self, context: GameContext) -> None:
        """Setup camera with map bounds after loading."""
        camera_manager = context.camera_manager
        if not camera_manager or not self.tile_map:
            return

        # Determine initial camera position based on follow configuration
        initial_pos = self._get_initial_camera_position(camera_manager, context)

        camera = arcade.camera.Camera2D(position=initial_pos)
        camera_manager.set_camera(camera)

        # Set bounds based on map size
        map_width = self.tile_map.width * self.tile_map.tile_width
        map_height = self.tile_map.height * self.tile_map.tile_height
        window = arcade.get_window()
        camera_manager.set_bounds(map_width, map_height, window.width, window.height)

        # Apply camera following configuration from map properties
        camera_manager.apply_follow_config(context)

    def _get_initial_camera_position(
        self, camera_manager: CameraBaseManager, context: GameContext
    ) -> tuple[float, float]:
        """Determine initial camera position based on follow configuration.

        Checks the camera's follow config (loaded from Tiled map properties) to
        determine where the camera should start. This prevents flickering when
        the camera should follow an NPC instead of the player.

        Args:
            camera_manager: The camera manager with follow config.
            context: Game context with player and NPCs.

        Returns:
            Tuple of (x, y) position for initial camera placement.
        """
        # Check if camera has follow config from Tiled
        follow_config = camera_manager.get_follow_config()

        if follow_config and follow_config.get("mode") == "npc":
            # Camera should follow NPC - position at NPC initially
            npc_name = follow_config.get("target")
            if npc_name:
                npc_manager = context.npc_manager
                if npc_manager:
                    npc_state = npc_manager.get_npc_by_name(npc_name)
                    if npc_state:
                        logger.debug(
                            "Initial camera position set to NPC '%s' at (%.1f, %.1f)",
                            npc_name,
                            npc_state.sprite.center_x,
                            npc_state.sprite.center_y,
                        )
                        return (npc_state.sprite.center_x, npc_state.sprite.center_y)

        # Default: position at player (or map center if no player)
        player_sprite = context.player_sprite
        if player_sprite:
            logger.debug(
                "Initial camera position set to player at (%.1f, %.1f)",
                player_sprite.center_x,
                player_sprite.center_y,
            )
            return (player_sprite.center_x, player_sprite.center_y)
        # Center of map
        if self.tile_map:
            map_width = self.tile_map.width * self.tile_map.tile_width
            map_height = self.tile_map.height * self.tile_map.tile_height
            logger.debug(
                "Initial camera position set to map center at (%.1f, %.1f)",
                map_width / 2,
                map_height / 2,
            )
            return (map_width / 2, map_height / 2)
        return (0.0, 0.0)

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
        """Draw the map scene and transition overlay."""
        # Draw the map scene
        if self.arcade_scene:
            self.arcade_scene.draw()

        # Draw transition overlay if transitioning
        if self.transition_state != TransitionState.NONE:
            self._draw_transition_overlay(context)

    def _draw_transition_overlay(self, context: GameContext) -> None:
        """Draw the black fade overlay."""
        camera_manager = context.camera_manager
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
