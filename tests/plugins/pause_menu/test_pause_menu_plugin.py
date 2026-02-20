"""Unit tests for PauseMenuPlugin in src/pedre/plugins/pause_menu/plugin.py."""

from typing import TYPE_CHECKING
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


class TestPauseMenuPlugin:
    """Test Suite for PauseMenuPlugin."""

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Fixture for mock context."""
        ctx = MagicMock()
        ctx.save_plugin = MagicMock()
        ctx.window = MagicMock()
        ctx.window.width = 800
        ctx.window.height = 600
        return ctx

    @pytest.fixture
    def plugin(self, mock_context: MagicMock) -> PauseMenuPlugin:
        """Fixture for PauseMenuPlugin."""
        p = PauseMenuPlugin()
        p.setup(mock_context)
        return p

    def test_initialization(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test proper initialization of the plugin."""
        assert plugin.name == "pause_menu"
        assert plugin.menu_state == PauseMenuState.MAIN_MENU
        assert plugin.selected_option == 0
        assert plugin.showing is False
        assert plugin.context == mock_context

    def test_show_hide(self, plugin: PauseMenuPlugin) -> None:
        """Test showing and hiding the menu."""
        # Show
        plugin.show()
        assert plugin.showing is True
        assert plugin.menu_state == PauseMenuState.MAIN_MENU
        assert plugin.selected_option == 0

        # Hide
        plugin.hide()
        assert plugin.showing is False

    def test_key_press_ignore_when_hidden(self, plugin: PauseMenuPlugin) -> None:
        """Test keys are ignored when menu is hidden."""
        assert plugin.showing is False
        handled = plugin.on_key_press(arcade.key.UP, 0)
        assert handled is False

    def test_key_press_escape(self, plugin: PauseMenuPlugin) -> None:
        """Test Escape key toggles menu or goes back."""
        # Show menu
        plugin.show()

        # In main menu, escape closes it
        handled = plugin.on_key_press(arcade.key.ESCAPE, 0)
        assert handled is True
        assert plugin.showing is False

        # In sub-menu, escape goes back
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS
        handled = plugin.on_key_press(arcade.key.ESCAPE, 0)
        assert handled is True
        assert plugin.showing is True
        assert plugin.menu_state == PauseMenuState.MAIN_MENU

    def test_navigation_main_menu(self, plugin: PauseMenuPlugin) -> None:
        """Test navigation in main menu."""
        plugin.show()
        # Assume options: Resume, New Game, Load, Save, Exit (5 options)
        num_options = len(PauseMenuOption)

        # Down
        plugin.selected_option = 0
        plugin.on_key_press(arcade.key.DOWN, 0)
        assert plugin.selected_option == 1

        # Wrap around down
        plugin.selected_option = num_options - 1
        plugin.on_key_press(arcade.key.DOWN, 0)
        assert plugin.selected_option == 0

        # Up
        plugin.selected_option = 1
        plugin.on_key_press(arcade.key.UP, 0)
        assert plugin.selected_option == 0

        # Wrap around up
        plugin.selected_option = 0
        plugin.on_key_press(arcade.key.UP, 0)
        assert plugin.selected_option == num_options - 1

    def test_navigation_sub_menus(self, plugin: PauseMenuPlugin) -> None:
        """Test navigation in sub menus (slots)."""
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS
        # Save slots: 1-3 (3 slots)
        num_slots = 3

        # Wrap around
        plugin.selected_option = 0
        plugin.on_key_press(arcade.key.UP, 0)
        assert plugin.selected_option == num_slots - 1

        plugin.on_key_press(arcade.key.DOWN, 0)
        assert plugin.selected_option == 0

    def test_execute_resume(self, plugin: PauseMenuPlugin) -> None:
        """Test executing Resume option."""
        plugin.show()
        # Resume is usually option 0 (PauseMenuOption.RESUME)
        plugin.selected_option = 0
        # Verify assumption
        assert PauseMenuOption(0) == PauseMenuOption.RESUME

        plugin.on_key_press(arcade.key.ENTER, 0)
        assert plugin.showing is False

    def test_execute_load_game_transition(self, plugin: PauseMenuPlugin) -> None:
        """Test entering Load Game menu."""
        plugin.show()
        # Find index for Load Game
        load_idx = list(PauseMenuOption).index(PauseMenuOption.LOAD_GAME)
        plugin.selected_option = load_idx

        plugin.on_key_press(arcade.key.ENTER, 0)

        assert plugin.menu_state == PauseMenuState.LOAD_SLOTS
        assert plugin.selected_option == 0

    def test_execute_save_slot(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test saving to a slot."""
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS
        plugin.selected_option = 0  # Maps to Slot 1

        # Mock save success
        mock_context.save_plugin.save_game.return_value = True

        plugin.on_key_press(arcade.key.ENTER, 0)

        mock_context.save_plugin.save_game.assert_called_with(slot=1)
        assert plugin.save_feedback_message == "Game Saved!"
        assert plugin.save_feedback_timer > 0

    def test_execute_new_game_confirmation(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test new game confirmation flow."""
        plugin.show()
        new_game_idx = list(PauseMenuOption).index(PauseMenuOption.NEW_GAME)
        plugin.selected_option = new_game_idx

        # Trigger confirmation
        plugin.on_key_press(arcade.key.ENTER, 0)
        assert plugin.menu_state == PauseMenuState.CONFIRMATION
        assert plugin.confirmation_action == "new_game"
        assert plugin.selected_option == 1  # Defaults to No

        # Select Yes (0)
        plugin.selected_option = 0
        plugin.on_key_press(arcade.key.ENTER, 0)

        mock_context.start_new_game.assert_called_once()
        assert plugin.showing is False

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")  # Patch Text class construction
    def test_draw_ui(
        self,
        mock_text_cls: MagicMock,
        mock_rect_outline: MagicMock,
        mock_rect_filled: MagicMock,
        plugin: PauseMenuPlugin,
    ) -> None:
        """Test drawing the UI."""
        plugin.show()

        # Mock Text instance behavior
        mock_text_instance = MagicMock()
        mock_text_cls.return_value = mock_text_instance

        plugin.on_draw_ui()

        # Verify overlay and box drawn
        assert mock_rect_filled.call_count >= 2  # Overlay + Box background
        assert mock_rect_outline.called

        # Verify text objects created and drawn
        # Title + options
        assert mock_text_cls.call_count > 0
        assert mock_text_instance.draw.called

    def test_draw_ui_hidden(self, plugin: PauseMenuPlugin) -> None:
        """Test nothing drawn when hidden."""
        plugin.hide()
        with patch("arcade.draw_lrbt_rectangle_filled") as mock_draw:
            plugin.on_draw_ui()
            mock_draw.assert_not_called()

    def test_update_timer(self, plugin: PauseMenuPlugin) -> None:
        """Test updating timers."""
        plugin.save_feedback_timer = 1.0
        plugin.save_feedback_message = "Saved"

        plugin.update(0.5)
        assert plugin.save_feedback_timer == 0.5
        assert plugin.save_feedback_message == "Saved"

        plugin.update(0.6)
        assert plugin.save_feedback_timer <= 0
        assert plugin.save_feedback_message is None

    @patch("arcade.close_window")
    def test_exit_game(self, mock_close: MagicMock, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test exiting the game."""
        plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        plugin.selected_option = exit_idx

        # Mock auto-save
        mock_context.save_plugin.auto_save.return_value = True

        plugin.on_key_press(arcade.key.ENTER, 0)

        mock_context.save_plugin.auto_save.assert_called_once()
        mock_close.assert_called_once()

    def test_cleanup(self, plugin: PauseMenuPlugin) -> None:
        """Test cleanup method."""
        plugin.show()
        assert plugin.showing is True

        plugin.cleanup()
        assert plugin.showing is False

    def test_navigation_load_slots(self, plugin: PauseMenuPlugin) -> None:
        """Test navigation in load slots menu."""
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS
        num_slots = 4  # Slots 0-3

        # Down
        plugin.selected_option = 0
        handled = plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True
        assert plugin.selected_option == 1

        # Wrap around down
        plugin.selected_option = num_slots - 1
        handled = plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True
        assert plugin.selected_option == 0

        # Up
        plugin.selected_option = 1
        handled = plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True
        assert plugin.selected_option == 0

        # Wrap around up
        plugin.selected_option = 0
        handled = plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True
        assert plugin.selected_option == num_slots - 1

    def test_execute_load_slot_with_save(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test loading from a slot with valid save data."""
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS
        plugin.selected_option = 1  # Slot 1

        # Mock save exists and load
        mock_save_data = {"map": "test_map", "position": [0, 0]}
        mock_context.save_plugin.save_exists.return_value = True
        mock_context.save_plugin.load_game.return_value = mock_save_data

        handled = plugin.on_key_press(arcade.key.ENTER, 0)

        assert handled is True
        mock_context.save_plugin.save_exists.assert_called_with(slot=1)
        mock_context.save_plugin.load_game.assert_called_with(slot=1)
        mock_context.load_game.assert_called_with(mock_save_data)
        assert plugin.showing is False

    def test_execute_load_slot_no_save(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test loading from an empty slot."""
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS
        plugin.selected_option = 2

        # Mock no save exists
        mock_context.save_plugin.save_exists.return_value = False

        handled = plugin.on_key_press(arcade.key.ENTER, 0)

        assert handled is True
        mock_context.save_plugin.save_exists.assert_called_with(slot=2)
        mock_context.save_plugin.load_game.assert_not_called()
        assert plugin.showing is True  # Still showing

    def test_execute_load_slot_failed_load(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test loading from a slot when load fails."""
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS
        plugin.selected_option = 0

        # Mock save exists but load fails
        mock_context.save_plugin.save_exists.return_value = True
        mock_context.save_plugin.load_game.return_value = None

        handled = plugin.on_key_press(arcade.key.ENTER, 0)

        assert handled is True
        mock_context.save_plugin.load_game.assert_called_with(slot=0)
        mock_context.load_game.assert_not_called()
        assert plugin.showing is True  # Still showing

    def test_execute_load_slot_no_context(self, plugin: PauseMenuPlugin) -> None:
        """Test loading when context is not available."""
        plugin.context = None
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS
        plugin.selected_option = 0

        plugin._execute_load_slot()
        # Should not crash, just log error

    def test_execute_save_slot_failed(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test saving to a slot when save fails."""
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS
        plugin.selected_option = 1  # Maps to Slot 2

        # Mock save failure
        mock_context.save_plugin.save_game.return_value = False

        plugin.on_key_press(arcade.key.ENTER, 0)

        mock_context.save_plugin.save_game.assert_called_with(slot=2)
        assert plugin.save_feedback_message is None
        assert plugin.menu_state == PauseMenuState.SAVE_SLOTS  # Still in save menu

    def test_execute_save_slot_no_context(self, plugin: PauseMenuPlugin) -> None:
        """Test saving when context is not available."""
        plugin.context = None
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS
        plugin.selected_option = 0

        plugin._execute_save_slot()
        # Should not crash, just log error

    def test_navigation_confirmation(self, plugin: PauseMenuPlugin) -> None:
        """Test navigation in confirmation overlay."""
        plugin.show()
        plugin.menu_state = PauseMenuState.CONFIRMATION
        num_options = 2  # Yes/No

        # Down
        plugin.selected_option = 0
        handled = plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True
        assert plugin.selected_option == 1

        # Wrap around down
        plugin.selected_option = num_options - 1
        handled = plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True
        assert plugin.selected_option == 0

        # Up
        plugin.selected_option = 1
        handled = plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True
        assert plugin.selected_option == 0

    def test_execute_confirmation_cancel(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test cancelling confirmation (selecting No)."""
        plugin.show()
        plugin.menu_state = PauseMenuState.CONFIRMATION
        plugin.confirmation_action = "new_game"
        plugin.selected_option = 1  # No

        handled = plugin.on_key_press(arcade.key.ENTER, 0)

        assert handled is True
        assert plugin.menu_state == PauseMenuState.MAIN_MENU
        assert plugin.selected_option == 0
        mock_context.start_new_game.assert_not_called()

    def test_key_press_consumes_all_input_when_showing(self, plugin: PauseMenuPlugin) -> None:
        """Test that all key presses are consumed when menu is showing."""
        plugin.show()
        # Try a random key that doesn't do anything
        handled = plugin.on_key_press(arcade.key.A, 0)
        assert handled is True

    def test_execute_save_game_transition(self, plugin: PauseMenuPlugin) -> None:
        """Test entering Save Game menu."""
        plugin.show()
        save_idx = list(PauseMenuOption).index(PauseMenuOption.SAVE_GAME)
        plugin.selected_option = save_idx

        plugin.on_key_press(arcade.key.ENTER, 0)

        assert plugin.menu_state == PauseMenuState.SAVE_SLOTS
        assert plugin.selected_option == 0

    @patch("arcade.close_window")
    def test_exit_game_auto_save_failed(
        self, mock_close: MagicMock, plugin: PauseMenuPlugin, mock_context: MagicMock
    ) -> None:
        """Test exiting when auto-save fails."""
        plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        plugin.selected_option = exit_idx

        # Mock auto-save failure
        mock_context.save_plugin.auto_save.return_value = False

        plugin.on_key_press(arcade.key.ENTER, 0)

        mock_context.save_plugin.auto_save.assert_called_once()
        mock_close.assert_called_once()  # Still exits

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_text_objects_load_slots(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test preparing text objects for load slots state."""
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS

        # Mock save info
        mock_context.save_plugin.get_save_info.side_effect = [
            {"map": "Map1", "date_string": "2024-01-01"},
            None,  # Slot 1 empty
            {"map": "Map3", "date_string": "2024-01-03"},
            None,  # Slot 3 empty
        ]

        plugin.on_draw_ui()

        # Verify get_save_info called for all slots
        assert mock_context.save_plugin.get_save_info.call_count == 4

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_text_objects_save_slots(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test preparing text objects for save slots state."""
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS

        # Mock save info
        mock_context.save_plugin.get_save_info.side_effect = [
            {"map": "Map1", "date_string": "2024-01-01"},
            None,  # Slot 2 empty
            {"map": "Map3", "date_string": "2024-01-03"},
        ]

        plugin.on_draw_ui()

        # Verify get_save_info called for slots 1-3
        assert mock_context.save_plugin.get_save_info.call_count == 3

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_text_objects_confirmation(self, plugin: PauseMenuPlugin) -> None:
        """Test preparing text objects for confirmation state."""
        plugin.show()
        plugin.menu_state = PauseMenuState.CONFIRMATION
        plugin.confirmation_message = "Are you sure?"

        plugin.on_draw_ui()

        # Text objects are created (we can't easily assert on them without accessing the mock)

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_text_objects_main_menu(self, plugin: PauseMenuPlugin) -> None:
        """Test preparing text objects for main menu state."""
        plugin.show()
        plugin.menu_state = PauseMenuState.MAIN_MENU

        plugin.on_draw_ui()

        # Text objects are created (we can't easily assert on them without accessing the mock)

    def test_draw_ui_no_context(self, plugin: PauseMenuPlugin) -> None:
        """Test drawing when context is not available."""
        plugin.context = None
        plugin.show()

        with patch("arcade.draw_lrbt_rectangle_filled") as mock_draw:
            plugin.on_draw_ui()
            mock_draw.assert_not_called()

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_load_slots(self, plugin: PauseMenuPlugin) -> None:
        """Test drawing load slots menu."""
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS

        plugin.on_draw_ui()

        # Verify drawing completes without error

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_save_slots(self, plugin: PauseMenuPlugin) -> None:
        """Test drawing save slots menu."""
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS

        plugin.on_draw_ui()

        # Verify drawing completes without error

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_confirmation(self, plugin: PauseMenuPlugin) -> None:
        """Test drawing confirmation overlay."""
        plugin.show()
        plugin.menu_state = PauseMenuState.CONFIRMATION
        plugin.confirmation_message = "Test message"

        plugin.on_draw_ui()

        # Verify drawing completes without error

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_with_feedback_message(self, plugin: PauseMenuPlugin) -> None:
        """Test drawing with save feedback message."""
        plugin.show()
        plugin.save_feedback_message = "Game Saved!"
        plugin.save_feedback_timer = 1.0

        plugin.on_draw_ui()

        # Verify drawing completes without error (feedback text should be shown)

    def test_update_timer_zero_or_negative(self, plugin: PauseMenuPlugin) -> None:
        """Test update with timer already at zero or negative."""
        # Timer already at 0
        plugin.save_feedback_timer = 0
        plugin.save_feedback_message = "Saved"
        plugin.update(0.1)
        # Message should remain since timer wasn't positive
        assert plugin.save_feedback_message == "Saved"

        # Timer negative
        plugin.save_feedback_timer = -0.5
        plugin.update(0.1)
        assert plugin.save_feedback_message == "Saved"

    def test_execute_confirmation_without_context(self, plugin: PauseMenuPlugin) -> None:
        """Test confirmation execution without context."""
        plugin.context = None
        plugin.show()
        plugin.menu_state = PauseMenuState.CONFIRMATION
        plugin.confirmation_action = "new_game"
        plugin.selected_option = 0  # Yes

        # Should not crash without context
        plugin._execute_confirmation()

    def test_execute_confirmation_unknown_action(self, plugin: PauseMenuPlugin) -> None:
        """Test confirmation with unknown action."""
        plugin.show()
        plugin.menu_state = PauseMenuState.CONFIRMATION
        plugin.confirmation_action = "unknown_action"
        plugin.selected_option = 0  # Yes

        # Should not crash with unknown action
        plugin._execute_confirmation()

    @patch("arcade.close_window")
    def test_exit_game_no_context(self, mock_close: MagicMock, plugin: PauseMenuPlugin) -> None:
        """Test exiting when context is not available."""
        plugin.context = None
        plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        plugin.selected_option = exit_idx

        plugin._execute_main_menu_option()

        # Should not crash
        mock_close.assert_not_called()

    @patch("arcade.close_window")
    def test_exit_game_no_window_attribute(self, mock_close: MagicMock, plugin: PauseMenuPlugin) -> None:
        """Test exiting when context has no window attribute."""
        # Create a context without window attribute
        context_without_window = MagicMock()
        context_without_window.save_plugin = MagicMock()
        context_without_window.save_plugin.auto_save.return_value = True
        del context_without_window.window  # Remove window attribute

        plugin.context = context_without_window
        plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        plugin.selected_option = exit_idx

        plugin.on_key_press(arcade.key.ENTER, 0)

        # Should not crash, and close_window should not be called
        mock_close.assert_not_called()

    def test_execute_load_slot_no_save_plugin(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test loading when save plugin is not available."""
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS
        plugin.selected_option = 0

        # Remove save plugin
        mock_context.save_plugin = None

        plugin._execute_load_slot()
        # Should not crash, just log error

    def test_execute_save_slot_no_save_plugin(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test saving when save plugin is not available."""
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS
        plugin.selected_option = 0

        # Remove save plugin
        mock_context.save_plugin = None

        plugin._execute_save_slot()
        # Should not crash, just log error

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_ui_no_window(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test drawing when context has no window."""
        plugin.context = mock_context
        plugin.context.window = None
        plugin.show()

        with patch("arcade.draw_lrbt_rectangle_filled") as mock_draw:
            plugin.on_draw_ui()
            mock_draw.assert_not_called()

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_load_slots_no_save_plugin(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test preparing load slots when save plugin is not available."""
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS

        # Remove save plugin
        mock_context.save_plugin = None

        plugin.on_draw_ui()
        # Should not crash

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_load_slots_no_context(self, plugin: PauseMenuPlugin) -> None:
        """Test preparing load slots when context is not available."""
        plugin.context = None
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS

        # Set up a mock window since we need it for drawing
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_context = MagicMock()
        mock_context.window = mock_window
        mock_context.save_plugin = None
        plugin.context = mock_context

        plugin.on_draw_ui()
        # Should not crash

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_save_slots_no_save_plugin(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test preparing save slots when save plugin is not available."""
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS

        # Remove save plugin
        mock_context.save_plugin = None

        plugin.on_draw_ui()
        # Should not crash

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_save_slots_no_context(self, plugin: PauseMenuPlugin) -> None:
        """Test preparing save slots when context is not available."""
        plugin.context = None
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS

        # Set up a mock window since we need it for drawing
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_context = MagicMock()
        mock_context.window = mock_window
        mock_context.save_plugin = None
        plugin.context = mock_context

        plugin.on_draw_ui()
        # Should not crash

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_without_feedback_message(self, plugin: PauseMenuPlugin) -> None:
        """Test drawing without save feedback message (coverage for branch where feedback is None)."""
        plugin.show()
        plugin.save_feedback_message = None
        plugin.save_feedback_timer = 0

        plugin.on_draw_ui()
        # Should draw without feedback text

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_with_different_menu_states(self, plugin: PauseMenuPlugin) -> None:
        """Test drawing in all different menu states for full branch coverage."""
        plugin.show()

        # Test MAIN_MENU state
        plugin.menu_state = PauseMenuState.MAIN_MENU
        plugin.on_draw_ui()

        # Test LOAD_SLOTS state
        plugin.menu_state = PauseMenuState.LOAD_SLOTS
        plugin.on_draw_ui()

        # Test SAVE_SLOTS state
        plugin.menu_state = PauseMenuState.SAVE_SLOTS
        plugin.on_draw_ui()

        # Test CONFIRMATION state
        plugin.menu_state = PauseMenuState.CONFIRMATION
        plugin.confirmation_message = "Test"
        plugin.on_draw_ui()

    def test_key_press_load_slots_all_keys(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test all key presses in load slots state for branch coverage."""
        plugin.show()
        plugin.menu_state = PauseMenuState.LOAD_SLOTS
        plugin.selected_option = 0

        # Test UP key
        handled = plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True

        # Test DOWN key
        handled = plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True

        # Test ENTER key (should trigger load slot execution)
        mock_context.save_plugin.save_exists.return_value = False
        handled = plugin.on_key_press(arcade.key.ENTER, 0)
        assert handled is True

        # Test other keys (should still be consumed)
        handled = plugin.on_key_press(arcade.key.A, 0)
        assert handled is True

    def test_key_press_save_slots_all_keys(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test all key presses in save slots state for branch coverage."""
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS
        plugin.selected_option = 0

        # Test UP key
        handled = plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True

        # Test DOWN key
        handled = plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True

        # Test ENTER key (should trigger save slot execution)
        mock_context.save_plugin.save_game.return_value = True
        handled = plugin.on_key_press(arcade.key.ENTER, 0)
        assert handled is True

        # Test other keys (should still be consumed)
        handled = plugin.on_key_press(arcade.key.B, 0)
        assert handled is True

    def test_key_press_confirmation_all_keys(self, plugin: PauseMenuPlugin, mock_context: MagicMock) -> None:
        """Test all key presses in confirmation state for branch coverage."""
        plugin.show()
        plugin.menu_state = PauseMenuState.CONFIRMATION
        plugin.confirmation_action = "new_game"
        plugin.selected_option = 1  # No

        # Test UP key
        handled = plugin.on_key_press(arcade.key.UP, 0)
        assert handled is True
        assert plugin.selected_option == 0

        # Test DOWN key
        handled = plugin.on_key_press(arcade.key.DOWN, 0)
        assert handled is True
        assert plugin.selected_option == 1

        # Test ENTER key (should execute confirmation)
        handled = plugin.on_key_press(arcade.key.ENTER, 0)
        assert handled is True

        # Test other keys (should still be consumed)
        plugin.menu_state = PauseMenuState.CONFIRMATION
        handled = plugin.on_key_press(arcade.key.C, 0)
        assert handled is True

    @patch("arcade.close_window")
    def test_exit_game_with_context_no_window(
        self, mock_close: MagicMock, plugin: PauseMenuPlugin, mock_context: MagicMock
    ) -> None:
        """Test exiting when context exists but has no window attribute."""
        plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        plugin.selected_option = exit_idx

        # Mock auto-save success
        mock_context.save_plugin.auto_save.return_value = True

        # Remove window attribute
        mock_ctx = MagicMock()
        mock_ctx.save_plugin = mock_context.save_plugin
        # Don't set window attribute at all
        if hasattr(mock_ctx, "window"):
            delattr(mock_ctx, "window")
        plugin.context = mock_ctx

        plugin.on_key_press(arcade.key.ENTER, 0)

        # close_window should not be called
        mock_close.assert_not_called()

    def test_key_press_save_slots_non_action_key(self, plugin: PauseMenuPlugin) -> None:
        """Test pressing a non-action key in save slots state (for branch 144->162)."""
        plugin.show()
        plugin.menu_state = PauseMenuState.SAVE_SLOTS
        plugin.selected_option = 0

        # Press a key that's not UP, DOWN, or ENTER
        # This should fall through to the final return True at line 162
        handled = plugin.on_key_press(arcade.key.SPACE, 0)
        assert handled is True

        # State should remain unchanged
        assert plugin.menu_state == PauseMenuState.SAVE_SLOTS
        assert plugin.selected_option == 0

    def test_key_press_confirmation_non_action_key(self, plugin: PauseMenuPlugin) -> None:
        """Test pressing a non-action key in confirmation state."""
        plugin.show()
        plugin.menu_state = PauseMenuState.CONFIRMATION
        plugin.confirmation_action = "new_game"
        plugin.selected_option = 1

        # Press a key that's not UP, DOWN, or ENTER
        # This should fall through to the final return True at line 162
        handled = plugin.on_key_press(arcade.key.SPACE, 0)
        assert handled is True

        # State should remain unchanged
        assert plugin.menu_state == PauseMenuState.CONFIRMATION
        assert plugin.selected_option == 1

    @patch("arcade.close_window")
    def test_exit_without_context(self, mock_close: MagicMock, plugin: PauseMenuPlugin) -> None:
        """Test exit option when context is None."""
        # Set context to None
        plugin.context = None
        plugin.show()
        exit_idx = list(PauseMenuOption).index(PauseMenuOption.EXIT)
        plugin.selected_option = exit_idx

        # Execute the exit option directly
        plugin._execute_main_menu_option()

        # close_window should not be called since there's no context
        mock_close.assert_not_called()

    def test_execute_main_menu_unknown_option(self, plugin: PauseMenuPlugin) -> None:
        """Test executing main menu with unknown option (tests else branch)."""
        plugin.show()

        # Create a fake enum value that's not in the if/elif chain
        # We need to mock the PauseMenuOption constructor to return a value
        # that doesn't match any of the handled cases
        fake_option = MagicMock()
        fake_option.__eq__ = MagicMock(return_value=False)  # Never equals any option

        with patch("pedre.plugins.pause_menu.plugin.PauseMenuOption", return_value=fake_option):
            # This should hit the else branch and log an error
            plugin._execute_main_menu_option()

        # Menu should still be showing (no action taken)
        assert plugin.showing is True

    def test_key_press_invalid_menu_state_fallthrough(self, plugin: PauseMenuPlugin) -> None:
        """Test key press with invalid menu state falls through to line 162 (branch 149->162)."""
        plugin.show()

        # Manually set an invalid state (bypassing enum type checking)
        # This simulates state corruption or an unexpected state value
        plugin.menu_state = "invalid_state"

        # Any key press should still be consumed and return True
        handled = plugin.on_key_press(arcade.key.ENTER, 0)
        assert handled is True

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_prepare_text_invalid_state_fallthrough(self, plugin: PauseMenuPlugin) -> None:
        """Test _prepare_text_objects with invalid state (branch 331->335)."""
        plugin.show()

        # Set an invalid menu state
        plugin.menu_state = "invalid_state"

        # Should not crash, will skip state-specific text preparation
        plugin.on_draw_ui()

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_invalid_state_fallthrough(self, plugin: PauseMenuPlugin) -> None:
        """Test on_draw_ui with invalid state (branch 740->744)."""
        plugin.show()

        # Set an invalid menu state after title is created
        plugin.menu_state = PauseMenuState.MAIN_MENU
        plugin.on_draw_ui()  # Create title_text first

        # Now set invalid state
        plugin.menu_state = "invalid_state"

        # Should still draw title but skip state-specific rendering
        plugin.on_draw_ui()

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_title_none(self, plugin: PauseMenuPlugin) -> None:
        """Test drawing when title_text is None (branch 730->734)."""
        plugin.show()

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
            plugin.on_draw_ui()

    @pytest.mark.usefixtures("mock_arcade_text", "mock_arcade_rect_filled", "mock_arcade_rect_outline")
    def test_draw_confirmation_message_text_none(self, plugin: PauseMenuPlugin) -> None:
        """Test drawing confirmation when confirmation_message_text is None (branch 765->769)."""
        plugin.show()
        plugin.menu_state = PauseMenuState.CONFIRMATION
        plugin.confirmation_message = "Test"

        # Mock Text to return None for confirmation_message_text
        call_count = [0]

        def mock_text_factory(*_args: object, **_kwargs: object) -> MagicMock | None:
            call_count[0] += 1
            # Return None for the confirmation message text (second call after title)
            if call_count[0] == 2:  # Confirmation message is created after title
                return None
            return MagicMock()

        with patch("arcade.Text", side_effect=mock_text_factory):
            plugin.on_draw_ui()

        # Should not crash when confirmation_message_text is None
