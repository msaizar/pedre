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

    @patch("arcade.Text")
    def test_draw_ui_no_player(self, mock_text_cls: MagicMock) -> None:
        """Test UI drawing when player is None."""
        self.plugin.debug_mode = True

        # Return None for player
        self.mock_context.player_plugin.get_player_sprite.return_value = None

        # Setup mock NPCs
        mock_npc_plugin = self.mock_context.npc_plugin
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.visible = True
        mock_npc_state.sprite.center_x = 240.0
        mock_npc_state.sprite.center_y = 256.0
        mock_npc_state.dialog_level = 1
        mock_npc_plugin.get_npcs.return_value = {"guard": mock_npc_state}

        # Call draw_ui - should handle None player gracefully
        self.plugin.on_draw_ui()

        # Should still process NPCs
        assert len(self.plugin.debug_text_objects) > 0
        assert mock_text_cls.called

    @patch("arcade.Text")
    def test_draw_ui_no_npc_plugin(self, mock_text_cls: MagicMock) -> None:
        """Test UI drawing when npc_plugin is None."""
        self.plugin.debug_mode = True

        # Setup mock player
        mock_player = MagicMock()
        mock_player.center_x = 120
        mock_player.center_y = 128
        self.mock_context.player_plugin.get_player_sprite.return_value = mock_player

        # Set npc_plugin to None
        self.mock_context.npc_plugin = None

        # Call draw_ui - should handle None npc_plugin gracefully
        self.plugin.on_draw_ui()

        # Should have player info
        assert len(self.plugin.debug_text_objects) == 1
        assert mock_text_cls.called

    @patch("arcade.Text")
    def test_draw_ui_invisible_npc(self, mock_text_cls: MagicMock) -> None:
        """Test UI drawing skips invisible NPCs."""
        self.plugin.debug_mode = True

        # Setup mock player
        mock_player = MagicMock()
        mock_player.center_x = 120
        mock_player.center_y = 128
        self.mock_context.player_plugin.get_player_sprite.return_value = mock_player

        # Setup mock NPCs with invisible sprite
        mock_npc_plugin = self.mock_context.npc_plugin
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.visible = False  # Invisible
        mock_npc_state.sprite.center_x = 240.0
        mock_npc_state.sprite.center_y = 256.0
        mock_npc_state.dialog_level = 1
        mock_npc_plugin.get_npcs.return_value = {"guard": mock_npc_state}

        # Call draw_ui
        self.plugin.on_draw_ui()

        # Should only have player (no NPC)
        assert len(self.plugin.debug_text_objects) == 1
        assert mock_text_cls.called

    @patch("arcade.Text")
    def test_draw_ui_updates_existing_text_objects(self, mock_text_cls: MagicMock) -> None:
        """Test that existing text objects are updated instead of creating new ones."""
        self.plugin.debug_mode = True

        # Setup mock player
        mock_player = MagicMock()
        mock_player.center_x = 120
        mock_player.center_y = 128
        self.mock_context.player_plugin.get_player_sprite.return_value = mock_player
        self.mock_context.npc_plugin.get_npcs.return_value = {}

        # First draw - creates text objects
        self.plugin.on_draw_ui()
        initial_count = mock_text_cls.call_count
        assert len(self.plugin.debug_text_objects) == 1

        # Second draw with updated position - should update existing
        mock_player.center_x = 150
        mock_player.center_y = 160
        self.plugin.on_draw_ui()

        # Should not create new text objects, just update existing
        assert mock_text_cls.call_count == initial_count
        assert len(self.plugin.debug_text_objects) == 1
        # Verify text was updated
        text_obj = self.plugin.debug_text_objects[0]
        assert text_obj.text == "Player: coords (150, 160)"

    @patch("arcade.Text")
    def test_draw_ui_removes_extra_text_objects(self, mock_text_cls: MagicMock) -> None:
        """Test that extra text objects are removed when needed."""
        self.plugin.debug_mode = True

        # Setup mock player
        mock_player = MagicMock()
        mock_player.center_x = 120
        mock_player.center_y = 128
        self.mock_context.player_plugin.get_player_sprite.return_value = mock_player

        # First draw with player and NPC
        mock_npc_plugin = self.mock_context.npc_plugin
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.visible = True
        mock_npc_state.sprite.center_x = 240.0
        mock_npc_state.sprite.center_y = 256.0
        mock_npc_state.dialog_level = 1
        mock_npc_plugin.get_npcs.return_value = {"guard": mock_npc_state}

        self.plugin.on_draw_ui()
        assert len(self.plugin.debug_text_objects) == 2

        # Second draw with only player (NPC removed)
        mock_npc_plugin.get_npcs.return_value = {}
        self.plugin.on_draw_ui()

        # Should have removed the extra text object
        assert len(self.plugin.debug_text_objects) == 1
        assert mock_text_cls.called
