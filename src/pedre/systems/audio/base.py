"""Base class for AudiotSystem."""

from typing import TYPE_CHECKING

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    import arcade


class AudioBaseManager(BaseSystem):
    """Base class for AudioManager."""

    def get_music_cache(self) -> dict[str, arcade.Sound]:
        """Get music cache."""
        return {}

    def set_music_cache(self, cache_key: str, sound: arcade.Sound) -> None:
        """Set music cache."""
        return

    def play_sfx(self, sound_name: str, *, volume: float | None = None) -> bool:
        """Play a sound effect."""
        return False

    def mark_music_loading(self, filename: str) -> None:
        """Mark a music file as currently being loaded."""
        return

    def unmark_music_loading(self, filename: str) -> None:
        """Unmark a music file as being loaded."""
        return
