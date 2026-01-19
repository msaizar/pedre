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
from enum import Enum, auto
from typing import TYPE_CHECKING, ClassVar, cast

import arcade

from pedre.constants import asset_path
from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry
from pedre.systems.scene.events import SceneStartEvent

if TYPE_CHECKING:
    from typing import Any

    from pedre.caches.loader import CacheLoader
    from pedre.config import GameSettings
    from pedre.systems import CameraManager, PortalManager
    from pedre.systems.game_context import GameContext
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
    dependencies: ClassVar[list[str]] = ["npc", "portal", "interaction", "player", "script"]

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

        # Map data (merged from MapManager)
        self.tile_map: arcade.TileMap | None = None
        self.arcade_scene: arcade.Scene | None = None
        self.waypoints: dict[str, tuple[float, float]] = {}
        self.current_map: str = ""

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
        self._load_map(map_file, context, self._settings)

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

    def _load_map(self, map_file: str, context: GameContext, settings: GameSettings) -> None:
        """Load a Tiled map and populate game context and systems.

        Args:
            map_file: Filename of the .tmx map to load (e.g. "map.tmx").
            context: GameContext for updating shared state (wall_list, waypoints).
            settings: GameSettings for resolving asset paths.
        """
        map_path = asset_path(f"maps/{map_file}", settings.assets_handle)
        logger.info("Loading map: %s", map_path)
        self.current_map = map_file

        # 1. Load TileMap and Scene
        self.tile_map = arcade.load_tilemap(map_path, scaling=1.0)
        self.arcade_scene = arcade.Scene.from_tilemap(self.tile_map)

        # 2. Extract collision layers
        wall_list = arcade.SpriteList()
        collision_layer_names = ["Walls", "Collision", "Objects", "Buildings"]
        if self.arcade_scene:
            for layer_name in collision_layer_names:
                if layer_name in self.arcade_scene:
                    for sprite in self.arcade_scene[layer_name]:
                        wall_list.append(sprite)

        # Update context with wall list (needed by physics, pathfinding)
        context.wall_list = wall_list

        # 3. Load other components
        self._load_waypoints(settings)
        context.waypoints = self.waypoints

        # 4. Delegate to other systems
        self._load_npcs(context, settings)
        self._load_portals(context)
        self._load_interactive_objects(context)

        # 5. Let PlayerManager spawn player using new map data
        # Note: PlayerManager.setup() might have run earlier with no map.
        # We need to trigger player spawn now that map is loaded.
        player_manager = context.get_system("player")
        if player_manager and hasattr(player_manager, "spawn_player"):
            player_manager.spawn_player(context, settings)

        # 6. Invalidate physics engine so it recreates with new player/walls
        physics_manager = context.get_system("physics")
        if physics_manager and hasattr(physics_manager, "invalidate"):
            physics_manager.invalidate()

        # 7. Update Pathfinding (needs new wall list)
        pathfinding = context.get_system("pathfinding")
        if pathfinding and hasattr(pathfinding, "set_wall_list"):
            pathfinding.set_wall_list(wall_list)

        # 8. Setup camera with map bounds
        self._setup_camera(context, settings)

    def _load_waypoints(self, settings: GameSettings) -> None:
        """Load waypoints from object layer."""
        self.waypoints = {}
        if not self.tile_map:
            return

        waypoint_layer = self.tile_map.object_lists.get("Waypoints")
        if not waypoint_layer:
            return

        for waypoint in waypoint_layer:
            if waypoint.name:
                x = float(waypoint.shape[0])
                y = float(waypoint.shape[1])
                tile_x = int(x // settings.tile_size)
                tile_y = int(y // settings.tile_size)
                self.waypoints[waypoint.name] = (tile_x, tile_y)
                logger.debug(
                    "SceneManager: Loaded waypoint '%s' at pixel (%.1f, %.1f) -> tile (%d, %d)",
                    waypoint.name,
                    x,
                    y,
                    tile_x,
                    tile_y,
                )

    def _load_npcs(self, context: GameContext, settings: GameSettings) -> None:
        """Load NPCs from map and register with NPCManager."""
        npc_manager = context.get_system("npc")
        if not npc_manager:
            return

        # Try loading from object layer first (like Player, Portals, etc.)
        if self.tile_map and hasattr(npc_manager, "load_npcs_from_objects"):
            npc_layer = self.tile_map.object_lists.get("NPCs")
            if npc_layer:
                npc_manager.load_npcs_from_objects(npc_layer, self.arcade_scene, settings, context.wall_list)
                return

    def _load_portals(self, context: GameContext) -> None:
        """Load portals from map and register with PortalManager."""
        portal_manager = context.get_system("portal")
        if not portal_manager or not self.tile_map:
            return

        portal_manager.clear()  # Clear old portals

        portal_layer = self.tile_map.object_lists.get("Portals")
        if not portal_layer:
            return

        for portal in portal_layer:
            if not portal.name or not portal.properties or not portal.shape:
                continue

            # Extract shape logic (same as GameView)
            xs: list[float] = []
            ys: list[float] = []

            if isinstance(portal.shape, (list, tuple)) and len(portal.shape) > 0:
                first_elem = portal.shape[0]
                if isinstance(first_elem, (tuple, list)):
                    for p in portal.shape:
                        # the shape p is (x, y)
                        xs.append(float(p[0]))
                        ys.append(float(p[1]))
                else:
                    xs.append(float(portal.shape[0]))
                    ys.append(float(portal.shape[1]))
            else:
                continue

            sprite = arcade.Sprite()
            sprite.center_x = (min(xs) + max(xs)) / 2
            sprite.center_y = (min(ys) + max(ys)) / 2
            sprite.width = max(xs) - min(xs)
            sprite.height = max(ys) - min(ys)

            cast("PortalManager", portal_manager).register_portal(sprite=sprite, name=portal.name)

    def _load_interactive_objects(self, context: GameContext) -> None:
        """Register interactive objects from 'Interactive' layer."""
        interaction_manager = context.get_system("interaction")
        if not interaction_manager or not self.arcade_scene:
            return

        interaction_manager.clear()

        if "Interactive" in self.arcade_scene:
            for sprite in self.arcade_scene["Interactive"]:
                # Get name logic (same as GameView)
                name = None
                if hasattr(sprite, "properties") and sprite.properties:
                    name = sprite.properties.get("name")

                if not name and hasattr(sprite, "name"):
                    name = sprite.name

                if name:
                    interaction_manager.register_object(sprite, name.lower())

    def _setup_camera(self, context: GameContext, settings: GameSettings) -> None:
        """Setup camera with map bounds after loading."""
        camera_manager = cast("CameraManager", context.get_system("camera"))
        if not camera_manager or not self.tile_map:
            return

        # Create camera positioned at player (or map center if no player)
        player_sprite = context.player_sprite
        if player_sprite:
            initial_pos = (player_sprite.center_x, player_sprite.center_y)
        else:
            # Center of map
            map_width = self.tile_map.width * self.tile_map.tile_width
            map_height = self.tile_map.height * self.tile_map.tile_height
            initial_pos = (map_width / 2, map_height / 2)

        camera = arcade.camera.Camera2D(position=initial_pos)
        camera_manager.set_camera(camera)

        # Set bounds based on map size
        map_width = self.tile_map.width * self.tile_map.tile_width
        map_height = self.tile_map.height * self.tile_map.tile_height
        window = arcade.get_window()
        camera_manager.set_bounds(map_width, map_height, window.width, window.height)

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
