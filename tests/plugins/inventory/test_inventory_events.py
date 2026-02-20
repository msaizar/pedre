"""Unit tests for inventory events in src/pedre/plugins/inventory/events.py."""

from pedre.plugins.inventory.events import (
    InventoryClosedEvent,
    ItemAcquiredEvent,
    ItemAcquisitionFailedEvent,
    ItemConsumedEvent,
)
from pedre.types import EntityReference


class TestInventoryClosedEvent:
    """Test suite for InventoryClosedEvent."""

    def test_initialization(self) -> None:
        """Test event initialization with attributes."""
        event = InventoryClosedEvent(has_been_accessed=True)

        assert event.has_been_accessed is True

    def test_initialization_false(self) -> None:
        """Test event initialization with False value."""
        event = InventoryClosedEvent(has_been_accessed=False)

        assert event.has_been_accessed is False

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct data."""
        event = InventoryClosedEvent(has_been_accessed=True)

        script_data = event.get_script_data()

        assert "inventory_accessed" in script_data
        assert script_data["inventory_accessed"] is True

    def test_get_script_data_false(self) -> None:
        """Test get_script_data with False value."""
        event = InventoryClosedEvent(has_been_accessed=False)

        script_data = event.get_script_data()

        assert script_data["inventory_accessed"] is False


class TestItemAcquiredEvent:
    """Test suite for ItemAcquiredEvent."""

    def test_initialization(self) -> None:
        """Test event initialization with attributes."""
        event = ItemAcquiredEvent(item_id="test_item")

        assert event.item_id == "test_item"

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct data."""
        event = ItemAcquiredEvent(item_id="rusty_key")

        script_data = event.get_script_data()

        assert "item_id" in script_data
        assert script_data["item_id"] == "rusty_key"

    def test_different_items(self) -> None:
        """Test creating events for different items."""
        event1 = ItemAcquiredEvent(item_id="photo_01")
        event2 = ItemAcquiredEvent(item_id="note_01")

        assert event1.item_id == "photo_01"
        assert event2.item_id == "note_01"


class TestItemAcquisitionFailedEvent:
    """Test suite for ItemAcquisitionFailedEvent."""

    def test_initialization_capacity(self) -> None:
        """Test event initialization with capacity reason."""
        event = ItemAcquisitionFailedEvent(item_id="test_item", reason="capacity")

        assert event.item_id == "test_item"
        assert event.reason == "capacity"

    def test_initialization_already_owned(self) -> None:
        """Test event initialization with already_owned reason."""
        event = ItemAcquisitionFailedEvent(item_id="owned_item", reason="already_owned")

        assert event.item_id == "owned_item"
        assert event.reason == "already_owned"

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct data."""
        event = ItemAcquisitionFailedEvent(item_id="test_item", reason="capacity")

        script_data = event.get_script_data()

        assert "item_id" in script_data
        assert "reason" in script_data
        assert script_data["item_id"] == "test_item"
        assert script_data["reason"] == "capacity"

    def test_all_failure_reasons(self) -> None:
        """Test creating events with all documented failure reasons."""
        reasons = ["capacity", "unknown_item", "already_owned"]

        for reason in reasons:
            event = ItemAcquisitionFailedEvent(item_id="test_item", reason=reason)
            assert event.reason == reason
            assert event.get_script_data()["reason"] == reason


class TestItemConsumedEvent:
    """Test suite for ItemConsumedEvent."""

    def test_initialization(self) -> None:
        """Test event initialization with attributes."""
        event = ItemConsumedEvent(item_id="potion_01", category="consumable")

        assert event.item_id == "potion_01"
        assert event.category == "consumable"

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct data."""
        event = ItemConsumedEvent(item_id="potion_01", category="consumable")

        script_data = event.get_script_data()

        assert "item_id" in script_data
        assert "category" in script_data
        assert script_data["item_id"] == "potion_01"
        assert script_data["category"] == "consumable"
        # item_name should not be in script data
        assert "item_name" not in script_data

    def test_different_categories(self) -> None:
        """Test creating events with different categories."""
        event1 = ItemConsumedEvent(item_id="item1", category="consumable")
        event2 = ItemConsumedEvent(item_id="item2", category="food")
        event3 = ItemConsumedEvent(item_id="item3", category="general")

        assert event1.category == "consumable"
        assert event2.category == "food"
        assert event3.category == "general"

    def test_script_data_includes_category(self) -> None:
        """Test that script data includes category for filtering."""
        event = ItemConsumedEvent(item_id="apple", category="food")

        script_data = event.get_script_data()

        # Both item_id and category should be included for flexible filtering
        assert script_data["item_id"] == "apple"
        assert script_data["category"] == "food"


class TestInventoryEventsIntegration:
    """Integration tests for inventory events."""

    def test_events_are_dataclasses(self) -> None:
        """Test that all events are properly defined as dataclasses."""
        events = [
            InventoryClosedEvent,
            ItemAcquiredEvent,
            ItemAcquisitionFailedEvent,
            ItemConsumedEvent,
        ]

        for event_class in events:
            # Dataclasses have __dataclass_fields__ attribute
            assert hasattr(event_class, "__dataclass_fields__")

    def test_script_data_always_returns_dict(self) -> None:
        """Test that all events return dict from get_script_data."""
        events = [
            InventoryClosedEvent(has_been_accessed=True),
            ItemAcquiredEvent(item_id="test"),
            ItemAcquisitionFailedEvent(item_id="test", reason="capacity"),
            ItemConsumedEvent(item_id="test", category="general"),
        ]

        for event in events:
            script_data = event.get_script_data()
            assert isinstance(script_data, dict)
            assert len(script_data) > 0


class TestInventoryEventReferences:
    """Test get_references() on inventory events using reference_fields."""

    def test_item_acquired_event_with_item_id_filter(self) -> None:
        """Test ItemAcquiredEvent.get_references returns inventory_item ref when item_id set."""
        refs = ItemAcquiredEvent.get_references({"item_id": "rusty_key"})
        assert refs == {EntityReference(type="inventory_item", name="rusty_key")}

    def test_item_acquired_event_without_item_id_filter(self) -> None:
        """Test ItemAcquiredEvent.get_references returns empty set when no item_id filter."""
        refs = ItemAcquiredEvent.get_references({})
        assert refs == set()

    def test_item_acquisition_failed_event_with_item_id_filter(self) -> None:
        """Test ItemAcquisitionFailedEvent.get_references returns inventory_item ref."""
        refs = ItemAcquisitionFailedEvent.get_references({"item_id": "rusty_key", "reason": "capacity"})
        assert refs == {EntityReference(type="inventory_item", name="rusty_key")}

    def test_item_acquisition_failed_event_with_reason_only(self) -> None:
        """Test ItemAcquisitionFailedEvent.get_references returns empty set when no item_id."""
        refs = ItemAcquisitionFailedEvent.get_references({"reason": "capacity"})
        assert refs == set()

    def test_item_consumed_event_with_item_id_filter(self) -> None:
        """Test ItemConsumedEvent.get_references returns inventory_item ref when item_id set."""
        refs = ItemConsumedEvent.get_references({"item_id": "health_potion"})
        assert refs == {EntityReference(type="inventory_item", name="health_potion")}

    def test_item_consumed_event_with_category_only(self) -> None:
        """Test ItemConsumedEvent.get_references returns empty set when only category filter."""
        refs = ItemConsumedEvent.get_references({"category": "consumable"})
        assert refs == set()

    def test_inventory_closed_event_returns_empty_set(self) -> None:
        """Test InventoryClosedEvent.get_references returns empty set (no item reference)."""
        refs = InventoryClosedEvent.get_references({"inventory_accessed": True})
        assert refs == set()
