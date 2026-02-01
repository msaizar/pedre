"""Base class for CameraManager."""

from abc import ABC, abstractmethod

from pedre.plugins.base import BasePlugin


class CameraBaseManager(BasePlugin, ABC):
    """Base class for CameraManager."""

    role = "camera_manager"

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
