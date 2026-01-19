"""Audio save provider for persisting audio settings."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.saves.base import BaseSaveProvider
from pedre.saves.registry import SaveRegistry

if TYPE_CHECKING:
    from pedre.systems.audio import AudioManager
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@dataclass
class AudioState:
    """State for audio settings.

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


@SaveRegistry.register
class AudioSaveProvider(BaseSaveProvider):
    """Save provider for audio settings persistence."""

    name: ClassVar[str] = "audio"
    priority: ClassVar[int] = 130

    def __init__(self) -> None:
        """Initialize the audio save provider."""
        self._state: AudioState | None = None

    def gather(self, context: GameContext) -> None:
        """Gather audio settings from the audio manager."""
        audio_manager = cast("AudioManager | None", context.get_system("audio"))
        if not audio_manager:
            return

        self._state = AudioState(
            music_volume=audio_manager.music_volume,
            sfx_volume=audio_manager.sfx_volume,
            music_enabled=audio_manager.music_enabled,
            sfx_enabled=audio_manager.sfx_enabled,
        )
        logger.debug("Gathered audio settings")

    def restore(self, context: GameContext) -> bool:
        """Restore audio settings to the audio manager."""
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
        """Serialize audio state for save files."""
        if self._state:
            return self._state.to_dict()
        return {}

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore audio state from save file data."""
        if data:
            self._state = AudioState.from_dict(data)
        else:
            self._state = None

    def clear(self) -> None:
        """Clear cached audio state."""
        self._state = None
