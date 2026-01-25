"""Base class for SceneManager."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    import arcade

    from pedre.systems.cache_manager import CacheManager
    from pedre.systems.game_context import GameContext


class TransitionState(Enum):
    """Enum for scene transition states."""

    NONE = auto()  # No transition happening
    FADING_OUT = auto()  # Fading out old scene
    LOADING = auto()  # Loading new scene (internal state)
    FADING_IN = auto()  # Fading in new scene


class SceneBaseManager(BaseSystem, ABC):
    """Base class for SceneManager."""

    @abstractmethod
    def load_level(self, map_file: str, spawn_waypoint: str | None, context: GameContext) -> None:
        """Central orchestration for loading a new map/level."""
        ...

    @abstractmethod
    def get_transition_state(self) -> TransitionState:
        """Get transition state."""
        ...

    @classmethod
    @abstractmethod
    def get_cache_manager(cls) -> CacheManager | None:
        """Get the cache manager instance."""
        ...

    @classmethod
    @abstractmethod
    def restore_cache_state(cls, cache_states: dict[str, Any]) -> None:
        """Restore the cache state from saved data."""
        ...

    @classmethod
    @abstractmethod
    def get_cache_state_dict(cls) -> dict[str, Any]:
        """Get the cache state as a dictionary for saving."""
        ...

    @abstractmethod
    def get_current_map(self) -> str:
        """Get current map."""
        ...

    @abstractmethod
    def get_arcade_scene(self) -> arcade.Scene | None:
        """Get arcade scene."""
        ...

    @abstractmethod
    def get_tile_map(self) -> arcade.TileMap | None:
        """Get tile map."""
        ...

    @abstractmethod
    def request_transition(self, map_file: str, spawn_waypoint: str | None = None) -> None:
        """Request a transition to a new map."""
        ...
