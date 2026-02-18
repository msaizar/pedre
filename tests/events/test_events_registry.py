"""Tests for EventRegistry."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

import pytest

from pedre.events import Event
from pedre.events.registry import EventRegistry

if TYPE_CHECKING:
    from collections.abc import Generator


@dataclass
class SimpleEvent(Event):
    """Simple test event."""

    value: str


@dataclass
class AnotherEvent(Event):
    """Another test event."""

    count: int


@dataclass
class ThirdEvent(Event):
    """Third test event."""

    flag: bool


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None]:
    """Clear the registry before and after each test."""
    EventRegistry.clear()
    yield
    EventRegistry.clear()


class TestEventRegistryRegister:
    """Tests for the register decorator."""

    def test_register_event(self) -> None:
        """Test registering a simple event."""

        @EventRegistry.register
        class TestEvent(SimpleEvent):
            name: ClassVar[str] = "simple_event"

        # Verify event is registered
        event_class = EventRegistry.get("simple_event")
        assert event_class == TestEvent

    def test_register_multiple_events(self) -> None:
        """Test registering multiple events."""

        @EventRegistry.register
        class Event1(SimpleEvent):
            name: ClassVar[str] = "event1"

        @EventRegistry.register
        class Event2(AnotherEvent):
            name: ClassVar[str] = "event2"

        # Verify both events are registered
        assert EventRegistry.get("event1") == Event1
        assert EventRegistry.get("event2") == Event2

    def test_register_returns_class(self) -> None:
        """Test that register decorator returns the original class."""

        @EventRegistry.register
        class TestEvent(SimpleEvent):
            name: ClassVar[str] = "return_test"

        # The decorator should return the class unchanged
        assert TestEvent.__name__ == "TestEvent"
        # And the class should still be usable
        event = TestEvent(value="test")
        assert event.value == "test"

    def test_register_logs_debug_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that registration logs a debug message."""
        caplog.set_level("DEBUG")

        @EventRegistry.register
        class TestEvent(SimpleEvent):
            name: ClassVar[str] = "debug_event"

        assert "Registered event: debug_event" in caplog.text


class TestEventRegistryGet:
    """Tests for the get method."""

    def test_get_registered_event(self) -> None:
        """Test getting a registered event class."""

        @EventRegistry.register
        class TestEvent(SimpleEvent):
            name: ClassVar[str] = "test_event"

        event_class = EventRegistry.get("test_event")
        assert event_class == TestEvent

    def test_get_unregistered_event(self) -> None:
        """Test getting an unregistered event name returns None."""
        event_class = EventRegistry.get("unknown_event")
        assert event_class is None

    def test_get_after_multiple_registrations(self) -> None:
        """Test getting events after registering multiple types."""

        @EventRegistry.register
        class EventA(SimpleEvent):
            name: ClassVar[str] = "event_a"

        @EventRegistry.register
        class EventB(AnotherEvent):
            name: ClassVar[str] = "event_b"

        @EventRegistry.register
        class EventC(ThirdEvent):
            name: ClassVar[str] = "event_c"

        assert EventRegistry.get("event_a") == EventA
        assert EventRegistry.get("event_b") == EventB
        assert EventRegistry.get("event_c") == EventC


class TestEventRegistryClear:
    """Tests for the clear method."""

    def test_clear_empty_registry(self) -> None:
        """Test that clear works on an already empty registry."""
        EventRegistry.clear()
        EventRegistry.clear()  # Should not raise
        assert EventRegistry.get("any_event") is None

    def test_clear_removes_all_events(self) -> None:
        """Test that clear removes all registered events."""

        @EventRegistry.register
        class Event1(SimpleEvent):
            name: ClassVar[str] = "event1"

        @EventRegistry.register
        class Event2(AnotherEvent):
            name: ClassVar[str] = "event2"

        @EventRegistry.register
        class Event3(ThirdEvent):
            name: ClassVar[str] = "event3"

        # Verify events are registered
        assert EventRegistry.get("event1") is not None
        assert EventRegistry.get("event2") is not None
        assert EventRegistry.get("event3") is not None

        # Clear the registry
        EventRegistry.clear()

        # Verify everything is cleared
        assert EventRegistry.get("event1") is None
        assert EventRegistry.get("event2") is None
        assert EventRegistry.get("event3") is None

    def test_clear_allows_re_registration(self) -> None:
        """Test that events can be re-registered after clear."""

        @EventRegistry.register
        class TestEvent(SimpleEvent):
            name: ClassVar[str] = "reusable_event"

        assert EventRegistry.get("reusable_event") == TestEvent

        # Clear and re-register
        EventRegistry.clear()
        assert EventRegistry.get("reusable_event") is None

        @EventRegistry.register
        class NewTestEvent(AnotherEvent):
            name: ClassVar[str] = "reusable_event"

        assert EventRegistry.get("reusable_event") == NewTestEvent


class TestEventRegistryIntrospection:
    """Tests for registry introspection methods."""

    def test_is_registered_returns_true_for_registered_event(self) -> None:
        """Test is_registered returns True for registered events."""

        @EventRegistry.register
        class TestEvent(SimpleEvent):
            name: ClassVar[str] = "test_event"

        assert EventRegistry.is_registered("test_event") is True

    def test_is_registered_returns_false_for_unregistered_event(self) -> None:
        """Test is_registered returns False for unregistered events."""
        assert EventRegistry.is_registered("nonexistent_event") is False

    def test_get_all_types_returns_empty_list_initially(self) -> None:
        """Test get_all_types returns empty list when no events registered."""
        assert EventRegistry.get_all_names() == []

    def test_get_all_types_returns_registered_events(self) -> None:
        """Test get_all_types returns all registered event names."""

        @EventRegistry.register
        class Event1(SimpleEvent):
            name: ClassVar[str] = "event1"

        @EventRegistry.register
        class Event2(AnotherEvent):
            name: ClassVar[str] = "event2"

        types = EventRegistry.get_all_names()
        assert len(types) == 2
        assert "event1" in types
        assert "event2" in types

    def test_get_all_types_after_clear_returns_empty_list(self) -> None:
        """Test get_all_types returns empty list after clear."""

        @EventRegistry.register
        class TempEvent(SimpleEvent):
            name: ClassVar[str] = "temp_event"

        assert len(EventRegistry.get_all_names()) == 1

        EventRegistry.clear()

        assert EventRegistry.get_all_names() == []
