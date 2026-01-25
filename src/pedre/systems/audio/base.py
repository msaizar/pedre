"""Base class for AudioManager."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    import arcade


class AudioBaseManager(BaseSystem, ABC):
    """Base class for AudioManager."""

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
    def mark_music_loading(self, filename: str) -> None:
        """Mark a music file as currently being loaded."""
        ...

    @abstractmethod
    def unmark_music_loading(self, filename: str) -> None:
        """Unmark a music file as being loaded."""
        ...

    @abstractmethod
    def play_music(self, filename: str, *, loop: bool = True, volume: float | None = None) -> bool:
        """Play background music."""
        ...
