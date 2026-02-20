"""Unit tests for DebugPlugin in src/pedre/plugins/debug/plugin.py."""

from unittest.mock import MagicMock, patch

import arcade
import pytest

from pedre.plugins.debug.plugin import DebugPlugin


class TestDebugPlugin:
    """Test Suite for DebugPlugin."""

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Fixture for mock context."""
        return MagicMock()

    @pytest.fixture
    def plugin(self, mock_context: MagicMock) -> DebugPlugin:
        """Fixture for DebugPlugin."""
        p = DebugPlugin()
        p.setup(mock_context)
        return p

    def test_initialization(self, plugin: DebugPlugin, mock_context: MagicMock) -> None:
        """Test proper initialization of the plugin."""
        assert plugin.name == "debug"
        assert "npc" in plugin.dependencies
        assert plugin.debug_mode is False
        assert plugin.debug_text_objects == []
        assert plugin.context == mock_context

    def test_toggle_debug_mode(self, plugin: DebugPlugin) -> None:
        """Test toggling debug mode with key press."""
        # Initial state
        assert plugin.debug_mode is False

        # Toggle ON (Shift + D)
        handled = plugin.on_key_press(arcade.key.D, arcade.key.MOD_SHIFT)
        assert handled is True
        assert plugin.debug_mode is True

        # Toggle OFF
        handled = plugin.on_key_press(arcade.key.D, arcade.key.MOD_SHIFT)
        assert handled is True
        assert plugin.debug_mode is False
        assert plugin.debug_text_objects == []  # Should be cleared

    def test_ignore_other_keys(self, plugin: DebugPlugin) -> None:
        """Test that other keys are ignored."""
        # Just D without shift
        handled = plugin.on_key_press(arcade.key.D, 0)
        assert handled is False
        assert plugin.debug_mode is False

        # Shift + Other key
        handled = plugin.on_key_press(arcade.key.A, arcade.key.MOD_SHIFT)
        assert handled is False
        assert plugin.debug_mode is False

    @patch("arcade.Text")
    def test_draw_ui_debug_enabled(
        self, mock_text_cls: MagicMock, plugin: DebugPlugin, mock_context: MagicMock
    ) -> None:
        """Test UI drawing interactions when debug is enabled."""
        plugin.debug_mode = True

        # Setup mock player
        mock_player = MagicMock()
        mock_player.center_x = 120
        mock_player.center_y = 128
        mock_context.player_plugin.get_player_sprite.return_value = mock_player

        # Setup mock NPCs
        mock_npc_plugin = mock_context.npc_plugin
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.visible = True
        mock_npc_state.sprite.center_x = 240.0
        mock_npc_state.sprite.center_y = 256.0
        mock_npc_state.dialog_level = 1
        mock_npc_plugin.get_npcs.return_value = {"guard": mock_npc_state}

        # Call draw_ui
        plugin.on_draw_ui()

        assert len(plugin.debug_text_objects) > 0
        assert mock_text_cls.return_value.draw.called

    def test_draw_ui_debug_disabled(self, plugin: DebugPlugin, mock_context: MagicMock) -> None:
        """Test UI drawing is skipped when debug is disabled."""
        plugin.debug_mode = False
        plugin.on_draw_ui()

        # Should NOT access player or NPCs
        mock_context.player_plugin.get_player_sprite.assert_not_called()
        mock_context.npc_plugin.get_npcs.assert_not_called()
        assert len(plugin.debug_text_objects) == 0

    def test_cleanup(self, plugin: DebugPlugin) -> None:
        """Test cleanup resets state."""
        plugin.debug_mode = True
        plugin.debug_text_objects = [MagicMock()]

        plugin.cleanup()

        assert plugin.debug_mode is False
        assert plugin.debug_text_objects == []

    @patch("arcade.Text")
    def test_draw_ui_no_player(self, mock_text_cls: MagicMock, plugin: DebugPlugin, mock_context: MagicMock) -> None:
        """Test UI drawing when player is None."""
        plugin.debug_mode = True

        # Return None for player
        mock_context.player_plugin.get_player_sprite.return_value = None

        # Setup mock NPCs
        mock_npc_plugin = mock_context.npc_plugin
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.visible = True
        mock_npc_state.sprite.center_x = 240.0
        mock_npc_state.sprite.center_y = 256.0
        mock_npc_state.dialog_level = 1
        mock_npc_plugin.get_npcs.return_value = {"guard": mock_npc_state}

        # Call draw_ui - should handle None player gracefully
        plugin.on_draw_ui()

        # Should still process NPCs
        assert len(plugin.debug_text_objects) > 0
        assert mock_text_cls.called

    @patch("arcade.Text")
    def test_draw_ui_no_npc_plugin(
        self, mock_text_cls: MagicMock, plugin: DebugPlugin, mock_context: MagicMock
    ) -> None:
        """Test UI drawing when npc_plugin is None."""
        plugin.debug_mode = True

        # Setup mock player
        mock_player = MagicMock()
        mock_player.center_x = 120
        mock_player.center_y = 128
        mock_context.player_plugin.get_player_sprite.return_value = mock_player

        # Set npc_plugin to None
        mock_context.npc_plugin = None

        # Call draw_ui - should handle None npc_plugin gracefully
        plugin.on_draw_ui()

        # Should have player info
        assert len(plugin.debug_text_objects) == 1
        assert mock_text_cls.called

    @patch("arcade.Text")
    def test_draw_ui_invisible_npc(
        self, mock_text_cls: MagicMock, plugin: DebugPlugin, mock_context: MagicMock
    ) -> None:
        """Test UI drawing skips invisible NPCs."""
        plugin.debug_mode = True

        # Setup mock player
        mock_player = MagicMock()
        mock_player.center_x = 120
        mock_player.center_y = 128
        mock_context.player_plugin.get_player_sprite.return_value = mock_player

        # Setup mock NPCs with invisible sprite
        mock_npc_plugin = mock_context.npc_plugin
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.visible = False  # Invisible
        mock_npc_state.sprite.center_x = 240.0
        mock_npc_state.sprite.center_y = 256.0
        mock_npc_state.dialog_level = 1
        mock_npc_plugin.get_npcs.return_value = {"guard": mock_npc_state}

        # Call draw_ui
        plugin.on_draw_ui()

        # Should only have player (no NPC)
        assert len(plugin.debug_text_objects) == 1
        assert mock_text_cls.called

    @patch("arcade.Text")
    def test_draw_ui_updates_existing_text_objects(
        self, mock_text_cls: MagicMock, plugin: DebugPlugin, mock_context: MagicMock
    ) -> None:
        """Test that existing text objects are updated instead of creating new ones."""
        plugin.debug_mode = True

        # Setup mock player
        mock_player = MagicMock()
        mock_player.center_x = 120
        mock_player.center_y = 128
        mock_context.player_plugin.get_player_sprite.return_value = mock_player
        mock_context.npc_plugin.get_npcs.return_value = {}

        # First draw - creates text objects
        plugin.on_draw_ui()
        initial_count = mock_text_cls.call_count
        assert len(plugin.debug_text_objects) == 1

        # Second draw with updated position - should update existing
        mock_player.center_x = 150
        mock_player.center_y = 160
        plugin.on_draw_ui()

        # Should not create new text objects, just update existing
        assert mock_text_cls.call_count == initial_count
        assert len(plugin.debug_text_objects) == 1
        # Verify text was updated
        text_obj = plugin.debug_text_objects[0]
        assert text_obj.text == "Player: coords (150, 160)"

    @patch("arcade.Text")
    def test_draw_ui_removes_extra_text_objects(
        self, mock_text_cls: MagicMock, plugin: DebugPlugin, mock_context: MagicMock
    ) -> None:
        """Test that extra text objects are removed when needed."""
        plugin.debug_mode = True

        # Setup mock player
        mock_player = MagicMock()
        mock_player.center_x = 120
        mock_player.center_y = 128
        mock_context.player_plugin.get_player_sprite.return_value = mock_player

        # First draw with player and NPC
        mock_npc_plugin = mock_context.npc_plugin
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.visible = True
        mock_npc_state.sprite.center_x = 240.0
        mock_npc_state.sprite.center_y = 256.0
        mock_npc_state.dialog_level = 1
        mock_npc_plugin.get_npcs.return_value = {"guard": mock_npc_state}

        plugin.on_draw_ui()
        assert len(plugin.debug_text_objects) == 2

        # Second draw with only player (NPC removed)
        mock_npc_plugin.get_npcs.return_value = {}
        plugin.on_draw_ui()

        # Should have removed the extra text object
        assert len(plugin.debug_text_objects) == 1
        assert mock_text_cls.called
