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

        # Create mock settings
        self.mock_settings = MagicMock()

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


if __name__ == "__main__":
    unittest.main()
