"""Unit tests for InventoryPlugin in src/pedre/plugins/inventory/plugin.py."""

import unittest
from unittest.mock import MagicMock, patch

import arcade

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

    def test_get_acquired_items(self) -> None:
        """Test filtering acquired items."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, category="photo")
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=False, category="photo")
        item3 = InventoryItem(id="i3", name="I3", description="D3", acquired=True, category="note")
        self.plugin.items = {"i1": item1, "i2": item2, "i3": item3}

        # Test all acquired
        acquired = self.plugin._get_acquired_items()
        assert len(acquired) == 2
        assert acquired[0].id == "i1"
        assert acquired[1].id == "i3"

        # Test filter by category
        photos = self.plugin._get_acquired_items(category="photo")
        assert len(photos) == 1
        assert photos[0].id == "i1"

    def test_get_acquired_count(self) -> None:
        """Test counting acquired items."""
        self.plugin.items = {
            "i1": InventoryItem(id="i1", name="I1", description="D1", acquired=True, category="photo"),
            "i2": InventoryItem(id="i2", name="I2", description="D2", acquired=True, category="note"),
        }
        assert self.plugin._get_acquired_count() == 2
        assert self.plugin._get_acquired_count(category="photo") == 1

    def test_has_been_accessed(self) -> None:
        """Test checking if inventory was accessed."""
        self.plugin.accessed = False
        assert self.plugin.has_been_accessed() is False
        self.plugin.accessed = True
        assert self.plugin.has_been_accessed() is True

    def test_serialization_dict(self) -> None:
        """Test to_dict and from_dict serialization."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumed=False)
        self.plugin.items = {"i1": item1}

        data = self.plugin.to_dict()
        assert "i1" in data["item_states"]
        assert data["item_states"]["i1"]["acquired"] is True

        # Load into a new plugin
        new_plugin = InventoryPlugin()
        new_plugin.items = {"i1": InventoryItem(id="i1", name="I1", description="D1", acquired=False)}
        new_plugin.from_dict(data)
        assert new_plugin.items["i1"].acquired is True

    def test_cleanup(self) -> None:
        """Test cleaning up resources."""
        self.plugin.items = {"i1": InventoryItem(id="i1", name="I1", description="D1")}
        self.plugin.accessed = True
        self.plugin.cleanup()
        assert self.plugin.items == {}
        assert self.plugin.accessed is False

    def test_on_key_press_toggle(self) -> None:
        """Test toggling inventory with key press."""
        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_KEY_TOGGLE = "I"
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None

            # Initial state
            assert not self.plugin.showing

            # Press I to show
            with patch.object(self.plugin, "_get_acquired_items") as mock_get:
                mock_get.return_value = []
                result = self.plugin.on_key_press(arcade.key.I, 0)
                assert result is True
                assert self.plugin.showing is True

            # Press ESC to hide
            result = self.plugin.on_key_press(arcade.key.ESCAPE, 0)
            assert result is True
            assert not self.plugin.showing
            # Should publish InventoryClosedEvent
            self.mock_context.event_bus.publish.assert_called()

    def test_on_key_press_navigation(self) -> None:
        """Test navigating within inventory grid."""
        self.plugin.showing = True
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        # Move Down
        self.plugin.on_key_press(arcade.key.DOWN, 0)
        assert self.plugin.selected_row == 1

        # Move Right
        self.plugin.on_key_press(arcade.key.RIGHT, 0)
        assert self.plugin.selected_col == 1

        # Move Up
        self.plugin.on_key_press(arcade.key.UP, 0)
        assert self.plugin.selected_row == 0

        # Move Left
        self.plugin.on_key_press(arcade.key.LEFT, 0)
        assert self.plugin.selected_col == 0

    def test_on_key_press_actions(self) -> None:
        """Test executing actions in inventory."""
        self.plugin.showing = True
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=True)
        self.plugin.all_items = [item]

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_KEY_CONSUME = "C"
            mock_settings.INVENTORY_KEY_VIEW = "V"
            mock_settings.INVENTORY_KEY_TOGGLE = "I"
            mock_settings.INVENTORY_GRID_COLS = 5

            # Consume item
            with patch.object(self.plugin, "consume_item") as mock_consume:
                mock_consume.return_value = True
                self.plugin.on_key_press(arcade.key.C, 0)
                mock_consume.assert_called_with("i1")

            # View photo
            item_photo = InventoryItem(id="p1", name="P1", description="D1", acquired=True, image_path="photo.png")
            self.plugin.all_items = [item_photo]
            with patch("arcade.load_texture") as mock_load:
                self.plugin.on_key_press(arcade.key.V, 0)
                assert self.plugin.viewing_photo is True
                mock_load.assert_called()

                # Close photo view with ESC
                self.plugin.on_key_press(arcade.key.ESCAPE, 0)
                assert not self.plugin.viewing_photo

    def test_add_item_capacity_fail(self) -> None:
        """Test adding a dynamic item that exceeds capacity."""
        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_MAX_SPACE = 0
            item = InventoryItem(id="i1", name="I1", description="D1", acquired=True)
            result = self.plugin.add_item(item)
            assert result is False
            assert "i1" not in self.plugin.items
            self.mock_context.event_bus.publish.assert_called()

    def test_consume_item_fail(self) -> None:
        """Test consuming failure cases."""
        # Non-existent item
        assert self.plugin.consume_item("none") is False

        # Not acquired
        self.plugin.items["i1"] = InventoryItem(id="i1", name="I1", description="D1", acquired=False)
        assert self.plugin.consume_item("i1") is False

    def test_on_draw_ui(self) -> None:
        """Test the UI drawing calls."""
        self.plugin.showing = True
        self.plugin.viewing_photo = False
        self.plugin.context.window = MagicMock()

        with patch.object(self.plugin, "_draw_inventory_grid") as mock_grid:
            self.plugin.on_draw_ui()
            mock_grid.assert_called_once()

        self.plugin.viewing_photo = True
        self.plugin.current_photo_texture = MagicMock()
        with patch.object(self.plugin, "_draw_photo_view") as mock_photo:
            self.plugin.on_draw_ui()
            mock_photo.assert_called_once()

    def test_draw_methods_smoke(self) -> None:
        """Smoke test for drawing methods to ensure they run without error."""
        item = InventoryItem(
            id="i1",
            name="I1",
            description="D1",
            acquired=True,
            icon_path="icon.png",
            consumable=True,
            image_path="photo.png",
        )
        self.plugin.all_items = [item]
        mock_texture = MagicMock()
        mock_texture.width = 100
        mock_texture.height = 100
        self.plugin.icon_textures = {"i1": mock_texture}
        window = MagicMock()
        window.width = 800
        window.height = 600

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_lrbt_rectangle_outline"),
            patch("arcade.draw_texture_rect"),
            patch("arcade.Text"),
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch("pedre.plugins.inventory.plugin.scale", side_effect=lambda x, _s: x),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
        ):
            # Test grid drawing
            self.plugin._draw_inventory_grid(window)

            # Test photo drawing
            mock_photo_tex = MagicMock()
            mock_photo_tex.width = 100
            mock_photo_tex.height = 100
            self.plugin.current_photo_texture = mock_photo_tex
            self.plugin.selected_row = 0
            self.plugin.selected_col = 0
            self.plugin._draw_photo_view(window)


if __name__ == "__main__":
    unittest.main()
