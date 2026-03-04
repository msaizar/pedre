"""Unit tests for InventoryPlugin in src/pedre/plugins/inventory/plugin.py."""

import json
from typing import cast
from unittest.mock import MagicMock, patch

import arcade
import pytest

from pedre.plugins.inventory.base import InventoryItem
from pedre.plugins.inventory.plugin import InventoryPlugin


@pytest.fixture
def mock_context() -> MagicMock:
    """Fixture for mock context."""
    ctx = MagicMock()
    ctx.event_bus = MagicMock()
    ctx.content_registry.get_sub_registry.return_value.all.return_value = {}
    return ctx


@pytest.fixture
def plugin(mock_context: MagicMock) -> InventoryPlugin:
    """Fixture for InventoryPlugin with empty content registry."""
    p = InventoryPlugin()
    p.setup(mock_context)
    p.items.clear()
    return p


class TestInventoryPlugin:
    """Test Suite for InventoryPlugin."""

    def test_initialization(self, plugin: InventoryPlugin, mock_context: MagicMock) -> None:
        """Test proper initialization of the plugin."""
        assert plugin.name == "inventory"
        assert plugin.items == {}
        assert plugin.dynamic_items == set()
        assert not plugin.accessed
        assert not plugin.showing
        assert plugin.context == mock_context

    def test_add_item(self, plugin: InventoryPlugin, mock_context: MagicMock) -> None:
        """Test adding a dynamic item."""
        item = InventoryItem(
            id="test_potion", name="Test Potion", description="Restores health", category="consumable", acquired=False
        )

        result = plugin.add_item(item)

        assert result is True
        assert "test_potion" in plugin.items
        assert "test_potion" in plugin.dynamic_items
        # Since acquired=False, no event should be published yet
        mock_context.event_bus.publish.assert_not_called()

    def test_add_item_already_acquired(self, plugin: InventoryPlugin, mock_context: MagicMock) -> None:
        """Test adding a dynamic item that is already acquired."""
        item = InventoryItem(id="test_sword", name="Test Sword", description="Sharp", category="weapon", acquired=True)

        result = plugin.add_item(item)

        assert result is True
        assert plugin.items["test_sword"].acquired is True
        # Should publish ItemAcquiredEvent
        mock_context.event_bus.publish.assert_called_once()
        args, _ = mock_context.event_bus.publish.call_args
        event = args[0]
        assert event.__class__.__name__ == "ItemAcquiredEvent"
        assert event.item_id == "test_sword"

    def test_add_item_duplicate_id(self, plugin: InventoryPlugin) -> None:
        """Test adding an item with a duplicate ID."""
        item1 = InventoryItem(id="duplicate_id", name="Item 1", description="First")
        plugin.add_item(item1)

        item2 = InventoryItem(id="duplicate_id", name="Item 2", description="Second")
        result = plugin.add_item(item2)

        assert result is False
        # Should still be the first item
        assert plugin.items["duplicate_id"].name == "Item 1"

    def test_acquire_item_success(self, plugin: InventoryPlugin, mock_context: MagicMock) -> None:
        """Test successfully acquiring an existing item."""
        item = InventoryItem(id="key", name="Key", description="Opens door", acquired=False)
        plugin.items["key"] = item

        result = plugin.acquire_item("key")

        assert result is True
        assert plugin.items["key"].acquired is True
        mock_context.event_bus.publish.assert_called_once()

    def test_acquire_item_already_acquired(self, plugin: InventoryPlugin, mock_context: MagicMock) -> None:
        """Test acquiring an item that is already acquired."""
        item = InventoryItem(id="key", name="Key", description="Opens door", acquired=True)
        plugin.items["key"] = item

        mock_context.event_bus.reset_mock()
        result = plugin.acquire_item("key")

        assert result is False  # False means "not NEWLY acquired"
        mock_context.event_bus.publish.assert_called_once()
        args, _ = mock_context.event_bus.publish.call_args
        event = args[0]
        assert event.__class__.__name__ == "ItemAcquisitionFailedEvent"
        assert event.reason == "already_owned"

    def test_acquire_item_unknown(self, plugin: InventoryPlugin, mock_context: MagicMock) -> None:
        """Test acquiring a non-existent item."""
        result = plugin.acquire_item("unknown_item")

        assert result is False
        # Should publish ItemAcquisitionFailedEvent
        mock_context.event_bus.publish.assert_called_once()
        args, _ = mock_context.event_bus.publish.call_args
        event = args[0]
        assert event.__class__.__name__ == "ItemAcquisitionFailedEvent"
        assert event.reason == "unknown_item"

    def test_acquire_item_capacity_limit(self, plugin: InventoryPlugin, mock_context: MagicMock) -> None:
        """Test acquiring item when inventory is full."""
        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_MAX_SPACE = 1

            # Add one acquired item
            item1 = InventoryItem(id="item1", name="Item 1", description="1", acquired=True)
            plugin.items["item1"] = item1

            # Try to acquire a second item
            item2 = InventoryItem(id="item2", name="Item 2", description="2", acquired=False)
            plugin.items["item2"] = item2

            result = plugin.acquire_item("item2")

            assert result is False
            assert plugin.items["item2"].acquired is False

            mock_context.event_bus.publish.assert_called()
            args, _ = mock_context.event_bus.publish.call_args
            event = args[0]
            assert event.__class__.__name__ == "ItemAcquisitionFailedEvent"
            assert event.reason == "capacity"

    def test_has_item(self, plugin: InventoryPlugin) -> None:
        """Test checking if player has an item."""
        item = InventoryItem(id="clock", name="Clock", description="Tick tock", acquired=True)
        plugin.items["clock"] = item

        assert plugin.has_item("clock") is True
        assert plugin.has_item("non_existent") is False

        item_unacquired = InventoryItem(id="future_item", name="Future", description="Later", acquired=False)
        plugin.items["future_item"] = item_unacquired
        assert plugin.has_item("future_item") is False

    def test_consume_item(self, plugin: InventoryPlugin) -> None:
        """Test consuming a consumable item."""
        item = InventoryItem(
            id="apple", name="Apple", description="Tasty", category="food", acquired=True, consumable=True
        )
        plugin.items["apple"] = item

        result = plugin.consume_item("apple")

        assert result is True
        assert plugin.items["apple"].consumed is True
        assert plugin.items["apple"].acquired is True

    def test_get_save_state_and_restore(self, plugin: InventoryPlugin) -> None:
        """Test saving and restoring inventory state."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True)
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=False)
        plugin.items = {"i1": item1, "i2": item2}
        plugin.dynamic_items = {"i1", "i2"}
        plugin.accessed = True

        save_state = plugin.get_save_state()

        plugin.reset()

        plugin.restore_save_state(save_state)

        assert "i1" in plugin.items
        assert "i2" in plugin.items
        assert plugin.items["i1"].acquired is True
        assert plugin.items["i2"].acquired is False
        assert "i1" in plugin.dynamic_items

    def test_reset(self, plugin: InventoryPlugin) -> None:
        """Test resetting the plugin."""
        plugin.items["temp"] = InventoryItem(id="temp", name="Temp", description="Temp")
        plugin.accessed = True
        plugin.showing = True

        with patch.object(plugin, "_initialize_default_items") as mock_init:
            plugin.reset()

            assert plugin.items == {}
            assert plugin.accessed is False
            assert plugin.showing is False
            mock_init.assert_called_once()

    def test_get_acquired_items(self, plugin: InventoryPlugin) -> None:
        """Test filtering acquired items."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, category="photo")
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=False, category="photo")
        item3 = InventoryItem(id="i3", name="I3", description="D3", acquired=True, category="note")
        plugin.items = {"i1": item1, "i2": item2, "i3": item3}

        acquired = plugin._get_acquired_items()
        assert len(acquired) == 2
        assert acquired[0].id == "i1"
        assert acquired[1].id == "i3"

        photos = plugin._get_acquired_items(category="photo")
        assert len(photos) == 1
        assert photos[0].id == "i1"

    def test_get_acquired_count(self, plugin: InventoryPlugin) -> None:
        """Test counting acquired items."""
        plugin.items = {
            "i1": InventoryItem(id="i1", name="I1", description="D1", acquired=True, category="photo"),
            "i2": InventoryItem(id="i2", name="I2", description="D2", acquired=True, category="note"),
        }
        assert plugin._get_acquired_count() == 2
        assert plugin._get_acquired_count(category="photo") == 1

    def test_has_been_accessed(self, plugin: InventoryPlugin) -> None:
        """Test checking if inventory was accessed."""
        plugin.accessed = False
        assert plugin.has_been_accessed() is False
        plugin.accessed = True
        assert plugin.has_been_accessed() is True

    def test_serialization_dict(self, plugin: InventoryPlugin) -> None:
        """Test to_dict and from_dict serialization."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumed=False)
        plugin.items = {"i1": item1}

        data = plugin.to_dict()
        assert "i1" in data["item_states"]
        assert data["item_states"]["i1"]["acquired"] is True

        new_plugin = InventoryPlugin()
        new_plugin.items = {"i1": InventoryItem(id="i1", name="I1", description="D1", acquired=False)}
        new_plugin.from_dict(data)
        assert new_plugin.items["i1"].acquired is True

    def test_cleanup(self, plugin: InventoryPlugin) -> None:
        """Test cleaning up resources."""
        plugin.items = {"i1": InventoryItem(id="i1", name="I1", description="D1")}
        plugin.accessed = True
        plugin.cleanup()
        assert plugin.items == {}
        assert plugin.accessed is False

    def test_on_key_press_toggle(self, plugin: InventoryPlugin, mock_context: MagicMock) -> None:
        """Test toggling inventory with key press."""
        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_KEY_TOGGLE = "I"
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None

            assert not plugin.showing

            with patch.object(plugin, "_get_acquired_items") as mock_get:
                mock_get.return_value = []
                result = plugin.on_key_press(arcade.key.I, 0)
                assert result is True
                assert plugin.showing is True

            result = plugin.on_key_press(arcade.key.ESCAPE, 0)
            assert result is True
            assert not plugin.showing
            # Should publish InventoryClosedEvent
            mock_context.event_bus.publish.assert_called()

    def test_on_key_press_navigation(self, plugin: InventoryPlugin) -> None:
        """Test navigating within inventory grid."""
        plugin.showing = True
        plugin.selected_row = 0
        plugin.selected_col = 0

        plugin.on_key_press(arcade.key.DOWN, 0)
        assert plugin.selected_row == 1

        plugin.on_key_press(arcade.key.RIGHT, 0)
        assert plugin.selected_col == 1

        plugin.on_key_press(arcade.key.UP, 0)
        assert plugin.selected_row == 0

        plugin.on_key_press(arcade.key.LEFT, 0)
        assert plugin.selected_col == 0

    def test_on_key_press_actions(self, plugin: InventoryPlugin) -> None:
        """Test executing actions in inventory."""
        plugin.showing = True
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=True)
        plugin.all_items = [item]

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_KEY_CONSUME = "C"
            mock_settings.INVENTORY_KEY_VIEW = "V"
            mock_settings.INVENTORY_KEY_TOGGLE = "I"
            mock_settings.INVENTORY_GRID_COLS = 5

            with patch.object(plugin, "consume_item") as mock_consume:
                mock_consume.return_value = True
                plugin.on_key_press(arcade.key.C, 0)
                mock_consume.assert_called_with("i1")

            item_photo = InventoryItem(id="p1", name="P1", description="D1", acquired=True, image_path="photo.png")
            plugin.all_items = [item_photo]
            with (
                patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/photo.png"),
                patch("arcade.load_texture") as mock_load,
            ):
                plugin.on_key_press(arcade.key.V, 0)
                assert plugin.viewing_photo is True
                mock_load.assert_called()

                plugin.on_key_press(arcade.key.ESCAPE, 0)
                assert not plugin.viewing_photo

    def test_add_item_capacity_fail(self, plugin: InventoryPlugin, mock_context: MagicMock) -> None:
        """Test adding a dynamic item that exceeds capacity."""
        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_MAX_SPACE = 0
            item = InventoryItem(id="i1", name="I1", description="D1", acquired=True)
            result = plugin.add_item(item)
            assert result is False
            assert "i1" not in plugin.items
            mock_context.event_bus.publish.assert_called()

    def test_consume_item_fail(self, plugin: InventoryPlugin) -> None:
        """Test consuming failure cases."""
        assert plugin.consume_item("none") is False

        plugin.items["i1"] = InventoryItem(id="i1", name="I1", description="D1", acquired=False)
        assert plugin.consume_item("i1") is False

    def test_on_draw_ui(self, plugin: InventoryPlugin) -> None:
        """Test the UI drawing calls."""
        plugin.showing = True
        plugin.viewing_photo = False
        plugin.context.window = MagicMock()

        with patch.object(plugin, "_draw_inventory_grid") as mock_grid:
            plugin.on_draw_ui()
            mock_grid.assert_called_once()

        plugin.viewing_photo = True
        plugin.current_photo_texture = MagicMock()
        with patch.object(plugin, "_draw_photo_view") as mock_photo:
            plugin.on_draw_ui()
            mock_photo.assert_called_once()

    def test_draw_methods_smoke(self, plugin: InventoryPlugin) -> None:
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
        plugin.all_items = [item]
        mock_texture = MagicMock()
        mock_texture.width = 100
        mock_texture.height = 100
        plugin.icon_textures = {"i1": mock_texture}
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
            plugin._draw_inventory_grid(window)

            mock_photo_tex = MagicMock()
            mock_photo_tex.width = 100
            mock_photo_tex.height = 100
            plugin.current_photo_texture = mock_photo_tex
            plugin.selected_row = 0
            plugin.selected_col = 0
            plugin._draw_photo_view(window)

    def test_show_inventory_loads_background_image(self, plugin: InventoryPlugin) -> None:
        """Test loading background image when showing inventory."""
        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/background.png"),
            patch("arcade.load_texture") as mock_load_texture,
            patch.object(plugin, "_get_acquired_items", return_value=[]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = "background.png"
            mock_settings.INVENTORY_KEY_TOGGLE = "I"
            mock_load_texture.return_value = MagicMock()

            plugin._show_inventory()

            assert plugin.background_texture is not None
            mock_load_texture.assert_called_once()

    def test_show_inventory_background_not_found(self, plugin: InventoryPlugin) -> None:
        """Test handling missing background image."""
        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/missing.png"),
            patch("arcade.load_texture") as mock_load_texture,
            patch.object(plugin, "_get_acquired_items", return_value=[]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = "missing.png"
            mock_load_texture.side_effect = FileNotFoundError("Not found")

            plugin._show_inventory()

            assert plugin.background_texture is None

    def test_show_inventory_first_time_access(self, plugin: InventoryPlugin) -> None:
        """Test marking inventory as accessed on first show."""
        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch.object(plugin, "_get_acquired_items", return_value=[]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None

            plugin.accessed = False
            plugin._show_inventory()

            assert plugin.accessed is True

    def test_show_inventory_loads_icons_with_failures(self, plugin: InventoryPlugin) -> None:
        """Test loading icons with some failures."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, icon_path="icon1.png")
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=True, icon_path="icon2.png")

        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/icon.png"),
            patch("arcade.load_texture") as mock_load_texture,
            patch.object(plugin, "_get_acquired_items", return_value=[item1, item2]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None
            mock_load_texture.side_effect = [MagicMock(), FileNotFoundError("Not found")]

            plugin._show_inventory()

            assert "i1" in plugin.icon_textures
            assert "i2" not in plugin.icon_textures

    def test_show_inventory_os_error_loading_icon(self, plugin: InventoryPlugin) -> None:
        """Test handling OSError when loading icons."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, icon_path="icon.png")

        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/icon.png"),
            patch("arcade.load_texture") as mock_load_texture,
            patch.object(plugin, "_get_acquired_items", return_value=[item]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None
            mock_load_texture.side_effect = OSError("OS error")

            plugin._show_inventory()

            assert "i1" not in plugin.icon_textures

    def test_consume_selected_item_not_consumable(self, plugin: InventoryPlugin) -> None:
        """Test attempting to consume a non-consumable item."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=False)
        plugin.all_items = [item]
        plugin.selected_row = 0
        plugin.selected_col = 0

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            plugin._consume_selected_item()

            assert not item.consumed

    def test_consume_selected_item_beyond_list(self, plugin: InventoryPlugin) -> None:
        """Test consuming when selection is beyond item list."""
        plugin.all_items = []
        plugin.selected_row = 0
        plugin.selected_col = 0

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            plugin._consume_selected_item()

    def test_consume_selected_item_adjusts_selection(self, plugin: InventoryPlugin) -> None:
        """Test selection adjustment after consuming last item."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=True)
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=True, consumable=True)
        item3 = InventoryItem(id="i3", name="I3", description="D3", acquired=True, consumable=True)
        plugin.items = {"i1": item1, "i2": item2, "i3": item3}
        plugin.all_items = [item1, item2, item3]

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            plugin.selected_row = 0
            plugin.selected_col = 2

            with patch.object(plugin, "_get_acquired_items", return_value=[item1, item2]):
                plugin._consume_selected_item()

                assert plugin.selected_row == 0
                assert plugin.selected_col == 1

    def test_view_selected_item_beyond_list(self, plugin: InventoryPlugin) -> None:
        """Test viewing when selection is beyond item list."""
        plugin.all_items = []
        plugin.selected_row = 0
        plugin.selected_col = 0

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            plugin._view_selected_item()

    def test_view_selected_item_no_image_path(self, plugin: InventoryPlugin) -> None:
        """Test viewing item without image path."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, image_path=None)
        plugin.all_items = [item]
        plugin.selected_row = 0
        plugin.selected_col = 0

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            plugin._view_selected_item()

            assert not plugin.viewing_photo

    def test_view_selected_item_load_exception(self, plugin: InventoryPlugin) -> None:
        """Test exception handling when loading photo."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, image_path="photo.png")
        plugin.all_items = [item]
        plugin.selected_row = 0
        plugin.selected_col = 0

        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/photo.png"),
            patch("arcade.load_texture") as mock_load_texture,
        ):
            mock_settings.INVENTORY_GRID_COLS = 5
            mock_load_texture.side_effect = Exception("Load error")

            plugin._view_selected_item()

            assert not plugin.viewing_photo

    def test_on_draw_ui_not_showing(self, plugin: InventoryPlugin) -> None:
        """Test on_draw_ui when overlay is not showing."""
        plugin.showing = False
        plugin.on_draw_ui()

    def test_on_draw_ui_no_window(self, plugin: InventoryPlugin) -> None:
        """Test on_draw_ui when window is None."""
        plugin.showing = True
        plugin.context.window = None
        plugin.on_draw_ui()

    def test_draw_inventory_grid_with_background_texture(self, plugin: InventoryPlugin) -> None:
        """Test drawing inventory grid with background texture."""
        window = MagicMock()
        window.width = 800
        window.height = 600

        plugin.background_texture = MagicMock()

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_lrbt_rectangle_outline"),
            patch("arcade.draw_texture_rect") as mock_draw_texture,
            patch("arcade.Text"),
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch("pedre.plugins.inventory.plugin.scale", side_effect=lambda x, _s: x),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
        ):
            plugin._draw_inventory_grid(window)

            mock_draw_texture.assert_any_call(plugin.background_texture, arcade.LBWH(0, 0, 800, 600))

    def test_draw_inventory_grid_selected_empty_box(self, plugin: InventoryPlugin) -> None:
        """Test drawing selected empty box with different border."""
        window = MagicMock()
        window.width = 800
        window.height = 600
        plugin.all_items = []
        plugin.selected_row = 0
        plugin.selected_col = 0

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_lrbt_rectangle_outline") as mock_outline,
            patch("arcade.Text"),
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch("pedre.plugins.inventory.plugin.scale", side_effect=lambda x, _s: x),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
        ):
            plugin._draw_inventory_grid(window)

            assert mock_outline.called

    def test_draw_inventory_grid_with_selected_item_text(self, plugin: InventoryPlugin) -> None:
        """Test drawing grid with selected item text updates."""
        item = InventoryItem(id="i1", name="Selected Item", description="D1", acquired=True, consumable=True)
        plugin.all_items = [item]
        plugin.selected_row = 0
        plugin.selected_col = 0

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

            plugin._draw_inventory_grid(window)

            item.name = "Updated Item"
            plugin._draw_inventory_grid(window)

            assert plugin.selected_item_text is not None

    def test_draw_inventory_grid_with_hints(self, plugin: InventoryPlugin) -> None:
        """Test drawing grid with hints for viewable and consumable items."""
        item = InventoryItem(
            id="i1", name="I1", description="D1", acquired=True, image_path="photo.png", consumable=True
        )
        plugin.all_items = [item]
        plugin.selected_row = 0
        plugin.selected_col = 0

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

            plugin._draw_inventory_grid(window)
            plugin._draw_inventory_grid(window)

            assert plugin.hint_text is not None

    def test_draw_inventory_grid_capacity_text_updates(self, plugin: InventoryPlugin) -> None:
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

            plugin._draw_inventory_grid(window)
            plugin._draw_inventory_grid(window)

            assert plugin.capacity_text is not None

    def test_draw_photo_view_no_texture(self, plugin: InventoryPlugin) -> None:
        """Test photo view early return when no texture."""
        window = MagicMock()
        window.width = 800
        window.height = 600

        plugin.current_photo_texture = None
        plugin._draw_photo_view(window)

    def test_draw_photo_view_out_of_bounds(self, plugin: InventoryPlugin) -> None:
        """Test photo view with out of bounds selection."""
        window = MagicMock()
        window.width = 800
        window.height = 600

        plugin.all_items = []
        plugin.selected_row = 5
        plugin.selected_col = 5
        mock_texture = MagicMock()
        mock_texture.width = 100
        mock_texture.height = 100
        plugin.current_photo_texture = mock_texture

        with (
            patch("arcade.draw_lrbt_rectangle_filled"),
            patch("arcade.draw_texture_rect"),
            patch("pedre.plugins.inventory.plugin.compute_ui_scale", return_value=1.0),
            patch("pedre.plugins.inventory.plugin.scale", side_effect=lambda x, _s: x),
            patch("pedre.plugins.inventory.plugin.scale_font", side_effect=lambda _x, _s, _min_s, _max_s: 12),
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
        ):
            mock_settings.INVENTORY_GRID_COLS = 5
            plugin._draw_photo_view(window)

    def test_draw_photo_view_text_updates(self, plugin: InventoryPlugin) -> None:
        """Test photo view title and description text updates."""
        item = InventoryItem(id="i1", name="Photo Title", description="Photo Description", acquired=True)
        plugin.all_items = [item]
        plugin.selected_row = 0
        plugin.selected_col = 0

        window = MagicMock()
        window.width = 800
        window.height = 600

        mock_texture = MagicMock()
        mock_texture.width = 100
        mock_texture.height = 100
        plugin.current_photo_texture = mock_texture

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

            plugin._draw_photo_view(window)

            item.name = "Updated Title"
            item.description = "Updated Description"
            plugin._draw_photo_view(window)

            assert plugin.photo_title_text is not None
            assert plugin.photo_description_text is not None

    def test_initialize_default_items_json_decode_error(self, plugin: InventoryPlugin) -> None:
        """Test handling JSON decode error."""
        with (
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/path"),
            patch("pathlib.Path.open") as mock_open,
        ):
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            with patch("json.load", side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0)):
                plugin._initialize_default_items()

                assert len(plugin.items) == 0

    def test_initialize_default_items_key_error(self, plugin: InventoryPlugin) -> None:
        """Test handling missing required field."""
        with (
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/path"),
            patch("pathlib.Path.open") as mock_open,
            patch("json.load", return_value={"items": [{"name": "Item"}]}),
        ):
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            plugin._initialize_default_items()

            assert len(plugin.items) == 0

    def test_initialize_default_items_os_error(self, plugin: InventoryPlugin) -> None:
        """Test handling OSError when loading items file."""
        with (
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/path"),
            patch("pathlib.Path.open", side_effect=OSError("No such file or directory")),
        ):
            plugin._initialize_default_items()

            assert len(plugin.items) == 0

    def test_initialize_default_items_generic_os_error(self, plugin: InventoryPlugin) -> None:
        """Test handling generic OSError."""
        with (
            patch("pedre.plugins.inventory.plugin.asset_path", return_value="/mock/path"),
            patch("pathlib.Path.open", side_effect=OSError("Permission denied")),
        ):
            plugin._initialize_default_items()

            assert len(plugin.items) == 0

    def test_from_dict_unknown_item(self, plugin: InventoryPlugin) -> None:
        """Test restoring with unknown item ID in save data."""
        data = {"item_states": {"unknown_id": {"acquired": True, "consumed": False}}, "dynamic_items": []}

        plugin.from_dict(data)

    def test_from_dict_restores_dynamic_items(self, plugin: InventoryPlugin) -> None:
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

        plugin.from_dict(data)

        assert "dynamic1" in plugin.items
        assert "dynamic1" in plugin.dynamic_items
        assert plugin.items["dynamic1"].name == "Dynamic Item"

    def test_to_dict_includes_dynamic_items(self, plugin: InventoryPlugin) -> None:
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
        plugin.items["dyn1"] = item
        plugin.dynamic_items.add("dyn1")

        data = plugin.to_dict()

        assert len(data["dynamic_items"]) == 1
        assert data["dynamic_items"][0]["id"] == "dyn1"
        assert data["dynamic_items"][0]["consumable"] is True

    def test_get_acquired_items_excludes_consumed(self, plugin: InventoryPlugin) -> None:
        """Test that consumed items are excluded from acquired list."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumed=False)
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=True, consumed=True)
        plugin.items = {"i1": item1, "i2": item2}

        acquired = plugin._get_acquired_items()

        assert len(acquired) == 1
        assert acquired[0].id == "i1"

    def test_on_key_press_consume_all_input_when_showing(self, plugin: InventoryPlugin) -> None:
        """Test that inventory consumes all input when showing."""
        plugin.showing = True
        result = plugin.on_key_press(arcade.key.A, 0)
        assert result is True

    def test_show_inventory_already_accessed(self, plugin: InventoryPlugin) -> None:
        """Test showing inventory when already accessed."""
        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch.object(plugin, "_get_acquired_items", return_value=[]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None

            plugin.accessed = False
            plugin._show_inventory()
            assert plugin.accessed is True

            plugin._show_inventory()
            assert plugin.accessed is True

    def test_show_inventory_with_icons_no_path(self, plugin: InventoryPlugin) -> None:
        """Test showing inventory with items that have no icon path."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, icon_path=None)

        with (
            patch("pedre.plugins.inventory.plugin.settings") as mock_settings,
            patch.object(plugin, "_get_acquired_items", return_value=[item]),
        ):
            mock_settings.INVENTORY_BACKGROUND_IMAGE = None

            plugin._show_inventory()

            assert "i1" not in plugin.icon_textures

    def test_consume_selected_item_adjusts_to_empty_inventory(self, plugin: InventoryPlugin) -> None:
        """Test consuming the last item in inventory."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=True)
        plugin.items = {"i1": item}
        plugin.all_items = [item]

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            plugin.selected_row = 0
            plugin.selected_col = 0

            with patch.object(plugin, "_get_acquired_items", return_value=[]):
                plugin._consume_selected_item()

    def test_draw_inventory_grid_with_selected_filled_box(self, plugin: InventoryPlugin) -> None:
        """Test drawing grid with selected filled box (different border)."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True)
        plugin.all_items = [item]
        plugin.selected_row = 0
        plugin.selected_col = 0

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

            plugin._draw_inventory_grid(window)

            assert mock_outline.called

    def test_initialize_default_items_registry_not_found(self, plugin: InventoryPlugin) -> None:
        """Test graceful handling when item registry is absent."""
        cast("MagicMock", plugin.context.content_registry.get_sub_registry).return_value = None

        plugin._initialize_default_items()

        assert len(plugin.items) == 0

    def test_initialize_default_items_success(self, plugin: InventoryPlugin) -> None:
        """Test successful loading of items from the content registry."""
        mock_registry = MagicMock()
        mock_registry.all.return_value = {
            "test_item": {
                "name": "Test Item",
                "description": "A test item",
                "image_path": "test.png",
                "icon_path": "icon.png",
                "category": "test",
                "acquired": False,
                "consumable": False,
            }
        }
        cast("MagicMock", plugin.context.content_registry.get_sub_registry).return_value = mock_registry

        plugin._initialize_default_items()

        assert len(plugin.items) == 1
        assert "test_item" in plugin.items
        assert plugin.items["test_item"].name == "Test Item"

    def test_consume_item_failed_to_consume(self, plugin: InventoryPlugin) -> None:
        """Test the logger message for failed consume."""
        item = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=True)
        plugin.items = {"i1": item}
        plugin.all_items = [item]

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_GRID_COLS = 5
            plugin.selected_row = 0
            plugin.selected_col = 0

            with (
                patch.object(plugin, "consume_item", return_value=False),
                patch.object(plugin, "_get_acquired_items", return_value=[item]),
            ):
                plugin._consume_selected_item()

    def test_draw_inventory_grid_unselected_filled_box(self, plugin: InventoryPlugin) -> None:
        """Test drawing grid with unselected filled box (regular border)."""
        item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True)
        item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=True)
        plugin.all_items = [item1, item2]
        plugin.selected_row = 0
        plugin.selected_col = 0

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

            plugin._draw_inventory_grid(window)

            assert mock_outline.called

    def test_on_key_press_not_handled(self, plugin: InventoryPlugin) -> None:
        """Test that unhandled key press returns False."""
        plugin.showing = False

        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_KEY_TOGGLE = "I"

            result = plugin.on_key_press(arcade.key.A, 0)

            assert result is False

    def test_viewing_photo_other_key_handled(self, plugin: InventoryPlugin) -> None:
        """Test that other keys are consumed when viewing photo - covers branch 194->225."""
        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_KEY_TOGGLE = "I"

            plugin.showing = True
            plugin.viewing_photo = True

            result = plugin.on_key_press(arcade.key.A, 0)

            assert result is True
            assert plugin.viewing_photo is True

    def test_consume_item_no_selection_adjustment(self, plugin: InventoryPlugin) -> None:
        """Test consuming item when selection doesn't need adjustment - covers branch 308->exit."""
        with patch("pedre.plugins.inventory.plugin.settings") as mock_settings:
            mock_settings.INVENTORY_MAX_SPACE = 10
            mock_settings.INVENTORY_GRID_COLS = 5

            item1 = InventoryItem(id="i1", name="I1", description="D1", acquired=True, consumable=True)
            item2 = InventoryItem(id="i2", name="I2", description="D2", acquired=True, consumable=True)
            item3 = InventoryItem(id="i3", name="I3", description="D3", acquired=True, consumable=True)

            plugin.items["i1"] = item1
            plugin.items["i2"] = item2
            plugin.items["i3"] = item3
            plugin.all_items = [item1, item2, item3]

            plugin.selected_row = 0
            plugin.selected_col = 0

            plugin._consume_selected_item()

            assert plugin.selected_row == 0
            assert plugin.selected_col == 0

    def test_restore_save_state_without_inventory_items(self, plugin: InventoryPlugin) -> None:
        """Test restore_save_state when inventory_items key is missing - covers branch 691->exit."""
        item = InventoryItem(id="test", name="Test", description="D", acquired=True)
        plugin.items["test"] = item

        state = {"some_other_key": "value"}

        plugin.restore_save_state(state)

        assert "test" in plugin.items

    def test_to_dict_dynamic_item_not_in_items(self, plugin: InventoryPlugin) -> None:
        """Test to_dict when dynamic item ID is not in items dict - covers branch 1037->1036."""
        plugin.dynamic_items.add("nonexistent_id")

        data = plugin.to_dict()

        assert "dynamic_items" in data
        dynamic_ids = [item["id"] for item in data["dynamic_items"]]
        assert "nonexistent_id" not in dynamic_ids

    def test_from_dict_dynamic_item_already_exists(self, plugin: InventoryPlugin) -> None:
        """Test from_dict when dynamic item already exists in items - covers branch 1094->1091."""
        existing_item = InventoryItem(id="existing", name="Existing", description="D", acquired=True)
        plugin.items["existing"] = existing_item
        plugin.dynamic_items.add("existing")

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

        plugin.from_dict(data)

        assert plugin.items["existing"].name == "Existing"
