"""Base class for SceneManager."""

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


class SceneBaseManager(BaseSystem):
    """Base class for SceneManager."""

    def load_level(self, map_file: str, spawn_waypoint: str | None, context: GameContext) -> None:
        """Central orchestration for loading a new map/level."""
        return

    def get_transition_state(self) -> TransitionState:
        """Get transition state."""
        return TransitionState()

    @classmethod
    def get_cache_manager(cls) -> CacheManager | None:
        """Get the cache manager instance."""
        return

    @classmethod
    def restore_cache_state(cls, cache_states: dict[str, Any]) -> None:  # noqa: ARG003
        """Restore the cache state from saved data."""
        return

    @classmethod
    def get_cache_state_dict(cls) -> dict[str, Any]:
        """Get the cache state as a dictionary for saving."""
        return {}

    def get_current_map(self) -> str:
        """Get current map."""
        return ""

    def get_arcade_scene(self) -> arcade.Scene | None:
        """Get arcade scene."""
        return

    def get_tile_map(self) -> arcade.TileMap | None:
        """Get tile map."""
        return
