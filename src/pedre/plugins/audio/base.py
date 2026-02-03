"""Base class for AudioPlugin."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pedre.plugins.base import BasePlugin

if TYPE_CHECKING:
    import arcade


class AudioBasePlugin(BasePlugin, ABC):
    """Base class for AudioPlugin."""

    role = "audio_plugin"

    @abstractmethod
    def get_music_cache(self) -> dict[str, arcade.Sound]:
        """Get music cache."""
        ...

    @abstractmethod
    def set_music_cache(self, cache_key: str, sound: arcade.Sound) -> None:
        """Set music cache."""
        ...

    @abstractmethod
    def play_sfx(self, sound_name: str, *, volume: float | None = None) -> bool:
        """Play a sound effect."""
        ...

    @abstractmethod
    def play_music(self, filename: str, *, loop: bool = True, volume: float | None = None) -> bool:
        """Play background music."""
        ...
