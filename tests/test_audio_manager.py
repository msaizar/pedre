"""Unit tests for AudioManager."""

import unittest
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from pedre.systems.audio.manager import AudioManager

if TYPE_CHECKING:
    from unittest.mock import Mock


class TestAudioManager(unittest.TestCase):
    """Unit test class for AudioManager."""

    def setUp(self) -> None:
        """Set up AudioManager for each test."""
        self.manager = AudioManager()

    @patch("pedre.systems.audio.manager.arcade.load_sound")
    @patch("pedre.systems.audio.manager.asset_path")
    def test_load_from_tiled_with_music_property(self, mock_asset_path: Mock, mock_load_sound: Mock) -> None:
        """Test loading music from Tiled map property."""
        # Mock the tile map with a music property
        mock_tile_map = MagicMock()
        mock_tile_map.properties = {"music": "village_theme.ogg"}

        # Mock arcade sound loading
        mock_sound = MagicMock()
        mock_sound.play.return_value = MagicMock()  # music_player
        mock_load_sound.return_value = mock_sound
        mock_asset_path.return_value = "/path/to/music/village_theme.ogg"

        mock_scene = MagicMock()
        mock_context = MagicMock()
        mock_settings = MagicMock()

        # Call load_from_tiled
        self.manager.load_from_tiled(mock_tile_map, mock_scene, mock_context, mock_settings)

        # Verify music was loaded and played
        mock_asset_path.assert_called_once_with("audio/music/village_theme.ogg")
        mock_load_sound.assert_called_once()
        mock_sound.play.assert_called_once()
        assert self.manager.current_music == mock_sound

    def test_load_from_tiled_without_music_property(self) -> None:
        """Test that missing music property is handled gracefully."""
        mock_tile_map = MagicMock()
        mock_tile_map.properties = {}  # No music property

        mock_scene = MagicMock()
        mock_context = MagicMock()
        mock_settings = MagicMock()

        # Should not raise exception
        self.manager.load_from_tiled(mock_tile_map, mock_scene, mock_context, mock_settings)

        # No music should be playing
        assert self.manager.current_music is None

    def test_load_from_tiled_without_properties_attribute(self) -> None:
        """Test handling of tile_map without properties attribute."""
        mock_tile_map = MagicMock(spec=[])  # No properties attribute
        mock_scene = MagicMock()
        mock_context = MagicMock()
        mock_settings = MagicMock()

        # Should not raise exception
        self.manager.load_from_tiled(mock_tile_map, mock_scene, mock_context, mock_settings)

        assert self.manager.current_music is None

    def test_load_from_tiled_with_invalid_music_value(self) -> None:
        """Test handling of invalid music property values."""
        mock_tile_map = MagicMock()
        mock_tile_map.properties = {"music": ""}  # Empty string

        mock_scene = MagicMock()
        mock_context = MagicMock()
        mock_settings = MagicMock()

        self.manager.load_from_tiled(mock_tile_map, mock_scene, mock_context, mock_settings)

        assert self.manager.current_music is None

    def test_load_from_tiled_respects_music_disabled(self) -> None:
        """Test that load_from_tiled respects music_enabled flag."""
        self.manager.music_enabled = False

        mock_tile_map = MagicMock()
        mock_tile_map.properties = {"music": "village_theme.ogg"}

        mock_scene = MagicMock()
        mock_context = MagicMock()
        mock_settings = MagicMock()

        # Should not play music when disabled
        self.manager.load_from_tiled(mock_tile_map, mock_scene, mock_context, mock_settings)

        assert self.manager.current_music is None


if __name__ == "__main__":
    unittest.main()
