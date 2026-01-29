"""Base class for PlayerManager."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    from pedre.systems.player.sprites import AnimatedPlayer


class PlayerBaseManager(BaseSystem, ABC):
    """Base class for PlayerManager."""

    role = "player_manager"

    @abstractmethod
    def get_player_sprite(self) -> AnimatedPlayer | None:
        """Get the player sprite."""
        ...
