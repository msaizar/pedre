"""Unit tests for PauseMenuPlugin in src/pedre/plugins/pause_menu/plugin.py."""

import unittest
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

import arcade
import pytest

from pedre.plugins.pause_menu.base import PauseMenuOption, PauseMenuState
from pedre.plugins.pause_menu.plugin import PauseMenuPlugin

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def mock_arcade_text() -> Iterator[MagicMock]:
    """Mock arcade.Text for drawing tests."""
    with patch("arcade.Text") as mock:
        yield mock


@pytest.fixture
def mock_arcade_rect_filled() -> Iterator[MagicMock]:
    """Mock arcade.draw_lrbt_rectangle_filled for drawing tests."""
    with patch("arcade.draw_lrbt_rectangle_filled") as mock:
        yield mock


@pytest.fixture
def mock_arcade_rect_outline() -> Iterator[MagicMock]:
    """Mock arcade.draw_lrbt_rectangle_outline for drawing tests."""
    with patch("arcade.draw_lrbt_rectangle_outline") as mock:
        yield mock


class TestPauseMenuPlugin(unittest.TestCase):
    """Test Suite for PauseMenuPlugin."""

    def setUp(self) -> None:
        """Set up the PauseMenuPlugin and mock context."""
        self.plugin = PauseMenuPlugin()
        self.mock_context = MagicMock()
        self.mock_context.save_plugin = MagicMock()
        self.mock_context.window = MagicMock()
        self.mock_context.window.width = 800
        self.mock_context.window.height = 600
        self.plugin.setup(self.mock_context)

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        assert self.plugin.name == "pause_menu"
        assert self.plugin.menu_state == PauseMenuState.MAIN_MENU
        assert self.plugin.selected_option == 0
        assert self.plugin.showing is False
        assert self.plugin.context == self.mock_context

    def test_show_hide(self) -> None:
        """Test showing and hiding the menu."""
        # Show
        self.plugin.show()
        assert self.plugin.showing is True
        assert self.plugin.menu_state == PauseMenuState.MAIN_MENU
        assert self.plugin.selected_option == 0

        # Hide
        self.plugin.hide()
        assert self.plugin.showing is False

    def test_key_press_ignore_when_hidden(self) -> None:
        """Test keys are ignored when menu is hidden."""
        assert self.plugin.showing is False
        handled = self.plugin.on_key_press(arcade.key.UP, 0)
        assert handled is False

    def test_key_press_escape(self) -> None:
        """Test Escape key toggles menu or goes back."""
        # Show menu
        self.plugin.show()

        # In main menu, escape closes it
        handled = self.plugin.on_key_press(arcade.key.ESCAPE, 0)
        assert handled is True
        assert self.plugin.showing is False

        # In sub-menu, escape goes back
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS
        handled = self.plugin.on_key_press(arcade.key.ESCAPE, 0)
        assert handled is True
        assert self.plugin.showing is True
        assert self.plugin.menu_state == PauseMenuState.MAIN_MENU

    def test_navigation_main_menu(self) -> None:
        """Test navigation in main menu."""
        self.plugin.show()
        # Assume options: Resume, New Game, Load, Save, Exit (5 options)
        num_options = len(PauseMenuOption)

        # Down
        self.plugin.selected_option = 0
        self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert self.plugin.selected_option == 1

        # Wrap around down
        self.plugin.selected_option = num_options - 1
        self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert self.plugin.selected_option == 0

        # Up
        self.plugin.selected_option = 1
        self.plugin.on_key_press(arcade.key.UP, 0)
        assert self.plugin.selected_option == 0

        # Wrap around up
        self.plugin.selected_option = 0
        self.plugin.on_key_press(arcade.key.UP, 0)
        assert self.plugin.selected_option == num_options - 1

    def test_navigation_sub_menus(self) -> None:
        """Test navigation in sub menus (slots)."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS
        # Save slots: 1-3 (3 slots)
        num_slots = 3

        # Wrap around
        self.plugin.selected_option = 0
        self.plugin.on_key_press(arcade.key.UP, 0)
        assert self.plugin.selected_option == num_slots - 1

        self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert self.plugin.selected_option == 0

    def test_execute_resume(self) -> None:
        """Test executing Resume option."""
        self.plugin.show()
        # Resume is usually option 0 (PauseMenuOption.RESUME)
        self.plugin.selected_option = 0
        # Verify assumption
        assert PauseMenuOption(0) == PauseMenuOption.RESUME

        self.plugin.on_key_press(arcade.key.ENTER, 0)
        assert self.plugin.showing is False

    def test_execute_load_game_transition(self) -> None:
        """Test entering Load Game menu."""
        self.plugin.show()
        # Find index for Load Game
        load_idx = list(PauseMenuOption).index(PauseMenuOption.LOAD_GAME)
        self.plugin.selected_option = load_idx

        self.plugin.on_key_press(arcade.key.ENTER, 0)

        assert self.plugin.menu_state == PauseMenuState.LOAD_SLOTS
        assert self.plugin.selected_option == 0

    def test_execute_save_slot(self) -> None:
        """Test saving to a slot."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS
        self.plugin.selected_option = 0  # Maps to Slot 1

        # Mock save success
        self.mock_context.save_plugin.save_game.return_value = True

        self.plugin.on_key_press(arcade.key.ENTER, 0)

        self.mock_context.save_plugin.save_game.assert_called_with(slot=1)
        assert self.plugin.save_feedback_message == "Game Saved!"
        assert self.plugin.save_feedback_timer > 0

    def test_execute_new_game_confirmation(self) -> None:
        """Test new game confirmation flow."""
        self.plugin.show()
        new_game_idx = list(PauseMenuOption).index(PauseMenuOption.NEW_GAME)
        self.plugin.selected_option = new_game_idx

        # Trigger confirmation
        self.plugin.on_key_press(arcade.key.ENTER, 0)
        assert self.plugin.menu_state == PauseMenuState.CONFIRMATION
        assert self.plugin.confirmation_action == "new_game"
        assert self.plugin.selected_option == 1  # Defaults to No

        # Select Yes (0)
        self.plugin.selected_option = 0
        self.plugin.on_key_press(arcade.key.ENTER, 0)

        self.mock_context.start_new_game.assert_called_once()
        assert self.plugin.showing is False

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")  # Patch Text class construction
    def test_draw_ui(self, mock_text_cls: MagicMock, mock_rect_outline: MagicMock, mock_rect_filled: MagicMock) -> None:
        """Test drawing the UI."""
        self.plugin.show()

        # Mock Text instance behavior
        mock_text_instance = MagicMock()
        mock_text_cls.return_value = mock_text_instance

        self.plugin.on_draw_ui()

        # Verify overlay and box drawn
        assert mock_rect_filled.call_count >= 2  # Overlay + Box background
        assert mock_rect_outline.called

        # Verify text objects created and drawn
        # Title + options
        assert mock_text_cls.call_count > 0
        assert mock_text_instance.draw.called

    def test_draw_ui_hidden(self) -> None:
        """Test nothing drawn when hidden."""
        self.plugin.hide()
        with patch("arcade.draw_lrbt_rectangle_filled") as mock_draw:
            self.plugin.on_draw_ui()
            mock_draw.assert_not_called()

    def test_update_timer(self) -> None:
        """Test updating timers."""
        self.plugin.save_feedback_timer = 1.0
        self.plugin.save_feedback_message = "Saved"

        self.plugin.update(0.5)
        assert self.plugin.save_feedback_timer == 0.5
        assert self.plugin.save_feedback_message == "Saved"

        self.plugin.update(0.6)
        assert self.plugin.save_feedback_timer <= 0
        assert self.plugin.save_feedback_message is None

    @patch("arcade.close_window")
    def test_exit_game(self, mock_close: MagicMock) -> None:
        """Test exiting the game."""
        self.plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        self.plugin.selected_option = exit_idx

        # Mock auto-save
        self.mock_context.save_plugin.auto_save.return_value = True

        self.plugin.on_key_press(arcade.key.ENTER, 0)

        self.mock_context.save_plugin.auto_save.assert_called_once()
        mock_close.assert_called_once()

    def test_cleanup(self) -> None:
        """Test cleanup method."""
        self.plugin.show()
        assert self.plugin.showing is True

        self.plugin.cleanup()
        assert self.plugin.showing is False

    def test_navigation_load_slots(self) -> None:
        """Test navigation in load slots menu."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS
        num_slots = 4  # Slots 0-3

        # Down
        self.plugin.selected_option = 0
        handled = self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True
        assert self.plugin.selected_option == 1

        # Wrap around down
        self.plugin.selected_option = num_slots - 1
        handled = self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True
        assert self.plugin.selected_option == 0

        # Up
        self.plugin.selected_option = 1
        handled = self.plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True
        assert self.plugin.selected_option == 0

        # Wrap around up
        self.plugin.selected_option = 0
        handled = self.plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True
        assert self.plugin.selected_option == num_slots - 1

    def test_execute_load_slot_with_save(self) -> None:
        """Test loading from a slot with valid save data."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS
        self.plugin.selected_option = 1  # Slot 1

        # Mock save exists and load
        mock_save_data = {"map": "test_map", "position": [0, 0]}
        self.mock_context.save_plugin.save_exists.return_value = True
        self.mock_context.save_plugin.load_game.return_value = mock_save_data

        handled = self.plugin.on_key_press(arcade.key.ENTER, 0)

        assert handled is True
        self.mock_context.save_plugin.save_exists.assert_called_with(slot=1)
        self.mock_context.save_plugin.load_game.assert_called_with(slot=1)
        self.mock_context.load_game.assert_called_with(mock_save_data)
        assert self.plugin.showing is False

    def test_execute_load_slot_no_save(self) -> None:
        """Test loading from an empty slot."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS
        self.plugin.selected_option = 2

        # Mock no save exists
        self.mock_context.save_plugin.save_exists.return_value = False

        handled = self.plugin.on_key_press(arcade.key.ENTER, 0)

        assert handled is True
        self.mock_context.save_plugin.save_exists.assert_called_with(slot=2)
        self.mock_context.save_plugin.load_game.assert_not_called()
        assert self.plugin.showing is True  # Still showing

    def test_execute_load_slot_failed_load(self) -> None:
        """Test loading from a slot when load fails."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS
        self.plugin.selected_option = 0

        # Mock save exists but load fails
        self.mock_context.save_plugin.save_exists.return_value = True
        self.mock_context.save_plugin.load_game.return_value = None

        handled = self.plugin.on_key_press(arcade.key.ENTER, 0)

        assert handled is True
        self.mock_context.save_plugin.load_game.assert_called_with(slot=0)
        self.mock_context.load_game.assert_not_called()
        assert self.plugin.showing is True  # Still showing

    def test_execute_load_slot_no_context(self) -> None:
        """Test loading when context is not available."""
        self.plugin.context = None
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS
        self.plugin.selected_option = 0

        self.plugin._execute_load_slot()
        # Should not crash, just log error

    def test_execute_save_slot_failed(self) -> None:
        """Test saving to a slot when save fails."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS
        self.plugin.selected_option = 1  # Maps to Slot 2

        # Mock save failure
        self.mock_context.save_plugin.save_game.return_value = False

        self.plugin.on_key_press(arcade.key.ENTER, 0)

        self.mock_context.save_plugin.save_game.assert_called_with(slot=2)
        assert self.plugin.save_feedback_message is None
        assert self.plugin.menu_state == PauseMenuState.SAVE_SLOTS  # Still in save menu

    def test_execute_save_slot_no_context(self) -> None:
        """Test saving when context is not available."""
        self.plugin.context = None
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS
        self.plugin.selected_option = 0

        self.plugin._execute_save_slot()
        # Should not crash, just log error

    def test_navigation_confirmation(self) -> None:
        """Test navigation in confirmation overlay."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        num_options = 2  # Yes/No

        # Down
        self.plugin.selected_option = 0
        handled = self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True
        assert self.plugin.selected_option == 1

        # Wrap around down
        self.plugin.selected_option = num_options - 1
        handled = self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True
        assert self.plugin.selected_option == 0

        # Up
        self.plugin.selected_option = 1
        handled = self.plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True
        assert self.plugin.selected_option == 0

    def test_execute_confirmation_cancel(self) -> None:
        """Test cancelling confirmation (selecting No)."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        self.plugin.confirmation_action = "new_game"
        self.plugin.selected_option = 1  # No

        handled = self.plugin.on_key_press(arcade.key.ENTER, 0)

        assert handled is True
        assert self.plugin.menu_state == PauseMenuState.MAIN_MENU
        assert self.plugin.selected_option == 0
        self.mock_context.start_new_game.assert_not_called()

    def test_key_press_consumes_all_input_when_showing(self) -> None:
        """Test that all key presses are consumed when menu is showing."""
        self.plugin.show()
        # Try a random key that doesn't do anything
        handled = self.plugin.on_key_press(arcade.key.A, 0)
        assert handled is True

    def test_execute_save_game_transition(self) -> None:
        """Test entering Save Game menu."""
        self.plugin.show()
        save_idx = list(PauseMenuOption).index(PauseMenuOption.SAVE_GAME)
        self.plugin.selected_option = save_idx

        self.plugin.on_key_press(arcade.key.ENTER, 0)

        assert self.plugin.menu_state == PauseMenuState.SAVE_SLOTS
        assert self.plugin.selected_option == 0

    @patch("arcade.close_window")
    def test_exit_game_auto_save_failed(self, mock_close: MagicMock) -> None:
        """Test exiting when auto-save fails."""
        self.plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        self.plugin.selected_option = exit_idx

        # Mock auto-save failure
        self.mock_context.save_plugin.auto_save.return_value = False

        self.plugin.on_key_press(arcade.key.ENTER, 0)

        self.mock_context.save_plugin.auto_save.assert_called_once()
        mock_close.assert_called_once()  # Still exits

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_text_objects_load_slots(self) -> None:
        """Test preparing text objects for load slots state."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS

        # Mock save info
        self.mock_context.save_plugin.get_save_info.side_effect = [
            {"map": "Map1", "date_string": "2024-01-01"},
            None,  # Slot 1 empty
            {"map": "Map3", "date_string": "2024-01-03"},
            None,  # Slot 3 empty
        ]

        self.plugin.on_draw_ui()

        # Verify get_save_info called for all slots
        assert self.mock_context.save_plugin.get_save_info.call_count == 4

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_text_objects_save_slots(self) -> None:
        """Test preparing text objects for save slots state."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS

        # Mock save info
        self.mock_context.save_plugin.get_save_info.side_effect = [
            {"map": "Map1", "date_string": "2024-01-01"},
            None,  # Slot 2 empty
            {"map": "Map3", "date_string": "2024-01-03"},
        ]

        self.plugin.on_draw_ui()

        # Verify get_save_info called for slots 1-3
        assert self.mock_context.save_plugin.get_save_info.call_count == 3

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_text_objects_confirmation(self) -> None:
        """Test preparing text objects for confirmation state."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        self.plugin.confirmation_message = "Are you sure?"

        self.plugin.on_draw_ui()

        # Text objects are created (we can't easily assert on them without accessing the mock)

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_text_objects_main_menu(self) -> None:
        """Test preparing text objects for main menu state."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.MAIN_MENU

        self.plugin.on_draw_ui()

        # Text objects are created (we can't easily assert on them without accessing the mock)

    def test_draw_ui_no_context(self) -> None:
        """Test drawing when context is not available."""
        self.plugin.context = None
        self.plugin.show()

        with patch("arcade.draw_lrbt_rectangle_filled") as mock_draw:
            self.plugin.on_draw_ui()
            mock_draw.assert_not_called()

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_load_slots(self) -> None:
        """Test drawing load slots menu."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS

        self.plugin.on_draw_ui()

        # Verify drawing completes without error

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_save_slots(self) -> None:
        """Test drawing save slots menu."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS

        self.plugin.on_draw_ui()

        # Verify drawing completes without error

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_confirmation(self) -> None:
        """Test drawing confirmation overlay."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        self.plugin.confirmation_message = "Test message"

        self.plugin.on_draw_ui()

        # Verify drawing completes without error

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_with_feedback_message(self) -> None:
        """Test drawing with save feedback message."""
        self.plugin.show()
        self.plugin.save_feedback_message = "Game Saved!"
        self.plugin.save_feedback_timer = 1.0

        self.plugin.on_draw_ui()

        # Verify drawing completes without error (feedback text should be shown)

    def test_update_timer_zero_or_negative(self) -> None:
        """Test update with timer already at zero or negative."""
        # Timer already at 0
        self.plugin.save_feedback_timer = 0
        self.plugin.save_feedback_message = "Saved"
        self.plugin.update(0.1)
        # Message should remain since timer wasn't positive
        assert self.plugin.save_feedback_message == "Saved"

        # Timer negative
        self.plugin.save_feedback_timer = -0.5
        self.plugin.update(0.1)
        assert self.plugin.save_feedback_message == "Saved"

    def test_execute_confirmation_without_context(self) -> None:
        """Test confirmation execution without context."""
        self.plugin.context = None
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        self.plugin.confirmation_action = "new_game"
        self.plugin.selected_option = 0  # Yes

        # Should not crash without context
        self.plugin._execute_confirmation()

    def test_execute_confirmation_unknown_action(self) -> None:
        """Test confirmation with unknown action."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        self.plugin.confirmation_action = "unknown_action"
        self.plugin.selected_option = 0  # Yes

        # Should not crash with unknown action
        self.plugin._execute_confirmation()

    @patch("arcade.close_window")
    def test_exit_game_no_context(self, mock_close: MagicMock) -> None:
        """Test exiting when context is not available."""
        self.plugin.context = None
        self.plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        self.plugin.selected_option = exit_idx

        self.plugin._execute_main_menu_option()

        # Should not crash
        mock_close.assert_not_called()

    @patch("arcade.close_window")
    def test_exit_game_no_window_attribute(self, mock_close: MagicMock) -> None:
        """Test exiting when context has no window attribute."""
        # Create a context without window attribute
        context_without_window = MagicMock()
        context_without_window.save_plugin = MagicMock()
        context_without_window.save_plugin.auto_save.return_value = True
        del context_without_window.window  # Remove window attribute

        self.plugin.context = context_without_window
        self.plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        self.plugin.selected_option = exit_idx

        self.plugin.on_key_press(arcade.key.ENTER, 0)

        # Should not crash, and close_window should not be called
        mock_close.assert_not_called()

    def test_execute_load_slot_no_save_plugin(self) -> None:
        """Test loading when save plugin is not available."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS
        self.plugin.selected_option = 0

        # Remove save plugin
        self.mock_context.save_plugin = None

        self.plugin._execute_load_slot()
        # Should not crash, just log error

    def test_execute_save_slot_no_save_plugin(self) -> None:
        """Test saving when save plugin is not available."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS
        self.plugin.selected_option = 0

        # Remove save plugin
        self.mock_context.save_plugin = None

        self.plugin._execute_save_slot()
        # Should not crash, just log error

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_ui_no_window(self) -> None:
        """Test drawing when context has no window."""
        self.plugin.context = self.mock_context
        cast("MagicMock", self.plugin.context).window = None
        self.plugin.show()

        with patch("arcade.draw_lrbt_rectangle_filled") as mock_draw:
            self.plugin.on_draw_ui()
            mock_draw.assert_not_called()

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_load_slots_no_save_plugin(self) -> None:
        """Test preparing load slots when save plugin is not available."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS

        # Remove save plugin
        self.mock_context.save_plugin = None

        self.plugin.on_draw_ui()
        # Should not crash

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_load_slots_no_context(self) -> None:
        """Test preparing load slots when context is not available."""
        self.plugin.context = None
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS

        # Set up a mock window since we need it for drawing
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_context = MagicMock()
        mock_context.window = mock_window
        mock_context.save_plugin = None
        self.plugin.context = mock_context

        self.plugin.on_draw_ui()
        # Should not crash

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_save_slots_no_save_plugin(self) -> None:
        """Test preparing save slots when save plugin is not available."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS

        # Remove save plugin
        self.mock_context.save_plugin = None

        self.plugin.on_draw_ui()
        # Should not crash

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_save_slots_no_context(self) -> None:
        """Test preparing save slots when context is not available."""
        self.plugin.context = None
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS

        # Set up a mock window since we need it for drawing
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_context = MagicMock()
        mock_context.window = mock_window
        mock_context.save_plugin = None
        self.plugin.context = mock_context

        self.plugin.on_draw_ui()
        # Should not crash

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_without_feedback_message(self) -> None:
        """Test drawing without save feedback message (coverage for branch where feedback is None)."""
        self.plugin.show()
        self.plugin.save_feedback_message = None
        self.plugin.save_feedback_timer = 0

        self.plugin.on_draw_ui()
        # Should draw without feedback text

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_with_different_menu_states(self) -> None:
        """Test drawing in all different menu states for full branch coverage."""
        self.plugin.show()

        # Test MAIN_MENU state
        self.plugin.menu_state = PauseMenuState.MAIN_MENU
        self.plugin.on_draw_ui()

        # Test LOAD_SLOTS state
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS
        self.plugin.on_draw_ui()

        # Test SAVE_SLOTS state
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS
        self.plugin.on_draw_ui()

        # Test CONFIRMATION state
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        self.plugin.confirmation_message = "Test"
        self.plugin.on_draw_ui()

    def test_key_press_load_slots_all_keys(self) -> None:
        """Test all key presses in load slots state for branch coverage."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.LOAD_SLOTS
        self.plugin.selected_option = 0

        # Test UP key
        handled = self.plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True

        # Test DOWN key
        handled = self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True

        # Test ENTER key (should trigger load slot execution)
        self.mock_context.save_plugin.save_exists.return_value = False
        handled = self.plugin.on_key_press(arcade.key.ENTER, 0)
        assert handled is True

        # Test other keys (should still be consumed)
        handled = self.plugin.on_key_press(arcade.key.A, 0)
        assert handled is True

    def test_key_press_save_slots_all_keys(self) -> None:
        """Test all key presses in save slots state for branch coverage."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS
        self.plugin.selected_option = 0

        # Test UP key
        handled = self.plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True

        # Test DOWN key
        handled = self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True

        # Test ENTER key (should trigger save slot execution)
        self.mock_context.save_plugin.save_game.return_value = True
        handled = self.plugin.on_key_press(arcade.key.ENTER, 0)
        assert handled is True

        # Test other keys (should still be consumed)
        handled = self.plugin.on_key_press(arcade.key.B, 0)
        assert handled is True

    def test_key_press_confirmation_all_keys(self) -> None:
        """Test all key presses in confirmation state for branch coverage."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        self.plugin.confirmation_action = "new_game"
        self.plugin.selected_option = 1  # No

        # Test UP key
        handled = self.plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True
        assert self.plugin.selected_option == 0

        # Test DOWN key
        handled = self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True
        assert self.plugin.selected_option == 1

        # Test ENTER key (should execute confirmation)
        handled = self.plugin.on_key_press(arcade.key.ENTER, 0)
        assert handled is True

        # Test other keys (should still be consumed)
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        handled = self.plugin.on_key_press(arcade.key.C, 0)
        assert handled is True

    @patch("arcade.close_window")
    def test_exit_game_with_context_no_window(self, mock_close: MagicMock) -> None:
        """Test exiting when context exists but has no window attribute."""
        self.plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        self.plugin.selected_option = exit_idx

        # Mock auto-save success
        self.mock_context.save_plugin.auto_save.return_value = True

        # Remove window attribute
        mock_context = MagicMock()
        mock_context.save_plugin = self.mock_context.save_plugin
        # Don't set window attribute at all
        if hasattr(mock_context, "window"):
            delattr(mock_context, "window")
        self.plugin.context = mock_context

        self.plugin.on_key_press(arcade.key.ENTER, 0)

        # close_window should not be called
        mock_close.assert_not_called()

    def test_key_press_save_slots_non_action_key(self) -> None:
        """Test pressing a non-action key in save slots state (for branch 144->162)."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.SAVE_SLOTS
        self.plugin.selected_option = 0

        # Press a key that's not UP, DOWN, or ENTER
        # This should fall through to the final return True at line 162
        handled = self.plugin.on_key_press(arcade.key.SPACE, 0)
        assert handled is True

        # State should remain unchanged
        assert self.plugin.menu_state == PauseMenuState.SAVE_SLOTS
        assert self.plugin.selected_option == 0

    def test_key_press_confirmation_non_action_key(self) -> None:
        """Test pressing a non-action key in confirmation state."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        self.plugin.confirmation_action = "new_game"
        self.plugin.selected_option = 1

        # Press a key that's not UP, DOWN, or ENTER
        # This should fall through to the final return True at line 162
        handled = self.plugin.on_key_press(arcade.key.SPACE, 0)
        assert handled is True

        # State should remain unchanged
        assert self.plugin.menu_state == PauseMenuState.CONFIRMATION
        assert self.plugin.selected_option == 1

    @patch("arcade.close_window")
    def test_exit_without_context(self, mock_close: MagicMock) -> None:
        """Test exit option when context is None."""
        # Set context to None
        self.plugin.context = None
        self.plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        self.plugin.selected_option = exit_idx

        # Execute the exit option directly
        self.plugin._execute_main_menu_option()

        # close_window should not be called since there's no context
        mock_close.assert_not_called()

    def test_execute_main_menu_unknown_option(self) -> None:
        """Test executing main menu with unknown option (tests else branch)."""
        self.plugin.show()

        # Create a fake enum value that's not in the if/elif chain
        # We need to mock the PauseMenuOption constructor to return a value
        # that doesn't match any of the handled cases
        fake_option = MagicMock()
        fake_option.__eq__ = MagicMock(return_value=False)  # Never equals any option

        with patch("pedre.plugins.pause_menu.plugin.PauseMenuOption", return_value=fake_option):
            # This should hit the else branch and log an error
            self.plugin._execute_main_menu_option()

        # Menu should still be showing (no action taken)
        assert self.plugin.showing is True

    def test_key_press_invalid_menu_state_fallthrough(self) -> None:
        """Test key press with invalid menu state falls through to line 162 (branch 149->162)."""
        self.plugin.show()

        # Manually set an invalid state (bypassing enum type checking)
        # This simulates state corruption or an unexpected state value
        self.plugin.menu_state = "invalid_state"

        # Any key press should still be consumed and return True
        handled = self.plugin.on_key_press(arcade.key.ENTER, 0)
        assert handled is True

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_text_invalid_state_fallthrough(self) -> None:
        """Test _prepare_text_objects with invalid state (branch 331->335)."""
        self.plugin.show()

        # Set an invalid menu state
        self.plugin.menu_state = "invalid_state"

        # Should not crash, will skip state-specific text preparation
        self.plugin.on_draw_ui()

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_invalid_state_fallthrough(self) -> None:
        """Test on_draw_ui with invalid state (branch 740->744)."""
        self.plugin.show()

        # Set an invalid menu state after title is created
        self.plugin.menu_state = PauseMenuState.MAIN_MENU
        self.plugin.on_draw_ui()  # Create title_text first

        # Now set invalid state
        self.plugin.menu_state = "invalid_state"

        # Should still draw title but skip state-specific rendering
        self.plugin.on_draw_ui()

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_title_none(self) -> None:
        """Test drawing when title_text is None (branch 730->734)."""
        self.plugin.show()

        # Mock arcade.Text to return None only for the title (first call)
        call_count = [0]

        def mock_text_factory(*_args: object, **_kwargs: object) -> MagicMock | None:
            call_count[0] += 1
            if call_count[0] == 1:  # First call is for title
                return None
            mock = MagicMock()
            mock.draw = MagicMock()
            return mock

        with patch("arcade.Text", side_effect=mock_text_factory):
            # Should not crash when title_text is None
            self.plugin.on_draw_ui()

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_confirmation_message_text_none(self) -> None:
        """Test drawing confirmation when confirmation_message_text is None (branch 765->769)."""
        self.plugin.show()
        self.plugin.menu_state = PauseMenuState.CONFIRMATION
        self.plugin.confirmation_message = "Test"

        # Mock Text to return None for confirmation_message_text
        call_count = [0]

        def mock_text_factory(*_args: object, **_kwargs: object) -> MagicMock | None:
            call_count[0] += 1
            # Return None for the confirmation message text (second call after title)
            if call_count[0] == 2:  # Confirmation message is created after title
                return None
            return MagicMock()

        with patch("arcade.Text", side_effect=mock_text_factory):
            self.plugin.on_draw_ui()

        # Should not crash when confirmation_message_text is None
