"""Audio plugin with manager and actions.

This module provides the audio management plugin for the game, handling both
background music and sound effects with caching, volume control, and playback
state management.

The audio plugin consists of:
- AudioPlugin: Main plugin for managing music and SFX playback

Actions (registered via INSTALLED_ACTIONS):
- PlayMusicAction: Script action to play background music
- PlaySFXAction: Script action to play sound effects
"""

from pedre.plugins.audio.manager import AudioBasePlugin, AudioPlugin

__all__ = ["AudioBasePlugin", "AudioPlugin"]
