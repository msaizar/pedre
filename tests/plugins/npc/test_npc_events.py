"""Unit tests for NPC events in src/pedre/plugins/npc/events.py."""

import unittest
from dataclasses import is_dataclass

from pedre.plugins.npc.events import (
    NPCAppearCompleteEvent,
    NPCDisappearCompleteEvent,
    NPCInteractedEvent,
    NPCMovementCompleteEvent,
)


class TestNPCInteractedEvent(unittest.TestCase):
    """Test suite for NPCInteractedEvent."""

    def test_event_creation(self) -> None:
        """Test creating an NPCInteractedEvent."""
        event = NPCInteractedEvent(npc_name="martin", dialog_level=2)

        assert event.npc_name == "martin"
        assert event.dialog_level == 2

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct data."""
        event = NPCInteractedEvent(npc_name="guard", dialog_level=0)

        data = event.get_script_data()

        assert data == {"npc": "guard", "dialog_level": 0}

    def test_event_with_different_dialog_levels(self) -> None:
        """Test event with various dialog levels."""
        event_level_0 = NPCInteractedEvent(npc_name="merchant", dialog_level=0)
        event_level_5 = NPCInteractedEvent(npc_name="merchant", dialog_level=5)

        assert event_level_0.get_script_data() == {"npc": "merchant", "dialog_level": 0}
        assert event_level_5.get_script_data() == {"npc": "merchant", "dialog_level": 5}


class TestNPCMovementCompleteEvent(unittest.TestCase):
    """Test suite for NPCMovementCompleteEvent."""

    def test_event_creation(self) -> None:
        """Test creating an NPCMovementCompleteEvent."""
        event = NPCMovementCompleteEvent(npc_name="walker")

        assert event.npc_name == "walker"

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct data."""
        event = NPCMovementCompleteEvent(npc_name="patrol_guard")

        data = event.get_script_data()

        assert data == {"npc": "patrol_guard"}

    def test_multiple_events_with_different_npcs(self) -> None:
        """Test creating multiple events for different NPCs."""
        event1 = NPCMovementCompleteEvent(npc_name="npc1")
        event2 = NPCMovementCompleteEvent(npc_name="npc2")

        assert event1.get_script_data() == {"npc": "npc1"}
        assert event2.get_script_data() == {"npc": "npc2"}


class TestNPCAppearCompleteEvent(unittest.TestCase):
    """Test suite for NPCAppearCompleteEvent."""

    def test_event_creation(self) -> None:
        """Test creating an NPCAppearCompleteEvent."""
        event = NPCAppearCompleteEvent(npc_name="spirit")

        assert event.npc_name == "spirit"

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct data."""
        event = NPCAppearCompleteEvent(npc_name="ghost")

        data = event.get_script_data()

        assert data == {"npc": "ghost"}

    def test_event_for_animated_npc(self) -> None:
        """Test event for an animated NPC."""
        event = NPCAppearCompleteEvent(npc_name="animated_sprite")

        assert event.npc_name == "animated_sprite"
        assert event.get_script_data() == {"npc": "animated_sprite"}


class TestNPCDisappearCompleteEvent(unittest.TestCase):
    """Test suite for NPCDisappearCompleteEvent."""

    def test_event_creation(self) -> None:
        """Test creating an NPCDisappearCompleteEvent."""
        event = NPCDisappearCompleteEvent(npc_name="vanishing_npc")

        assert event.npc_name == "vanishing_npc"

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct data."""
        event = NPCDisappearCompleteEvent(npc_name="disappearing_guard")

        data = event.get_script_data()

        assert data == {"npc": "disappearing_guard"}

    def test_event_after_animation(self) -> None:
        """Test event creation after disappear animation completes."""
        event = NPCDisappearCompleteEvent(npc_name="fading_enemy")

        assert event.npc_name == "fading_enemy"
        assert event.get_script_data() == {"npc": "fading_enemy"}


class TestNPCEventsIntegration(unittest.TestCase):
    """Integration tests for all NPC events."""

    def test_all_events_have_get_script_data(self) -> None:
        """Test that all events implement get_script_data method."""
        events = [
            NPCInteractedEvent(npc_name="test", dialog_level=0),
            NPCMovementCompleteEvent(npc_name="test"),
            NPCAppearCompleteEvent(npc_name="test"),
            NPCDisappearCompleteEvent(npc_name="test"),
        ]

        for event in events:
            # Should not raise an error
            data = event.get_script_data()
            # All should return a dict with at least "npc" key
            assert isinstance(data, dict)
            assert "npc" in data

    def test_events_are_dataclasses(self) -> None:
        """Test that all event classes are dataclasses."""
        event_classes = [
            NPCInteractedEvent,
            NPCMovementCompleteEvent,
            NPCAppearCompleteEvent,
            NPCDisappearCompleteEvent,
        ]

        for event_class in event_classes:
            assert is_dataclass(event_class)

    def test_npc_interacted_event_has_additional_field(self) -> None:
        """Test that NPCInteractedEvent has dialog_level in addition to npc_name."""
        event = NPCInteractedEvent(npc_name="test", dialog_level=3)
        data = event.get_script_data()

        # NPCInteractedEvent should have both npc and dialog_level
        assert "npc" in data
        assert "dialog_level" in data
        assert data["dialog_level"] == 3

    def test_other_events_only_have_npc_field(self) -> None:
        """Test that other events only have npc_name field."""
        events = [
            NPCMovementCompleteEvent(npc_name="test"),
            NPCAppearCompleteEvent(npc_name="test"),
            NPCDisappearCompleteEvent(npc_name="test"),
        ]

        for event in events:
            data = event.get_script_data()
            # Should only have "npc" key
            assert list(data.keys()) == ["npc"]


if __name__ == "__main__":
    unittest.main()
