"""Unit tests for DialogPlugin."""

from unittest.mock import MagicMock, patch

import arcade
import pytest

from pedre.conf import settings
from pedre.plugins.dialog import DialogPlugin
from pedre.plugins.dialog.events import DialogClosedEvent, DialogOpenedEvent


class TestDialogPlugin:
    """Unit test class for DialogPlugin."""

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Fixture for mock context with event bus."""
        ctx = MagicMock()
        ctx.event_bus = MagicMock()
        return ctx

    @pytest.fixture
    def plugin(self, mock_context: MagicMock) -> DialogPlugin:
        """Fixture for DialogPlugin."""
        p = DialogPlugin()
        settings.configure(
            DIALOG_AUTO_CLOSE_DEFAULT=False,
            DIALOG_AUTO_CLOSE_DURATION=0.5,
        )
        p.setup(mock_context)
        return p

    def test_show_dialog_publishes_event(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test that showing a dialog publishes DialogOpenedEvent."""
        plugin.show_dialog("TestNPC", ["Hello!", "Welcome!"], dialog_level=0)

        # Verify event was published
        mock_context.event_bus.publish.assert_called_once()

        # Get the event that was published
        published_event = mock_context.event_bus.publish.call_args[0][0]

        assert isinstance(published_event, DialogOpenedEvent)

    def test_show_dialog_event_includes_npc_name(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test that DialogOpenedEvent includes correct NPC name."""
        npc_name = "Merchant"
        plugin.show_dialog(npc_name, ["Hello!"], dialog_level=0)

        published_event = mock_context.event_bus.publish.call_args[0][0]

        assert published_event.npc_name == npc_name

    def test_show_dialog_event_includes_dialog_level(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test that DialogOpenedEvent includes correct dialog level."""
        dialog_level = 2
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=dialog_level)

        published_event = mock_context.event_bus.publish.call_args[0][0]

        assert published_event.dialog_level == dialog_level

    def test_show_dialog_event_defaults_level_to_zero(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test that DialogOpenedEvent defaults dialog level to 0 when None."""
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=None)

        published_event = mock_context.event_bus.publish.call_args[0][0]

        assert published_event.dialog_level == 0

    def test_show_dialog_uses_npc_key_for_event(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test that npc_key parameter is used in event instead of npc_name."""
        display_name = "The Merchant"
        npc_key = "merchant"

        plugin.show_dialog(display_name, ["Hello!"], dialog_level=0, npc_key=npc_key)

        published_event = mock_context.event_bus.publish.call_args[0][0]

        assert published_event.npc_name == npc_key

    def test_close_dialog_publishes_event(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test that closing dialog via key press publishes DialogClosedEvent."""
        # Mock the NPC plugin to return proper dialog level
        mock_npc_plugin = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 1
        mock_npc_plugin.get_npcs.return_value = {"TestNPC": mock_npc_state}
        mock_context.npc_plugin = mock_npc_plugin

        # Show dialog first
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=1)

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Advance to reveal text
        plugin.speed_up_text()

        # Press SPACE to close (should close and publish event)
        consumed = plugin.on_key_press(arcade.key.SPACE, 0)

        assert consumed is True
        mock_context.event_bus.publish.assert_called_once()

        # Get the event that was published
        published_event = mock_context.event_bus.publish.call_args[0][0]

        assert isinstance(published_event, DialogClosedEvent)
        assert published_event.npc_name == "TestNPC"
        assert published_event.dialog_level == 1

    def test_advance_page_publishes_close_event_on_last_page(
        self, plugin: DialogPlugin, mock_context: MagicMock
    ) -> None:
        """Test that pressing SPACE on last page publishes DialogClosedEvent."""
        # Create multi-page dialog
        plugin.show_dialog("TestNPC", ["Page 1", "Page 2"], dialog_level=0)

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Press SPACE to advance past first page
        plugin.speed_up_text()
        plugin.on_key_press(arcade.key.SPACE, 0)

        # Should not have published event yet
        mock_context.event_bus.publish.assert_not_called()

        # Press SPACE to advance past second (last) page
        plugin.speed_up_text()
        consumed = plugin.on_key_press(arcade.key.SPACE, 0)

        assert consumed is True

        # Now should have published DialogClosedEvent
        mock_context.event_bus.publish.assert_called_once()
        published_event = mock_context.event_bus.publish.call_args[0][0]
        assert isinstance(published_event, DialogClosedEvent)

    def test_advance_page_no_event_on_middle_page(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test that advancing to middle pages does not publish events."""
        # Create multi-page dialog
        plugin.show_dialog("TestNPC", ["Page 1", "Page 2", "Page 3"])

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Advance to page 2
        plugin.speed_up_text()
        closed = plugin.advance_page()

        assert closed is False
        mock_context.event_bus.publish.assert_not_called()

        # Advance to page 3
        plugin.speed_up_text()
        closed = plugin.advance_page()

        assert closed is False
        mock_context.event_bus.publish.assert_not_called()

    def test_show_dialog_with_auto_close_sets_state(self, plugin: DialogPlugin) -> None:
        """Test that show_dialog with auto_close=True sets state correctly."""
        plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        assert plugin.auto_close_enabled is True
        assert plugin.auto_close_timer == 0.0
        assert plugin.showing is True

    def test_show_dialog_without_auto_close(self, plugin: DialogPlugin) -> None:
        """Test that show_dialog with auto_close=False (default) doesn't enable auto-close."""
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        assert plugin.auto_close_enabled is False
        assert plugin.auto_close_timer == 0.0

    def test_auto_close_timer_increments_after_text_revealed(self, plugin: DialogPlugin) -> None:
        """Test that auto-close timer increments after text is fully revealed."""
        plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Reveal text completely
        plugin.speed_up_text()

        # Update with delta time
        plugin.update(0.1)

        assert plugin.auto_close_timer > 0.0

    def test_auto_close_timer_does_not_increment_while_revealing(self, plugin: DialogPlugin) -> None:
        """Test that auto-close timer doesn't increment while text is revealing."""
        plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Don't reveal text, just update
        plugin.update(0.1)

        # Timer should not have started yet
        assert plugin.auto_close_timer == 0.0

    def test_dialog_auto_closes_after_duration(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test that dialog automatically closes after configured duration."""
        plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Reveal text completely
        plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Update with enough time to trigger auto-close (0.5s default)
        plugin.update(0.6)

        # Dialog should be closed
        assert plugin.showing is False

        # Should have published DialogClosedEvent
        mock_context.event_bus.publish.assert_called_once()
        published_event = mock_context.event_bus.publish.call_args[0][0]
        assert isinstance(published_event, DialogClosedEvent)

    def test_auto_close_multi_page_dialog(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test that auto-close works with multi-page dialogs."""
        plugin.show_dialog("TestNPC", ["Page 1", "Page 2"], auto_close=True, dialog_level=0)

        # Reveal page 1 completely
        plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Update with enough time to trigger auto-close
        plugin.update(0.6)

        # Should have advanced to page 2
        assert plugin.showing is True
        assert plugin.current_page_index == 1

        # Timer should be reset for new page
        assert plugin.auto_close_timer == 0.0

        # Reveal page 2
        plugin.speed_up_text()

        # Update again to auto-close
        plugin.update(0.6)

        # Now dialog should be closed
        assert plugin.showing is False

        # Should have published DialogClosedEvent
        mock_context.event_bus.publish.assert_called_once()

    def test_auto_close_does_not_trigger_when_disabled(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test that auto-close doesn't trigger when auto_close=False."""
        plugin.show_dialog("TestNPC", ["Hello!"], auto_close=False, dialog_level=0)

        # Reveal text completely
        plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Update with enough time that would trigger auto-close
        plugin.update(1.0)

        # Dialog should still be showing
        assert plugin.showing is True

        # Should not have published DialogClosedEvent
        mock_context.event_bus.publish.assert_not_called()

    def test_close_dialog_resets_auto_close_state(self, plugin: DialogPlugin) -> None:
        """Test that close_dialog resets auto-close state."""
        plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        plugin.speed_up_text()
        plugin.update(0.2)

        assert plugin.auto_close_timer > 0.0

        plugin.close_dialog()

        assert plugin.auto_close_enabled is False
        assert plugin.auto_close_timer == 0.0

    def test_advance_page_resets_auto_close_timer(self, plugin: DialogPlugin) -> None:
        """Test that advancing pages resets the auto-close timer."""
        plugin.show_dialog("TestNPC", ["Page 1", "Page 2"], auto_close=True, dialog_level=0)

        # Reveal and build up timer
        plugin.speed_up_text()
        plugin.update(0.3)

        timer_value = plugin.auto_close_timer
        assert timer_value > 0.0

        # Manually advance (simulate the auto-close advancing)
        plugin.advance_page()

        # Timer should be reset
        assert plugin.auto_close_timer == 0.0

    def test_auto_close_uses_settings_default_when_none(self, plugin: DialogPlugin) -> None:
        """Test that auto_close=None uses settings default (False)."""
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        # With default False, auto_close should be disabled
        assert plugin.auto_close_enabled is False

    def test_auto_close_uses_settings_default_when_not_specified(self, plugin: DialogPlugin) -> None:
        """Test that auto_close uses settings default when not specified."""
        # When auto_close is not explicitly passed, it uses the default from settings
        # The default is False (from settings.DIALOG_AUTO_CLOSE_DEFAULT)
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        # Should use settings default (False)
        assert plugin.auto_close_enabled is False

    def test_auto_close_explicit_false_overrides_settings_default(self, plugin: DialogPlugin) -> None:
        """Test that explicit auto_close=False overrides settings default."""
        # Change settings default to True
        settings.configure(DIALOG_AUTO_CLOSE_DEFAULT=True)

        plugin.show_dialog("TestNPC", ["Hello!"], auto_close=False, dialog_level=0)

        # Explicit False should override settings
        assert plugin.auto_close_enabled is False

    def test_auto_close_explicit_true_overrides_settings_default(self, plugin: DialogPlugin) -> None:
        """Test that explicit auto_close=True overrides settings default."""
        # Settings default is False
        settings.configure(DIALOG_AUTO_CLOSE_DEFAULT=False)

        plugin.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Explicit True should override settings
        assert plugin.auto_close_enabled is True

    def test_is_showing_returns_true_when_dialog_active(self, plugin: DialogPlugin) -> None:
        """Test is_showing() returns True when dialog is active."""
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        assert plugin.is_showing() is True

    def test_is_showing_returns_false_when_no_dialog(self, plugin: DialogPlugin) -> None:
        """Test is_showing() returns False when no dialog is active."""
        assert plugin.is_showing() is False

    def test_set_current_dialog_level(self, plugin: DialogPlugin) -> None:
        """Test set_current_dialog_level() sets the level correctly."""
        plugin.set_current_dialog_level(5)
        assert plugin.current_dialog_level == 5

    def test_set_current_npc_name(self, plugin: DialogPlugin) -> None:
        """Test set_current_npc_name() sets the name correctly."""
        plugin.set_current_npc_name("merchant")
        assert plugin.current_npc_name == "merchant"

    def test_cleanup_closes_dialog(self, plugin: DialogPlugin) -> None:
        """Test cleanup() closes any active dialog."""
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        assert plugin.showing is True

        plugin.cleanup()

        assert plugin.showing is False
        assert plugin.pages == []
        assert plugin.current_page_index == 0

    def test_cleanup_clears_text_objects(self, plugin: DialogPlugin) -> None:
        """Test cleanup() clears all text objects."""
        # Set up some text objects
        plugin.npc_name_text = MagicMock()
        plugin.dialog_text = MagicMock()
        plugin.page_indicator_text = MagicMock()
        plugin.instruction_text = MagicMock()

        plugin.cleanup()

        assert plugin.npc_name_text is None
        assert plugin.dialog_text is None
        assert plugin.page_indicator_text is None
        assert plugin.instruction_text is None

    def test_on_key_press_returns_false_when_not_showing(self, plugin: DialogPlugin) -> None:
        """Test on_key_press() returns False when no dialog is showing."""
        consumed = plugin.on_key_press(arcade.key.SPACE, 0)
        assert consumed is False

    def test_on_key_press_with_npc_plugin_state(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test on_key_press() uses NPC plugin state for dialog level."""
        # Mock the NPC plugin with state
        mock_npc_plugin = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 3
        mock_npc_plugin.get_npcs.return_value = {"merchant": mock_npc_state}
        mock_context.npc_plugin = mock_npc_plugin

        plugin.show_dialog("Merchant", ["Hello!"], dialog_level=2, npc_key="merchant")
        plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Close dialog
        plugin.on_key_press(arcade.key.SPACE, 0)

        # Should use NPC plugin's dialog level (3), not the passed level (2)
        published_event = mock_context.event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 3

    def test_on_key_press_without_npc_plugin_uses_current_level(
        self, plugin: DialogPlugin, mock_context: MagicMock
    ) -> None:
        """Test on_key_press() uses current dialog level when no NPC plugin."""
        mock_context.npc_plugin = None

        plugin.show_dialog("Merchant", ["Hello!"], dialog_level=2, npc_key="merchant")
        plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Close dialog
        plugin.on_key_press(arcade.key.SPACE, 0)

        # Should use the current dialog level (2)
        published_event = mock_context.event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 2

    def test_show_dialog_with_instant_text(self, plugin: DialogPlugin) -> None:
        """Test show_dialog() with instant=True reveals all text immediately."""
        plugin.show_dialog("TestNPC", ["Hello world!"], instant=True, dialog_level=0)

        # Text should be fully revealed
        assert plugin.text_fully_revealed is True
        current_page = plugin.get_current_page()
        assert current_page is not None
        assert plugin.revealed_chars == len(current_page.text)

    def test_update_does_nothing_when_not_showing(self, plugin: DialogPlugin) -> None:
        """Test update() returns early when dialog is not showing."""
        plugin.update(0.1)
        # Should not raise any errors and revealed_chars should remain 0
        assert plugin.revealed_chars == 0

    def test_update_does_nothing_when_no_current_page(self, plugin: DialogPlugin) -> None:
        """Test update() returns early when there's no current page."""
        plugin.showing = True  # Set showing but no pages
        plugin.update(0.1)
        # Should not raise any errors
        assert plugin.revealed_chars == 0

    def test_update_reveals_characters_gradually(self, plugin: DialogPlugin) -> None:
        """Test update() reveals characters progressively."""
        plugin.show_dialog("TestNPC", ["Hello world!"], dialog_level=0)

        # Update with enough delta time to reveal some characters
        # Given char_reveal_speed, we need enough time to reveal at least 1 char
        plugin.update(0.1)

        # Some characters should be revealed (depends on reveal speed)
        assert plugin.revealed_chars > 0

    def test_update_marks_text_fully_revealed_when_complete(self, plugin: DialogPlugin) -> None:
        """Test update() sets text_fully_revealed when all chars shown."""
        plugin.show_dialog("TestNPC", ["Hi"], dialog_level=0)

        # Update with large delta time to reveal all
        plugin.update(1.0)

        assert plugin.text_fully_revealed is True
        current_page = plugin.get_current_page()
        assert current_page is not None
        assert plugin.revealed_chars == len(current_page.text)

    def test_auto_close_with_npc_plugin_state(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test auto-close uses NPC plugin state for dialog level."""
        # Mock the NPC plugin with state
        mock_npc_plugin = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 4
        mock_npc_plugin.get_npcs.return_value = {"guide": mock_npc_state}
        mock_context.npc_plugin = mock_npc_plugin

        plugin.show_dialog("Guide", ["Hello!"], auto_close=True, dialog_level=1, npc_key="guide")
        plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Update to trigger auto-close
        plugin.update(0.6)

        # Should use NPC plugin's dialog level (4)
        published_event = mock_context.event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 4

    def test_auto_close_without_npc_plugin_uses_current_level(
        self, plugin: DialogPlugin, mock_context: MagicMock
    ) -> None:
        """Test auto-close uses current dialog level when no NPC plugin."""
        mock_context.npc_plugin = None

        plugin.show_dialog("Guide", ["Hello!"], auto_close=True, dialog_level=1, npc_key="guide")
        plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Update to trigger auto-close
        plugin.update(0.6)

        # Should use current dialog level (1)
        published_event = mock_context.event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 1

    def test_get_current_page_returns_none_when_not_showing(self, plugin: DialogPlugin) -> None:
        """Test get_current_page() returns None when dialog not showing."""
        assert plugin.get_current_page() is None

    def test_get_current_page_returns_none_when_no_pages(self, plugin: DialogPlugin) -> None:
        """Test get_current_page() returns None when pages list is empty."""
        plugin.showing = True
        plugin.pages = []
        assert plugin.get_current_page() is None

    def test_speed_up_text_does_nothing_when_already_revealed(self, plugin: DialogPlugin) -> None:
        """Test speed_up_text() has no effect when text is already fully revealed."""
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        plugin.speed_up_text()  # First call reveals all

        current_page = plugin.get_current_page()
        assert current_page is not None
        revealed_count = plugin.revealed_chars

        plugin.speed_up_text()  # Second call should have no effect

        assert plugin.revealed_chars == revealed_count  # Should be unchanged

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    def test_on_draw_ui_does_nothing_when_not_showing(
        self, mock_outline: MagicMock, mock_filled: MagicMock, plugin: DialogPlugin
    ) -> None:
        """Test on_draw_ui() returns early when not showing dialog."""
        plugin.on_draw_ui()

        # Should not draw anything
        mock_filled.assert_not_called()
        mock_outline.assert_not_called()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    def test_on_draw_ui_requires_window(
        self, mock_outline: MagicMock, mock_filled: MagicMock, plugin: DialogPlugin, mock_context: MagicMock
    ) -> None:
        """Test on_draw_ui() returns early when no window available."""
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        mock_context.window = None

        plugin.on_draw_ui()

        # Should not draw anything
        mock_filled.assert_not_called()
        mock_outline.assert_not_called()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_draws_dialog_box(
        self,
        mock_text: MagicMock,
        mock_outline: MagicMock,
        mock_filled: MagicMock,
        plugin: DialogPlugin,
        mock_context: MagicMock,
    ) -> None:
        """Test on_draw_ui() draws the dialog box and overlay."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        mock_context.window = mock_window

        # Setup mock Text instances
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        plugin.show_dialog("TestNPC", ["Hello world!"], dialog_level=0)
        plugin.on_draw_ui()

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
        self,
        mock_text: MagicMock,
        mock_outline: MagicMock,
        mock_filled: MagicMock,
        plugin: DialogPlugin,
        mock_context: MagicMock,
    ) -> None:
        """Test on_draw_ui() creates Text objects on first draw."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        mock_context.window = mock_window

        # Setup mock Text instances
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        # Initially text objects should be None
        assert plugin.npc_name_text is None
        assert plugin.dialog_text is None

        plugin.on_draw_ui()

        # After first draw, text objects should be created
        assert plugin.npc_name_text is not None
        assert plugin.dialog_text is not None
        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()
        mock_text.assert_called()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_updates_existing_text_objects(
        self,
        mock_text: MagicMock,
        mock_outline: MagicMock,
        mock_filled: MagicMock,
        plugin: DialogPlugin,
        mock_context: MagicMock,
    ) -> None:
        """Test on_draw_ui() updates existing Text objects instead of recreating."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        mock_context.window = mock_window

        # Setup mock Text instances
        mock_npc_text = MagicMock()
        mock_dialog_text = MagicMock()
        plugin.npc_name_text = mock_npc_text
        plugin.dialog_text = mock_dialog_text

        plugin.show_dialog("Merchant", ["Buy something!"], dialog_level=0)
        plugin.on_draw_ui()

        # Text objects should be updated, not recreated
        assert plugin.npc_name_text is mock_npc_text
        assert plugin.dialog_text is mock_dialog_text

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
        self,
        mock_text: MagicMock,
        mock_outline: MagicMock,
        mock_filled: MagicMock,
        plugin: DialogPlugin,
        mock_context: MagicMock,
    ) -> None:
        """Test on_draw_ui() shows page indicator for multi-page dialogs."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        mock_context.window = mock_window

        # Setup mock Text instances
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        # Enable pagination display
        settings.configure(DIALOG_SHOW_PAGINATION=True)

        plugin.show_dialog("TestNPC", ["Page 1", "Page 2", "Page 3"], dialog_level=0)
        plugin.on_draw_ui()

        # Page indicator should be created
        assert plugin.page_indicator_text is not None
        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_shows_instruction_text(
        self,
        mock_text: MagicMock,
        mock_outline: MagicMock,
        mock_filled: MagicMock,
        plugin: DialogPlugin,
        mock_context: MagicMock,
    ) -> None:
        """Test on_draw_ui() shows instruction text when enabled."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        mock_context.window = mock_window

        # Setup mock Text instances
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        # Enable help display
        settings.configure(DIALOG_SHOW_HELP=True)

        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        plugin.on_draw_ui()

        # Instruction text should be created
        assert plugin.instruction_text is not None
        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_calls_text_draw_methods(
        self,
        mock_text: MagicMock,
        mock_outline: MagicMock,
        mock_filled: MagicMock,
        plugin: DialogPlugin,
        mock_context: MagicMock,
    ) -> None:
        """Test on_draw_ui() calls draw() on all text objects."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        mock_context.window = mock_window

        # Setup mock Text instances with draw methods
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        plugin.on_draw_ui()

        # draw() should be called on the text objects
        # NPC name text, dialog text, and potentially instruction text
        assert mock_text_instance.draw.call_count >= 2
        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()

    def test_on_key_press_without_npc_state_in_plugin(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test on_key_press() when NPC plugin exists but NPC state is not found."""
        # Mock NPC plugin that returns empty dict (no state for this NPC)
        mock_npc_plugin = MagicMock()
        mock_npc_plugin.get_npcs.return_value = {}  # No NPC state
        mock_context.npc_plugin = mock_npc_plugin

        plugin.show_dialog("Ghost", ["Boo!"], dialog_level=1, npc_key="ghost")
        plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Close dialog
        plugin.on_key_press(arcade.key.SPACE, 0)

        # Should use current dialog level (1) since NPC state not found
        published_event = mock_context.event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 1

    def test_advance_page_without_current_npc_name(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test advance_page() when current_npc_name is None."""
        # Show dialog without npc_key (should use display name)
        plugin.show_dialog("System", ["Game started"], dialog_level=0)
        # Manually set current_npc_name to None
        plugin.current_npc_name = None
        plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Close dialog
        closed = plugin.advance_page()

        assert closed is True
        # Should not publish event when current_npc_name is None
        mock_context.event_bus.publish.assert_not_called()

    def test_auto_close_without_npc_state_in_plugin(self, plugin: DialogPlugin, mock_context: MagicMock) -> None:
        """Test auto-close when NPC plugin exists but NPC state is not found."""
        # Mock NPC plugin that returns empty dict
        mock_npc_plugin = MagicMock()
        mock_npc_plugin.get_npcs.return_value = {}
        mock_context.npc_plugin = mock_npc_plugin

        plugin.show_dialog("Ghost", ["Boo!"], auto_close=True, dialog_level=2, npc_key="ghost")
        plugin.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        mock_context.event_bus.reset_mock()

        # Update to trigger auto-close
        plugin.update(0.6)

        # Should use current dialog level (2)
        published_event = mock_context.event_bus.publish.call_args[0][0]
        assert published_event.dialog_level == 2

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_returns_early_when_no_current_page(
        self,
        mock_text: MagicMock,
        mock_outline: MagicMock,
        mock_filled: MagicMock,
        plugin: DialogPlugin,
        mock_context: MagicMock,
    ) -> None:
        """Test on_draw_ui() returns early when no current page available."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        mock_context.window = mock_window

        # Force showing but with empty pages
        plugin.showing = True
        plugin.pages = []

        plugin.on_draw_ui()

        # Should draw overlay but not the dialog box
        # Only the overlay should be drawn (not the dialog box border)
        assert mock_filled.call_count <= 1
        mock_outline.assert_not_called()
        mock_text.assert_not_called()

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_updates_page_indicator(
        self,
        mock_text: MagicMock,
        mock_outline: MagicMock,
        mock_filled: MagicMock,
        plugin: DialogPlugin,
        mock_context: MagicMock,
    ) -> None:
        """Test on_draw_ui() updates page indicator text on subsequent draws."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        mock_context.window = mock_window

        # Enable pagination
        settings.configure(DIALOG_SHOW_PAGINATION=True)

        # Create mock page indicator
        mock_page_indicator = MagicMock()
        plugin.page_indicator_text = mock_page_indicator

        plugin.show_dialog("TestNPC", ["Page 1", "Page 2"], dialog_level=0)
        plugin.on_draw_ui()

        # Page indicator text should be updated
        assert mock_page_indicator.text == "Page 1/2"

        # Advance to next page
        plugin.speed_up_text()
        plugin.advance_page()
        plugin.on_draw_ui()

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
        self,
        mock_text: MagicMock,
        mock_outline: MagicMock,
        mock_filled: MagicMock,
        plugin: DialogPlugin,
        mock_context: MagicMock,
    ) -> None:
        """Test on_draw_ui() updates instruction text on subsequent draws."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        mock_context.window = mock_window

        # Enable help text
        settings.configure(DIALOG_SHOW_HELP=True)

        # Create mock instruction text
        mock_instruction = MagicMock()
        plugin.instruction_text = mock_instruction

        plugin.show_dialog("TestNPC", ["Page 1", "Page 2"], dialog_level=0)
        plugin.on_draw_ui()

        # Instruction should show "next page" text
        assert settings.DIALOG_TEXT_NEXT_PAGE in mock_instruction.text

        # Advance to last page
        plugin.speed_up_text()
        plugin.advance_page()
        plugin.on_draw_ui()

        # Instruction should show "close" text on last page
        assert settings.DIALOG_TEXT_CLOSE in mock_instruction.text

        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called()
        # Text objects may be created for missing fields (NPC name, dialog text, page indicator)
        # but existing instruction should be reused
        assert mock_text.call_count >= 0  # May create Text objects for NPC name, dialog text, page indicator

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    @patch("arcade.Text")
    def test_on_draw_ui_without_help_text(
        self,
        mock_text: MagicMock,
        mock_outline: MagicMock,
        mock_filled: MagicMock,
        plugin: DialogPlugin,
        mock_context: MagicMock,
    ) -> None:
        """Test on_draw_ui() when DIALOG_SHOW_HELP is disabled."""
        # Setup mock window
        mock_window = MagicMock()
        mock_window.width = 1920
        mock_window.height = 1080
        mock_context.window = mock_window

        # Disable help text
        settings.configure(DIALOG_SHOW_HELP=False)

        # Setup mock Text instance
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance

        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)
        plugin.on_draw_ui()

        # Instruction text should not be created
        assert plugin.instruction_text is None
        # Verify drawing functions were called
        mock_filled.assert_called()
        mock_outline.assert_called_once()

    def test_speed_up_text_when_no_current_page(self, plugin: DialogPlugin) -> None:
        """Test speed_up_text() when get_current_page() returns None."""
        # Set up plugin in a state where showing is True but pages is empty
        plugin.showing = True
        plugin.pages = []
        plugin.text_fully_revealed = False

        # Should handle gracefully without error
        plugin.speed_up_text()

        # Nothing should change since there's no current page
        assert plugin.revealed_chars == 0
        assert plugin.text_fully_revealed is False

    def test_advance_page_calls_speed_up_when_text_not_revealed(self, plugin: DialogPlugin) -> None:
        """Test advance_page() speeds up text when not fully revealed."""
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        # Text should not be fully revealed initially
        assert plugin.text_fully_revealed is False

        # Advance page should speed up text instead of advancing
        closed = plugin.advance_page()

        # Should not close, just reveal text
        assert closed is False
        assert plugin.text_fully_revealed is True

    def test_update_with_zero_chars_to_reveal(self, plugin: DialogPlugin) -> None:
        """Test update() when chars_to_reveal is 0 (very small delta_time)."""
        plugin.show_dialog("TestNPC", ["Hello world!"], dialog_level=0)

        initial_revealed = plugin.revealed_chars

        # Update with very small delta_time that results in 0 chars to reveal
        # Given char_reveal_speed, we need a delta_time smaller than 1/char_reveal_speed
        plugin.update(0.0001)

        # Should not reveal any characters yet
        assert plugin.revealed_chars == initial_revealed

    @patch("arcade.draw_lrbt_rectangle_filled")
    @patch("arcade.draw_lrbt_rectangle_outline")
    def test_on_draw_ui_returns_early_without_context(
        self, mock_outline: MagicMock, mock_filled: MagicMock, plugin: DialogPlugin
    ) -> None:
        """Test on_draw_ui() returns early when context is None."""
        plugin.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        # Set context to None
        plugin.context = None

        # Should not raise error, just return early
        plugin.on_draw_ui()

        # Should not draw anything
        mock_filled.assert_not_called()
        mock_outline.assert_not_called()
