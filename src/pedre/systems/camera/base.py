"""Base class for CameraManager."""

from typing import TYPE_CHECKING, Any

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    import arcade

    from pedre.systems.game_context import GameContext


class CameraBaseManager(BaseSystem):
    """Base class for CameraManager."""

    def set_camera(self, camera: arcade.camera.Camera2D) -> None:
        """Set the camera to manage."""
        return

    def set_bounds(
        self,
        map_width: float,
        map_height: float,
        viewport_width: float,
        viewport_height: float,
    ) -> None:
        """Set camera bounds based on map and viewport size."""
        return

    def get_follow_config(self) -> dict[str, Any] | None:
        """Get the stored follow config."""
        return

    def apply_follow_config(self, context: GameContext) -> None:
        """Apply camera following configuration loaded from Tiled."""
        return

    def use(self) -> None:
        """Activate this camera for rendering."""
        return
