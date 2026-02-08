"""Tests for EventRegistry."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

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

        @EventRegistry.register("simple_event")
        class TestEvent(SimpleEvent):
            pass

        # Verify event is registered
        event_class = EventRegistry.get("simple_event")
        assert event_class == TestEvent

        # Verify reverse lookup
        event_name = EventRegistry.get_name(TestEvent)
        assert event_name == "simple_event"

    def test_register_multiple_events(self) -> None:
        """Test registering multiple events."""

        @EventRegistry.register("event1")
        class Event1(SimpleEvent):
            pass

        @EventRegistry.register("event2")
        class Event2(AnotherEvent):
            pass

        # Verify both events are registered
        assert EventRegistry.get("event1") == Event1
        assert EventRegistry.get("event2") == Event2

        # Verify reverse lookups
        assert EventRegistry.get_name(Event1) == "event1"
        assert EventRegistry.get_name(Event2) == "event2"

    def test_register_returns_class(self) -> None:
        """Test that register decorator returns the original class."""

        @EventRegistry.register("return_test")
        class TestEvent(SimpleEvent):
            pass

        # The decorator should return the class unchanged
        assert TestEvent.__name__ == "TestEvent"
        # And the class should still be usable
        event = TestEvent(value="test")
        assert event.value == "test"

    def test_register_logs_debug_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that registration logs a debug message."""
        caplog.set_level("DEBUG")

        @EventRegistry.register("debug_event")
        class TestEvent(SimpleEvent):
            pass

        assert "Registered event: debug_event -> TestEvent" in caplog.text

    def test_register_duplicate_name_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that re-registering an event name logs a warning."""

        @EventRegistry.register("duplicate_event")
        class FirstEvent(SimpleEvent):
            pass

        # Clear caplog before second registration
        caplog.clear()

        @EventRegistry.register("duplicate_event")
        class SecondEvent(AnotherEvent):
            pass

        # Verify warning was logged
        assert "Event 'duplicate_event' is being re-registered" in caplog.text
        assert "was FirstEvent" in caplog.text
        assert "now SecondEvent" in caplog.text

        # Verify the second registration took precedence
        assert EventRegistry.get("duplicate_event") == SecondEvent

    def test_register_same_class_different_names(self) -> None:
        """Test registering the same class with different names."""

        @EventRegistry.register("name1")
        class TestEvent(SimpleEvent):
            pass

        # Register the same class with a different name
        EventRegistry.register("name2")(TestEvent)

        # Both names should resolve to the same class
        assert EventRegistry.get("name1") == TestEvent
        assert EventRegistry.get("name2") == TestEvent

        # Reverse lookup should return the most recent registration
        assert EventRegistry.get_name(TestEvent) == "name2"


class TestEventRegistryGet:
    """Tests for the get method."""

    def test_get_registered_event(self) -> None:
        """Test getting a registered event class."""

        @EventRegistry.register("test_event")
        class TestEvent(SimpleEvent):
            pass

        event_class = EventRegistry.get("test_event")
        assert event_class == TestEvent

    def test_get_unregistered_event(self) -> None:
        """Test getting an unregistered event name returns None."""
        event_class = EventRegistry.get("unknown_event")
        assert event_class is None

    def test_get_after_multiple_registrations(self) -> None:
        """Test getting events after registering multiple types."""

        @EventRegistry.register("event_a")
        class EventA(SimpleEvent):
            pass

        @EventRegistry.register("event_b")
        class EventB(AnotherEvent):
            pass

        @EventRegistry.register("event_c")
        class EventC(ThirdEvent):
            pass

        assert EventRegistry.get("event_a") == EventA
        assert EventRegistry.get("event_b") == EventB
        assert EventRegistry.get("event_c") == EventC


class TestEventRegistryGetName:
    """Tests for the get_name method."""

    def test_get_name_registered_event(self) -> None:
        """Test getting the name of a registered event class."""

        @EventRegistry.register("named_event")
        class TestEvent(SimpleEvent):
            pass

        name = EventRegistry.get_name(TestEvent)
        assert name == "named_event"

    def test_get_name_unregistered_event(self) -> None:
        """Test getting the name of an unregistered event class returns None."""

        class UnregisteredEvent(SimpleEvent):
            pass

        name = EventRegistry.get_name(UnregisteredEvent)
        assert name is None

    def test_get_name_after_re_registration(self) -> None:
        """Test that get_name returns the most recent name after re-registration."""

        @EventRegistry.register("first_name")
        class TestEvent(SimpleEvent):
            pass

        # Re-register with a different name
        EventRegistry.register("second_name")(TestEvent)

        # Should return the most recent name
        name = EventRegistry.get_name(TestEvent)
        assert name == "second_name"

    def test_get_name_multiple_events(self) -> None:
        """Test getting names for multiple registered events."""

        @EventRegistry.register("event_x")
        class EventX(SimpleEvent):
            pass

        @EventRegistry.register("event_y")
        class EventY(AnotherEvent):
            pass

        assert EventRegistry.get_name(EventX) == "event_x"
        assert EventRegistry.get_name(EventY) == "event_y"


class TestEventRegistryClear:
    """Tests for the clear method."""

    def test_clear_empty_registry(self) -> None:
        """Test that clear works on an already empty registry."""
        EventRegistry.clear()
        EventRegistry.clear()  # Should not raise
        assert EventRegistry.get("any_event") is None

    def test_clear_removes_all_events(self) -> None:
        """Test that clear removes all registered events."""

        @EventRegistry.register("event1")
        class Event1(SimpleEvent):
            pass

        @EventRegistry.register("event2")
        class Event2(AnotherEvent):
            pass

        @EventRegistry.register("event3")
        class Event3(ThirdEvent):
            pass

        # Verify events are registered
        assert EventRegistry.get("event1") is not None
        assert EventRegistry.get("event2") is not None
        assert EventRegistry.get("event3") is not None
        assert EventRegistry.get_name(Event1) is not None
        assert EventRegistry.get_name(Event2) is not None
        assert EventRegistry.get_name(Event3) is not None

        # Clear the registry
        EventRegistry.clear()

        # Verify everything is cleared
        assert EventRegistry.get("event1") is None
        assert EventRegistry.get("event2") is None
        assert EventRegistry.get("event3") is None
        assert EventRegistry.get_name(Event1) is None
        assert EventRegistry.get_name(Event2) is None
        assert EventRegistry.get_name(Event3) is None

    def test_clear_allows_re_registration(self) -> None:
        """Test that events can be re-registered after clear."""

        @EventRegistry.register("reusable_event")
        class TestEvent(SimpleEvent):
            pass

        assert EventRegistry.get("reusable_event") == TestEvent

        # Clear and re-register
        EventRegistry.clear()
        assert EventRegistry.get("reusable_event") is None

        @EventRegistry.register("reusable_event")
        class NewTestEvent(AnotherEvent):
            pass

        assert EventRegistry.get("reusable_event") == NewTestEvent


class TestEventRegistryIntrospection:
    """Tests for registry introspection methods."""

    def test_is_registered_returns_true_for_registered_event(self) -> None:
        """Test is_registered returns True for registered events."""

        @EventRegistry.register("test_event")
        class TestEvent(SimpleEvent):
            pass

        assert EventRegistry.is_registered("test_event") is True

    def test_is_registered_returns_false_for_unregistered_event(self) -> None:
        """Test is_registered returns False for unregistered events."""
        assert EventRegistry.is_registered("nonexistent_event") is False

    def test_get_all_types_returns_empty_list_initially(self) -> None:
        """Test get_all_types returns empty list when no events registered."""
        assert EventRegistry.get_all_types() == []

    def test_get_all_types_returns_registered_events(self) -> None:
        """Test get_all_types returns all registered event names."""

        @EventRegistry.register("event1")
        class Event1(SimpleEvent):
            pass

        @EventRegistry.register("event2")
        class Event2(AnotherEvent):
            pass

        types = EventRegistry.get_all_types()
        assert len(types) == 2
        assert "event1" in types
        assert "event2" in types

    def test_get_all_types_after_clear_returns_empty_list(self) -> None:
        """Test get_all_types returns empty list after clear."""

        @EventRegistry.register("temp_event")
        class TempEvent(SimpleEvent):
            pass

        assert len(EventRegistry.get_all_types()) == 1

        EventRegistry.clear()

        assert EventRegistry.get_all_types() == []


class TestEventRegistryIntegration:
    """Integration tests for EventRegistry."""

    def test_register_and_instantiate_event(self) -> None:
        """Test that registered events can be instantiated and used."""

        @EventRegistry.register("user_event")
        @dataclass
        class UserEvent(Event):
            username: str
            action: str

        # Get the class and instantiate it
        event_class = EventRegistry.get("user_event")
        assert event_class is not None

        event = event_class(username="test_user", action="login")
        assert isinstance(event, Event)
        assert event.username == "test_user"
        assert event.action == "login"

    def test_bidirectional_lookup(self) -> None:
        """Test bidirectional lookup between names and classes."""

        @EventRegistry.register("bidirectional_event")
        class TestEvent(SimpleEvent):
            pass

        # Forward lookup
        event_class = EventRegistry.get("bidirectional_event")
        assert event_class == TestEvent

        # Reverse lookup
        event_name = EventRegistry.get_name(TestEvent)
        assert event_name == "bidirectional_event"

        # Round trip
        event_name_retrieved = EventRegistry.get_name(TestEvent)
        assert event_name_retrieved is not None
        assert EventRegistry.get(event_name_retrieved) == TestEvent

    def test_multiple_decorators_on_same_class(self) -> None:
        """Test applying the register decorator multiple times to the same class."""

        @EventRegistry.register("name_a")
        @EventRegistry.register("name_b")
        class MultiNameEvent(SimpleEvent):
            pass

        # Both names should resolve to the same class
        assert EventRegistry.get("name_a") == MultiNameEvent
        assert EventRegistry.get("name_b") == MultiNameEvent

        # The most recent registration wins for reverse lookup
        assert EventRegistry.get_name(MultiNameEvent) == "name_a"
