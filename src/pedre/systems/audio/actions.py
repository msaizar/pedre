"""Actions for audio system."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self, cast

from pedre.actions import Action
from pedre.actions.registry import ActionRegistry

if TYPE_CHECKING:
    from pedre.systems.audio.manager import AudioManager
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@ActionRegistry.register("play_sfx")
class PlaySFXAction(Action):
    """Play a sound effect.

    This action plays a one-time sound effect through the audio manager. Sound effects
    are short audio clips that don't loop, such as footsteps, item pickups, or interaction
    sounds.

    The sfx_file should be the filename without the path - the audio manager handles
    locating the file in the appropriate sound effects directory.

    Example usage:
        {
            "type": "play_sfx",
            "sfx": "door_open.wav"
        }
    """

    def __init__(self, sfx_file: str) -> None:
        """Initialize SFX action.

        Args:
            sfx_file: Name of the sound effect file to play.
        """
        self.sfx_file = sfx_file
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Play the sound effect."""
        if not self.executed:
            audio_manager = cast("AudioManager", context.get_system("audio"))
            audio_manager.play_sfx(self.sfx_file)
            self.executed = True
            logger.debug("PlaySFXAction: Playing %s", self.sfx_file)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create PlaySFXAction from a dictionary."""
        return cls(sfx_file=data.get("file", ""))


@ActionRegistry.register("play_music")
class PlayMusicAction(Action):
    """Play background music.

    This action plays or changes the background music track. Unlike sound effects,
    music tracks typically loop continuously to create atmosphere. The action can
    optionally override the default volume level.

    If music is already playing, it will be stopped and the new track will start.
    The music_file should be the filename without the path - the audio manager handles
    locating the file in the appropriate music directory.

    Example usage:
        # Standard looping music
        {
            "type": "play_music",
            "music": "town_theme.ogg"
        }

        # One-time music at custom volume
        {
            "type": "play_music",
            "music": "victory_fanfare.ogg",
            "loop": false,
            "volume": 0.8
        }
    """

    def __init__(self, music_file: str, *, loop: bool = True, volume: float | None = None) -> None:
        """Initialize music action.

        Args:
            music_file: Name of the music file to play.
            loop: Whether to loop the music (default True).
            volume: Optional volume override (0.0 to 1.0).
        """
        self.music_file = music_file
        self.loop = loop
        self.volume = volume
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Play the background music."""
        if not self.executed:
            audio_manager = cast("AudioManager", context.get_system("audio"))
            audio_manager.play_music(self.music_file, loop=self.loop, volume=self.volume)
            self.executed = True
            logger.debug("PlayMusicAction: Playing %s (loop=%s)", self.music_file, self.loop)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create PlayMusicAction from a dictionary."""
        return cls(
            music_file=data.get("file", ""),
            loop=data.get("loop", True),
            volume=data.get("volume"),
        )
