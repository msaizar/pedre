"""Base class for CameraManager."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    import arcade

    from pedre.systems.game_context import GameContext


class CameraBaseManager(BaseSystem, ABC):
    """Base class for CameraManager."""

    role = "camera_manager"

    @abstractmethod
    def set_camera(self, camera: arcade.camera.Camera2D) -> None:
        """Set the camera to manage."""
        ...

    @abstractmethod
    def set_bounds(
        self,
        map_width: float,
        map_height: float,
        viewport_width: float,
        viewport_height: float,
    ) -> None:
        """Set camera bounds based on map and viewport size."""
        ...

    @abstractmethod
    def get_follow_config(self) -> dict[str, Any] | None:
        """Get the stored follow config."""
        ...

    @abstractmethod
    def apply_follow_config(self, context: GameContext) -> None:
        """Apply camera following configuration loaded from Tiled."""
        ...

    @abstractmethod
    def use(self) -> None:
        """Activate this camera for rendering."""
        ...

    @abstractmethod
    def set_follow_player(self, *, smooth: bool = True) -> None:
        """Set camera to follow the player."""
        ...

    @abstractmethod
    def stop_follow(self) -> None:
        """Stop camera following, keeping it at current position."""
        ...

    @abstractmethod
    def set_follow_npc(self, npc_name: str, *, smooth: bool = True) -> None:
        """Set camera to follow a specific NPC."""
        ...
