"""Audio cache provider for persisting audio settings."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.caches.base import BaseCacheProvider
from pedre.caches.registry import CacheRegistry

if TYPE_CHECKING:
    from pedre.systems.audio import AudioManager
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@dataclass
class AudioState:
    """State for audio settings.

    Audio settings are global (not per-scene), so we store a single state.

    Attributes:
        music_volume: Music volume level (0.0 to 1.0).
        sfx_volume: Sound effects volume level (0.0 to 1.0).
        music_enabled: Whether music playback is enabled.
        sfx_enabled: Whether sound effects are enabled.
    """

    music_volume: float
    sfx_volume: float
    music_enabled: bool
    sfx_enabled: bool

    def to_dict(self) -> dict[str, float | bool]:
        """Convert to dictionary for serialization."""
        return {
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "music_enabled": self.music_enabled,
            "sfx_enabled": self.sfx_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float | bool]) -> AudioState:
        """Create from dictionary loaded from save file."""
        return cls(
            music_volume=float(data.get("music_volume", 0.5)),
            sfx_volume=float(data.get("sfx_volume", 0.7)),
            music_enabled=bool(data.get("music_enabled", True)),
            sfx_enabled=bool(data.get("sfx_enabled", True)),
        )


@CacheRegistry.register
class AudioCacheProvider(BaseCacheProvider):
    """Cache provider for audio settings persistence.

    Audio settings are global (not per-scene), so this cache stores
    a single state rather than per-scene states.
    """

    name: ClassVar[str] = "audio"
    priority: ClassVar[int] = 130

    def __init__(self) -> None:
        """Initialize the audio cache provider."""
        self._state: AudioState | None = None

    def cache(self, scene_name: str, context: GameContext) -> None:
        """Cache audio settings (ignores scene_name since audio is global)."""
        audio_manager = cast("AudioManager | None", context.get_system("audio"))
        if not audio_manager:
            return

        self._state = AudioState(
            music_volume=audio_manager.music_volume,
            sfx_volume=audio_manager.sfx_volume,
            music_enabled=audio_manager.music_enabled,
            sfx_enabled=audio_manager.sfx_enabled,
        )
        logger.debug("Cached audio settings")

    def restore(self, scene_name: str, context: GameContext) -> bool:
        """Restore audio settings (ignores scene_name since audio is global)."""
        if not self._state:
            return False

        audio_manager = cast("AudioManager | None", context.get_system("audio"))
        if not audio_manager:
            return False

        audio_manager.set_music_volume(self._state.music_volume)
        audio_manager.set_sfx_volume(self._state.sfx_volume)
        audio_manager.music_enabled = self._state.music_enabled
        audio_manager.sfx_enabled = self._state.sfx_enabled

        logger.debug("Restored audio settings")
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize audio cache state for save files."""
        if self._state:
            return self._state.to_dict()
        return {}

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore audio cache state from save file data."""
        if data:
            self._state = AudioState.from_dict(data)
        else:
            self._state = None

    def clear(self) -> None:
        """Clear cached audio state."""
        self._state = None

    def has_cached_state(self, scene_name: str) -> bool:
        """Check if audio state is cached (ignores scene_name)."""
        return self._state is not None
