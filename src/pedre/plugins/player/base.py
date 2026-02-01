"""Base class for PlayerManager."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pedre.plugins.base import BasePlugin

if TYPE_CHECKING:
    from pedre.plugins.player.sprites import AnimatedPlayer


class PlayerBaseManager(BasePlugin, ABC):
    """Base class for PlayerManager."""

    role = "player_manager"

    @abstractmethod
    def get_player_sprite(self) -> AnimatedPlayer | None:
        """Get the player sprite."""
        ...
