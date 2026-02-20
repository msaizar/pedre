"""Unit tests for InputPlugin in src/pedre/plugins/input/plugin.py."""

import unittest
from unittest.mock import MagicMock

import arcade

from pedre.conf import settings
from pedre.plugins.input.plugin import InputPlugin


class TestInputPlugin(unittest.TestCase):
    """Test Suite for InputPlugin."""

    def setUp(self) -> None:
        """Set up the InputPlugin and mock context."""
        self.plugin = InputPlugin()
        self.mock_context = MagicMock()
        self.plugin.setup(self.mock_context)

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        assert self.plugin.name == "input"
        assert self.plugin.keys_pressed == set()
        assert self.plugin.movement_speed == settings.PLAYER_MOVEMENT_SPEED
        assert self.plugin.context == self.mock_context

    def test_key_press_release(self) -> None:
        """Test tracking of key presses and releases."""
        # Press W
        handled = self.plugin.on_key_press(arcade.key.W, 0)
        assert handled is False  # Input plugin returns False to allow others to process
        assert arcade.key.W in self.plugin.keys_pressed
        assert self.plugin.is_key_pressed(arcade.key.W) is True

        # Press D
        self.plugin.on_key_press(arcade.key.D, 0)
        assert arcade.key.D in self.plugin.keys_pressed
        assert len(self.plugin.keys_pressed) == 2

        # Release W
        handled = self.plugin.on_key_release(arcade.key.W, 0)
        assert handled is False
        assert arcade.key.W not in self.plugin.keys_pressed
        assert arcade.key.D in self.plugin.keys_pressed

    def test_movement_vector_cardinal(self) -> None:
        """Test movement vector validation for cardinal directions."""
        delta_time = 1.0
        speed = self.plugin.movement_speed

        # Move RIGHT (D)
        self.plugin.keys_pressed = {arcade.key.D}
        dx, dy = self.plugin.get_movement_vector(delta_time)
        assert dx == speed
        assert dy == 0.0

        # Move UP (W)
        self.plugin.keys_pressed = {arcade.key.W}
        dx, dy = self.plugin.get_movement_vector(delta_time)
        assert dx == 0.0
        assert dy == speed

        # Move LEFT (A)
        self.plugin.keys_pressed = {arcade.key.A}
        dx, dy = self.plugin.get_movement_vector(delta_time)
        assert dx == -speed
        assert dy == 0.0

        # Move DOWN (S)
        self.plugin.keys_pressed = {arcade.key.S}
        dx, dy = self.plugin.get_movement_vector(delta_time)
        assert dx == 0.0
        assert dy == -speed

    def test_movement_vector_diagonal(self) -> None:
        """Test movement vector validation for diagonal directions (normalized)."""
        delta_time = 1.0
        speed = self.plugin.movement_speed
        expected_component = speed * 0.7071067811865476

        # Move UP-RIGHT (W + D)
        self.plugin.keys_pressed = {arcade.key.W, arcade.key.D}
        dx, dy = self.plugin.get_movement_vector(delta_time)
        assert abs(dx - expected_component) < 0.0001
        assert abs(dy - expected_component) < 0.0001

    def test_movement_arrows_vs_wasd(self) -> None:
        """Test that arrow keys work same as WASD."""
        delta_time = 1.0
        # speed variable removed as it was unused

        # Arrow UP
        self.plugin.keys_pressed = {arcade.key.UP}
        dx_arrow, dy_arrow = self.plugin.get_movement_vector(delta_time)

        self.plugin.keys_pressed = {arcade.key.W}
        dx_wasd, dy_wasd = self.plugin.get_movement_vector(delta_time)

        assert dx_arrow == dx_wasd
        assert dy_arrow == dy_wasd

    def test_conflicting_inputs(self) -> None:
        """Test conflicting inputs cancel out (e.g. Left + Right)."""
        delta_time = 1.0

        # Left + Right
        self.plugin.keys_pressed = {arcade.key.LEFT, arcade.key.RIGHT}
        dx, dy = self.plugin.get_movement_vector(delta_time)
        assert dx == 0.0
        assert dy == 0.0

    def test_clear_state(self) -> None:
        """Test clearing input state."""
        self.plugin.keys_pressed = {arcade.key.W, arcade.key.SPACE}

        self.plugin.clear()

        assert self.plugin.keys_pressed == set()
        assert self.plugin.is_key_pressed(arcade.key.W) is False

    def test_pause_menu_trigger(self) -> None:
        """Test detecting pause menu trigger (Escape)."""
        # Setup mock pause menu plugin
        mock_pause_menu = MagicMock()
        mock_pause_menu.showing = False
        self.mock_context.pause_menu_plugin = mock_pause_menu

        handled = self.plugin.on_key_press(arcade.key.ESCAPE, 0)

        assert handled is True
        mock_pause_menu.show.assert_called_once()

    def test_save_restore_state(self) -> None:
        """Test save/restore of input settings."""
        self.plugin.movement_speed = 999.0

        state = self.plugin.get_save_state()
        assert state["movement_speed"] == 999.0

        # Restore
        self.plugin.movement_speed = 0.0
        self.plugin.restore_save_state(state)
        assert self.plugin.movement_speed == 999.0

    def test_cleanup(self) -> None:
        """Test cleanup clears all pressed keys."""
        # Add some keys
        self.plugin.keys_pressed = {arcade.key.W, arcade.key.D, arcade.key.SPACE}

        # Cleanup
        self.plugin.cleanup()

        assert self.plugin.keys_pressed == set()

    def test_pause_menu_not_shown_when_already_showing(self) -> None:
        """Test that pause menu is not shown when already showing."""
        # Setup mock pause menu plugin that's already showing
        mock_pause_menu = MagicMock()
        mock_pause_menu.showing = True
        self.mock_context.pause_menu_plugin = mock_pause_menu

        handled = self.plugin.on_key_press(arcade.key.ESCAPE, 0)

        # Should still handle the key press
        assert handled is True
        # But should not call show() since it's already showing
        mock_pause_menu.show.assert_not_called()
