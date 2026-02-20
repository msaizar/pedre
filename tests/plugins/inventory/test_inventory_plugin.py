"""Unit tests for InventoryPlugin in src/pedre/plugins/inventory/plugin.py."""

import json
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

    def test_show_inventory_loads_background_image(self) -> None:
        """Test loading background image when showing inventory."""
        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch("arcade.load_texture") as mock_load_texture,
            patch.object(self.plugin, "_get_acquired_items", return_value=[]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = "background.png"
            mock_settings.INVENTORY_KEY_TOGGLE = "I"
            mock_load_texture.return_value = MagicMock()

            self.plugin._show_inventory()

            assert self.plugin.background_texture is not None
            mock_load_texture.assert_called_once()

    def test_show_inventory_background_not_found(self) -> None:
        """Test handling missing background image."""
        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch("arcade.load_texture") as mock_load_texture,
            patch.object(self.plugin, "_get_acquired_items", return_value=[]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = "missing.png"
            mock_load_texture.side_effect = FileNotFoundError("Not found")

            self.plugin._show_inventory()

            assert self.plugin.background_texture is None

    def test_show_inventory_first_time_access(self) -> None:
        """Test marking inventory as accessed on first show."""
        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch.object(self.plugin, "_get_acquired_items", return_value=[]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None

            self.plugin.accessed = False
            self.plugin._show_inventory()

            assert self.plugin.accessed is True

    def test_show_inventory_loads_icons_with_failures(self) -> None:
        """Test loading icons with some failures."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, icon_path="icon1.png")
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=True, icon_path="icon2.png")

        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch("arcade.load_texture") as mock_load_texture,
            patch.object(self.plugin, "_get_acquired_items", return_value=[item1, item2]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None
            # First icon loads successfully, second fails
            mock_load_texture.side_effect = [MagicMock(), FileNotFoundError("Not found")]

            self.plugin._show_inventory()

            assert "i1" in self.plugin.icon_textures
            assert "i2" not in self.plugin.icon_textures

    def test_show_inventory_os_error_loading_icon(self) -> None:
        """Test handling OSError when loading icons."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, icon_path="icon.png")

        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch("arcade.load_texture") as mock_load_texture,
            patch.object(self.plugin, "_get_acquired_items", return_value=[item]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None
            mock_load_texture.side_effect = OSError("OS error")

            self.plugin._show_inventory()

            assert "i1" not in self.plugin.icon_textures

    def test_consume_selected_item_not_consumable(self) -> None:
        """Test attempting to consume a non-consumable item."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=False)
        self.plugin.all_items = [item]
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            self.plugin._consume_selected_item()

            # Item should not be consumed
            assert not item.consumed

    def test_consume_selected_item_beyond_list(self) -> None:
        """Test consuming when selection is beyond item list."""
        self.plugin.all_items = []
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            # Should not crash
            self.plugin._consume_selected_item()

    def test_consume_selected_item_adjusts_selection(self) -> None:
        """Test selection adjustment after consuming last item."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=True)
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=True, consumable=True)
        item3 = InventoryItem(id="i3", name="I3", description="D3", acquired=True, consumable=True)
        self.plugin.items = {"i1": item1, "i2": item2, "i3": item3}
        self.plugin.all_items = [item1, item2, item3]

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            # Select last item
            self.plugin.selected_row = 0
            self.plugin.selected_col = 2

            # Consume it
            with patch.object(self.plugin, "_get_acquired_items", return_value=[item1, item2]):
                self.plugin._consume_selected_item()

                # Selection should adjust to new last item
                assert self.plugin.selected_row == 0
                assert self.plugin.selected_col == 1

    def test_view_selected_item_beyond_list(self) -> None:
        """Test viewing when selection is beyond item list."""
        self.plugin.all_items = []
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            # Should not crash
            self.plugin._view_selected_item()

    def test_view_selected_item_no_image_path(self) -> None:
        """Test viewing item without image path."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, image_path=None)
        self.plugin.all_items = [item]
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            self.plugin._view_selected_item()

            assert not self.plugin.viewing_photo

    def test_view_selected_item_load_exception(self) -> None:
        """Test exception handling when loading photo."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, image_path="photo.png")
        self.plugin.all_items = [item]
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch("arcade.load_texture") as mock_load_texture,
        ):
            mock_settings.INVENTORY_GRID_COLS = 5
            mock_load_texture.side_effect = Exception("Load error")

            self.plugin._view_selected_item()

            assert not self.plugin.viewing_photo

    def test_on_draw_ui_not_showing(self) -> None:
        """Test on_draw_ui when overlay is not showing."""
        self.plugin.showing = False
        # Should return early without drawing
        self.plugin.on_draw_ui()

    def test_on_draw_ui_no_window(self) -> None:
        """Test on_draw_ui when window is None."""
        self.plugin.showing = True
        self.plugin.context.window = None
        # Should return early without drawing
        self.plugin.on_draw_ui()

    def test_draw_inventory_grid_with_background_texture(self) -> None:
        """Test drawing inventory grid with background texture."""
        window = MagicMock()
        window.width = 800
        window.height = 600

        self.plugin.background_texture = MagicMock()

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_lrbt_rectangle_outline"),
            patch("arcade.draw_texture_rect") as mock_draw_texture,
            patch("arcade.Text"),
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch("pedre.plugins.inventory.plugin.scale", side_effect=lambda x, _s: x),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
        ):
            self.plugin._draw_inventory_grid(window)

            # Verify background texture was drawn
            mock_draw_texture.assert_any_call(self.plugin.background_texture, arcade.LBWH(0, 0, 800, 600))

    def test_draw_inventory_grid_selected_empty_box(self) -> None:
        """Test drawing selected empty box with different border."""
        window = MagicMock()
        window.width = 800
        window.height = 600
        self.plugin.all_items = []  # Empty inventory
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_lrbt_rectangle_outline") as mock_outline,
            patch("arcade.Text"),
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch("pedre.plugins.inventory.plugin.scale", side_effect=lambda x, _s: x),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
        ):
            self.plugin._draw_inventory_grid(window)

            # Check that selected border was drawn
            assert mock_outline.called

    def test_draw_inventory_grid_with_selected_item_text(self) -> None:
        """Test drawing grid with selected item text updates."""
        item = InventoryItem(id="i1", name="Selected Item", description="D1", acquired=True, consumable=True)
        self.plugin.all_items = [item]
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        window = MagicMock()
        window.width = 800
        window.height = 600

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_lrbt_rectangle_outline"),
            patch("arcade.Text") as mock_text_class,
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch("pedre.plugins.inventory.plugin.scale", side_effect=lambda x, _s: x),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
        ):
            mock_text = MagicMock()
            mock_text_class.return_value = mock_text

            # First draw - creates text objects
            self.plugin._draw_inventory_grid(window)

            # Second draw - updates existing text objects
            item.name = "Updated Item"
            self.plugin._draw_inventory_grid(window)

            assert self.plugin.selected_item_text is not None

    def test_draw_inventory_grid_with_hints(self) -> None:
        """Test drawing grid with hints for viewable and consumable items."""
        item = InventoryItem(
            id="i1", name="I1", description="D1", acquired=True, image_path="photo.png", consumable=True
        )
        self.plugin.all_items = [item]
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        window = MagicMock()
        window.width = 800
        window.height = 600

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_lrbt_rectangle_outline"),
            patch("arcade.Text") as mock_text_class,
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch(
                "pedre.plugins.inventory.plugin.scale",
                side_effect=lambda x, _s: x if not isinstance(x, MagicMock) else 10,
            ),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
        ):
            mock_settings.INVENTORY_HINT_VIEW = "[V] View"
            mock_settings.INVENTORY_HINT_CONSUME = "[C] Consume"
            mock_settings.INVENTORY_GRID_COLS = 5
            mock_settings.INVENTORY_GRID_ROWS = 3
            mock_settings.INVENTORY_MAX_SPACE = 15
            mock_settings.INVENTORY_DESIGN = {
                "box_size": 50,
                "box_spacing": 5,
                "box_border_width": 2,
                "icon_padding": 5,
                "grid_y_offset": 10,
                "item_name_y_offset": 5,
                "hint_y_offset": 5,
                "capacity_x_offset": 10,
                "capacity_y_offset": 5,
                "overlay_height_fraction": 0.5,
            }
            mock_settings.INVENTORY_COLOR_OVERLAY = (0, 0, 0)
            mock_settings.INVENTORY_OVERLAY_ALPHA = 200
            mock_settings.INVENTORY_COLOR_BOX_FILLED = (50, 50, 50)
            mock_settings.INVENTORY_COLOR_BOX_BORDER = (255, 255, 255)
            mock_settings.INVENTORY_COLOR_BOX_BORDER_SELECTED = (255, 255, 0)
            mock_settings.INVENTORY_COLOR_BOX_EMPTY = (0, 0, 0)
            mock_settings.INVENTORY_COLOR_BOX_BORDER_EMPTY = (100, 100, 100)
            mock_settings.INVENTORY_EMPTY_BOX_ALPHA = 100
            mock_settings.INVENTORY_COLOR_TEXT_ITEM_NAME = (255, 255, 255)
            mock_settings.INVENTORY_COLOR_TEXT_HINT = (200, 200, 200)
            mock_settings.INVENTORY_COLOR_TEXT_CAPACITY = (180, 180, 180)
            mock_settings.UI_FONT_NORMAL = 14
            mock_settings.UI_FONT_SMALL = 10
            mock_settings.INVENTORY_UI_SCALE_MIN = 1.0
            mock_settings.INVENTORY_UI_SCALE_MAX = 2.0

            mock_text = MagicMock()
            mock_text_class.return_value = mock_text

            # First draw - creates hint text
            self.plugin._draw_inventory_grid(window)

            # Second draw - updates hint text
            self.plugin._draw_inventory_grid(window)

            assert self.plugin.hint_text is not None

    def test_draw_inventory_grid_capacity_text_updates(self) -> None:
        """Test capacity text creation and updates."""
        window = MagicMock()
        window.width = 800
        window.height = 600

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_lrbt_rectangle_outline"),
            patch("arcade.Text") as mock_text_class,
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch("pedre.plugins.inventory.plugin.scale", side_effect=lambda x, _s: x),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
        ):
            mock_text = MagicMock()
            mock_text_class.return_value = mock_text

            # First draw - creates capacity text
            self.plugin._draw_inventory_grid(window)

            # Second draw - updates capacity text
            self.plugin._draw_inventory_grid(window)

            assert self.plugin.capacity_text is not None

    def test_draw_photo_view_no_texture(self) -> None:
        """Test photo view early return when no texture."""
        window = MagicMock()
        window.width = 800
        window.height = 600

        self.plugin.current_photo_texture = None
        # Should return early
        self.plugin._draw_photo_view(window)

    def test_draw_photo_view_out_of_bounds(self) -> None:
        """Test photo view with out of bounds selection."""
        window = MagicMock()
        window.width = 800
        window.height = 600

        self.plugin.all_items = []
        self.plugin.selected_row = 5
        self.plugin.selected_col = 5
        mock_texture = MagicMock()
        mock_texture.width = 100
        mock_texture.height = 100
        self.plugin.current_photo_texture = mock_texture

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_texture_rect"),
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch("pedre.plugins.inventory.plugin.scale", side_effect=lambda x, _s: x),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
        ):
            mock_settings.INVENTORY_GRID_COLS = 5
            # Should not crash when selection is out of bounds
            self.plugin._draw_photo_view(window)

    def test_draw_photo_view_text_updates(self) -> None:
        """Test photo view title and description text updates."""
        item = InventoryItem(id="i1", name="Photo Title", description="Photo Description", acquired=True)
        self.plugin.all_items = [item]
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        window = MagicMock()
        window.width = 800
        window.height = 600

        mock_texture = MagicMock()
        mock_texture.width = 100
        mock_texture.height = 100
        self.plugin.current_photo_texture = mock_texture

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_texture_rect"),
            patch("arcade.Text") as mock_text_class,
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch(
                "pedre.plugins.inventory.plugin.scale",
                side_effect=lambda x, _s: x if not isinstance(x, MagicMock) else 10,
            ),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
        ):
            mock_settings.INVENTORY_GRID_COLS = 5
            mock_settings.INVENTORY_DESIGN = {
                "photo_text_area_height": 100,
                "photo_title_y_offset": 50,
                "photo_description_y_offset": 30,
                "photo_max_width_fraction": 0.8,
                "photo_max_height_fraction": 0.8,
            }
            mock_settings.UI_FONT_LARGE = 20
            mock_settings.UI_FONT_SMALL = 12
            mock_settings.INVENTORY_UI_SCALE_MIN = 1.0
            mock_settings.INVENTORY_UI_SCALE_MAX = 2.0
            mock_settings.INVENTORY_COLOR_PHOTO_BACKGROUND = (0, 0, 0)
            mock_settings.INVENTORY_COLOR_TEXT_PHOTO_TITLE = (255, 255, 255)
            mock_settings.INVENTORY_COLOR_TEXT_PHOTO_DESCRIPTION = (200, 200, 200)

            mock_text = MagicMock()
            mock_text_class.return_value = mock_text

            # First draw - creates text objects
            self.plugin._draw_photo_view(window)

            # Second draw - updates text objects
            item.name = "Updated Title"
            item.description = "Updated Description"
            self.plugin._draw_photo_view(window)

            assert self.plugin.photo_title_text is not None
            assert self.plugin.photo_description_text is not None

    def test_initialize_default_items_json_decode_error(self) -> None:
        """Test handling JSON decode error."""
        with (
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/path"),
            patch("pathlib.Path.open") as mock_open,
        ):
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            with patch("json.load", side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0)):
                self.plugin._initialize_default_items()

                # Should handle error gracefully
                assert len(self.plugin.items) == 0

    def test_initialize_default_items_key_error(self) -> None:
        """Test handling missing required field."""
        with (
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/path"),
            patch("pathlib.Path.open") as mock_open,
            patch("json.load", return_value={"items": [{"name": "Item"}]}),  # Missing 'id' field
        ):
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            self.plugin._initialize_default_items()

            # Should handle error gracefully
            assert len(self.plugin.items) == 0

    def test_initialize_default_items_os_error(self) -> None:
        """Test handling OSError when loading items file."""
        with (
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/path"),
            patch("pathlib.Path.open", side_effect=OSError("No such file or directory")),
        ):
            self.plugin._initialize_default_items()

            # Should handle error gracefully
            assert len(self.plugin.items) == 0

    def test_initialize_default_items_generic_os_error(self) -> None:
        """Test handling generic OSError."""
        with (
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/path"),
            patch("pathlib.Path.open", side_effect=OSError("Permission denied")),
        ):
            self.plugin._initialize_default_items()

            # Should handle error gracefully
            assert len(self.plugin.items) == 0

    def test_from_dict_unknown_item(self) -> None:
        """Test restoring with unknown item ID in save data."""
        data = {"item_states": {"unknown_id": {"acquired": True, "consumed": False}}, "dynamic_items": []}

        self.plugin.from_dict(data)

        # Should handle unknown item gracefully without crashing

    def test_from_dict_restores_dynamic_items(self) -> None:
        """Test restoring dynamically added items from save data."""
        data = {
            "item_states": {},
            "dynamic_items": [
                {
                    "id": "dynamic1",
                    "name": "Dynamic Item",
                    "description": "Dynamically added",
                    "image_path": "img.png",
                    "icon_path": "icon.png",
                    "category": "general",
                    "acquired": True,
                    "consumed": False,
                    "consumable": True,
                }
            ],
        }

        self.plugin.from_dict(data)

        assert "dynamic1" in self.plugin.items
        assert "dynamic1" in self.plugin.dynamic_items
        assert self.plugin.items["dynamic1"].name == "Dynamic Item"

    def test_to_dict_includes_dynamic_items(self) -> None:
        """Test serialization includes full data for dynamic items."""
        item = InventoryItem(
            id="dyn1",
            name="Dynamic",
            description="Desc",
            image_path="img.png",
            icon_path="icon.png",
            category="test",
            acquired=True,
            consumed=False,
            consumable=True,
        )
        self.plugin.items["dyn1"] = item
        self.plugin.dynamic_items.add("dyn1")

        data = self.plugin.to_dict()

        assert len(data["dynamic_items"]) == 1
        assert data["dynamic_items"][0]["id"] == "dyn1"
        assert data["dynamic_items"][0]["consumable"] is True

    def test_get_acquired_items_excludes_consumed(self) -> None:
        """Test that consumed items are excluded from acquired list."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumed=False)
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=True, consumed=True)
        self.plugin.items = {"i1": item1, "i2": item2}

        acquired = self.plugin._get_acquired_items()

        assert len(acquired) == 1
        assert acquired[0].id == "i1"

    def test_on_key_press_consume_all_input_when_showing(self) -> None:
        """Test that inventory consumes all input when showing."""
        self.plugin.showing = True
        # Any random key should be consumed
        result = self.plugin.on_key_press(arcade.key.A, 0)
        assert result is True

    def test_show_inventory_already_accessed(self) -> None:
        """Test showing inventory when already accessed."""
        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch.object(self.plugin, "_get_acquired_items", return_value=[]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None

            # First access
            self.plugin.accessed = False
            self.plugin._show_inventory()
            assert self.plugin.accessed is True

            # Second access - should remain True
            self.plugin._show_inventory()
            assert self.plugin.accessed is True

    def test_show_inventory_with_icons_no_path(self) -> None:
        """Test showing inventory with items that have no icon path."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, icon_path=None)

        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch.object(self.plugin, "_get_acquired_items", return_value=[item]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None

            self.plugin._show_inventory()

            # Should not try to load icon
            assert "i1" not in self.plugin.icon_textures

    def test_consume_selected_item_adjusts_to_empty_inventory(self) -> None:
        """Test consuming the last item in inventory."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=True)
        self.plugin.items = {"i1": item}
        self.plugin.all_items = [item]

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            self.plugin.selected_row = 0
            self.plugin.selected_col = 0

            # Consume the only item
            with patch.object(self.plugin, "_get_acquired_items", return_value=[]):
                self.plugin._consume_selected_item()

                # Inventory is now empty, but shouldn't crash

    def test_draw_inventory_grid_with_selected_filled_box(self) -> None:
        """Test drawing grid with selected filled box (different border)."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True)
        self.plugin.all_items = [item]
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0

        window = MagicMock()
        window.width = 800
        window.height = 600

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_lrbt_rectangle_outline") as mock_outline,
            patch("arcade.Text"),
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch(
                "pedre.plugins.inventory.plugin.scale",
                side_effect=lambda x, _s: x if not isinstance(x, MagicMock) else 10,
            ),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
        ):
            mock_settings.INVENTORY_GRID_COLS = 5
            mock_settings.INVENTORY_GRID_ROWS = 3
            mock_settings.INVENTORY_MAX_SPACE = 15
            mock_settings.INVENTORY_DESIGN = {
                "box_size": 50,
                "box_spacing": 5,
                "box_border_width": 2,
                "icon_padding": 5,
                "grid_y_offset": 10,
                "item_name_y_offset": 5,
                "hint_y_offset": 5,
                "capacity_x_offset": 10,
                "capacity_y_offset": 5,
                "overlay_height_fraction": 0.5,
            }
            mock_settings.INVENTORY_COLOR_OVERLAY = (0, 0, 0)
            mock_settings.INVENTORY_OVERLAY_ALPHA = 200
            mock_settings.INVENTORY_COLOR_BOX_FILLED = (50, 50, 50)
            mock_settings.INVENTORY_COLOR_BOX_BORDER = (255, 255, 255)
            mock_settings.INVENTORY_COLOR_BOX_BORDER_SELECTED = (255, 255, 0)
            mock_settings.INVENTORY_COLOR_BOX_EMPTY = (0, 0, 0)
            mock_settings.INVENTORY_COLOR_BOX_BORDER_EMPTY = (100, 100, 100)
            mock_settings.INVENTORY_EMPTY_BOX_ALPHA = 100
            mock_settings.INVENTORY_COLOR_TEXT_ITEM_NAME = (255, 255, 255)
            mock_settings.INVENTORY_COLOR_TEXT_HINT = (200, 200, 200)
            mock_settings.INVENTORY_COLOR_TEXT_CAPACITY = (180, 180, 180)
            mock_settings.UI_FONT_NORMAL = 14
            mock_settings.UI_FONT_SMALL = 10
            mock_settings.INVENTORY_UI_SCALE_MIN = 1.0
            mock_settings.INVENTORY_UI_SCALE_MAX = 2.0

            self.plugin._draw_inventory_grid(window)

            # Selected filled box should have a different border
            assert mock_outline.called

    def test_initialize_default_items_file_not_found_with_filename(self) -> None:
        """Test handling FileNotFoundError with filename attribute."""
        with (
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/path"),
            patch("pathlib.Path.open") as mock_open,
        ):
            error = FileNotFoundError("File not found")
            error.filename = "/mock/path/items.json"
            mock_open.side_effect = error

            self.plugin._initialize_default_items()

            # Should handle error gracefully
            assert len(self.plugin.items) == 0

    def test_initialize_default_items_success(self) -> None:
        """Test successful loading of items from JSON."""
        with (
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/path"),
            patch("pathlib.Path.open") as mock_open,
            patch(
                "json.load",
                return_value={
                    "items": [
                        {
                            "id": "test_item",
                            "name": "Test Item",
                            "description": "A test item",
                            "image_path": "test.png",
                            "icon_path": "icon.png",
                            "category": "test",
                            "acquired": False,
                            "consumable": False,
                        }
                    ]
                },
            ),
        ):
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            self.plugin._initialize_default_items()

            # Should load item successfully
            assert len(self.plugin.items) == 1
            assert "test_item" in self.plugin.items
            assert self.plugin.items["test_item"].name == "Test Item"

    def test_consume_item_failed_to_consume(self) -> None:
        """Test the logger message for failed consume."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=True)
        self.plugin.items = {"i1": item}
        self.plugin.all_items = [item]

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            self.plugin.selected_row = 0
            self.plugin.selected_col = 0

            # Mock consume_item to return False
            with (
                patch.object(self.plugin, "consume_item", return_value=False),
                patch.object(self.plugin, "_get_acquired_items", return_value=[item]),
            ):
                self.plugin._consume_selected_item()
                # Line 313 should be covered when consume fails

    def test_draw_inventory_grid_unselected_filled_box(self) -> None:
        """Test drawing grid with unselected filled box (regular border)."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True)
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=True)
        self.plugin.all_items = [item1, item2]
        self.plugin.selected_row = 0
        self.plugin.selected_col = 0  # First item selected

        window = MagicMock()
        window.width = 800
        window.height = 600

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_lrbt_rectangle_outline") as mock_outline,
            patch("arcade.Text"),
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch(
                "pedre.plugins.inventory.plugin.scale",
                side_effect=lambda x, _s: x if not isinstance(x, MagicMock) else 10,
            ),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
        ):
            mock_settings.INVENTORY_GRID_COLS = 5
            mock_settings.INVENTORY_GRID_ROWS = 3
            mock_settings.INVENTORY_MAX_SPACE = 15
            mock_settings.INVENTORY_DESIGN = {
                "box_size": 50,
                "box_spacing": 5,
                "box_border_width": 2,
                "icon_padding": 5,
                "grid_y_offset": 10,
                "item_name_y_offset": 5,
                "hint_y_offset": 5,
                "capacity_x_offset": 10,
                "capacity_y_offset": 5,
                "overlay_height_fraction": 0.5,
            }
            mock_settings.INVENTORY_COLOR_OVERLAY = (0, 0, 0)
            mock_settings.INVENTORY_OVERLAY_ALPHA = 200
            mock_settings.INVENTORY_COLOR_BOX_FILLED = (50, 50, 50)
            mock_settings.INVENTORY_COLOR_BOX_BORDER = (255, 255, 255)
            mock_settings.INVENTORY_COLOR_BOX_BORDER_SELECTED = (255, 255, 0)
            mock_settings.INVENTORY_COLOR_BOX_EMPTY = (0, 0, 0)
            mock_settings.INVENTORY_COLOR_BOX_BORDER_EMPTY = (100, 100, 100)
            mock_settings.INVENTORY_EMPTY_BOX_ALPHA = 100
            mock_settings.INVENTORY_COLOR_TEXT_ITEM_NAME = (255, 255, 255)
            mock_settings.INVENTORY_COLOR_TEXT_HINT = (200, 200, 200)
            mock_settings.INVENTORY_COLOR_TEXT_CAPACITY = (180, 180, 180)
            mock_settings.UI_FONT_NORMAL = 14
            mock_settings.UI_FONT_SMALL = 10
            mock_settings.INVENTORY_UI_SCALE_MIN = 1.0
            mock_settings.INVENTORY_UI_SCALE_MAX = 2.0

            self.plugin._draw_inventory_grid(window)

            # Second item (unselected) should have regular border - lines 439-440
            assert mock_outline.called

    def test_on_key_press_not_handled(self) -> None:
        """Test that unhandled key press returns False."""
        self.plugin.showing = False

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_KEY_TOGGLE = "I"

            # Press a key that's not the toggle key
            result = self.plugin.on_key_press(arcade.key.A, 0)

            # Should return False (not handled)
            assert result is False

    def test_viewing_photo_other_key_handled(self) -> None:
        """Test that other keys are consumed when viewing photo - covers branch 194->225."""
        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_KEY_TOGGLE = "I"

            self.plugin.showing = True
            self.plugin.viewing_photo = True

            # Press a key that's not ESCAPE while viewing photo
            result = self.plugin.on_key_press(arcade.key.A, 0)

            # Should return True (consumed) to prevent other handlers
            assert result is True
            # Photo should still be showing
            assert self.plugin.viewing_photo is True

    def test_consume_item_no_selection_adjustment(self) -> None:
        """Test consuming item when selection doesn't need adjustment - covers branch 308->exit."""
        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_MAX_SPACE = 10
            mock_settings.INVENTORY_GRID_COLS = 5

            # Add multiple items
            item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=True)
            item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=True, consumable=True)
            item3 = InventoryItem(id="i3", name="I3", description="D3", acquired=True, consumable=True)

            self.plugin.items["i1"] = item1
            self.plugin.items["i2"] = item2
            self.plugin.items["i3"] = item3
            self.plugin.all_items = [item1, item2, item3]

            # Select the first item (index 0)
            self.plugin.selected_row = 0
            self.plugin.selected_col = 0

            # Consume it via _consume_selected_item
            self.plugin._consume_selected_item()

            # After consuming i1, we have i2 and i3
            # Selection at index 0 is still valid (now pointing to i2)
            # So no adjustment should occur - this covers the branch where current_index <= max_index
            assert self.plugin.selected_row == 0
            assert self.plugin.selected_col == 0

    def test_restore_save_state_without_inventory_items(self) -> None:
        """Test restore_save_state when inventory_items key is missing - covers branch 691->exit."""
        # Add some items to verify they remain unchanged
        item = InventoryItem(id="test", name="Test", description="D", acquired=True)
        self.plugin.items["test"] = item

        # State without inventory_items key
        state = {"some_other_key": "value"}

        # Should not raise and handle gracefully
        self.plugin.restore_save_state(state)

        # No changes should occur - items should remain
        assert "test" in self.plugin.items

    def test_to_dict_dynamic_item_not_in_items(self) -> None:
        """Test to_dict when dynamic item ID is not in items dict - covers branch 1037->1036."""
        # Add a dynamic item ID that doesn't exist in items
        self.plugin.dynamic_items.add("nonexistent_id")

        # Should not crash when serializing
        data = self.plugin.to_dict()

        # Should not include the nonexistent item
        assert "dynamic_items" in data
        # Check that nonexistent_id is not in the serialized dynamic items
        dynamic_ids = [item["id"] for item in data["dynamic_items"]]
        assert "nonexistent_id" not in dynamic_ids

    def test_from_dict_dynamic_item_already_exists(self) -> None:
        """Test from_dict when dynamic item already exists in items - covers branch 1094->1091."""
        # Add an item that we'll try to restore
        existing_item = InventoryItem(id="existing", name="Existing", description="D", acquired=True)
        self.plugin.items["existing"] = existing_item
        self.plugin.dynamic_items.add("existing")

        # Try to restore with the same item in dynamic_items
        data = {
            "item_states": {},
            "dynamic_items": [
                {
                    "id": "existing",
                    "name": "Existing Updated",
                    "description": "Updated description",
                    "category": "general",
                    "acquired": True,
                    "consumed": False,
                    "consumable": False,
                }
            ],
        }

        self.plugin.from_dict(data)

        # Should skip adding the duplicate
        # The original item should remain unchanged
        assert self.plugin.items["existing"].name == "Existing"
