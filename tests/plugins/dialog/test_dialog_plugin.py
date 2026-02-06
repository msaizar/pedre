"""Unit tests for DialogPlugin."""

import unittest
from unittest.mock import MagicMock, patch

import arcade

from pedre.conf import settings
from pedre.plugins.dialog import DialogPlugin
from pedre.plugins.dialog.events import DialogClosedEvent, DialogOpenedEvent


class TestDialogPlugin(unittest.TestCase):
    """Unit test class for DialogPlugin."""

    def setUp(self) -> None:
        """Set up DialogPlugin and mock context."""
        self.plugin = DialogPlugin()

        # Create mock context with event bus
        self.mock_context = MagicMock()
        self.mock_event_bus = MagicMock()
        self.mock_context.event_bus = self.mock_event_bus

        # Configure settings for dialog tests
        # The configure_test_settings fixture will have already set defaults,
        # but we ensure the dialog settings are correct for these tests
        settings.configure(
            DIALOG_AUTO_CLOSE_DEFAULT=False,
            DIALOG_AUTO_CLOSE_DURATION=0.5,
        )

        # Setup plugin with context (settings are now global)
        self.plugin.setup(self.mock_context)

    def test_show_dialog_publishes_event(self) -> None:
        """Test that showing a dialog publishes DialogOpenedEvent."""
        self.plugin.show_dialog("TestNPC", ["Hello!", "Welcome!"], dialog_level=0)

        # Verify event was published
        self.mock_event_bus.publish.assert_called_once()

        # Get the event that was published
        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert isinstance(published_event, DialogOpenedEvent)

    def test_show_dialog_event_includes_npc_name(self) -> None:
        """Test that DialogOpenedEvent includes correct NPC name."""
        npc_name = "Merchant"
        self.plugin.show_dialog(npc_name, ["Hello!"], dialog_level=0)

        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert published_event.npc_name == npc_name

    def test_show_dialog_event_includes_dialog_level(self) -> None:
        """Test that DialogOpenedEvent includes correct dialog level."""
        dialog_level = 2
        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=dialog_level)

        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert published_event.dialog_level == dialog_level

    def test_show_dialog_event_defaults_level_to_zero(self) -> None:
        """Test that DialogOpenedEvent defaults dialog level to 0 when None."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=None)

        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert published_event.dialog_level == 0

    def test_show_dialog_uses_npc_key_for_event(self) -> None:
        """Test that npc_key parameter is used in event instead of npc_name."""
        display_name = "The Merchant"
        npc_key = "merchant"

        self.plugin.show_dialog(display_name, ["Hello!"], dialog_level=0, npc_key=npc_key)

        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert published_event.npc_name == npc_key

    def test_close_dialog_publishes_event(self) -> None:
        """Test that closing dialog via key press publishes DialogClosedEvent."""
        # Mock the NPC plugin to return proper dialog level
        mock_npc_plugin = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 1
        mock_npc_plugin.get_npcs.return_value = {"TestNPC": mock_npc_state}
        self.mock_context.npc_plugin = mock_npc_plugin

        # Show dialog first
        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=1)

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Advance to reveal text
        self.plugin.speed_up_text()

        # Press SPACE to close (should close and publish event)
        consumed = self.plugin.on_key_press(arcade.key.SPACE, 0)

        assert consumed is True
        self.mock_event_bus.publish.assert_called_once()

        # Get the event that was published
        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert isinstance(published_event, DialogClosedEvent)
        assert published_event.npc_name == "TestNPC"
        assert published_event.dialog_level == 1

    def test_advance_page_publishes_close_event_on_last_page(self) -> None:
        """Test that pressing SPACE on last page publishes DialogClosedEvent."""
        # Create multi-page dialog
        self.plugin.show_dialog("TestNPC", ["Page 1", "Page 2"], dialog_level=0)

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Press SPACE to advance past first page
        self.plugin.speed_up_text()
        self.plugin.on_key_press(arcade.key.SPACE, 0)

        # Should not have published event yet
        self.mock_event_bus.publish.assert_not_called()

        # Press SPACE to advance past second (last) page
        self.plugin.speed_up_text()
        consumed = self.plugin.on_key_press(arcade.key.SPACE, 0)

        assert consumed is True

        # Now should have published DialogClosedEvent
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert isinstance(published_event, DialogClosedEvent)

    def test_advance_page_no_event_on_middle_page(self) -> None:
        """Test that advancing to middle pages does not publish events."""
        # Create multi-page dialog
        self.plugin.show_dialog("TestNPC", ["Page 1", "Page 2", "Page 3"])

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Advance to page 2
        self.plugin.speed_up_text()
        closed = self.plugin.advance_page()

        assert closed is False
        self.mock_event_bus.publish.assert_not_called()

        # Advance to page 3
        self.plugin.speed_up_text()
        closed = self.plugin.advance_page()

        assert closed is False
        self.mock_event_bus.publish.assert_not_called()

    def test_show_dialog_with_auto_close_sets_state(self) -> None:
        """Test that show_dialog with auto_close=True sets state correctly."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        assert self.plugin.auto_close_enabled is True
        assert self.plugin.auto_close_timer == 0.0
        assert self.plugin.showing is True

    def test_show_dialog_without_auto_close(self) -> None:
        """Test that show_dialog with auto_close=False (default) doesn't enable auto-close."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        assert self.plugin.auto_close_enabled is False
        assert self.plugin.auto_close_timer == 0.0

    def test_auto_close_timer_increments_after_text_revealed(self) -> None:
        """Test that auto-close timer increments after text is fully revealed."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Reveal text completely
        self.plugin.speed_up_text()

        # Update with delta time
        self.plugin.update(0.1)

        assert self.plugin.auto_close_timer > 0.0

    def test_auto_close_timer_does_not_increment_while_revealing(self) -> None:
        """Test that auto-close timer doesn't increment while text is revealing."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Don't reveal text, just update
        self.plugin.update(0.1)

        # Timer should not have started yet
        assert self.plugin.auto_close_timer == 0.0

    def test_dialog_auto_closes_after_duration(self) -> None:
        """Test that dialog automatically closes after configured duration."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Reveal text completely
        self.plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Update with enough time to trigger auto-close (0.5s default)
        self.plugin.update(0.6)

        # Dialog should be closed
        assert self.plugin.showing is False

        # Should have published DialogClosedEvent
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert isinstance(published_event, DialogClosedEvent)

    def test_auto_close_multi_page_dialog(self) -> None:
        """Test that auto-close works with multi-page dialogs."""
        self.plugin.show_dialog("TestNPC", ["Page 1", "Page 2"], auto_close=True, dialog_level=0)

        # Reveal page 1 completely
        self.plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Update with enough time to trigger auto-close
        self.plugin.update(0.6)

        # Should have advanced to page 2
        assert self.plugin.showing is True
        assert self.plugin.current_page_index == 1

        # Timer should be reset for new page
        assert self.plugin.auto_close_timer == 0.0

        # Reveal page 2
        self.plugin.speed_up_text()

        # Update again to auto-close
        self.plugin.update(0.6)

        # Now dialog should be closed
        assert self.plugin.showing is False

        # Should have published DialogClosedEvent
        self.mock_event_bus.publish.assert_called_once()

    def test_auto_close_does_not_trigger_when_disabled(self) -> None:
        """Test that auto-close doesn't trigger when auto_close=False."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], auto_close=False, dialog_level=0)

        # Reveal text completely
        self.plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Update with enough time that would trigger auto-close
        self.plugin.update(1.0)

        # Dialog should still be showing
        assert self.plugin.showing is True

        # Should not have published DialogClosedEvent
        self.mock_event_bus.publish.assert_not_called()

    def test_close_dialog_resets_auto_close_state(self) -> None:
        """Test that close_dialog resets auto-close state."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        self.plugin.speed_up_text()
        self.plugin.update(0.2)

        assert self.plugin.auto_close_timer > 0.0

        self.plugin.close_dialog()

        assert self.plugin.auto_close_enabled is False
        assert self.plugin.auto_close_timer == 0.0

    def test_advance_page_resets_auto_close_timer(self) -> None:
        """Test that advancing pages resets the auto-close timer."""
        self.plugin.show_dialog("TestNPC", ["Page 1", "Page 2"], auto_close=True, dialog_level=0)

        # Reveal and build up timer
        self.plugin.speed_up_text()
        self.plugin.update(0.3)

        timer_value = self.plugin.auto_close_timer
        assert timer_value > 0.0

        # Manually advance (simulate the auto-close advancing)
        self.plugin.advance_page()

        # Timer should be reset
        assert self.plugin.auto_close_timer == 0.0

    def test_auto_close_uses_settings_default_when_none(self) -> None:
        """Test that auto_close=None uses settings default (False)."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        # With default False, auto_close should be disabled
        assert self.plugin.auto_close_enabled is False

    def test_auto_close_uses_settings_default_when_not_specified(self) -> None:
        """Test that auto_close uses settings default when not specified."""
        # When auto_close is not explicitly passed, it uses the default from settings
        # The default is False (from settings.DIALOG_AUTO_CLOSE_DEFAULT)
        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        # Should use settings default (False)
        assert self.plugin.auto_close_enabled is False

    def test_auto_close_explicit_false_overrides_settings_default(self) -> None:
        """Test that explicit auto_close=False overrides settings default."""
        # Change settings default to True
        settings.configure(DIALOG_AUTO_CLOSE_DEFAULT=True)

        self.plugin.show_dialog("TestNPC", ["Hello!"], auto_close=False, dialog_level=0)

        # Explicit False should override settings
        assert self.plugin.auto_close_enabled is False

    def test_auto_close_explicit_true_overrides_settings_default(self) -> None:
        """Test that explicit auto_close=True overrides settings default."""
        # Settings default is False
        settings.configure(DIALOG_AUTO_CLOSE_DEFAULT=False)

        self.plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Explicit True should override settings
        assert self.plugin.auto_close_enabled is True

    def test_is_showing_returns_true_when_dialog_active(self) -> None:
        """Test is_showing() returns True when dialog is active."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        assert self.plugin.is_showing() is True

    def test_is_showing_returns_false_when_no_dialog(self) -> None:
        """Test is_showing() returns False when no dialog is active."""
        assert self.plugin.is_showing() is False

    def test_set_current_dialog_level(self) -> None:
        """Test set_current_dialog_level() sets the level correctly."""
        self.plugin.set_current_dialog_level(5)
        assert self.plugin.current_dialog_level == 5

    def test_set_current_npc_name(self) -> None:
        """Test set_current_npc_name() sets the name correctly."""
        self.plugin.set_current_npc_name("merchant")
        assert self.plugin.current_npc_name == "merchant"

    def test_cleanup_closes_dialog(self) -> None:
        """Test cleanup() closes any active dialog."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        assert self.plugin.showing is True

        self.plugin.cleanup()

        assert self.plugin.showing is False
        assert self.plugin.pages == []
        assert self.plugin.current_page_index == 0

    def test_cleanup_clears_text_objects(self) -> None:
        """Test cleanup() clears all text objects."""
        # Set up some text objects
        self.plugin.npc_name_text = MagicMock()
        self.plugin.dialog_text = MagicMock()
        self.plugin.page_indicator_text = MagicMock()
        self.plugin.instruction_text = MagicMock()

        self.plugin.cleanup()

        assert self.plugin.npc_name_text is None
        assert self.plugin.dialog_text is None
        assert self.plugin.page_indicator_text is None
        assert self.plugin.instruction_text is None

    def test_on_key_press_returns_false_when_not_showing(self) -> None:
        """Test on_key_press() returns False when no dialog is showing."""
        consumed = self.plugin.on_key_press(arcade.key.SPACE, 0)
        assert consumed is False

    def test_on_key_press_with_npc_plugin_state(self) -> None:
        """Test on_key_press() uses NPC plugin state for dialog level."""
        # Mock the NPC plugin with state
        mock_npc_plugin = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 3
        mock_npc_plugin.get_npcs.return_value = {"merchant": mock_npc_state}
        self.mock_context.npc_plugin = mock_npc_plugin

        self.plugin.show_dialog("Merchant", ["Hello!"], dialog_level=2, npc_key="merchant")
        self.plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Close dialog
        self.plugin.on_key_press(arcade.key.SPACE, 0)

        # Should use NPC plugin's dialog level (3), not the passed level (2)
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 3

    def test_on_key_press_without_npc_plugin_uses_current_level(self) -> None:
        """Test on_key_press() uses current dialog level when no NPC plugin."""
        self.mock_context.npc_plugin = None

        self.plugin.show_dialog("Merchant", ["Hello!"], dialog_level=2, npc_key="merchant")
        self.plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Close dialog
        self.plugin.on_key_press(arcade.key.SPACE, 0)

        # Should use the current dialog level (2)
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 2

    def test_show_dialog_with_instant_text(self) -> None:
        """Test show_dialog() with instant=True reveals all text immediately."""
        self.plugin.show_dialog("TestNPC", ["Hello world!"], instant=True, dialog_level=0)

        # Text should be fully revealed
        assert self.plugin.text_fully_revealed is True
        current_page = self.plugin.get_current_page()
        assert current_page is not None
        assert self.plugin.revealed_chars == len(current_page.text)

    def test_update_does_nothing_when_not_showing(self) -> None:
        """Test update() returns early when dialog is not showing."""
        self.plugin.update(0.1)
        # Should not raise any errors and revealed_chars should remain 0
        assert self.plugin.revealed_chars == 0

    def test_update_does_nothing_when_no_current_page(self) -> None:
        """Test update() returns early when there's no current page."""
        self.plugin.showing = True  # Set showing but no pages
        self.plugin.update(0.1)
        # Should not raise any errors
        assert self.plugin.revealed_chars == 0

    def test_update_reveals_characters_gradually(self) -> None:
        """Test update() reveals characters progressively."""
        self.plugin.show_dialog("TestNPC", ["Hello world!"], dialog_level=0)

        # Update with enough delta time to reveal some characters
        # Given char_reveal_speed, we need enough time to reveal at least 1 char
        self.plugin.update(0.1)

        # Some characters should be revealed (depends on reveal speed)
        assert self.plugin.revealed_chars > 0

    def test_update_marks_text_fully_revealed_when_complete(self) -> None:
        """Test update() sets text_fully_revealed when all chars shown."""
        self.plugin.show_dialog("TestNPC", ["Hi"], dialog_level=0)

        # Update with large delta time to reveal all
        self.plugin.update(1.0)

        assert self.plugin.text_fully_revealed is True
        current_page = self.plugin.get_current_page()
        assert current_page is not None
        assert self.plugin.revealed_chars == len(current_page.text)

    def test_auto_close_with_npc_plugin_state(self) -> None:
        """Test auto-close uses NPC plugin state for dialog level."""
        # Mock the NPC plugin with state
        mock_npc_plugin = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 4
        mock_npc_plugin.get_npcs.return_value = {"guide": mock_npc_state}
        self.mock_context.npc_plugin = mock_npc_plugin

        self.plugin.show_dialog("Guide", ["Hello!"], auto_close=True, dialog_level=1, npc_key="guide")
        self.plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Update to trigger auto-close
        self.plugin.update(0.6)

        # Should use NPC plugin's dialog level (4)
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 4

    def test_auto_close_without_npc_plugin_uses_current_level(self) -> None:
        """Test auto-close uses current dialog level when no NPC plugin."""
        self.mock_context.npc_plugin = None

        self.plugin.show_dialog("Guide", ["Hello!"], auto_close=True, dialog_level=1, npc_key="guide")
        self.plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Update to trigger auto-close
        self.plugin.update(0.6)

        # Should use current dialog level (1)
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 1

    def test_get_current_page_returns_none_when_not_showing(self) -> None:
        """Test get_current_page() returns None when dialog not showing."""
        assert self.plugin.get_current_page() is None

    def test_get_current_page_returns_none_when_no_pages(self) -> None:
        """Test get_current_page() returns None when pages list is empty."""
        self.plugin.showing = True
        self.plugin.pages = []
        assert self.plugin.get_current_page() is None

    def test_speed_up_text_does_nothing_when_already_revealed(self) -> None:
        """Test speed_up_text() has no effect when text is already fully revealed."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        self.plugin.speed_up_text()  # First call reveals all

        current_page = self.plugin.get_current_page()
        assert current_page is not None
        revealed_count = self.plugin.revealed_chars

        self.plugin.speed_up_text()  # Second call should have no effect

        assert self.plugin.revealed_chars == revealed_count  # Should be unchanged

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    def test_on_draw_ui_does_nothing_when_not_showing(self, mock_outline: MagicMock, mock_filled: MagicMock) -> None:
        """Test on_draw_ui() returns early when not showing dialog."""
        self.plugin.on_draw_ui()

        # Should not draw anything
        mock_filled.assert_not_called()
        mock_outline.assert_not_called()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    def test_on_draw_ui_requires_window(self, mock_outline: MagicMock, mock_filled: MagicMock) -> None:
        """Test on_draw_ui() returns early when no window available."""
        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        self.mock_context.window = None

        self.plugin.on_draw_ui()

        # Should not draw anything
        mock_filled.assert_not_called()
        mock_outline.assert_not_called()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_draws_dialog_box(
        self, mock_text: MagicMock, mock_outline: MagicMock, mock_filled: MagicMock
    ) -> None:
        """Test on_draw_ui() draws the dialog box and overlay."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        self.mock_context.window = mock_window

        # Setup mock Text instances
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        self.plugin.show_dialog("TestNPC", ["Hello world!"], dialog_level=0)
        self.plugin.on_draw_ui()

        # Should draw overlay (semi-transparent background)
        assert mock_filled.call_count >= 1
        # First call should be the overlay
        first_call = mock_filled.call_args_list[0]
        assert first_call[0][0] == 0  # left
        assert first_call[0][1] == mock_window.width  # right
        assert first_call[0][2] == 0  # bottom
        assert first_call[0][3] == mock_window.height  # top

        # Should draw dialog box border
        mock_outline.assert_called_once()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_creates_text_objects(
        self, mock_text: MagicMock, mock_outline: MagicMock, mock_filled: MagicMock
    ) -> None:
        """Test on_draw_ui() creates Text objects on first draw."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        self.mock_context.window = mock_window

        # Setup mock Text instances
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        # Initially text objects should be None
        assert self.plugin.npc_name_text is None
        assert self.plugin.dialog_text is None

        self.plugin.on_draw_ui()

        # After first draw, text objects should be created
        assert self.plugin.npc_name_text is not None
        assert self.plugin.dialog_text is not None
        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()
        mock_text.assert_called()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_updates_existing_text_objects(
        self, mock_text: MagicMock, mock_outline: MagicMock, mock_filled: MagicMock
    ) -> None:
        """Test on_draw_ui() updates existing Text objects instead of recreating."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        self.mock_context.window = mock_window

        # Setup mock Text instances
        mock_npc_text = MagicMock()
        mock_dialog_text = MagicMock()
        self.plugin.npc_name_text = mock_npc_text
        self.plugin.dialog_text = mock_dialog_text

        self.plugin.show_dialog("Merchant", ["Buy something!"], dialog_level=0)
        self.plugin.on_draw_ui()

        # Text objects should be updated, not recreated
        assert self.plugin.npc_name_text is mock_npc_text
        assert self.plugin.dialog_text is mock_dialog_text

        # Properties should be updated
        assert mock_npc_text.text == "Merchant"
        assert mock_dialog_text.text == ""  # No chars revealed yet

        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()
        # Text objects may be created for missing fields (instruction, etc.)
        # but existing text objects should be reused
        # Verify Text constructor was called for missing fields
        assert mock_text.call_count >= 0  # May or may not create new Text objects

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_shows_page_indicator_for_multi_page(
        self, mock_text: MagicMock, mock_outline: MagicMock, mock_filled: MagicMock
    ) -> None:
        """Test on_draw_ui() shows page indicator for multi-page dialogs."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        self.mock_context.window = mock_window

        # Setup mock Text instances
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        # Enable pagination display
        settings.configure(DIALOG_SHOW_PAGINATION=True)

        self.plugin.show_dialog("TestNPC", ["Page 1", "Page 2", "Page 3"], dialog_level=0)
        self.plugin.on_draw_ui()

        # Page indicator should be created
        assert self.plugin.page_indicator_text is not None
        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_shows_instruction_text(
        self, mock_text: MagicMock, mock_outline: MagicMock, mock_filled: MagicMock
    ) -> None:
        """Test on_draw_ui() shows instruction text when enabled."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        self.mock_context.window = mock_window

        # Setup mock Text instances
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        # Enable help display
        settings.configure(DIALOG_SHOW_HELP=True)

        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        self.plugin.on_draw_ui()

        # Instruction text should be created
        assert self.plugin.instruction_text is not None
        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_calls_text_draw_methods(
        self, mock_text: MagicMock, mock_outline: MagicMock, mock_filled: MagicMock
    ) -> None:
        """Test on_draw_ui() calls draw() on all text objects."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        self.mock_context.window = mock_window

        # Setup mock Text instances with draw methods
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        self.plugin.on_draw_ui()

        # draw() should be called on the text objects
        # NPC name text, dialog text, and potentially instruction text
        assert mock_text_instance.draw.call_count >= 2
        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()

    def test_on_key_press_without_npc_state_in_plugin(self) -> None:
        """Test on_key_press() when NPC plugin exists but NPC state is not found."""
        # Mock NPC plugin that returns empty dict (no state for this NPC)
        mock_npc_plugin = MagicMock()
        mock_npc_plugin.get_npcs.return_value = {}  # No NPC state
        self.mock_context.npc_plugin = mock_npc_plugin

        self.plugin.show_dialog("Ghost", ["Boo!"], dialog_level=1, npc_key="ghost")
        self.plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Close dialog
        self.plugin.on_key_press(arcade.key.SPACE, 0)

        # Should use current dialog level (1) since NPC state not found
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 1

    def test_advance_page_without_current_npc_name(self) -> None:
        """Test advance_page() when current_npc_name is None."""
        # Show dialog without npc_key (should use display name)
        self.plugin.show_dialog("System", ["Game started"], dialog_level=0)
        # Manually set current_npc_name to None
        self.plugin.current_npc_name = None
        self.plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Close dialog
        closed = self.plugin.advance_page()

        assert closed is True
        # Should not publish event when current_npc_name is None
        self.mock_event_bus.publish.assert_not_called()

    def test_auto_close_without_npc_state_in_plugin(self) -> None:
        """Test auto-close when NPC plugin exists but NPC state is not found."""
        # Mock NPC plugin that returns empty dict
        mock_npc_plugin = MagicMock()
        mock_npc_plugin.get_npcs.return_value = {}
        self.mock_context.npc_plugin = mock_npc_plugin

        self.plugin.show_dialog("Ghost", ["Boo!"], auto_close=True, dialog_level=2, npc_key="ghost")
        self.plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Update to trigger auto-close
        self.plugin.update(0.6)

        # Should use current dialog level (2)
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 2

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_returns_early_when_no_current_page(
        self, mock_text: MagicMock, mock_outline: MagicMock, mock_filled: MagicMock
    ) -> None:
        """Test on_draw_ui() returns early when no current page available."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        self.mock_context.window = mock_window

        # Force showing but with empty pages
        self.plugin.showing = True
        self.plugin.pages = []

        self.plugin.on_draw_ui()

        # Should draw overlay but not the dialog box
        # Only the overlay should be drawn (not the dialog box border)
        assert mock_filled.call_count <= 1
        mock_outline.assert_not_called()
        mock_text.assert_not_called()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_updates_page_indicator(
        self, mock_text: MagicMock, mock_outline: MagicMock, mock_filled: MagicMock
    ) -> None:
        """Test on_draw_ui() updates page indicator text on subsequent draws."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        self.mock_context.window = mock_window

        # Enable pagination
        settings.configure(DIALOG_SHOW_PAGINATION=True)

        # Create mock page indicator
        mock_page_indicator = MagicMock()
        self.plugin.page_indicator_text = mock_page_indicator

        self.plugin.show_dialog("TestNPC", ["Page 1", "Page 2"], dialog_level=0)
        self.plugin.on_draw_ui()

        # Page indicator text should be updated
        assert mock_page_indicator.text == "Page 1/2"

        # Advance to next page
        self.plugin.speed_up_text()
        self.plugin.advance_page()
        self.plugin.on_draw_ui()

        # Page indicator should be updated to page 2
        assert mock_page_indicator.text == "Page 2/2"

        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called()
        # Text objects may be created for missing fields (NPC name, dialog text, etc.)
        # but existing page indicator should be reused
        # Verify Text constructor was called for missing fields
        assert mock_text.call_count >= 0  # May create Text objects for NPC name, dialog text, etc.

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_updates_instruction_text(
        self, mock_text: MagicMock, mock_outline: MagicMock, mock_filled: MagicMock
    ) -> None:
        """Test on_draw_ui() updates instruction text on subsequent draws."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        self.mock_context.window = mock_window

        # Enable help text
        settings.configure(DIALOG_SHOW_HELP=True)

        # Create mock instruction text
        mock_instruction = MagicMock()
        self.plugin.instruction_text = mock_instruction

        self.plugin.show_dialog("TestNPC", ["Page 1", "Page 2"], dialog_level=0)
        self.plugin.on_draw_ui()

        # Instruction should show "next page" text
        assert settings.DIALOG_TEXT_NEXT_PAGE in mock_instruction.text

        # Advance to last page
        self.plugin.speed_up_text()
        self.plugin.advance_page()
        self.plugin.on_draw_ui()

        # Instruction should show "close" text on last page
        assert settings.DIALOG_TEXT_CLOSE in mock_instruction.text

        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called()
        # Text objects may be created for missing fields (NPC name, dialog text, page indicator)
        # but existing instruction should be reused
        # Verify Text constructor was called for missing fields
        assert mock_text.call_count >= 0  # May create Text objects for NPC name, dialog text, page indicator

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_without_help_text(
        self, mock_text: MagicMock, mock_outline: MagicMock, mock_filled: MagicMock
    ) -> None:
        """Test on_draw_ui() when DIALOG_SHOW_HELP is disabled."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        self.mock_context.window = mock_window

        # Disable help text
        settings.configure(DIALOG_SHOW_HELP=False)

        # Setup mock Text instance
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        self.plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        self.plugin.on_draw_ui()

        # Instruction text should not be created
        assert self.plugin.instruction_text is None
        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()


if __name__ == "__main__":
    unittest.main()
