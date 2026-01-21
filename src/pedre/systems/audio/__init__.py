"""Audio system with manager and actions.

This module provides the audio management system for the game, handling both
background music and sound effects with caching, volume control, and playback
state management.

The audio system consists of:
- AudioManager: Main system for managing music and SFX playback
- PlayMusicAction: Script action to play background music
- PlaySFXAction: Script action to play sound effects
"""

from pedre.systems.audio.actions import PlayMusicAction, PlaySFXAction
from pedre.systems.audio.manager import AudioManager

__all__ = ["AudioManager", "PlayMusicAction", "PlaySFXAction"]
