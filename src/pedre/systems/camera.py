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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import arcade


class CameraManager:
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

    def __init__(
        self,
        camera: arcade.camera.Camera2D,
        lerp_speed: float = 0.1,
        *,
        use_bounds: bool = False,
    ) -> None:
        """Initialize the camera manager.

        Creates a camera manager that will smooth follow a target position
        with optional boundary constraints.

        Args:
            camera: The arcade Camera2D to manage. This is the camera that
                will be positioned and used for rendering.
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
        self.camera = camera
        self.lerp_speed = lerp_speed
        self.use_bounds = use_bounds
        self.bounds: tuple[float, float, float, float] | None = None  # (min_x, max_x, min_y, max_y)

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
        # Apply bounds if enabled
        if self.use_bounds and self.bounds:
            min_x, max_x, min_y, max_y = self.bounds
            target_x = max(min_x, min(max_x, target_x))
            target_y = max(min_y, min(max_y, target_y))

        self.camera.position = (target_x, target_y)

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
        self.camera.use()
