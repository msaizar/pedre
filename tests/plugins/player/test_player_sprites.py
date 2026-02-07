"""Unit tests for AnimatedPlayer in src/pedre/plugins/player/sprites.py."""

import unittest
from unittest.mock import MagicMock, patch

from pedre.plugins.player.sprites import AnimatedPlayer


class TestAnimatedPlayer(unittest.TestCase):
    """Test Suite for AnimatedPlayer."""

    @patch("pedre.plugins.player.sprites.AnimatedSprite.__init__")
    def test_animated_player_initialization(self, mock_super_init: MagicMock) -> None:
        """Test AnimatedPlayer initialization calls parent class properly."""
        # Mock the parent __init__ to return None (as __init__ should)
        mock_super_init.return_value = None

        # Create player with various animation parameters
        sprite_sheet_path = "test/path/player.png"
        AnimatedPlayer(
            sprite_sheet_path,
            tile_size=32,
            scale=2.0,
            center_x=100.0,
            center_y=200.0,
            idle_up_frames=4,
            idle_up_row=0,
            idle_down_frames=4,
            idle_down_row=1,
            idle_left_frames=4,
            idle_left_row=2,
            idle_right_frames=4,
            idle_right_row=3,
            walk_up_frames=6,
            walk_up_row=4,
            walk_down_frames=6,
            walk_down_row=5,
            walk_left_frames=6,
            walk_left_row=6,
            walk_right_frames=6,
            walk_right_row=7,
        )

        # Verify super().__init__ was called with correct parameters
        mock_super_init.assert_called_once_with(
            sprite_sheet_path,
            tile_size=32,
            scale=2.0,
            center_x=100.0,
            center_y=200.0,
            idle_up_frames=4,
            idle_up_row=0,
            idle_down_frames=4,
            idle_down_row=1,
            idle_left_frames=4,
            idle_left_row=2,
            idle_right_frames=4,
            idle_right_row=3,
            walk_up_frames=6,
            walk_up_row=4,
            walk_down_frames=6,
            walk_down_row=5,
            walk_left_frames=6,
            walk_left_row=6,
            walk_right_frames=6,
            walk_right_row=7,
        )

    @patch("pedre.plugins.player.sprites.AnimatedSprite.__init__")
    def test_animated_player_minimal_initialization(self, mock_super_init: MagicMock) -> None:
        """Test AnimatedPlayer with minimal parameters."""
        mock_super_init.return_value = None

        sprite_sheet_path = "test/path/player.png"
        AnimatedPlayer(sprite_sheet_path)

        # Verify super().__init__ was called with defaults
        mock_super_init.assert_called_once()
        call_args = mock_super_init.call_args

        # Check positional args
        assert call_args[0][0] == sprite_sheet_path

        # Check that all animation parameters were passed as None
        assert call_args[1]["idle_up_frames"] is None
        assert call_args[1]["idle_down_frames"] is None
        assert call_args[1]["walk_up_frames"] is None
        assert call_args[1]["walk_down_frames"] is None


if __name__ == "__main__":
    unittest.main()
