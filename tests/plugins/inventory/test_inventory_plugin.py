"""Unit tests for InventoryPlugin in src/pedre/plugins/inventory/plugin.py."""

import unittest
from unittest.mock import MagicMock, patch

from pedre.plugins.inventory.base import InventoryItem
from pedre.plugins.inventory.plugin import InventoryPlugin


class TestInventoryPlugin(unittest.TestCase):
    """Test Suite for InventoryPlugin."""

    def setUp(self) -> None:
        """Set up the InventoryPlugin and mock context."""
        # Patch asset_path to avoid resource handle errors
        self.asset_patcher = patch("pedre.plugins.inventory.plugin.asset_path")
        self.mock_asset_path = self.asset_patcher.start()
        self.mock_asset_path.return_value = "/mock/path"

        # Patch Path.open to avoid FileNotFoundError
        self.path_open_patcher = patch("pathlib.Path.open")
        self.mock_path_open = self.path_open_patcher.start()
        self.mock_file = MagicMock()
        self.mock_path_open.return_value.__enter__.return_value = self.mock_file

        # Mock json.load to return empty dict
        self.json_load_patcher = patch("json.load")
        self.mock_json_load = self.json_load_patcher.start()
        self.mock_json_load.return_value = {"items": []}

        self.plugin = InventoryPlugin()
        self.mock_context = MagicMock()
        self.mock_context.event_bus = MagicMock()
        self.plugin.setup(self.mock_context)

        # Clear items loaded from default file to have a clean slate
        self.plugin.items.clear()

    def tearDown(self) -> None:
        """Stop patches."""
        self.asset_patcher.stop()
        self.path_open_patcher.stop()
        self.json_load_patcher.stop()

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        assert self.plugin.name == "inventory"
        assert self.plugin.items == {}
        assert self.plugin.dynamic_items == set()
        assert not self.plugin.accessed
        assert not self.plugin.showing
        assert self.plugin.context == self.mock_context

    def test_add_item(self) -> None:
        """Test adding a dynamic item."""
        item = InventoryItem(
            id="test_potion", name="Test Potion", description="Restores health", category="consumable", acquired=False
        )

        result = self.plugin.add_item(item)

        assert result is True
        assert "test_potion" in self.plugin.items
        assert "test_potion" in self.plugin.dynamic_items
        # Since acquired=False, no event should be published yet
        self.mock_context.event_bus.publish.assert_not_called()

    def test_add_item_already_acquired(self) -> None:
        """Test adding a dynamic item that is already acquired."""
        item = InventoryItem(id="test_sword", name="Test Sword", description="Sharp", category="weapon", acquired=True)

        result = self.plugin.add_item(item)

        assert result is True
        assert self.plugin.items["test_sword"].acquired is True
        # Should publish ItemAcquiredEvent
        self.mock_context.event_bus.publish.assert_called_once()
        args, _ = self.mock_context.event_bus.publish.call_args
        event = args[0]
        assert event.__class__.__name__ == "ItemAcquiredEvent"
        assert event.item_id == "test_sword"

    def test_add_item_duplicate_id(self) -> None:
        """Test adding an item with a duplicate ID."""
        item1 = InventoryItem(id="duplicate_id", name="Item 1", description="First")
        self.plugin.add_item(item1)

        item2 = InventoryItem(id="duplicate_id", name="Item 2", description="Second")
        result = self.plugin.add_item(item2)

        assert result is False
        # Should still be the first item
        assert self.plugin.items["duplicate_id"].name == "Item 1"

    def test_acquire_item_success(self) -> None:
        """Test successfully acquiring an existing item."""
        item = InventoryItem(id="key", name="Key", description="Opens door", acquired=False)
        self.plugin.items["key"] = item

        result = self.plugin.acquire_item("key")

        assert result is True
        assert self.plugin.items["key"].acquired is True
        self.mock_context.event_bus.publish.assert_called_once()

    def test_acquire_item_already_acquired(self) -> None:
        """Test acquiring an item that is already acquired."""
        item = InventoryItem(id="key", name="Key", description="Opens door", acquired=True)
        self.plugin.items["key"] = item

        self.mock_context.event_bus.reset_mock()
        result = self.plugin.acquire_item("key")

        assert result is False  # False means "not NEWLY acquired"
        self.mock_context.event_bus.publish.assert_called_once()
        args, _ = self.mock_context.event_bus.publish.call_args
        event = args[0]
        assert event.__class__.__name__ == "ItemAcquisitionFailedEvent"
        assert event.reason == "already_owned"

    def test_acquire_item_unknown(self) -> None:
        """Test acquiring a non-existent item."""
        result = self.plugin.acquire_item("unknown_item")

        assert result is False
        # Should publish ItemAcquisitionFailedEvent
        self.mock_context.event_bus.publish.assert_called_once()
        args, _ = self.mock_context.event_bus.publish.call_args
        event = args[0]
        assert event.__class__.__name__ == "ItemAcquisitionFailedEvent"
        assert event.reason == "unknown_item"

    def test_acquire_item_capacity_limit(self) -> None:
        """Test acquiring item when inventory is full."""
        # Fill inventory to capacity
        # Assuming settings.INVENTORY_MAX_SPACE is reasonably small, or we mock it
        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_MAX_SPACE = 1

            # Add one acquired item
            item1 = InventoryItem(id="item1", name="Item 1", description="1", acquired=True)
            self.plugin.items["item1"] = item1

            # Try to acquire a second item
            item2 = InventoryItem(id="item2", name="Item 2", description="2", acquired=False)
            self.plugin.items["item2"] = item2

            result = self.plugin.acquire_item("item2")

            assert result is False
            assert self.plugin.items["item2"].acquired is False

            self.mock_context.event_bus.publish.assert_called()
            args, _ = self.mock_context.event_bus.publish.call_args
            event = args[0]
            assert event.__class__.__name__ == "ItemAcquisitionFailedEvent"
            assert event.reason == "capacity"

    def test_has_item(self) -> None:
        """Test checking if player has an item."""
        item = InventoryItem(id="clock", name="Clock", description="Tick tock", acquired=True)
        self.plugin.items["clock"] = item

        assert self.plugin.has_item("clock") is True
        assert self.plugin.has_item("non_existent") is False

        item_unacquired = InventoryItem(id="future_item", name="Future", description="Later", acquired=False)
        self.plugin.items["future_item"] = item_unacquired
        assert self.plugin.has_item("future_item") is False

    def test_consume_item(self) -> None:
        """Test consuming a consumable item."""
        item = InventoryItem(
            id="apple", name="Apple", description="Tasty", category="food", acquired=True, consumable=True
        )
        self.plugin.items["apple"] = item

        result = self.plugin.consume_item("apple")

        assert result is True
        assert self.plugin.items["apple"].consumed is True
        assert self.plugin.items["apple"].acquired is True

    def test_get_save_state_and_restore(self) -> None:
        """Test saving and restoring inventory state."""
        # Add a mix of items
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True)
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=False)
        self.plugin.items = {"i1": item1, "i2": item2}
        self.plugin.dynamic_items = {"i1", "i2"}
        self.plugin.accessed = True

        save_state = self.plugin.get_save_state()

        # Clear everything
        self.plugin.reset()

        # Restore
        self.plugin.restore_save_state(save_state)

        assert "i1" in self.plugin.items
        assert "i2" in self.plugin.items
        assert self.plugin.items["i1"].acquired is True
        assert self.plugin.items["i2"].acquired is False
        assert "i1" in self.plugin.dynamic_items

    def test_reset(self) -> None:
        """Test resetting the plugin."""
        self.plugin.items["temp"] = InventoryItem(id="temp", name="Temp", description="Temp")
        self.plugin.accessed = True
        self.plugin.showing = True

        # Mock _initialize_default_items to avoid file I/O
        with patch.object(self.plugin, "_initialize_default_items") as mock_init:
            self.plugin.reset()

            assert self.plugin.items == {}
            assert self.plugin.accessed is False
            assert self.plugin.showing is False
            mock_init.assert_called_once()


if __name__ == "__main__":
    unittest.main()
