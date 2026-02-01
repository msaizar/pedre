"""Unit tests for DialogPlugin."""

import unittest
from unittest.mock import MagicMock

import arcade
from pedre.plugins.dialog.plugin import DialogPlugin

from pedre.conf import settings
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


if __name__ == "__main__":
    unittest.main()
