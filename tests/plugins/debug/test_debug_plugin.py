"""Unit tests for DebugPlugin in src/pedre/plugins/debug/plugin.py."""

import unittest
from unittest.mock import MagicMock, patch

import arcade

from pedre.plugins.debug.plugin import DebugPlugin


class TestDebugPlugin(unittest.TestCase):
    """Test Suite for DebugPlugin."""

    def setUp(self) -> None:
        """Set up the DebugPlugin and mock context."""
        self.plugin = DebugPlugin()
        self.mock_context = MagicMock()
        self.plugin.setup(self.mock_context)

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        assert self.plugin.name == "debug"
        assert "npc" in self.plugin.dependencies
        assert self.plugin.debug_mode is False
        assert self.plugin.debug_text_objects == []
        assert self.plugin.context == self.mock_context

    def test_toggle_debug_mode(self) -> None:
        """Test toggling debug mode with key press."""
        # Initial state
        assert self.plugin.debug_mode is False

        # Toggle ON (Shift + D)
        handled = self.plugin.on_key_press(arcade.key.D, arcade.key.MOD_SHIFT)
        assert handled is True
        assert self.plugin.debug_mode is True

        # Toggle OFF
        handled = self.plugin.on_key_press(arcade.key.D, arcade.key.MOD_SHIFT)
        assert handled is True
        assert self.plugin.debug_mode is False
        assert self.plugin.debug_text_objects == []  # Should be cleared

    def test_ignore_other_keys(self) -> None:
        """Test that other keys are ignored."""
        # Just D without shift
        handled = self.plugin.on_key_press(arcade.key.D, 0)
        assert handled is False
        assert self.plugin.debug_mode is False

        # Shift + Other key
        handled = self.plugin.on_key_press(arcade.key.A, arcade.key.MOD_SHIFT)
        assert handled is False
        assert self.plugin.debug_mode is False

    @patch("arcade.Text")
    def test_draw_ui_debug_enabled(self, mock_text_cls: MagicMock) -> None:
        """Test UI drawing interactions when debug is enabled."""
        self.plugin.debug_mode = True

        # Setup mock player
        mock_player = MagicMock()
        mock_player.center_x = 120
        mock_player.center_y = 128
        self.mock_context.player_plugin.get_player_sprite.return_value = mock_player

        # Setup mock NPCs
        mock_npc_plugin = self.mock_context.npc_plugin
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.visible = True
        mock_npc_state.sprite.center_x = 240.0
        mock_npc_state.sprite.center_y = 256.0
        mock_npc_state.dialog_level = 1
        mock_npc_plugin.get_npcs.return_value = {"guard": mock_npc_state}

        # Call draw_ui
        self.plugin.on_draw_ui()

        assert len(self.plugin.debug_text_objects) > 0

        assert mock_text_cls.return_value.draw.called

    def test_draw_ui_debug_disabled(self) -> None:
        """Test UI drawing is skipped when debug is disabled."""
        self.plugin.debug_mode = False
        self.plugin.on_draw_ui()

        # Should NOT access player or NPCs
        self.mock_context.player_plugin.get_player_sprite.assert_not_called()
        self.mock_context.npc_plugin.get_npcs.assert_not_called()
        assert len(self.plugin.debug_text_objects) == 0

    def test_cleanup(self) -> None:
        """Test cleanup resets state."""
        self.plugin.debug_mode = True
        self.plugin.debug_text_objects = [MagicMock()]

        self.plugin.cleanup()

        assert self.plugin.debug_mode is False
        assert self.plugin.debug_text_objects == []


if __name__ == "__main__":
    unittest.main()
