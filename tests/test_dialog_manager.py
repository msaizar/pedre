"""Unit tests for DialogManager."""

import unittest
from unittest.mock import MagicMock

import arcade

from pedre.systems.dialog.events import DialogClosedEvent, DialogOpenedEvent
from pedre.systems.dialog.manager import DialogManager


class TestDialogManager(unittest.TestCase):
    """Unit test class for DialogManager."""

    def setUp(self) -> None:
        """Set up DialogManager and mock context."""
        self.manager = DialogManager()

        # Create mock context with event bus
        self.mock_context = MagicMock()
        self.mock_event_bus = MagicMock()
        self.mock_context.event_bus = self.mock_event_bus

        # Create mock settings with dialog_auto_close_duration
        self.mock_settings = MagicMock()
        self.mock_settings.dialog_auto_close_default = False
        self.mock_settings.dialog_auto_close_duration = 0.5

        # Setup manager with mocks
        self.manager.setup(self.mock_context, self.mock_settings)

    def test_show_dialog_publishes_event(self) -> None:
        """Test that showing a dialog publishes DialogOpenedEvent."""
        self.manager.show_dialog("TestNPC", ["Hello!", "Welcome!"], dialog_level=0)

        # Verify event was published
        self.mock_event_bus.publish.assert_called_once()

        # Get the event that was published
        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert isinstance(published_event, DialogOpenedEvent)

    def test_show_dialog_event_includes_npc_name(self) -> None:
        """Test that DialogOpenedEvent includes correct NPC name."""
        npc_name = "Merchant"
        self.manager.show_dialog(npc_name, ["Hello!"], dialog_level=0)

        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert published_event.npc_name == npc_name

    def test_show_dialog_event_includes_dialog_level(self) -> None:
        """Test that DialogOpenedEvent includes correct dialog level."""
        dialog_level = 2
        self.manager.show_dialog("TestNPC", ["Hello!"], dialog_level=dialog_level)

        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert published_event.dialog_level == dialog_level

    def test_show_dialog_event_defaults_level_to_zero(self) -> None:
        """Test that DialogOpenedEvent defaults dialog level to 0 when None."""
        self.manager.show_dialog("TestNPC", ["Hello!"], dialog_level=None)

        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert published_event.dialog_level == 0

    def test_show_dialog_uses_npc_key_for_event(self) -> None:
        """Test that npc_key parameter is used in event instead of npc_name."""
        display_name = "The Merchant"
        npc_key = "merchant"

        self.manager.show_dialog(display_name, ["Hello!"], dialog_level=0, npc_key=npc_key)

        published_event = self.mock_event_bus.publish.call_args[0][0]

        assert published_event.npc_name == npc_key

    def test_close_dialog_publishes_event(self) -> None:
        """Test that closing dialog via key press publishes DialogClosedEvent."""
        # Mock the NPC manager to return proper dialog level
        mock_npc_manager = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 1
        mock_npc_manager.npcs = {"TestNPC": mock_npc_state}
        self.mock_context.get_system.return_value = mock_npc_manager

        # Show dialog first
        self.manager.show_dialog("TestNPC", ["Hello!"], dialog_level=1)

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Advance to reveal text
        self.manager.speed_up_text()

        # Press SPACE to close (should close and publish event)
        consumed = self.manager.on_key_press(arcade.key.SPACE, 0, self.mock_context)

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
        self.manager.show_dialog("TestNPC", ["Page 1", "Page 2"], dialog_level=0)

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Press SPACE to advance past first page
        self.manager.speed_up_text()
        self.manager.on_key_press(arcade.key.SPACE, 0, self.mock_context)

        # Should not have published event yet
        self.mock_event_bus.publish.assert_not_called()

        # Press SPACE to advance past second (last) page
        self.manager.speed_up_text()
        consumed = self.manager.on_key_press(arcade.key.SPACE, 0, self.mock_context)

        assert consumed is True

        # Now should have published DialogClosedEvent
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert isinstance(published_event, DialogClosedEvent)

    def test_advance_page_no_event_on_middle_page(self) -> None:
        """Test that advancing to middle pages does not publish events."""
        # Create multi-page dialog
        self.manager.show_dialog("TestNPC", ["Page 1", "Page 2", "Page 3"])

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Advance to page 2
        self.manager.speed_up_text()
        closed = self.manager.advance_page()

        assert closed is False
        self.mock_event_bus.publish.assert_not_called()

        # Advance to page 3
        self.manager.speed_up_text()
        closed = self.manager.advance_page()

        assert closed is False
        self.mock_event_bus.publish.assert_not_called()

    def test_no_event_without_event_bus(self) -> None:
        """Test that showing dialog without event_bus doesn't crash."""
        # Create manager without event bus
        manager_no_bus = DialogManager()
        mock_context_no_bus = MagicMock()
        mock_context_no_bus.event_bus = None

        manager_no_bus.setup(mock_context_no_bus, self.mock_settings)

        # Should not crash
        manager_no_bus.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        # Verify dialog is showing
        assert manager_no_bus.showing is True

    def test_show_dialog_with_auto_close_sets_state(self) -> None:
        """Test that show_dialog with auto_close=True sets state correctly."""
        self.manager.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        assert self.manager.auto_close_enabled is True
        assert self.manager.auto_close_timer == 0.0
        assert self.manager.showing is True

    def test_show_dialog_without_auto_close(self) -> None:
        """Test that show_dialog with auto_close=False (default) doesn't enable auto-close."""
        self.manager.show_dialog("TestNPC", ["Hello!"], dialog_level=0)

        assert self.manager.auto_close_enabled is False
        assert self.manager.auto_close_timer == 0.0

    def test_auto_close_timer_increments_after_text_revealed(self) -> None:
        """Test that auto-close timer increments after text is fully revealed."""
        self.manager.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Reveal text completely
        self.manager.speed_up_text()

        # Update with delta time
        self.manager.update(0.1, self.mock_context)

        assert self.manager.auto_close_timer > 0.0

    def test_auto_close_timer_does_not_increment_while_revealing(self) -> None:
        """Test that auto-close timer doesn't increment while text is revealing."""
        self.manager.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Don't reveal text, just update
        self.manager.update(0.1, self.mock_context)

        # Timer should not have started yet
        assert self.manager.auto_close_timer == 0.0

    def test_dialog_auto_closes_after_duration(self) -> None:
        """Test that dialog automatically closes after configured duration."""
        self.manager.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Reveal text completely
        self.manager.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Update with enough time to trigger auto-close (0.5s default)
        self.manager.update(0.6, self.mock_context)

        # Dialog should be closed
        assert self.manager.showing is False

        # Should have published DialogClosedEvent
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert isinstance(published_event, DialogClosedEvent)

    def test_auto_close_multi_page_dialog(self) -> None:
        """Test that auto-close works with multi-page dialogs."""
        self.manager.show_dialog("TestNPC", ["Page 1", "Page 2"], auto_close=True, dialog_level=0)

        # Reveal page 1 completely
        self.manager.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Update with enough time to trigger auto-close
        self.manager.update(0.6, self.mock_context)

        # Should have advanced to page 2
        assert self.manager.showing is True
        assert self.manager.current_page_index == 1

        # Timer should be reset for new page
        assert self.manager.auto_close_timer == 0.0

        # Reveal page 2
        self.manager.speed_up_text()

        # Update again to auto-close
        self.manager.update(0.6, self.mock_context)

        # Now dialog should be closed
        assert self.manager.showing is False

        # Should have published DialogClosedEvent
        self.mock_event_bus.publish.assert_called_once()

    def test_auto_close_does_not_trigger_when_disabled(self) -> None:
        """Test that auto-close doesn't trigger when auto_close=False."""
        self.manager.show_dialog("TestNPC", ["Hello!"], auto_close=False, dialog_level=0)

        # Reveal text completely
        self.manager.speed_up_text()

        # Reset mock to clear the DialogOpenedEvent call
        self.mock_event_bus.reset_mock()

        # Update with enough time that would trigger auto-close
        self.manager.update(1.0, self.mock_context)

        # Dialog should still be showing
        assert self.manager.showing is True

        # Should not have published DialogClosedEvent
        self.mock_event_bus.publish.assert_not_called()

    def test_close_dialog_resets_auto_close_state(self) -> None:
        """Test that close_dialog resets auto-close state."""
        self.manager.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        self.manager.speed_up_text()
        self.manager.update(0.2, self.mock_context)

        assert self.manager.auto_close_timer > 0.0

        self.manager.close_dialog()

        assert self.manager.auto_close_enabled is False
        assert self.manager.auto_close_timer == 0.0

    def test_advance_page_resets_auto_close_timer(self) -> None:
        """Test that advancing pages resets the auto-close timer."""
        self.manager.show_dialog("TestNPC", ["Page 1", "Page 2"], auto_close=True, dialog_level=0)

        # Reveal and build up timer
        self.manager.speed_up_text()
        self.manager.update(0.3, self.mock_context)

        timer_value = self.manager.auto_close_timer
        assert timer_value > 0.0

        # Manually advance (simulate the auto-close advancing)
        self.manager.advance_page()

        # Timer should be reset
        assert self.manager.auto_close_timer == 0.0

    def test_auto_close_uses_settings_default_when_none(self) -> None:
        """Test that auto_close=None uses settings default (False)."""
        self.manager.show_dialog("TestNPC", ["Hello!"], auto_close=None, dialog_level=0)

        # With default False, auto_close should be disabled
        assert self.manager.auto_close_enabled is False

    def test_auto_close_uses_settings_default_when_true(self) -> None:
        """Test that auto_close=None uses settings default when set to True."""
        # Change settings default to True
        self.mock_settings.dialog_auto_close_default = True

        self.manager.show_dialog("TestNPC", ["Hello!"], auto_close=None, dialog_level=0)

        # Should use settings default (True)
        assert self.manager.auto_close_enabled is True

    def test_auto_close_explicit_false_overrides_settings_default(self) -> None:
        """Test that explicit auto_close=False overrides settings default."""
        # Change settings default to True
        self.mock_settings.dialog_auto_close_default = True

        self.manager.show_dialog("TestNPC", ["Hello!"], auto_close=False, dialog_level=0)

        # Explicit False should override settings
        assert self.manager.auto_close_enabled is False

    def test_auto_close_explicit_true_overrides_settings_default(self) -> None:
        """Test that explicit auto_close=True overrides settings default."""
        # Settings default is False
        self.mock_settings.dialog_auto_close_default = False

        self.manager.show_dialog("TestNPC", ["Hello!"], auto_close=True, dialog_level=0)

        # Explicit True should override settings
        assert self.manager.auto_close_enabled is True


if __name__ == "__main__":
    unittest.main()
