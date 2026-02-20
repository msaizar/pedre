"""Unit tests for InputPlugin in src/pedre/plugins/input/plugin.py."""

from unittest.mock import MagicMock

import arcade
import pytest

from pedre.conf import settings
from pedre.plugins.input.plugin import InputPlugin


class TestInputPlugin:
    """Test Suite for InputPlugin."""

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Fixture for mock context."""
        return MagicMock()

    @pytest.fixture
    def plugin(self, mock_context: MagicMock) -> InputPlugin:
        """Fixture for InputPlugin."""
        p = InputPlugin()
        p.setup(mock_context)
        return p

    def test_initialization(self, plugin: InputPlugin, mock_context: MagicMock) -> None:
        """Test proper initialization of the plugin."""
        assert plugin.name == "input"
        assert plugin.keys_pressed == set()
        assert plugin.movement_speed == settings.PLAYER_MOVEMENT_SPEED
        assert plugin.context == mock_context

    def test_key_press_release(self, plugin: InputPlugin) -> None:
        """Test tracking of key presses and releases."""
        # Press W
        handled = plugin.on_key_press(arcade.key.W, 0)
        assert handled is False  # Input plugin returns False to allow others to process
        assert arcade.key.W in plugin.keys_pressed
        assert plugin.is_key_pressed(arcade.key.W) is True

        # Press D
        plugin.on_key_press(arcade.key.D, 0)
        assert arcade.key.D in plugin.keys_pressed
        assert len(plugin.keys_pressed) == 2

        # Release W
        handled = plugin.on_key_release(arcade.key.W, 0)
        assert handled is False
        assert arcade.key.W not in plugin.keys_pressed
        assert arcade.key.D in plugin.keys_pressed

    def test_movement_vector_cardinal(self, plugin: InputPlugin) -> None:
        """Test movement vector validation for cardinal directions."""
        delta_time = 1.0
        speed = plugin.movement_speed

        # Move RIGHT (D)
        plugin.keys_pressed = {arcade.key.D}
        dx, dy = plugin.get_movement_vector(delta_time)
        assert dx == speed
        assert dy == 0.0

        # Move UP (W)
        plugin.keys_pressed = {arcade.key.W}
        dx, dy = plugin.get_movement_vector(delta_time)
        assert dx == 0.0
        assert dy == speed

        # Move LEFT (A)
        plugin.keys_pressed = {arcade.key.A}
        dx, dy = plugin.get_movement_vector(delta_time)
        assert dx == -speed
        assert dy == 0.0

        # Move DOWN (S)
        plugin.keys_pressed = {arcade.key.S}
        dx, dy = plugin.get_movement_vector(delta_time)
        assert dx == 0.0
        assert dy == -speed

    def test_movement_vector_diagonal(self, plugin: InputPlugin) -> None:
        """Test movement vector validation for diagonal directions (normalized)."""
        delta_time = 1.0
        speed = plugin.movement_speed
        expected_component = speed * 0.7071067811865476

        # Move UP-RIGHT (W + D)
        plugin.keys_pressed = {arcade.key.W, arcade.key.D}
        dx, dy = plugin.get_movement_vector(delta_time)
        assert abs(dx - expected_component) < 0.0001
        assert abs(dy - expected_component) < 0.0001

    def test_movement_arrows_vs_wasd(self, plugin: InputPlugin) -> None:
        """Test that arrow keys work same as WASD."""
        delta_time = 1.0

        # Arrow UP
        plugin.keys_pressed = {arcade.key.UP}
        dx_arrow, dy_arrow = plugin.get_movement_vector(delta_time)

        plugin.keys_pressed = {arcade.key.W}
        dx_wasd, dy_wasd = plugin.get_movement_vector(delta_time)

        assert dx_arrow == dx_wasd
        assert dy_arrow == dy_wasd

    def test_conflicting_inputs(self, plugin: InputPlugin) -> None:
        """Test conflicting inputs cancel out (e.g. Left + Right)."""
        delta_time = 1.0

        # Left + Right
        plugin.keys_pressed = {arcade.key.LEFT, arcade.key.RIGHT}
        dx, dy = plugin.get_movement_vector(delta_time)
        assert dx == 0.0
        assert dy == 0.0

    def test_clear_state(self, plugin: InputPlugin) -> None:
        """Test clearing input state."""
        plugin.keys_pressed = {arcade.key.W, arcade.key.SPACE}

        plugin.clear()

        assert plugin.keys_pressed == set()
        assert plugin.is_key_pressed(arcade.key.W) is False

    def test_pause_menu_trigger(self, plugin: InputPlugin, mock_context: MagicMock) -> None:
        """Test detecting pause menu trigger (Escape)."""
        # Setup mock pause menu plugin
        mock_pause_menu = MagicMock()
        mock_pause_menu.showing = False
        mock_context.pause_menu_plugin = mock_pause_menu

        handled = plugin.on_key_press(arcade.key.ESCAPE, 0)

        assert handled is True
        mock_pause_menu.show.assert_called_once()

    def test_save_restore_state(self, plugin: InputPlugin) -> None:
        """Test save/restore of input settings."""
        plugin.movement_speed = 999.0

        state = plugin.get_save_state()
        assert state["movement_speed"] == 999.0

        # Restore
        plugin.movement_speed = 0.0
        plugin.restore_save_state(state)
        assert plugin.movement_speed == 999.0

    def test_cleanup(self, plugin: InputPlugin) -> None:
        """Test cleanup clears all pressed keys."""
        # Add some keys
        plugin.keys_pressed = {arcade.key.W, arcade.key.D, arcade.key.SPACE}

        # Cleanup
        plugin.cleanup()

        assert plugin.keys_pressed == set()

    def test_pause_menu_not_shown_when_already_showing(self, plugin: InputPlugin, mock_context: MagicMock) -> None:
        """Test that pause menu is not shown when already showing."""
        # Setup mock pause menu plugin that's already showing
        mock_pause_menu = MagicMock()
        mock_pause_menu.showing = True
        mock_context.pause_menu_plugin = mock_pause_menu

        handled = plugin.on_key_press(arcade.key.ESCAPE, 0)

        # Should still handle the key press
        assert handled is True
        # But should not call show() since it's already showing
        mock_pause_menu.show.assert_not_called()
