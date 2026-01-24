"""Camera management system for smooth camera movement.

This module provides camera control for the game, enabling smooth following
of the player sprite with optional boundary constraints to prevent the camera
from showing areas outside the game map.

Key Features:
    - Smooth camera following using linear interpolation (lerp)
    - Configurable follow speed for different camera feel
    - Map boundary constraints to prevent showing empty space
    - Instant teleport for scene transitions
    - Support for small maps (smaller than viewport)

Camera Behavior:
    The camera follows the player's position with a slight delay, creating a
    smooth, cinematic feel. The interpolation speed controls how quickly the
    camera catches up to the player:
    - Lower lerp_speed (e.g., 0.05): Slower, more dramatic camera
    - Higher lerp_speed (e.g., 0.2): Faster, more responsive camera
    - lerp_speed = 1.0: Instant following (no smoothing)

Boundary System:
    When boundaries are enabled, the camera is constrained to keep the viewport
    within the map area. This prevents showing black space beyond map edges.
    For maps smaller than the viewport, the camera centers on the map.

Usage Example:
    # Initialize camera manager
    camera_manager = CameraManager(camera, lerp_speed=0.1)

    # Set boundaries based on map size
    camera_manager.set_bounds(
        map_width=1600,
        map_height=1200,
        viewport_width=1024,
        viewport_height=768
    )

    # Each frame, follow the player smoothly
    camera_manager.smooth_follow(player.center_x, player.center_y)

    # Activate camera for rendering
    camera_manager.use()

Integration:
    - Created during map loading in GameView
    - Updated every frame in on_update()
    - Used before drawing world objects in on_draw()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    import arcade

    from pedre.systems.game_context import GameContext
    from pedre.systems.npc import NPCManager

logger = logging.getLogger(__name__)


@SystemRegistry.register
class CameraManager(BaseSystem):
    """Manages camera with smooth following and optional boundaries.

    The CameraManager wraps an Arcade Camera2D object and provides smooth
    following behavior with boundary constraints. It uses linear interpolation
    (lerp) to gradually move the camera toward the target position each frame,
    creating a pleasant, non-jarring camera experience.

    The manager can constrain the camera to map boundaries, ensuring the
    viewport never shows areas outside the game world. This is essential for
    maintaining immersion and preventing visual glitches.

    Attributes:
        camera: The Arcade Camera2D being managed.
        lerp_speed: Speed of interpolation (0.0 to 1.0).
            - 0.05: Very slow, dramatic following
            - 0.1: Default smooth following
            - 0.2: Responsive following
            - 1.0: Instant following (no smoothing)
        use_bounds: Whether boundary constraints are active.
        bounds: Boundary limits as (min_x, max_x, min_y, max_y) or None.

    Technical Details:
        - Camera position represents the center point of the viewport
        - Bounds account for half-viewport size to prevent edge showing
        - Small maps (< viewport size) are handled by centering
        - All positions are in world coordinates (pixels)
    """

    name: ClassVar[str] = "camera"
    dependencies: ClassVar[list[str]] = ["npc"]  # Need NPC system for validation

    def __init__(
        self,
        camera: arcade.camera.Camera2D | None = None,
        lerp_speed: float = 0.1,
        *,
        use_bounds: bool = False,
    ) -> None:
        """Initialize the camera manager.

        Creates a camera manager that will smooth follow a target position
        with optional boundary constraints.

        Args:
            camera: The arcade Camera2D to manage. This is the camera that
                will be positioned and used for rendering. Can be None if
                the camera will be set later via set_camera().
            lerp_speed: Speed of camera interpolation (0.0 to 1.0).
                Higher values make the camera catch up faster. Default 0.1
                provides a good balance between smooth and responsive.
            use_bounds: Whether to initially enable boundary constraints.
                Default False. Use set_bounds() to configure and enable.

        Example:
            # Create smooth camera with default settings
            camera_manager = CameraManager(camera, lerp_speed=0.1)

            # Create more responsive camera
            camera_manager = CameraManager(camera, lerp_speed=0.2)
        """
        self.camera: arcade.camera.Camera2D | None = camera
        self.lerp_speed = lerp_speed
        self.use_bounds = use_bounds
        self.bounds: tuple[float, float, float, float] | None = None  # (min_x, max_x, min_y, max_y)
        self.follow_mode: str | None = None  # None, "player", "npc"
        self.follow_target_npc: str | None = None
        self.follow_smooth: bool = True
        # Tiled configuration (applied after camera is set)
        self._follow_config: dict[str, Any] | None = None

    def setup(self, context: GameContext) -> None:
        """Initialize the camera system with game context and settings.

        Args:
            context: Game context providing access to other systems.
        """
        logger.debug("CameraManager setup complete")

    def cleanup(self) -> None:
        """Clean up camera resources when the scene unloads."""
        self.camera = None
        self.bounds = None
        self.use_bounds = False
        self.follow_mode = None
        self.follow_target_npc = None
        self._follow_config = None
        logger.debug("CameraManager cleanup complete")

    def get_state(self) -> dict[str, Any]:
        """Return serializable state for saving (BaseSystem interface).

        Camera state typically doesn't need to be saved as it follows the player,
        but we save the lerp_speed in case it was modified during gameplay.
        """
        return {
            "lerp_speed": self.lerp_speed,
            "use_bounds": self.use_bounds,
            "follow_mode": self.follow_mode,
            "follow_target_npc": self.follow_target_npc,
            "follow_smooth": self.follow_smooth,
        }

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restore state from save data (BaseSystem interface)."""
        self.lerp_speed = state.get("lerp_speed", 0.1)
        self.use_bounds = state.get("use_bounds", False)
        self.follow_mode = state.get("follow_mode")
        self.follow_target_npc = state.get("follow_target_npc")
        self.follow_smooth = state.get("follow_smooth", True)

    def set_camera(self, camera: arcade.camera.Camera2D) -> None:
        """Set the camera to manage.

        Args:
            camera: The arcade Camera2D to manage.
        """
        self.camera = camera

    def set_bounds(
        self,
        map_width: float,
        map_height: float,
        viewport_width: float,
        viewport_height: float,
    ) -> None:
        """Set camera bounds based on map and viewport size.

        Calculates and sets the camera boundary constraints to prevent showing
        areas outside the map. The bounds are calculated to keep the viewport
        fully within the map area, accounting for the fact that camera position
        represents the viewport center.

        Special handling for small maps:
        - If map width < viewport width: Centers horizontally
        - If map height < viewport height: Centers vertically
        - If both: Centers the map in the viewport

        The method automatically enables boundary constraints after calculating.

        Args:
            map_width: Total width of the map in pixels. Typically calculated
                as map_width_tiles * tile_size.
            map_height: Total height of the map in pixels. Typically calculated
                as map_height_tiles * tile_size.
            viewport_width: Width of the viewport/window in pixels.
                Use window.width for fullscreen or window dimensions.
            viewport_height: Height of the viewport/window in pixels.
                Use window.height for fullscreen or window dimensions.

        Example:
            # Set bounds for a 50x40 tile map with 32px tiles
            # on a 1024x768 window
            camera_manager.set_bounds(
                map_width=50 * 32,      # 1600 pixels
                map_height=40 * 32,     # 1280 pixels
                viewport_width=1024,
                viewport_height=768
            )

            # Result: Camera can move in range:
            # X: 512 to 1088 (centers player without showing map edges)
            # Y: 384 to 896

        Note:
            Call this after loading a new map or on window resize to ensure
            camera stays properly constrained.
        """
        # Camera is centered on position, so bounds are half viewport from edges
        half_viewport_width = viewport_width / 2
        half_viewport_height = viewport_height / 2

        min_x = half_viewport_width
        max_x = map_width - half_viewport_width
        min_y = half_viewport_height
        max_y = map_height - half_viewport_height

        # If map is smaller than viewport, center it
        if max_x < min_x:
            min_x = max_x = map_width / 2
        if max_y < min_y:
            min_y = max_y = map_height / 2

        self.bounds = (min_x, max_x, min_y, max_y)
        self.use_bounds = True

    def smooth_follow(self, target_x: float, target_y: float) -> None:
        """Smoothly move camera towards target position.

        Uses linear interpolation (lerp) to gradually move the camera from its
        current position toward the target position. This creates a smooth,
        cinematic following effect where the camera appears to "chase" the target
        with a slight delay.

        The interpolation formula is:
            new_position = current + (target - current) * lerp_speed

        This means the camera moves a fraction (lerp_speed) of the remaining
        distance each frame, creating an easing effect that slows as it approaches
        the target.

        Boundary constraints (if enabled) are applied to the target position
        before interpolation, ensuring the camera never exceeds map bounds.

        Call this method every frame in your game's update loop for continuous
        smooth following.

        Args:
            target_x: Target x position in world coordinates. Typically the
                player's center_x position.
            target_y: Target y position in world coordinates. Typically the
                player's center_y position.

        Example:
            # In game update loop (60 FPS)
            camera_manager.smooth_follow(
                player_sprite.center_x,
                player_sprite.center_y
            )

        Note:
            With lerp_speed=0.1 at 60 FPS, the camera reaches 99% of target
            distance in approximately 0.75 seconds, creating a smooth but
            responsive feel.
        """
        if self.camera is None:
            return

        current_x, current_y = self.camera.position

        # Apply bounds if enabled
        if self.use_bounds and self.bounds:
            min_x, max_x, min_y, max_y = self.bounds
            target_x = max(min_x, min(max_x, target_x))
            target_y = max(min_y, min(max_y, target_y))

        # Smooth interpolation (lerp)
        new_x = current_x + (target_x - current_x) * self.lerp_speed
        new_y = current_y + (target_y - current_y) * self.lerp_speed

        self.camera.position = (new_x, new_y)

    def instant_follow(self, target_x: float, target_y: float) -> None:
        """Instantly move camera to target position.

        Immediately sets the camera position to the target without interpolation
        or smoothing. This is useful for:
        - Scene transitions (teleporting between maps)
        - Initial camera positioning when loading a map
        - Cutscenes requiring instant camera cuts
        - Resetting camera after player respawn

        Unlike smooth_follow(), there is no gradual movement - the camera jumps
        directly to the target position in a single frame.

        Boundary constraints (if enabled) are still applied to ensure the camera
        stays within valid map bounds.

        Args:
            target_x: Target x position in world coordinates. Typically the
                player's center_x or a specific world position.
            target_y: Target y position in world coordinates. Typically the
                player's center_y or a specific world position.

        Example:
            # Teleport camera to spawn point when loading map
            spawn_x, spawn_y = get_spawn_position()
            camera_manager.instant_follow(spawn_x, spawn_y)

            # Cut to specific location for cutscene
            camera_manager.instant_follow(1024, 768)

        Note:
            Use smooth_follow() for normal gameplay camera following.
            Use instant_follow() only when you want an immediate cut.
        """
        if self.camera is None:
            return

        # Apply bounds if enabled
        if self.use_bounds and self.bounds:
            min_x, max_x, min_y, max_y = self.bounds
            target_x = max(min_x, min(max_x, target_x))
            target_y = max(min_y, min(max_y, target_y))

        self.camera.position = (target_x, target_y)

    def set_follow_player(self, *, smooth: bool = True) -> None:
        """Set camera to follow the player.

        Args:
            smooth: If True, use smooth_follow. If False, use instant_follow.
        """
        self.follow_mode = "player"
        self.follow_target_npc = None
        self.follow_smooth = smooth
        logger.debug("Camera set to follow player (smooth=%s)", smooth)

    def set_follow_npc(self, npc_name: str, *, smooth: bool = True) -> None:
        """Set camera to follow a specific NPC.

        Args:
            npc_name: Name of the NPC to follow.
            smooth: If True, use smooth_follow. If False, use instant_follow.
        """
        self.follow_mode = "npc"
        self.follow_target_npc = npc_name
        self.follow_smooth = smooth
        logger.debug("Camera set to follow NPC '%s' (smooth=%s)", npc_name, smooth)

    def stop_follow(self) -> None:
        """Stop camera following, keeping it at current position."""
        self.follow_mode = None
        self.follow_target_npc = None
        logger.debug("Camera following stopped")

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update camera position based on follow mode.

        Called automatically every frame by SystemLoader.

        Args:
            delta_time: Time since last update (unused).
            context: Game context with player and systems.
        """
        if self.follow_mode == "player":
            if context.player_sprite:
                if self.follow_smooth:
                    self.smooth_follow(context.player_sprite.center_x, context.player_sprite.center_y)
                else:
                    self.instant_follow(context.player_sprite.center_x, context.player_sprite.center_y)
        elif self.follow_mode == "npc":
            npc_manager = cast("NPCManager", context.get_system("npc"))
            if npc_manager and self.follow_target_npc:
                npc_state = npc_manager.get_npc_by_name(self.follow_target_npc)
                if npc_state:
                    if self.follow_smooth:
                        self.smooth_follow(npc_state.sprite.center_x, npc_state.sprite.center_y)
                    else:
                        self.instant_follow(npc_state.sprite.center_x, npc_state.sprite.center_y)

    def load_from_tiled(
        self,
        tile_map: arcade.TileMap,
        arcade_scene: arcade.Scene,
        context: GameContext,
    ) -> None:
        """Load camera configuration from Tiled map properties.

        Reads camera_follow and camera_smooth properties to configure
        camera behavior. Configuration is stored and applied later via
        apply_follow_config() after the camera object is created.

        Map Property Configuration in Tiled:
            1. Click on the map name in Layers panel (deselect any layers)
            2. Open Properties panel (View → Properties)
            3. Add custom properties as needed

        Supported Properties:
            - camera_follow (string): "player", "npc:<name>", or "none"
              Default: "player"
            - camera_smooth (bool): true for smooth, false for instant
              Default: true

        Examples:
            camera_follow: "player"           # Follow player (default)
            camera_follow: "npc:merchant"     # Follow NPC named merchant
            camera_follow: "none"             # Static camera
            camera_smooth: false              # Instant following

        Args:
            tile_map: Loaded TileMap with properties.
            arcade_scene: Scene created from tile_map (unused).
            context: GameContext for NPC validation.
        """
        # Check if tile_map has properties
        if not hasattr(tile_map, "properties") or tile_map.properties is None:
            logger.debug("TileMap does not have properties, using defaults")
            self._follow_config = {"mode": "player", "smooth": True}
            return

        # Get camera properties with defaults
        camera_follow = tile_map.properties.get("camera_follow", "player")
        camera_smooth = tile_map.properties.get("camera_smooth", True)

        # Validate types
        if not isinstance(camera_follow, str):
            logger.warning("Invalid camera_follow property type: %s, using 'player'", type(camera_follow))
            camera_follow = "player"

        if not isinstance(camera_smooth, bool):
            logger.warning("Invalid camera_smooth property type: %s, using True", type(camera_smooth))
            camera_smooth = True

        # Parse camera_follow
        camera_follow = camera_follow.strip().lower()

        if camera_follow == "none":
            config = {"mode": "none", "smooth": camera_smooth}
        elif camera_follow == "player":
            config = {"mode": "player", "smooth": camera_smooth}
        elif camera_follow.startswith("npc:"):
            npc_name = camera_follow[4:].strip()
            if not npc_name:
                logger.warning("camera_follow 'npc:' requires NPC name, using 'player'")
                config = {"mode": "player", "smooth": camera_smooth}
            else:
                # Validate NPC exists
                npc_manager = cast("NPCManager", context.get_system("npc"))
                if npc_manager:
                    # NPCs are registered during load_from_tiled phase
                    # We can check if NPC will exist (it's in the map)
                    npc_state = npc_manager.get_npc_by_name(npc_name)
                    if npc_state is None:
                        logger.warning(
                            "camera_follow references NPC '%s' which does not exist, using 'player'",
                            npc_name,
                        )
                        config = {"mode": "player", "smooth": camera_smooth}
                    else:
                        logger.info("Camera will follow NPC: %s", npc_name)
                        config = {"mode": "npc", "target": npc_name, "smooth": camera_smooth}
                else:
                    logger.warning("NPCManager not available, cannot follow NPC, using 'player'")
                    config = {"mode": "player", "smooth": camera_smooth}
        else:
            logger.warning("Invalid camera_follow value: '%s', using 'player'", camera_follow)
            config = {"mode": "player", "smooth": camera_smooth}

        self._follow_config = config
        logger.debug("Camera follow config loaded: %s", config)

    def apply_follow_config(self, context: GameContext) -> None:
        """Apply camera following configuration loaded from Tiled.

        Called by SceneManager after camera is created and set.
        This applies the configuration stored by load_from_tiled().

        Args:
            context: GameContext with player and systems.
        """
        if not self._follow_config:
            # Default behavior if no config loaded
            if context.player_sprite:
                self.set_follow_player(smooth=True)
                logger.debug("Applied default camera following: player")
            return

        mode = self._follow_config["mode"]
        smooth = self._follow_config.get("smooth", True)

        if mode == "none":
            self.stop_follow()
            logger.info("Camera following disabled (static camera)")
        elif mode == "player":
            if context.player_sprite:
                self.set_follow_player(smooth=smooth)
                logger.info("Camera following player (smooth=%s)", smooth)
            else:
                logger.warning("Cannot follow player: player sprite not available")
        elif mode == "npc":
            npc_name = self._follow_config.get("target")
            if npc_name:
                self.set_follow_npc(npc_name, smooth=smooth)
                logger.info("Camera following NPC '%s' (smooth=%s)", npc_name, smooth)
            else:
                logger.error("NPC mode but no target specified")

    def shake(self, intensity: float = 10.0, duration: float = 0.5) -> None:
        """Add camera shake effect (for future implementation).

        PLACEHOLDER: This method is not yet implemented.

        Camera shake would add a temporary random offset to the camera position,
        creating a screen shake effect useful for:
        - Explosions and impacts
        - Earthquakes or environmental effects
        - Damage feedback to the player
        - Emphasizing dramatic moments

        Args:
            intensity: Shake intensity in pixels. Higher values create more
                pronounced shaking. Default 10.0 for subtle shake.
            duration: Shake duration in seconds. How long the shake effect
                lasts before gradually dampening. Default 0.5 seconds.

        Future Implementation Notes:
            - Would require tracking shake state (remaining duration, offset)
            - Update method would need to be called each frame
            - Random offset would be added to camera position
            - Intensity should gradually decrease over duration
            - Should work alongside smooth_follow() without interfering

        Example (when implemented):
            # Shake camera on explosion
            camera_manager.shake(intensity=20.0, duration=0.3)

            # Subtle shake for damage feedback
            camera_manager.shake(intensity=5.0, duration=0.2)
        """
        # Future enhancement: Implement camera shake
        # This would require tracking shake state and updating in the game loop

    def use(self) -> None:
        """Activate this camera for rendering.

        Makes this camera the active camera for all subsequent draw calls.
        In Arcade, this sets up the projection matrix for rendering the game
        world with the camera's current position and zoom level.

        This method should be called at the start of your draw loop, before
        drawing any world objects (sprites, tiles, etc.). UI elements typically
        use a separate camera or screen coordinates.

        Example:
            def on_draw(self):
                self.clear()

                # Activate game camera for world rendering
                self.camera_manager.use()

                # Draw world objects
                self.wall_list.draw()
                self.npc_list.draw()
                self.player_list.draw()

                # Switch to GUI camera for UI
                self.gui_camera.use()
                self.ui_elements.draw()

        Note:
            This is a thin wrapper around arcade.camera.Camera2D.use() for
            convenience and consistency with the manager pattern.
        """
        if self.camera is not None:
            self.camera.use()
