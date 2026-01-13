"""Audio system for music and sound effects.

This module provides the audio management system for the game, handling both
background music and sound effects with caching, volume control, and playback
state management.

Audio Organization:
    The audio system expects files to be organized in the assets/audio/ directory:

    assets/audio/
    ├── music/           # Background music tracks (looping)
    │   ├── background.ogg
    │   ├── beach.ogg
    │   └── turntable.mp3
    └── sfx/             # Sound effects (one-shot)
        ├── avi.mp3
        ├── martin.mp3
        └── feliz_cumple.mp3

Key Features:
    - Music caching for faster scene transitions
    - Sound effect caching for reduced loading times
    - Independent volume controls for music and SFX
    - Toggle support for muting music/SFX independently
    - Streaming support for non-looping music (reduces memory)
    - Background preloading with wait mechanism

Usage from Code:
    # Play background music
    audio_manager.play_music("background.ogg", loop=True, volume=0.7)

    # Play a sound effect
    audio_manager.play_sfx("avi.mp3")

    # Control volume
    audio_manager.set_music_volume(0.5)
    audio_manager.set_sfx_volume(0.8)

Usage from Scripts:
    [
        {"type": "play_music", "music": "beach.ogg", "loop": true},
        {"type": "play_sfx", "sfx": "feliz_cumple.mp3"}
    ]

Integration:
    - PlayMusicAction and PlaySFXAction in the scripting system
    - Called by game view for scene transitions and events
    - Responds to user settings for volume and enable/disable
"""

import logging
import time
from typing import Any

import arcade

from pedre.constants import asset_path

logger = logging.getLogger(__name__)


class AudioManager:
    """Manages background music and sound effects.

    The AudioManager is the central system for all audio playback in the game.
    It provides:
    - Background music playback with looping and volume control
    - Sound effect playback for game events and interactions
    - Intelligent caching to reduce loading times and improve performance
    - Independent enable/disable and volume controls for music and SFX
    - Streaming support for large, non-looping audio files

    Performance Optimizations:
    - Music files are cached after first load for instant replay
    - Sound effects are cached on first use and reused
    - Non-looping music uses streaming to avoid memory overhead
    - Background preloading with synchronization support

    State Management:
    - Tracks currently playing music and its player
    - Maintains separate enabled states for music and SFX
    - Stores volume preferences independently for music and SFX
    - Manages cache lifecycle to balance memory and performance
    """

    def __init__(self) -> None:
        """Initialize the audio manager.

        Creates an audio manager with default settings:
        - Music volume: 0.5 (50%)
        - SFX volume: 0.7 (70%)
        - Both music and SFX enabled
        - Empty caches ready for lazy loading
        """
        # Current music player
        self.current_music: arcade.Sound | None = None
        self.music_player: Any = None  # arcade.media.Player type not exposed in typing

        # Music cache (for faster scene transitions)
        self.music_cache: dict[str, arcade.Sound] = {}
        self._music_loading: set[str] = set()  # Track files currently being loaded

        # Sound effect cache
        self.sfx_cache: dict[str, arcade.Sound] = {}

        # Volume settings (0.0 to 1.0)
        self.music_volume = 0.5
        self.sfx_volume = 0.7

        # Track if music is enabled
        self.music_enabled = True
        self.sfx_enabled = True

    def play_music(self, filename: str, *, loop: bool = True, volume: float | None = None) -> bool:
        """Play background music.

        This method stops any currently playing music and starts a new track.
        Music files are automatically cached for faster replay on subsequent calls.
        Non-looping music uses streaming to reduce memory usage.

        Caching behavior:
        - Looping music: Loaded fully and cached for instant replay
        - Non-looping music: Streamed and not cached (saves memory)
        - Background preloading: Waits briefly if file is being preloaded

        Args:
            filename: Music file name (in assets/audio/music/). Examples:
                - "background.ogg" - Main game background music
                - "beach.ogg" - Beach scene music
                - "turntable.mp3" - Turntable interaction music
            loop: Whether to loop the music continuously (default True).
                Set to False for one-time tracks like victory fanfares.
            volume: Optional volume override (0.0 to 1.0). If not provided,
                uses the current music_volume setting (default 0.5).

        Returns:
            True if music started playing successfully, False otherwise.
            Returns False immediately if music is disabled via music_enabled.

        Example:
            # Play looping background music at default volume
            audio_manager.play_music("background.ogg")

            # Play one-time victory music at high volume
            audio_manager.play_music("victory.ogg", loop=False, volume=0.9)

        Note:
            This method automatically stops any currently playing music before
            starting the new track. There is no crossfade or overlap.
        """
        if not self.music_enabled:
            return False

        try:
            # Stop current music if playing
            self.stop_music()

            # If file is currently being loaded in background, wait briefly for it
            if filename in self._music_loading:
                logger.debug("Waiting for background preload of: %s", filename)
                max_wait = 50  # Wait up to 50 iterations (~ 0.5 seconds)
                wait_count = 0
                while filename in self._music_loading and wait_count < max_wait:
                    time.sleep(0.01)  # 10ms sleep
                    wait_count += 1

                if filename in self.music_cache:
                    logger.info("Background preload completed for: %s", filename)

            # Check cache first for faster loading
            if filename in self.music_cache:
                self.current_music = self.music_cache[filename]
                logger.debug("Using cached music: %s", filename)
            else:
                # Load and cache new music
                music_file = asset_path(f"audio/music/{filename}")

                # Use streaming for non-looping music to avoid loading delays
                # Note: streaming=True disables looping, so only use it when loop=False
                use_streaming = not loop
                self.current_music = arcade.load_sound(music_file, streaming=use_streaming)

                # Cache music for future use (only cache looping music, not streaming)
                if not use_streaming:
                    self.music_cache[filename] = self.current_music
                    logger.info("Loaded and cached music: %s", filename)
                else:
                    logger.info("Loaded streaming music (not cached): %s", filename)

            actual_volume = volume if volume is not None else self.music_volume

            self.music_player = self.current_music.play(
                volume=actual_volume,
                loop=loop,
            )

        except Exception:
            logger.exception("Failed to play music")
            return False
        else:
            return True

    def stop_music(self) -> None:
        """Stop currently playing music.

        Immediately stops music playback and clears the music player reference.
        The music file remains cached and can be replayed without reloading.

        This is called automatically by play_music() before starting a new track.
        Also called when music is toggled off via toggle_music().

        Example:
            audio_manager.stop_music()  # Silence the music
        """
        if self.music_player:
            try:
                self.music_player.pause()
                self.music_player = None
                logger.debug("Music stopped")
            except Exception:
                logger.exception("Error stopping music")

    def pause_music(self) -> None:
        """Pause currently playing music.

        Pauses music playback at the current position. Music can be resumed
        from the same position using resume_music(). The music player and
        cached file remain in memory.

        Use this for temporary interruptions like pause menus where you want
        to continue from the same point. Use stop_music() if you want to
        restart from the beginning next time.

        Example:
            # Pause when entering menu
            audio_manager.pause_music()
        """
        if self.music_player:
            try:
                self.music_player.pause()
                logger.debug("Music paused")
            except Exception:
                logger.exception("Error pausing music")

    def resume_music(self) -> None:
        """Resume paused music.

        Continues playing music from where it was paused. Does nothing if
        music was not previously paused or if music has been stopped.

        Example:
            # Resume when exiting menu
            audio_manager.resume_music()
        """
        if self.music_player:
            try:
                self.music_player.play()
                logger.debug("Music resumed")
            except Exception:
                logger.exception("Error resuming music")

    def set_music_volume(self, volume: float) -> None:
        """Set music volume.

        Updates the music volume for all music playback. If music is currently
        playing, the volume change takes effect immediately. The volume is
        automatically clamped to the valid range of 0.0 to 1.0.

        Args:
            volume: Volume level (0.0 = silent, 1.0 = full volume).
                Values outside this range are clamped automatically.

        Example:
            # Set to half volume
            audio_manager.set_music_volume(0.5)

            # Mute music (alternative to toggle_music())
            audio_manager.set_music_volume(0.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))

        if self.music_player:
            try:
                self.music_player.volume = self.music_volume
            except Exception:
                logger.exception("Error setting music volume")

    def play_sfx(self, sound_name: str, *, volume: float | None = None) -> bool:
        """Play a sound effect.

        Plays a one-shot sound effect. Sound effects are automatically cached
        after first use for instant replay. Multiple sound effects can play
        simultaneously (no limit on concurrent sounds).

        Common use cases:
        - NPC voice clips when interacting (e.g., "martin.mp3")
        - UI feedback sounds (button clicks, menu navigation)
        - Game event sounds (item pickup, door open)
        - Ambient sounds and effects

        Args:
            sound_name: Sound effect file name (in assets/audio/sfx/). Examples:
                - "martin.mp3" - Martin's voice greeting
                - "avi.mp3" - Avi's voice
                - "feliz_cumple.mp3" - Birthday celebration sound
            volume: Optional volume override (0.0 to 1.0). If not provided,
                uses the current sfx_volume setting (default 0.7).

        Returns:
            True if sound played successfully, False otherwise.
            Returns False immediately if SFX is disabled via sfx_enabled.

        Example:
            # Play NPC voice at default volume
            audio_manager.play_sfx("martin.mp3")

            # Play UI sound at lower volume
            audio_manager.play_sfx("click.wav", volume=0.3)

        Note:
            Unlike music, multiple sound effects can overlap and play
            simultaneously. Each call creates a new playback instance.
        """
        if not self.sfx_enabled:
            return False

        try:
            # Load from cache or file
            if sound_name not in self.sfx_cache:
                sfx_file = asset_path(f"audio/sfx/{sound_name}")
                self.sfx_cache[sound_name] = arcade.load_sound(sfx_file)

            # Play the sound
            sound = self.sfx_cache[sound_name]
            actual_volume = volume if volume is not None else self.sfx_volume
            sound.play(volume=actual_volume)

            logger.debug("Playing SFX: %s", sound_name)

        except Exception:
            logger.exception("Failed to play SFX")
            return False
        else:
            return True

    def set_sfx_volume(self, volume: float) -> None:
        """Set sound effects volume.

        Updates the volume for all future sound effect playback. Does not
        affect currently playing sounds. The volume is automatically clamped
        to the valid range of 0.0 to 1.0.

        Args:
            volume: Volume level (0.0 = silent, 1.0 = full volume).
                Values outside this range are clamped automatically.

        Example:
            # Set SFX to 80% volume
            audio_manager.set_sfx_volume(0.8)
        """
        self.sfx_volume = max(0.0, min(1.0, volume))

    def toggle_music(self) -> bool:
        """Toggle music on/off.

        Toggles the music enabled state. When music is disabled, any currently
        playing music is stopped immediately. When re-enabled, music does not
        automatically resume - you must call play_music() again.

        This is useful for implementing user settings for music enable/disable.

        Returns:
            New music enabled state (True = enabled, False = disabled).

        Example:
            # Toggle music in response to user pressing 'M'
            new_state = audio_manager.toggle_music()
            print(f"Music is now {'on' if new_state else 'off'}")
        """
        self.music_enabled = not self.music_enabled

        if not self.music_enabled:
            self.stop_music()

        return self.music_enabled

    def toggle_sfx(self) -> bool:
        """Toggle sound effects on/off.

        Toggles the SFX enabled state. When SFX is disabled, all future
        play_sfx() calls will be ignored and return False immediately.
        Currently playing sound effects are not affected.

        This is useful for implementing user settings for SFX enable/disable.

        Returns:
            New SFX enabled state (True = enabled, False = disabled).

        Example:
            # Toggle SFX in response to user pressing 'S'
            new_state = audio_manager.toggle_sfx()
            print(f"Sound effects are now {'on' if new_state else 'off'}")
        """
        self.sfx_enabled = not self.sfx_enabled
        return self.sfx_enabled

    def clear_sfx_cache(self) -> None:
        """Clear the sound effects cache to free memory.

        Removes all cached sound effect files from memory. Useful for freeing
        memory when transitioning between major game sections or when memory
        is constrained.

        Sound effects will be reloaded from disk on next use. This may cause
        a brief delay the first time each sound is played again.

        Example:
            # Clear SFX cache after completing a level
            audio_manager.clear_sfx_cache()
        """
        self.sfx_cache.clear()
        logger.debug("SFX cache cleared")

    def clear_music_cache(self) -> None:
        """Clear the music cache to free memory.

        Removes all cached music files from memory. Useful for freeing memory
        when transitioning between major game sections or when memory is
        constrained.

        Music will be reloaded from disk on next use. This may cause a brief
        delay when starting the music again.

        Example:
            # Clear music cache before loading a new scene
            audio_manager.clear_music_cache()
        """
        self.music_cache.clear()
        logger.debug("Music cache cleared")

    def clear_all_caches(self) -> None:
        """Clear both music and SFX caches to free memory.

        Convenience method that clears both the music and sound effect caches
        simultaneously. Useful for complete memory cleanup when transitioning
        between major game sections.

        Example:
            # Full cache clear when returning to main menu
            audio_manager.clear_all_caches()
        """
        self.clear_music_cache()
        self.clear_sfx_cache()
        logger.info("All audio caches cleared")

    def mark_music_loading(self, filename: str) -> None:
        """Mark a music file as currently being loaded.

        Used for background preloading coordination. When a file is marked as
        loading, play_music() will wait briefly for the preload to complete
        before loading it again.

        This is part of the background preloading system to optimize scene
        transitions and prevent redundant loads.

        Args:
            filename: Name of the music file being loaded in background.

        Example:
            # In background preload task
            audio_manager.mark_music_loading("beach.ogg")
            # ... load the file ...
            audio_manager.unmark_music_loading("beach.ogg")
        """
        self._music_loading.add(filename)

    def unmark_music_loading(self, filename: str) -> None:
        """Unmark a music file as being loaded.

        Signals that a background music preload has completed. Should be called
        after mark_music_loading() once the file is loaded into the cache.

        Args:
            filename: Name of the music file that finished loading.

        Example:
            # After background load completes
            audio_manager.music_cache[filename] = loaded_sound
            audio_manager.unmark_music_loading(filename)
        """
        self._music_loading.discard(filename)

    def to_dict(self) -> dict[str, bool | float]:
        """Convert audio settings to dictionary for save data serialization.

        Exports the user-configurable audio settings as a dictionary suitable for
        JSON serialization. This includes volume levels and enable/disable states
        for both music and sound effects.

        Returns:
            Dictionary with audio settings. Example:
            {
                "music_volume": 0.5,
                "sfx_volume": 0.7,
                "music_enabled": True,
                "sfx_enabled": True
            }

        Example:
            # Save audio settings to JSON
            save_data = {
                "audio": audio_manager.to_dict(),
                # ... other save data
            }
        """
        return {
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "music_enabled": self.music_enabled,
            "sfx_enabled": self.sfx_enabled,
        }

    def from_dict(self, data: dict[str, bool | float]) -> None:
        """Load audio settings from saved dictionary data.

        Restores the user's audio preferences from a previously saved dictionary.
        This updates volume levels and enable/disable states without affecting
        currently playing audio or cached files.

        If any setting is missing from the data, it retains its current value
        (defaults from __init__ if newly created).

        Args:
            data: Dictionary with audio settings, typically loaded from a JSON
                 save file. Keys: "music_volume", "sfx_volume", "music_enabled",
                 "sfx_enabled".

        Example:
            # Load audio settings from JSON
            with open("save.json", "r") as f:
                save_data = json.load(f)

            audio_manager.from_dict(save_data["audio"])
            # User's audio preferences are now restored
        """
        if "music_volume" in data:
            self.set_music_volume(float(data["music_volume"]))

        if "sfx_volume" in data:
            self.set_sfx_volume(float(data["sfx_volume"]))

        if "music_enabled" in data:
            self.music_enabled = bool(data["music_enabled"])

        if "sfx_enabled" in data:
            self.sfx_enabled = bool(data["sfx_enabled"])

        logger.debug("Restored audio settings from save data")
