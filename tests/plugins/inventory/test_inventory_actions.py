"""Unit tests for inventory actions."""

import unittest
import uuid
from unittest.mock import MagicMock

from pedre.plugins.inventory.actions import (
    AcquireItemAction,
    AddItemAction,
    ConsumeItemAction,
    WaitForInventoryAccessAction,
)


class TestWaitForInventoryAccessAction(unittest.TestCase):
    """Test WaitForInventoryAccessAction."""

    def test_init(self) -> None:
        """Test WaitForInventoryAccessAction initialization."""
        action = WaitForInventoryAccessAction()
        assert action is not None

    def test_from_dict(self) -> None:
        """Test creating WaitForInventoryAccessAction from dictionary."""
        action = WaitForInventoryAccessAction.from_dict({})
        assert action is not None

    def test_execute_when_inventory_not_accessed(self) -> None:
        """Test execute returns False when inventory hasn't been accessed."""
        action = WaitForInventoryAccessAction()
        context = MagicMock()
        context.inventory_plugin.has_been_accessed = False

        result = action.execute(context)

        assert result is False

    def test_execute_when_inventory_accessed(self) -> None:
        """Test execute returns True when inventory has been accessed."""
        action = WaitForInventoryAccessAction()
        context = MagicMock()
        context.inventory_plugin.has_been_accessed = True

        result = action.execute(context)

        assert result is True


class TestAcquireItemAction(unittest.TestCase):
    """Test AcquireItemAction."""

    def test_init(self) -> None:
        """Test AcquireItemAction initialization."""
        action = AcquireItemAction("test_item")

        assert action.item_id == "test_item"
        assert action.started is False
        assert action.success is False

    def test_from_dict(self) -> None:
        """Test creating AcquireItemAction from dictionary."""
        data = {"item_id": "rusty_key"}
        action = AcquireItemAction.from_dict(data)

        assert action.item_id == "rusty_key"
        assert action.started is False
        assert action.success is False

    def test_from_dict_with_empty_item_id(self) -> None:
        """Test creating AcquireItemAction from dict without item_id."""
        data = {}
        action = AcquireItemAction.from_dict(data)

        assert action.item_id == ""

    def test_execute_successful_acquisition(self) -> None:
        """Test execute successfully acquires an item."""
        action = AcquireItemAction("test_item")
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.acquire_item.return_value = True
        context.inventory_plugin = inventory_plugin

        result = action.execute(context)

        assert result is True
        assert action.started is True
        assert action.success is True
        inventory_plugin.acquire_item.assert_called_once_with("test_item")

    def test_execute_failed_acquisition(self) -> None:
        """Test execute returns False when acquisition fails."""
        action = AcquireItemAction("unknown_item")
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.acquire_item.return_value = False
        context.inventory_plugin = inventory_plugin

        result = action.execute(context)

        assert result is False
        assert action.started is True
        assert action.success is False

    def test_execute_only_once(self) -> None:
        """Test that acquire is only attempted once even if execute called multiple times."""
        action = AcquireItemAction("test_item")
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.acquire_item.return_value = True
        context.inventory_plugin = inventory_plugin

        action.execute(context)
        action.execute(context)

        inventory_plugin.acquire_item.assert_called_once()

    def test_reset(self) -> None:
        """Test reset clears started and success flags."""
        action = AcquireItemAction("test_item")
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.acquire_item.return_value = True
        context.inventory_plugin = inventory_plugin

        action.execute(context)
        assert action.started is True
        assert action.success is True

        action.reset()
        assert action.started is False
        assert action.success is False


class TestAddItemAction(unittest.TestCase):
    """Test AddItemAction."""

    def test_init_with_all_parameters(self) -> None:
        """Test AddItemAction initialization with all parameters."""
        action = AddItemAction(
            name="Test Potion",
            description="Restores health",
            item_id="test_potion",
            image_path="items/potion.png",
            icon_path="items/icons/potion.png",
            category="potion",
            acquired=True,
            consumable=True,
        )

        assert action.name == "Test Potion"
        assert action.description == "Restores health"
        assert action.item_id == "test_potion"
        assert action.image_path == "items/potion.png"
        assert action.icon_path == "items/icons/potion.png"
        assert action.category == "potion"
        assert action.acquired is True
        assert action.consumable is True
        assert action.started is False
        assert action.success is False

    def test_init_with_defaults(self) -> None:
        """Test AddItemAction initialization with default values."""
        action = AddItemAction(name="Basic Item", description="A simple item")

        assert action.name == "Basic Item"
        assert action.description == "A simple item"
        assert action.image_path is None
        assert action.icon_path is None
        assert action.category == "general"
        assert action.acquired is True
        assert action.consumable is False

    def test_init_generates_uuid_when_no_item_id(self) -> None:
        """Test that UUID is generated when item_id is not provided."""
        action = AddItemAction(name="Item", description="Desc")

        # Should be a valid UUID string
        assert action.item_id is not None
        assert len(action.item_id) > 0
        # Try to parse as UUID to verify it's valid
        uuid.UUID(action.item_id)

    def test_init_generates_uuid_when_empty_item_id(self) -> None:
        """Test that UUID is generated when item_id is empty string."""
        action = AddItemAction(name="Item", description="Desc", item_id="")

        # Should be a valid UUID string
        assert action.item_id is not None
        assert len(action.item_id) > 0
        uuid.UUID(action.item_id)

    def test_init_uses_provided_item_id(self) -> None:
        """Test that provided item_id is used when given."""
        action = AddItemAction(name="Item", description="Desc", item_id="custom_id")

        assert action.item_id == "custom_id"

    def test_from_dict_with_all_fields(self) -> None:
        """Test creating AddItemAction from dictionary with all fields."""
        data = {
            "name": "Health Potion",
            "description": "Restores 50 HP",
            "item_id": "health_potion_1",
            "image_path": "items/potion.png",
            "icon_path": "items/icons/potion.png",
            "category": "potion",
            "acquired": True,
            "consumable": True,
        }
        action = AddItemAction.from_dict(data)

        assert action.name == "Health Potion"
        assert action.description == "Restores 50 HP"
        assert action.item_id == "health_potion_1"
        assert action.image_path == "items/potion.png"
        assert action.icon_path == "items/icons/potion.png"
        assert action.category == "potion"
        assert action.acquired is True
        assert action.consumable is True

    def test_from_dict_with_defaults(self) -> None:
        """Test creating AddItemAction from dict with missing optional fields."""
        data = {"name": "Key", "description": "Opens door"}
        action = AddItemAction.from_dict(data)

        assert action.name == "Key"
        assert action.description == "Opens door"
        assert action.image_path is None
        assert action.icon_path is None
        assert action.category == "general"
        assert action.acquired is True
        assert action.consumable is False

    def test_from_dict_generates_uuid_when_no_item_id(self) -> None:
        """Test UUID generation from dict when item_id not provided."""
        data = {"name": "Item", "description": "Desc"}
        action = AddItemAction.from_dict(data)

        # Should have a valid UUID
        assert action.item_id is not None
        uuid.UUID(action.item_id)

    def test_from_dict_generates_uuid_when_empty_item_id(self) -> None:
        """Test UUID generation from dict when item_id is empty."""
        data = {"name": "Item", "description": "Desc", "item_id": ""}
        action = AddItemAction.from_dict(data)

        # Should have a valid UUID
        assert action.item_id is not None
        uuid.UUID(action.item_id)

    def test_from_dict_with_acquired_false(self) -> None:
        """Test creating AddItemAction from dict with acquired=false."""
        data = {"name": "Item", "description": "Desc", "acquired": False}
        action = AddItemAction.from_dict(data)

        assert action.acquired is False

    def test_execute_successful_add(self) -> None:
        """Test execute successfully adds an item."""
        action = AddItemAction(
            name="Test Item",
            description="Test desc",
            item_id="test_id",
            category="test",
            acquired=True,
        )
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.add_item.return_value = True
        context.inventory_plugin = inventory_plugin

        result = action.execute(context)

        assert result is True
        assert action.started is True
        assert action.success is True
        inventory_plugin.add_item.assert_called_once()

        # Verify the item passed to add_item has correct properties
        call_args = inventory_plugin.add_item.call_args
        item = call_args[0][0]
        assert item.id == "test_id"
        assert item.name == "Test Item"
        assert item.description == "Test desc"
        assert item.category == "test"
        assert item.acquired is True

    def test_execute_failed_add(self) -> None:
        """Test execute returns False when add fails."""
        action = AddItemAction(name="Item", description="Desc", item_id="duplicate")
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.add_item.return_value = False
        context.inventory_plugin = inventory_plugin

        result = action.execute(context)

        assert result is False
        assert action.started is True
        assert action.success is False

    def test_execute_only_once(self) -> None:
        """Test that add is only attempted once even if execute called multiple times."""
        action = AddItemAction(name="Item", description="Desc")
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.add_item.return_value = True
        context.inventory_plugin = inventory_plugin

        action.execute(context)
        action.execute(context)

        inventory_plugin.add_item.assert_called_once()

    def test_execute_creates_consumable_item(self) -> None:
        """Test execute creates item with consumable flag."""
        action = AddItemAction(name="Potion", description="Heal", consumable=True)
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.add_item.return_value = True
        context.inventory_plugin = inventory_plugin

        action.execute(context)

        call_args = inventory_plugin.add_item.call_args
        item = call_args[0][0]
        assert item.consumable is True

    def test_execute_creates_non_acquired_item(self) -> None:
        """Test execute creates item with acquired=False."""
        action = AddItemAction(name="Item", description="Desc", acquired=False)
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.add_item.return_value = True
        context.inventory_plugin = inventory_plugin

        action.execute(context)

        call_args = inventory_plugin.add_item.call_args
        item = call_args[0][0]
        assert item.acquired is False

    def test_execute_with_image_paths(self) -> None:
        """Test execute creates item with image and icon paths."""
        action = AddItemAction(
            name="Photo",
            description="A picture",
            image_path="photos/pic.png",
            icon_path="photos/icons/pic.png",
        )
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.add_item.return_value = True
        context.inventory_plugin = inventory_plugin

        action.execute(context)

        call_args = inventory_plugin.add_item.call_args
        item = call_args[0][0]
        assert item.image_path == "photos/pic.png"
        assert item.icon_path == "photos/icons/pic.png"

    def test_reset(self) -> None:
        """Test reset clears started and success flags."""
        action = AddItemAction(name="Item", description="Desc")
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.add_item.return_value = True
        context.inventory_plugin = inventory_plugin

        action.execute(context)
        assert action.started is True
        assert action.success is True

        action.reset()
        assert action.started is False
        assert action.success is False


class TestConsumeItemAction(unittest.TestCase):
    """Test ConsumeItemAction."""

    def test_init(self) -> None:
        """Test ConsumeItemAction initialization."""
        action = ConsumeItemAction("test_item")

        assert action.item_id == "test_item"
        assert action.started is False

    def test_from_dict(self) -> None:
        """Test creating ConsumeItemAction from dictionary."""
        data = {"item_id": "health_potion"}
        action = ConsumeItemAction.from_dict(data)

        assert action.item_id == "health_potion"
        assert action.started is False

    def test_from_dict_with_empty_item_id(self) -> None:
        """Test creating ConsumeItemAction from dict without item_id."""
        data = {}
        action = ConsumeItemAction.from_dict(data)

        assert action.item_id == ""

    def test_execute_consumes_item(self) -> None:
        """Test execute consumes an item."""
        action = ConsumeItemAction("test_item")
        context = MagicMock()
        inventory_plugin = MagicMock()
        context.inventory_plugin = inventory_plugin

        result = action.execute(context)

        assert result is True
        assert action.started is True
        inventory_plugin.consume_item.assert_called_once_with("test_item")

    def test_execute_returns_true_even_if_consume_fails(self) -> None:
        """Test execute returns True even when consume fails (doesn't block progression)."""
        action = ConsumeItemAction("nonexistent")
        context = MagicMock()
        inventory_plugin = MagicMock()
        inventory_plugin.consume_item.return_value = False
        context.inventory_plugin = inventory_plugin

        result = action.execute(context)

        # Should still return True to not block script progression
        assert result is True
        assert action.started is True

    def test_execute_only_once(self) -> None:
        """Test that consume is only attempted once even if execute called multiple times."""
        action = ConsumeItemAction("test_item")
        context = MagicMock()
        inventory_plugin = MagicMock()
        context.inventory_plugin = inventory_plugin

        action.execute(context)
        action.execute(context)

        inventory_plugin.consume_item.assert_called_once()

    def test_reset(self) -> None:
        """Test reset clears started flag."""
        action = ConsumeItemAction("test_item")
        context = MagicMock()
        inventory_plugin = MagicMock()
        context.inventory_plugin = inventory_plugin

        action.execute(context)
        assert action.started is True

        action.reset()
        assert action.started is False


if __name__ == "__main__":
    unittest.main()
