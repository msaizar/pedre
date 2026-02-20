"""Actions for audio plugin."""

import logging
from typing import TYPE_CHECKING, Any, Self

from pedre.actions import Action
from pedre.actions.registry import ActionParseError, ActionRegistry
from pedre.conf import settings
from pedre.helpers import asset_exists

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


@ActionRegistry.register
class PlaySFXAction(Action):
    """Play a sound effect.

    This action plays a one-time sound effect through the audio plugin. Sound effects
    are short audio clips that don't loop, such as footsteps, item pickups, or interaction
    sounds.

    The sfx_file should be the filename without the path - the audio plugin handles
    locating the file in the appropriate sound effects directory.

    Example usage:
        {
            "name": "play_sfx",
            "sfx": "door_open.wav"
        }
    """

    name = "play_sfx"

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
            audio_plugin = context.audio_plugin
            audio_plugin.play_sfx(self.sfx_file)
            self.executed = True
            logger.debug("PlaySFXAction: Playing %s", self.sfx_file)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create PlaySFXAction from a dictionary."""
        file = data.get("file")

        if file is None:
            msg = "play_sfx: missing required 'file' field"
            raise ActionParseError(msg)

        if not isinstance(file, str):
            msg = "play_sfx: 'file' must be a string"
            raise ActionParseError(msg)

        full_path = f"{settings.AUDIO_SFX_DIRECTORY}/{file}"
        if not asset_exists(full_path):
            msg = f"play_sfx: '{full_path}' does not exist"
            raise ActionParseError(msg)

        return cls(sfx_file=file)


@ActionRegistry.register
class PlayMusicAction(Action):
    """Play background music.

    This action plays or changes the background music track. Unlike sound effects,
    music tracks typically loop continuously to create atmosphere. The action can
    optionally override the default volume level.

    If music is already playing, it will be stopped and the new track will start.
    The music_file should be the filename without the path - the audio plugin handles
    locating the file in the appropriate music directory.

    Example usage:
        # Standard looping music
        {
            "name": "play_music",
            "music": "town_theme.ogg"
        }

        # One-time music at custom volume
        {
            "name": "play_music",
            "music": "victory_fanfare.ogg",
            "loop": false,
            "volume": 0.8
        }
    """

    name = "play_music"

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
            audio_plugin = context.audio_plugin
            audio_plugin.play_music(self.music_file, loop=self.loop, volume=self.volume)
            self.executed = True
            logger.debug("PlayMusicAction: Playing %s (loop=%s)", self.music_file, self.loop)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create PlayMusicAction from a dictionary."""
        file = data.get("file")
        if file is None:
            msg = "play_music: missing required 'file' field"
            raise ActionParseError(msg)

        if not isinstance(file, str):
            msg = "play_music: 'file' must be a string"
            raise ActionParseError(msg)

        full_path = f"{settings.AUDIO_MUSIC_DIRECTORY}/{file}"
        if not asset_exists(full_path):
            msg = f"play_music: '{full_path}' does not exist"
            raise ActionParseError(msg)

        loop = data.get("loop", True)
        if not isinstance(loop, bool):
            msg = "play_music: 'loop' must be a bool"
            raise ActionParseError(msg)

        volume = data.get("volume")
        if volume is not None:
            if isinstance(volume, bool) or not isinstance(volume, (int, float)):
                msg = "play_music: 'volume' must be a number"
                raise ActionParseError(msg)
            volume = float(volume)

        return cls(
            music_file=file,
            loop=loop,
            volume=volume,
        )
