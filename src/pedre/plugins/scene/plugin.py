"""Scene management plugin for handling scene transitions, lifecycle, and map loading.

This module provides the ScenePlugin class, which manages the high-level state of the game
scenes, including:
- Loading and processing Tiled map files
- Tracking the current scene information
- Handling visual transitions (fade in/out) between scenes
- Coordinating plugin updates during transitions
"""

import logging
from typing import TYPE_CHECKING, ClassVar

import arcade

from pedre.conf import settings
from pedre.constants import asset_path
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.scene.base import SceneBasePlugin, TransitionState
from pedre.plugins.scene.events import SceneStartEvent

if TYPE_CHECKING:
    from typing import Any


logger = logging.getLogger(__name__)


@PluginRegistry.register
class ScenePlugin(SceneBasePlugin):
    """Manages scene transitions, lifecycle, and map loading.

    Responsibilities:
    - Load Tiled map files (.tmx)
    - Extract collision layers (walls, objects) to sprite lists
    - Extract and manage waypoints
    - Handle request_transition(map_file, waypoint)
    - Manage transition state machine (FADING_OUT -> LOADING -> FADING_IN -> NONE)
    - Render transition overlay
    - Orchestrate loading of map-dependent data for other plugins:
        - Portals (PortalPlugin)
        - Interactive objects (InteractionPlugin)
        - NPCs (NPCPlugin)

    Attributes:
        tile_map: The loaded arcade.TileMap instance.
        arcade_scene: The arcade.Scene created from the tile map.
        waypoints: Dictionary of waypoints {name: (x, y)} from map object layer.
        current_map: The filename of the currently loaded map.
        current_scene: The name of the current scene (derived from map filename).
    """

    name: ClassVar[str] = "scene"
    dependencies: ClassVar[list[str]] = ["cache", "waypoint", "npc", "portal", "interaction", "player", "script"]

    def get_current_map(self) -> str:
        """Get current map."""
        return self.current_map

    def get_current_scene(self) -> str:
        """Get current scene."""
        return self.current_map.replace(".tmx", "").lower()

    def get_transition_state(self) -> TransitionState:
        """Get transition state."""
        return self.transition_state

    def __init__(self) -> None:
        """Initialize the scene plugin."""
        self.current_scene: str = ""

        # Transition state
        self.transition_state: TransitionState = TransitionState.NONE
        self.transition_alpha: float = settings.SCENE_TRANSITION_ALPHA
        self.transition_speed: float = settings.SCENE_TRANSITION_SPEED

        # Pending transition data
        self.pending_map_file: str | None = None
        self.pending_spawn_waypoint: str | None = None

        # Map data (merged from MapPlugin)
        self.tile_map: arcade.TileMap | None = None
        self.arcade_scene: arcade.Scene | None = None
        self.current_map: str = ""
        self.wall_list: arcade.SpriteList = arcade.SpriteList()
        self.next_spawn_waypoint: str = ""

    def reset(self) -> None:
        """Reset scene plugin state for new game."""
        self.current_scene = ""
        self.current_map = ""
        self.transition_state = TransitionState.NONE
        self.transition_alpha = settings.SCENE_TRANSITION_ALPHA
        self.pending_map_file = None
        self.pending_spawn_waypoint = None
        self.wall_list.clear()
        logger.debug("ScenePlugin reset complete")

    def get_wall_list(self) -> arcade.SpriteList | None:
        """Get wall list."""
        return self.wall_list

    def remove_from_wall_list(self, sprite: arcade.Sprite) -> None:
        """Remove a sprite from the wall list."""
        self.wall_list.remove(sprite)

    def add_to_wall_list(self, sprite: arcade.Sprite) -> None:
        """Add a sprite to the wall list."""
        self.wall_list.append(sprite)

    def get_next_spawn_waypoint(self) -> str:
        """Get next spawn waypoint."""
        return self.next_spawn_waypoint

    def clear_next_spawn_waypoint(self) -> None:
        """Clear next spawn waypoint."""
        self.next_spawn_waypoint = ""

    def load_level(self, map_file: str, *, initial: bool = False) -> None:
        """Central orchestration for loading a new map/level.

        Args:
            map_file: The .tmx filename.
            initial: If it's the first level loading. Don't cache if not transitioning.
        """
        # Cache current scene state before transitioning
        cache_plugin = self.context.cache_plugin
        if not initial:
            cache_plugin.cache_scene(self.get_current_scene())

        logger.info("ScenePlugin: Loading level %s", map_file)
        current_scene = map_file.replace(".tmx", "").lower()
        self.current_scene = current_scene

        # Load map
        self._load_map(map_file)

        # Phase 2: Apply entity state from pending save data
        save_plugin = self.context.save_plugin
        save_plugin.apply_entity_states()

        # Load scene-specific dialogs
        npc_plugin = self.context.npc_plugin
        npc_plugin.load_scene_dialogs(current_scene)

        # Scripts are loaded globally at initialization, no per-scene loading needed

        # Restore scene state using cache plugin
        cache_plugin.restore_scene(current_scene)

        # Sync wall_list with NPC visibility after restore
        if self.wall_list:
            for npc_state in npc_plugin.get_npcs().values():
                if not npc_state.sprite.visible and npc_state.sprite in self.wall_list:
                    self.wall_list.remove(npc_state.sprite)
                elif npc_state.sprite.visible and npc_state.sprite not in self.wall_list:
                    self.wall_list.append(npc_state.sprite)

        # Emit SceneStartEvent
        self.context.event_bus.publish(SceneStartEvent(current_scene))

    def _load_map(self, map_file: str) -> None:
        """Load a Tiled map and populate game context and plugins.

        Args:
            map_file: Filename of the .tmx map to load (e.g. "map.tmx").

        """
        map_path = asset_path(f"{settings.SCENE_MAPS_FOLDER}/{map_file}", settings.ASSETS_HANDLE)
        logger.info("Loading map: %s", map_path)
        self.current_map = map_file

        # 1. Load TileMap and Scene
        self.tile_map = arcade.load_tilemap(map_path, scaling=settings.SCENE_TILEMAP_SCALING)
        self.arcade_scene = arcade.Scene.from_tilemap(self.tile_map)

        # 2. Extract collision layers (foundation for other plugins)
        self.wall_list = self._extract_collision_layers(self.arcade_scene)

        # 3. Let plugins load their Tiled data (in dependency order)
        # This includes waypoints, portals, interactions, player, NPCs, and camera
        self._load_plugins_from_tiled()

        # 4. Invalidate physics engine (needs new player/walls)
        physics_plugin = self.context.physics_plugin
        physics_plugin.invalidate()

    def _extract_collision_layers(self, arcade_scene: arcade.Scene | None) -> arcade.SpriteList:
        """Extract collision layers into a wall list."""
        wall_list = arcade.SpriteList()
        if arcade_scene:
            for layer_name in settings.SCENE_COLLISION_LAYER_NAMES:
                if layer_name in arcade_scene:
                    for sprite in arcade_scene[layer_name]:
                        wall_list.append(sprite)
        return wall_list

    def _load_plugins_from_tiled(self) -> None:
        """Call load_from_tiled() on all plugins that implement it."""
        # Iterate through all plugins (already in dependency order)
        for plugin in self.context.get_plugins().values():
            # Only call if plugin has load_from_tiled and both tile_map and arcade_scene are loaded
            if hasattr(plugin, "load_from_tiled") and self.tile_map is not None and self.arcade_scene is not None:
                plugin.load_from_tiled(
                    self.tile_map,
                    self.arcade_scene,
                )
                logger.debug("Loaded Tiled data for plugin: %s", plugin.name)

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
        self.transition_alpha = settings.SCENE_TRANSITION_ALPHA

    def on_draw(self) -> None:
        """Draw the map scene and transition overlay."""
        # Draw the map scene
        if self.arcade_scene:
            self.arcade_scene.draw()

        # Draw transition overlay if transitioning
        if self.transition_state != TransitionState.NONE:
            self._draw_transition_overlay()

    def _draw_transition_overlay(self) -> None:
        """Draw the black fade overlay."""
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

    def update(self, delta_time: float) -> None:
        """Update transition state."""
        if self.transition_state == TransitionState.NONE:
            return

        if self.transition_state == TransitionState.FADING_OUT:
            self.transition_alpha += self.transition_speed * delta_time
            if self.transition_alpha >= 1.0:
                self.transition_alpha = 1.0
                self.transition_state = TransitionState.LOADING

                # Perform the map switch
                self._perform_map_switch()

                self.transition_state = TransitionState.FADING_IN

        elif self.transition_state == TransitionState.FADING_IN:
            self.transition_alpha -= self.transition_speed * delta_time
            if self.transition_alpha <= 0.0:
                self.transition_alpha = 0.0
                self.transition_state = TransitionState.NONE
                logger.info("Transition complete")

    def _perform_map_switch(self) -> None:
        """Execute the logic to switch maps while screen is black."""
        if not self.pending_map_file:
            return

        # Use the pending data
        map_file = self.pending_map_file
        waypoint = self.pending_spawn_waypoint

        logger.debug(
            "ScenePlugin._perform_map_switch: map_file=%s, waypoint=%s",
            map_file,
            waypoint,
        )

        # Clear pending before loading to avoid re-entry issues
        self.pending_map_file = None
        self.pending_spawn_waypoint = None

        # Set spawn waypoint before loading if specified
        if waypoint:
            self.next_spawn_waypoint = waypoint
            logger.debug("ScenePlugin: Set next_spawn_waypoint to '%s'", waypoint)

        # Load the level through our own load_level method
        self.load_level(map_file)

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

    def get_save_state(self) -> dict[str, Any]:
        """Get save state."""
        return self.to_dict()

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Restore save state."""
        self.from_dict(state)

    def from_dict(self, data: dict[str, str]) -> None:
        """Convert audio settings to dictionary for save data serialization."""
        if "current_map" in data:
            self.current_map = data.get("current_map", "")

    def to_dict(self) -> dict[str, str]:
        """Load player coordinates from saved dictionary data."""
        if self.current_map:
            return {"current_map": self.current_map}
        return {}
