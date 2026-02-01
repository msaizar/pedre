"""Base class for ScenePlugin."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING

from pedre.plugins.base import BasePlugin

if TYPE_CHECKING:
    import arcade


class TransitionState(Enum):
    """Enum for scene transition states."""

    NONE = auto()  # No transition happening
    FADING_OUT = auto()  # Fading out old scene
    LOADING = auto()  # Loading new scene (internal state)
    FADING_IN = auto()  # Fading in new scene


class SceneBasePlugin(BasePlugin, ABC):
    """Base class for ScenePlugin."""

    role = "scene_plugin"

    @abstractmethod
    def get_current_scene(self) -> str:
        """Get current scene."""
        ...

    @abstractmethod
    def get_next_spawn_waypoint(self) -> str:
        """Get next spawn waypoint."""
        ...

    @abstractmethod
    def clear_next_spawn_waypoint(self) -> None:
        """Clear next spawn waypoint."""
        ...

    @abstractmethod
    def get_wall_list(self) -> arcade.SpriteList | None:
        """Get wall list."""
        ...

    @abstractmethod
    def remove_from_wall_list(self, sprite: arcade.Sprite) -> None:
        """Remove a sprite from the wall list."""
        ...

    @abstractmethod
    def add_to_wall_list(self, sprite: arcade.Sprite) -> None:
        """Add a sprite to the wall list."""
        ...

    @abstractmethod
    def load_level(self, map_file: str, *, initial: bool = False) -> None:
        """Central orchestration for loading a new map/level."""
        ...

    @abstractmethod
    def get_transition_state(self) -> TransitionState:
        """Get transition state."""
        ...

    @abstractmethod
    def get_current_map(self) -> str:
        """Get current map."""
        ...

    @abstractmethod
    def request_transition(self, map_file: str, spawn_waypoint: str | None = None) -> None:
        """Request a transition to a new map."""
        ...
