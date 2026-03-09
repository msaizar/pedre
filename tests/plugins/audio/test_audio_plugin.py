"""Unit tests for AudioPlugin."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from pedre.plugins.audio import AudioPlugin

if TYPE_CHECKING:
    from unittest.mock import Mock


@pytest.fixture
def plugin() -> AudioPlugin:
    """Fixture for AudioPlugin."""
    return AudioPlugin()


class TestAudioPlugin:
    """Unit test class for AudioPlugin."""

    # Test cleanup and reset methods
    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_cleanup(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test cleanup stops music and clears caches."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")
        plugin.play_sfx("test.mp3")

        # Verify state before cleanup
        assert plugin.current_music is not None
        assert plugin.music_player is not None
        assert len(plugin.music_cache) > 0

        # Cleanup
        plugin.cleanup()

        # Verify music stopped and caches cleared
        mock_player.pause.assert_called_once()
        assert plugin.music_player is None
        assert len(plugin.music_cache) == 0
        assert len(plugin.sfx_cache) == 0

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_reset(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test reset stops music but keeps cache."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")

        # Add to cache
        cache_size_before = len(plugin.music_cache)

        # Reset
        plugin.reset()

        # Verify music stopped but cache kept
        mock_player.pause.assert_called_once()
        assert plugin.music_player is None
        assert len(plugin.music_cache) == cache_size_before

    # Test cache getter and setter
    def test_get_music_cache(self, plugin: AudioPlugin) -> None:
        """Test getting music cache."""
        mock_sound = MagicMock()
        plugin.music_cache["test.ogg"] = mock_sound

        cache = plugin.get_music_cache()

        assert "test.ogg" in cache
        assert cache["test.ogg"] == mock_sound

    def test_set_music_cache(self, plugin: AudioPlugin) -> None:
        """Test setting music cache."""
        mock_sound = MagicMock()

        plugin.set_music_cache("test.ogg", mock_sound)

        assert "test.ogg" in plugin.music_cache
        assert plugin.music_cache["test.ogg"] == mock_sound

    # Test play_music with caching
    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_play_music_uses_cache(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test that play_music uses cached music."""
        # Set up mock
        mock_sound = MagicMock()
        mock_sound.play.return_value = MagicMock()
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        # First play - should load
        plugin.play_music("test.ogg")
        assert mock_load_sound.call_count == 1

        # Second play - should use cache
        plugin.play_music("test.ogg")
        assert mock_load_sound.call_count == 1  # Still 1, not 2

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_play_music_streaming_not_cached(
        self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin
    ) -> None:
        """Test that streaming (non-looping) music is not cached."""
        # Set up mock
        mock_sound = MagicMock()
        mock_sound.play.return_value = MagicMock()
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        # Play non-looping music
        plugin.play_music("test.ogg", loop=False)

        # Verify streaming was used
        mock_load_sound.assert_called_once()
        call_kwargs = mock_load_sound.call_args[1]
        assert call_kwargs.get("streaming") is True

        # Verify not cached
        assert "test.ogg" not in plugin.music_cache

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_play_music_exception_handling(
        self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin
    ) -> None:
        """Test that play_music handles exceptions gracefully."""
        # Make load_sound raise an exception
        mock_load_sound.side_effect = Exception("Test error")
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        # Should return False and not raise
        result = plugin.play_music("test.ogg")

        assert result is False
        assert plugin.current_music is None

    @patch("pedre.plugins.audio.plugin.time.sleep")
    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_play_music_waits_for_background_preload(
        self, mock_asset_path: Mock, mock_load_sound: Mock, mock_sleep: Mock, plugin: AudioPlugin
    ) -> None:
        """Test that play_music waits for background preloading to complete."""
        # Set up mock
        mock_sound = MagicMock()
        mock_sound.play.return_value = MagicMock()
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        # Simulate background loading in progress
        plugin._music_loading.add("test.ogg")

        # Simulate preload completing after a few iterations
        call_count = 0

        def complete_preload(*_args: object, **_kwargs: object) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                # After 3 sleep calls, complete the preload
                plugin._music_loading.discard("test.ogg")
                plugin.music_cache["test.ogg"] = mock_sound

        mock_sleep.side_effect = complete_preload

        # Play music - should wait for background preload
        result = plugin.play_music("test.ogg")

        assert result is True
        assert mock_sleep.call_count >= 3  # Should have waited
        assert "test.ogg" not in plugin._music_loading  # Should be cleared

    @patch("pedre.plugins.audio.plugin.time.sleep")
    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_play_music_timeout_waiting_for_preload(
        self, mock_asset_path: Mock, mock_load_sound: Mock, mock_sleep: Mock, plugin: AudioPlugin
    ) -> None:
        """Test that play_music times out if background preload takes too long."""
        # Set up mock
        mock_sound = MagicMock()
        mock_sound.play.return_value = MagicMock()
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        # Simulate background loading that never completes
        plugin._music_loading.add("test.ogg")

        # Play music - should timeout and load normally
        result = plugin.play_music("test.ogg")

        assert result is True
        # Should have waited max 50 iterations
        assert mock_sleep.call_count >= 50
        # Should have loaded the sound anyway
        mock_load_sound.assert_called_once()

    # Test stop_music
    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_stop_music(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test stopping music."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")
        assert plugin.music_player is not None

        # Stop music
        plugin.stop_music()

        mock_player.pause.assert_called_once()
        assert plugin.music_player is None

    def test_stop_music_with_no_player(self, plugin: AudioPlugin) -> None:
        """Test stopping music when no player exists."""
        # Should not raise
        plugin.stop_music()
        assert plugin.music_player is None

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_stop_music_exception_handling(
        self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin
    ) -> None:
        """Test that stop_music handles exceptions gracefully."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()
        mock_player.pause.side_effect = Exception("Test error")
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")

        # Should not raise
        plugin.stop_music()

    # Test pause and resume music
    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_pause_music(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test pausing music."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")

        # Pause music
        plugin.pause_music()

        mock_player.pause.assert_called()

    def test_pause_music_with_no_player(self, plugin: AudioPlugin) -> None:
        """Test pausing music when no player exists."""
        # Should not raise
        plugin.pause_music()

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_pause_music_exception_handling(
        self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin
    ) -> None:
        """Test that pause_music handles exceptions gracefully."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()
        mock_player.pause.side_effect = Exception("Test error")
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")

        # Should not raise
        plugin.pause_music()

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_resume_music(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test resuming music."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")
        plugin.pause_music()

        # Resume music
        plugin.resume_music()

        mock_player.play.assert_called_once()

    def test_resume_music_with_no_player(self, plugin: AudioPlugin) -> None:
        """Test resuming music when no player exists."""
        # Should not raise
        plugin.resume_music()

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_resume_music_exception_handling(
        self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin
    ) -> None:
        """Test that resume_music handles exceptions gracefully."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()
        mock_player.play.side_effect = Exception("Test error")
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")

        # Should not raise
        plugin.resume_music()

    # Test volume controls
    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_set_music_volume(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test setting music volume."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")

        # Set volume
        plugin.set_music_volume(0.8)

        assert plugin.music_volume == 0.8
        assert mock_player.volume == 0.8

    def test_set_music_volume_clamping(self, plugin: AudioPlugin) -> None:
        """Test that music volume is clamped to valid range."""
        # Test upper bound
        plugin.set_music_volume(1.5)
        assert plugin.music_volume == 1.0

        # Test lower bound
        plugin.set_music_volume(-0.5)
        assert plugin.music_volume == 0.0

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_set_music_volume_exception_handling(
        self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin
    ) -> None:
        """Test that set_music_volume handles exceptions gracefully."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()

        # Create a property that raises when setting volume
        test_error = RuntimeError("Test error")

        def _raise_on_set(*_args: object, **_kwargs: object) -> None:
            raise test_error

        type(mock_player).volume = property(lambda *_args: 0.5, _raise_on_set)
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")

        # Should not raise but still set internal volume
        plugin.set_music_volume(0.8)
        assert plugin.music_volume == 0.8

    # Test SFX functionality
    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_play_sfx(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test playing sound effects."""
        # Set up mock
        mock_sound = MagicMock()
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/sfx/test.mp3"

        # Play SFX
        result = plugin.play_sfx("test.mp3")

        assert result is True
        mock_asset_path.assert_called_once_with("audio/sfx/test.mp3")
        mock_load_sound.assert_called_once()
        mock_sound.play.assert_called_once()

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_play_sfx_with_custom_volume(
        self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin
    ) -> None:
        """Test playing SFX with custom volume."""
        # Set up mock
        mock_sound = MagicMock()
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/sfx/test.mp3"

        # Play SFX with custom volume
        result = plugin.play_sfx("test.mp3", volume=0.3)

        assert result is True
        call_kwargs = mock_sound.play.call_args[1]
        assert call_kwargs.get("volume") == 0.3

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_play_sfx_caching(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test that SFX are cached after first use."""
        # Set up mock
        mock_sound = MagicMock()
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/sfx/test.mp3"

        # First play - should load
        plugin.play_sfx("test.mp3")
        assert mock_load_sound.call_count == 1

        # Second play - should use cache
        plugin.play_sfx("test.mp3")
        assert mock_load_sound.call_count == 1  # Still 1, not 2

    def test_play_sfx_when_disabled(self, plugin: AudioPlugin) -> None:
        """Test that SFX doesn't play when disabled."""
        plugin.sfx_enabled = False

        result = plugin.play_sfx("test.mp3")

        assert result is False

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_play_sfx_file_not_found(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test that play_sfx handles missing files gracefully."""
        # Make load_sound raise FileNotFoundError
        mock_load_sound.side_effect = FileNotFoundError("File not found")
        mock_asset_path.return_value = "/path/to/sfx/missing.mp3"

        # Should return False and not raise
        result = plugin.play_sfx("missing.mp3")

        assert result is False

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_play_sfx_exception_handling(
        self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin
    ) -> None:
        """Test that play_sfx handles exceptions gracefully."""
        # Make load_sound raise a general exception
        mock_load_sound.side_effect = Exception("Test error")
        mock_asset_path.return_value = "/path/to/sfx/test.mp3"

        # Should return False and not raise
        result = plugin.play_sfx("test.mp3")

        assert result is False

    def test_set_sfx_volume(self, plugin: AudioPlugin) -> None:
        """Test setting SFX volume."""
        plugin.set_sfx_volume(0.8)

        assert plugin.sfx_volume == 0.8

    def test_set_sfx_volume_clamping(self, plugin: AudioPlugin) -> None:
        """Test that SFX volume is clamped to valid range."""
        # Test upper bound
        plugin.set_sfx_volume(1.5)
        assert plugin.sfx_volume == 1.0

        # Test lower bound
        plugin.set_sfx_volume(-0.5)
        assert plugin.sfx_volume == 0.0

    # Test toggle functions
    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_toggle_music(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test toggling music on and off."""
        # Set up music playing
        mock_sound = MagicMock()
        mock_player = MagicMock()
        mock_sound.play.return_value = mock_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        plugin.play_music("test.ogg")
        assert plugin.music_enabled is True

        # Toggle off
        result = plugin.toggle_music()

        assert result is False
        assert plugin.music_enabled is False
        mock_player.pause.assert_called_once()

        # Toggle back on
        result = plugin.toggle_music()

        assert result is True
        assert plugin.music_enabled is True

    def test_toggle_sfx(self, plugin: AudioPlugin) -> None:
        """Test toggling SFX on and off."""
        assert plugin.sfx_enabled is True

        # Toggle off
        result = plugin.toggle_sfx()

        assert result is False
        assert plugin.sfx_enabled is False

        # Toggle back on
        result = plugin.toggle_sfx()

        assert result is True
        assert plugin.sfx_enabled is True

    # Test cache clearing
    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_clear_sfx_cache(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test clearing SFX cache."""
        # Set up mock
        mock_sound = MagicMock()
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/sfx/test.mp3"

        # Add to cache
        plugin.play_sfx("test.mp3")
        assert len(plugin.sfx_cache) > 0

        # Clear cache
        plugin.clear_sfx_cache()

        assert len(plugin.sfx_cache) == 0

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_clear_music_cache(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test clearing music cache."""
        # Set up mock
        mock_sound = MagicMock()
        mock_sound.play.return_value = MagicMock()
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/test.ogg"

        # Add to cache
        plugin.play_music("test.ogg")
        assert len(plugin.music_cache) > 0

        # Clear cache
        plugin.clear_music_cache()

        assert len(plugin.music_cache) == 0

    @patch("pedre.plugins.audio.plugin.arcade.load_sound")
    @patch("pedre.plugins.audio.plugin.asset_path")
    def test_clear_all_caches(self, mock_asset_path: Mock, mock_load_sound: Mock, plugin: AudioPlugin) -> None:
        """Test clearing all caches."""
        # Set up mocks
        mock_sound = MagicMock()
        mock_sound.play.return_value = MagicMock()
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/audio/test"

        # Add to both caches
        plugin.play_music("test.ogg")
        plugin.play_sfx("test.mp3")
        assert len(plugin.music_cache) > 0
        assert len(plugin.sfx_cache) > 0

        # Clear all caches
        plugin.clear_all_caches()

        assert len(plugin.music_cache) == 0
        assert len(plugin.sfx_cache) == 0

    # Test serialization methods
    def test_to_dict(self, plugin: AudioPlugin) -> None:
        """Test converting audio settings to dictionary."""
        plugin.music_volume = 0.6
        plugin.sfx_volume = 0.8
        plugin.music_enabled = True
        plugin.sfx_enabled = False

        data = plugin.to_dict()

        assert data == {
            "music_volume": 0.6,
            "sfx_volume": 0.8,
            "music_enabled": True,
            "sfx_enabled": False,
        }

    def test_from_dict(self, plugin: AudioPlugin) -> None:
        """Test loading audio settings from dictionary."""
        data = {
            "music_volume": 0.3,
            "sfx_volume": 0.9,
            "music_enabled": False,
            "sfx_enabled": True,
        }

        plugin.from_dict(data)

        assert plugin.music_volume == 0.3
        assert plugin.sfx_volume == 0.9
        assert plugin.music_enabled is False
        assert plugin.sfx_enabled is True

    def test_from_dict_partial(self, plugin: AudioPlugin) -> None:
        """Test loading audio settings with missing keys."""
        # Set initial values
        plugin.music_volume = 0.5
        plugin.sfx_volume = 0.7
        plugin.music_enabled = True
        plugin.sfx_enabled = True

        # Load partial data
        data = {"music_volume": 0.3}

        plugin.from_dict(data)

        # Only music_volume should change
        assert plugin.music_volume == 0.3
        assert plugin.sfx_volume == 0.7  # Unchanged
        assert plugin.music_enabled is True  # Unchanged
        assert plugin.sfx_enabled is True  # Unchanged

    def test_from_dict_without_music_volume(self, plugin: AudioPlugin) -> None:
        """Test loading audio settings without music_volume key."""
        # Set initial values
        plugin.music_volume = 0.5
        plugin.sfx_volume = 0.7
        plugin.music_enabled = True
        plugin.sfx_enabled = True

        # Load data without music_volume to test branch coverage
        data = {"sfx_volume": 0.9}

        plugin.from_dict(data)

        # Only sfx_volume should change
        assert plugin.music_volume == 0.5  # Unchanged
        assert plugin.sfx_volume == 0.9
        assert plugin.music_enabled is True  # Unchanged
        assert plugin.sfx_enabled is True  # Unchanged

    def test_play_music_when_disabled(self, plugin: AudioPlugin) -> None:
        """play_music returns False immediately when music_enabled is False."""
        plugin.music_enabled = False
        result = plugin.play_music("test.ogg")
        assert result is False

    # Test on_scene_loaded
    def test_on_scene_loaded_plays_music_from_registry(self, plugin: AudioPlugin) -> None:
        """on_scene_loaded plays music defined in the map registry."""
        maps_mock = MagicMock()
        maps_mock.has.return_value = True
        maps_mock.get.return_value = {"music": "beach.ogg"}

        plugin.context = MagicMock()
        plugin.context.content_registry.get_sub_registry.return_value = maps_mock

        with patch.object(plugin, "play_music", return_value=True) as mock_play:
            plugin.on_scene_loaded("beach")

        mock_play.assert_called_once_with("beach.ogg", loop=True)

    def test_on_scene_loaded_no_music_in_registry(self, plugin: AudioPlugin) -> None:
        """on_scene_loaded does nothing when map has no music field."""
        maps_mock = MagicMock()
        maps_mock.has.return_value = True
        maps_mock.get.return_value = {}  # no music key

        plugin.context = MagicMock()
        plugin.context.content_registry.get_sub_registry.return_value = maps_mock

        with patch.object(plugin, "play_music") as mock_play:
            plugin.on_scene_loaded("map")

        mock_play.assert_not_called()

    def test_on_scene_loaded_no_registry_entry(self, plugin: AudioPlugin) -> None:
        """on_scene_loaded does nothing when map has no registry entry."""
        maps_mock = MagicMock()
        maps_mock.has.return_value = False

        plugin.context = MagicMock()
        plugin.context.content_registry.get_sub_registry.return_value = maps_mock

        with patch.object(plugin, "play_music") as mock_play:
            plugin.on_scene_loaded("unknown")

        mock_play.assert_not_called()

    def test_on_scene_loaded_no_maps_registry(self, plugin: AudioPlugin) -> None:
        """on_scene_loaded does nothing when maps sub-registry is absent."""
        plugin.context = MagicMock()
        plugin.context.content_registry.get_sub_registry.return_value = None

        with patch.object(plugin, "play_music") as mock_play:
            plugin.on_scene_loaded("map")

        mock_play.assert_not_called()

    def test_on_scene_loaded_logs_warning_on_failed_play(self, plugin: AudioPlugin) -> None:
        """on_scene_loaded logs a warning when play_music returns False."""
        maps_mock = MagicMock()
        maps_mock.has.return_value = True
        maps_mock.get.return_value = {"music": "missing.ogg"}

        plugin.context = MagicMock()
        plugin.context.content_registry.get_sub_registry.return_value = maps_mock

        with patch.object(plugin, "play_music", return_value=False):
            plugin.on_scene_loaded("map")  # Should not raise

    def test_get_save_state(self, plugin: AudioPlugin) -> None:
        """Test get_save_state delegates to to_dict."""
        plugin.music_volume = 0.6
        plugin.sfx_volume = 0.8

        state = plugin.get_save_state()

        # Should be same as to_dict
        assert state == plugin.to_dict()

    def test_restore_save_state(self, plugin: AudioPlugin) -> None:
        """Test restore_save_state delegates to from_dict."""
        state = {
            "music_volume": 0.3,
            "sfx_volume": 0.9,
            "music_enabled": False,
            "sfx_enabled": True,
        }

        plugin.restore_save_state(state)

        # Should be same as from_dict
        assert plugin.music_volume == 0.3
        assert plugin.sfx_volume == 0.9
        assert plugin.music_enabled is False
        assert plugin.sfx_enabled is True
