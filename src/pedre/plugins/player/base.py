"""Base class for PlayerPlugin."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pedre.plugins.base import BasePlugin

if TYPE_CHECKING:
    from pedre.sprites import AnimatedSprite


class PlayerBasePlugin(BasePlugin, ABC):
    """Base class for PlayerPlugin."""

    role = "player_plugin"

    @abstractmethod
    def get_player_sprite(self) -> AnimatedSprite | None:
        """Get the player sprite."""
        ...
