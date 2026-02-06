"""Inventory plugin for managing collectible items.

This module provides the InventoryPlugin class, which manages the player's collection
of items throughout the game. Items can represent various collectibles like photos,
notes, keys, or quest items that the player discovers and acquires during gameplay.

The inventory plugin supports:
- Defining items with metadata (name, description, image, category)
- Tracking which items the player has acquired
- Filtering items by category for organized display
- Persistence through save/load functionality
- Tracking first-time inventory access for tutorial/achievement plugins
- Publishing events when items are acquired

Items are organized into categories to allow for different types of collectibles:
- "photo": Visual memories and photographs
- "note": Written documents, letters, clues
- "key": Items that unlock doors or areas
- "general": Miscellaneous items

The plugin maintains a master list of all possible items, each with an 'acquired'
flag that tracks whether the player has collected it. This approach supports both
showing acquired items to the player and tracking completion progress.

Example usage:

    # Add a custom item
    key_item = InventoryItem(
        id="secret_key",
        name="Rusty Key",
        description="A key that might open something...",
        image_path="items/rusty_key.png",
        icon_path="items/icons/key_icon.png",
        category="key"
    )

    # Acquire item when player finds it (publishes ItemAcquiredEvent)
    if inventory_mgr.acquire_item("secret_key"):
        show_notification("Found: Rusty Key")

    # Check if player has item (for puzzle logic)
    if inventory_mgr.has_item("secret_key"):
        unlock_door()

    # Save/load support
    save_data = inventory_mgr.to_dict()
    # ... later ...
    inventory_mgr.from_dict(save_data)
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import arcade

from pedre.conf import settings
from pedre.constants import asset_path
from pedre.helpers import compute_ui_scale, matches_key, scale, scale_font
from pedre.plugins.inventory.base import InventoryBasePlugin, InventoryItem
from pedre.plugins.inventory.events import (
    InventoryClosedEvent,
    ItemAcquiredEvent,
    ItemAcquisitionFailedEvent,
    ItemConsumedEvent,
)
from pedre.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from typing import Any

    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


@PluginRegistry.register
class InventoryPlugin(InventoryBasePlugin):
    """Manages player's inventory and item collection.

    The InventoryPlugin acts as a central registry for all collectible items in game.
    It maintains a master list of possible items, tracks which ones player has acquired,
    and provides methods for querying, filtering, and persisting inventory state.

    This plugin supports multiple gameplay patterns:
    - **Collectathon**: Track progress toward collecting all items in a category
    - **Key items**: Gate progression behind acquiring specific items
    - **Gallery/album**: Display acquired photos or memories in a collection view
    - **Achievement tracking**: Monitor first-time inventory access for tutorials

    The plugin uses a dictionary-based storage where items are indexed by their unique ID
    for O(1) lookups. Items maintain insertion order (Python 3.7+), which is important for
    displaying items in a consistent, meaningful order (e.g., chronological for photos).

    The inventory state is designed to be serializable to/from dictionaries, making it
    compatible with JSON-based save plugins. The get_save_state() and restore_save_state() methods handle
    conversion between plugin's internal state and save data format.

    Attributes:
        items: Dictionary mapping item IDs to InventoryItem instances. Maintains insertion
              order for consistent display. All possible items are stored here regardless
              of acquisition status.
        accessed: Boolean flag tracking whether player has opened the inventory
                          view at least once. Used for tutorial prompts, achievements, or
                          quest progression that requires checking inventory.
        event_bus: Optional event bus for publishing ItemAcquiredEvent when items are obtained.
    """

    name: ClassVar[str] = "inventory"
    dependencies: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """Initialize inventory plugin with default items.

        Creates a new InventoryPlugin with an empty items dictionary and unaccessed status.
        Items will be loaded in setup() method.

        This initialization approach separates the plugin's setup (empty state) from
        the game's content (default items), making it easier to modify starting items
        or load from save data without changing the plugin's core initialization.
        """
        # Asset paths are resolved via resource handles - no need to store them

        # All available items
        self.items: dict[str, InventoryItem] = {}

        # Track dynamically added items (not from JSON file)
        self.dynamic_items: set[str] = set()

        # Track if inventory has been accessed
        self.accessed: bool = False

        # Overlay state
        self.showing: bool = False
        self.selected_row: int = 0
        self.selected_col: int = 0
        self.viewing_photo: bool = False
        self.current_photo_texture: arcade.Texture | None = None
        self.all_items: list[InventoryItem] = []

        # Texture caches
        self.icon_textures: dict[str, arcade.Texture] = {}
        self.background_texture: arcade.Texture | None = None

        # Text objects (created on first draw for efficiency)
        self.selected_item_text: arcade.Text | None = None
        self.photo_title_text: arcade.Text | None = None
        self.photo_description_text: arcade.Text | None = None
        self.capacity_text: arcade.Text | None = None
        self.hint_text: arcade.Text | None = None

    def setup(self, context: GameContext) -> None:
        """Initialize the inventory plugin with game context and settings.

        Args:
            context: Game context providing access to event bus.
        """
        super().setup(context)

        # Initialize default items
        self._initialize_default_items()

    def cleanup(self) -> None:
        """Clean up inventory resources when the scene unloads."""
        self.items.clear()
        self.accessed = False
        logger.debug("InventoryPlugin cleanup complete")

    def reset(self) -> None:
        """Reset inventory state for new game."""
        self.items.clear()
        self.dynamic_items.clear()  # Clear tracking of dynamic items
        self.accessed = False
        self.showing = False
        self.viewing_photo = False
        self.current_photo_texture = None
        self.all_items = []
        self.icon_textures.clear()
        self._initialize_default_items()
        logger.debug("InventoryPlugin reset complete")

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle key presses for inventory overlay."""
        # Toggle inventory with I key
        if matches_key(symbol, settings.INVENTORY_KEY_TOGGLE) and not self.showing:
            self._show_inventory()
            return True

        # Handle input when overlay is showing
        if self.showing:
            if self.viewing_photo:
                # Close photo view
                if symbol == arcade.key.ESCAPE:
                    self.viewing_photo = False
                    self.current_photo_texture = None
                    return True
            # Grid navigation
            elif symbol == arcade.key.ESCAPE:
                self.showing = False
                self.viewing_photo = False
                self.current_photo_texture = None
                self.context.event_bus.publish(InventoryClosedEvent(has_been_accessed=self.accessed))
                logger.info("Published InventoryClosedEvent (accessed=%s)", self.accessed)
                logger.debug("Inventory overlay hidden")
                return True
            elif symbol == arcade.key.UP:
                self._move_selection(0, -1)
                return True
            elif symbol == arcade.key.DOWN:
                self._move_selection(0, 1)
                return True
            elif symbol == arcade.key.LEFT:
                self._move_selection(-1, 0)
                return True
            elif symbol == arcade.key.RIGHT:
                self._move_selection(1, 0)
                return True
            elif matches_key(symbol, settings.INVENTORY_KEY_VIEW):
                self._view_selected_item()
                return True
            elif matches_key(symbol, settings.INVENTORY_KEY_CONSUME):
                self._consume_selected_item()
                return True
            return True  # Consume all input when overlay is showing

        return False

    def _show_inventory(self) -> None:
        """Show the inventory overlay."""
        self.showing = True
        self.viewing_photo = False
        self.current_photo_texture = None
        self.selected_row = 0
        self.selected_col = 0

        # Load background image if not already loaded
        if self.background_texture is None and settings.INVENTORY_BACKGROUND_IMAGE:
            background_path = asset_path(settings.INVENTORY_BACKGROUND_IMAGE, settings.ASSETS_HANDLE)
            try:
                self.background_texture = arcade.load_texture(background_path)
                logger.info("Loaded inventory background: %s", background_path)
            except FileNotFoundError:
                logger.warning("Background image not found: %s", background_path)

        # Mark inventory as accessed
        if not self.accessed:
            self.accessed = True
            logger.info("Inventory accessed for the first time")

        # Get only acquired items for grid display
        self.all_items = self._get_acquired_items()

        # Load icon textures for acquired items
        self.icon_textures.clear()

        for item in self.all_items:
            if item.icon_path:
                icon_path = asset_path(f"{item.icon_path}")
                try:
                    self.icon_textures[item.id] = arcade.load_texture(icon_path)
                    logger.debug("Loaded icon for item: %s", item.id)
                except (FileNotFoundError, OSError):
                    logger.warning("Failed to load icon for item: %s at %s", item.id, icon_path)

        logger.debug("Inventory overlay shown")

    def _move_selection(self, delta_col: int, delta_row: int) -> None:
        """Move selection in the grid with wrapping."""
        self.selected_col = (self.selected_col + delta_col) % settings.INVENTORY_GRID_COLS
        self.selected_row = (self.selected_row + delta_row) % settings.INVENTORY_GRID_ROWS

    def _consume_selected_item(self) -> None:
        """Consume the currently selected item if it's consumable."""
        selected_index = self.selected_row * settings.INVENTORY_GRID_COLS + self.selected_col

        if selected_index >= len(self.all_items):
            return

        item = self.all_items[selected_index]

        # Check if item is consumable
        if not item.consumable:
            logger.debug("Item %s is not consumable", item.id)
            return

        # Consume the item
        if self.consume_item(item.id):
            logger.info("Consumed item from inventory overlay: %s", item.name)

            self.context.event_bus.publish(
                ItemConsumedEvent(item_id=item.id, item_name=item.name, category=item.category)
            )
            logger.info(
                "Published ItemConsumedEvent (item_id=%s, item_name=%s, category=%s)",
                item.id,
                item.name,
                item.category,
            )

            # Refresh the item list to remove consumed item from display
            self.all_items = self._get_acquired_items()

            # Adjust selection if we're now beyond the end of the list
            max_index = len(self.all_items) - 1
            if max_index >= 0:
                current_index = self.selected_row * settings.INVENTORY_GRID_COLS + self.selected_col
                if current_index > max_index:
                    # Move selection to last item
                    self.selected_row = max_index // settings.INVENTORY_GRID_COLS
                    self.selected_col = max_index % settings.INVENTORY_GRID_COLS
        else:
            logger.debug("Failed to consume item: %s", item.id)

    def _view_selected_item(self) -> None:
        """View the currently selected item (photo) in full-screen mode."""
        selected_index = self.selected_row * settings.INVENTORY_GRID_COLS + self.selected_col

        if selected_index >= len(self.all_items):
            return

        item = self.all_items[selected_index]

        # Get image path
        if not item.image_path:
            logger.warning("No image path configured for item: %s", item.id)
            return

        image_path = asset_path(f"{item.image_path}")

        try:
            # Load and display photo
            self.current_photo_texture = arcade.load_texture(image_path)
            self.viewing_photo = True
            logger.info("Loaded photo: %s", item.name)
        except Exception:
            logger.exception("Failed to load photo: %s", image_path)

    def on_draw_ui(self) -> None:
        """Draw the inventory overlay in screen coordinates."""
        if not self.showing:
            return

        window = self.context.window
        if not window:
            return

        if self.viewing_photo and self.current_photo_texture:
            self._draw_photo_view(window)
        else:
            self._draw_inventory_grid(window)

    def _draw_inventory_grid(self, window: arcade.Window) -> None:
        """Draw the inventory grid overlay."""
        design = settings.INVENTORY_DESIGN

        # Compute scale factor
        ui_scale = compute_ui_scale(
            window.width,
            window.height,
            min_scale=settings.INVENTORY_UI_SCALE_MIN,
            max_scale=settings.INVENTORY_UI_SCALE_MAX,
        )

        # Scale design values
        box_size = scale(design["box_size"], ui_scale)
        box_spacing = scale(design["box_spacing"], ui_scale)
        box_border_width = scale(design["box_border_width"], ui_scale)
        icon_padding = scale(design["icon_padding"], ui_scale)
        grid_y_offset = scale(design["grid_y_offset"], ui_scale)
        item_name_y_offset = scale(design["item_name_y_offset"], ui_scale)
        hint_y_offset = scale(design["hint_y_offset"], ui_scale)
        capacity_x_offset = scale(design["capacity_x_offset"], ui_scale)
        capacity_y_offset = scale(design["capacity_y_offset"], ui_scale)

        # Scale fonts
        item_name_font_size = scale_font(
            settings.UI_FONT_NORMAL, ui_scale, settings.INVENTORY_UI_SCALE_MIN, settings.INVENTORY_UI_SCALE_MAX
        )
        hint_font_size = scale_font(
            settings.UI_FONT_SMALL, ui_scale, settings.INVENTORY_UI_SCALE_MIN, settings.INVENTORY_UI_SCALE_MAX
        )
        capacity_font_size = scale_font(
            settings.UI_FONT_SMALL, ui_scale, settings.INVENTORY_UI_SCALE_MIN, settings.INVENTORY_UI_SCALE_MAX
        )

        # Calculate overlay dimensions
        overlay_height = int(window.height * design["overlay_height_fraction"])

        # Draw solid background overlay
        arcade.draw_lrbt_rectangle_filled(
            0,
            window.width,
            0,
            overlay_height,
            (*settings.INVENTORY_COLOR_OVERLAY, settings.INVENTORY_OVERLAY_ALPHA),
        )

        # Draw background image if loaded (optional decorative background)
        if self.background_texture:
            arcade.draw_texture_rect(
                self.background_texture,
                arcade.LBWH(0, 0, window.width, window.height),
            )

        # Calculate grid positioning (centered within the overlay area)
        grid_width = settings.INVENTORY_GRID_COLS * box_size + (settings.INVENTORY_GRID_COLS - 1) * box_spacing
        grid_height = settings.INVENTORY_GRID_ROWS * box_size + (settings.INVENTORY_GRID_ROWS - 1) * box_spacing

        start_x = (window.width - grid_width) / 2
        start_y = (overlay_height - grid_height) / 2 + grid_y_offset  # Center within overlay with offset

        # Draw grid boxes
        for row in range(settings.INVENTORY_GRID_ROWS):
            for col in range(settings.INVENTORY_GRID_COLS):
                item_index = row * settings.INVENTORY_GRID_COLS + col

                # Calculate box position (top-left corner)
                x = start_x + col * (box_size + box_spacing)
                y = start_y + (settings.INVENTORY_GRID_ROWS - 1 - row) * (box_size + box_spacing)

                # Determine if this slot has an item
                has_item = item_index < len(self.all_items)
                item = self.all_items[item_index] if has_item else None
                is_selected = row == self.selected_row and col == self.selected_col

                # Draw box background and border based on slot state
                if item:
                    # FILLED SLOT: Draw solid background with item icon
                    arcade.draw_lrbt_rectangle_filled(
                        x, x + box_size, y, y + box_size, settings.INVENTORY_COLOR_BOX_FILLED
                    )

                    # Draw border (yellow if selected, white otherwise)
                    if is_selected:
                        border_color = settings.INVENTORY_COLOR_BOX_BORDER_SELECTED
                        border_width = box_border_width + 1
                    else:
                        border_color = settings.INVENTORY_COLOR_BOX_BORDER
                        border_width = box_border_width

                    arcade.draw_lrbt_rectangle_outline(
                        x,
                        x + box_size,
                        y,
                        y + box_size,
                        border_color,
                        border_width,
                    )

                    # Draw icon if available
                    icon_texture = self.icon_textures.get(item.id)
                    if icon_texture:
                        # Scale icon to fit box with padding
                        max_icon_size = box_size - (icon_padding * 2)

                        # Calculate scale to fit
                        scale_x = max_icon_size / icon_texture.width
                        scale_y = max_icon_size / icon_texture.height
                        icon_scale = min(scale_x, scale_y)

                        # Draw centered icon
                        icon_width = icon_texture.width * icon_scale
                        icon_height = icon_texture.height * icon_scale
                        icon_center_x = x + box_size / 2
                        icon_center_y = y + box_size / 2

                        arcade.draw_texture_rect(
                            icon_texture,
                            arcade.LRBT(
                                icon_center_x - icon_width / 2,
                                icon_center_x + icon_width / 2,
                                icon_center_y - icon_height / 2,
                                icon_center_y + icon_height / 2,
                            ),
                        )
                else:
                    # EMPTY SLOT: Draw semi-transparent dark background
                    arcade.draw_lrbt_rectangle_filled(
                        x,
                        x + box_size,
                        y,
                        y + box_size,
                        (*settings.INVENTORY_COLOR_BOX_EMPTY, settings.INVENTORY_EMPTY_BOX_ALPHA),
                    )

                    # Draw subdued border (yellow if selected, dim gray otherwise)
                    if is_selected:
                        border_color = settings.INVENTORY_COLOR_BOX_BORDER_SELECTED
                        border_width = box_border_width + 1
                    else:
                        border_color = settings.INVENTORY_COLOR_BOX_BORDER_EMPTY
                        border_width = max(1, box_border_width - 1)

                    arcade.draw_lrbt_rectangle_outline(
                        x,
                        x + box_size,
                        y,
                        y + box_size,
                        border_color,
                        border_width,
                    )

        # Draw selected item name and hints at bottom
        selected_index = self.selected_row * settings.INVENTORY_GRID_COLS + self.selected_col
        if selected_index < len(self.all_items):
            selected_item = self.all_items[selected_index]

            # Draw item name
            if self.selected_item_text is None:
                self.selected_item_text = arcade.Text(
                    selected_item.name,
                    window.width / 2,
                    item_name_y_offset,
                    settings.INVENTORY_COLOR_TEXT_ITEM_NAME,
                    font_size=item_name_font_size,
                    anchor_x="center",
                    anchor_y="bottom",
                    bold=True,
                )
            else:
                self.selected_item_text.text = selected_item.name
                self.selected_item_text.x = window.width / 2
                self.selected_item_text.y = item_name_y_offset
                self.selected_item_text.color = settings.INVENTORY_COLOR_TEXT_ITEM_NAME
                self.selected_item_text.font_size = item_name_font_size

            self.selected_item_text.draw()

            # Draw hints
            hints = []
            if selected_item.image_path:
                hints.append(settings.INVENTORY_HINT_VIEW)
            if selected_item.consumable:
                hints.append(settings.INVENTORY_HINT_CONSUME)

            if hints:
                hint_text_str = "  ".join(hints)
                if self.hint_text is None:
                    self.hint_text = arcade.Text(
                        hint_text_str,
                        window.width / 2,
                        hint_y_offset,
                        settings.INVENTORY_COLOR_TEXT_HINT,
                        font_size=hint_font_size,
                        anchor_x="center",
                        anchor_y="bottom",
                    )
                else:
                    self.hint_text.text = hint_text_str
                    self.hint_text.x = window.width / 2
                    self.hint_text.y = hint_y_offset
                    self.hint_text.color = settings.INVENTORY_COLOR_TEXT_HINT
                    self.hint_text.font_size = hint_font_size

                self.hint_text.draw()

        # Draw inventory capacity at bottom-right
        current_count = len(self.all_items)
        max_space = settings.INVENTORY_MAX_SPACE
        capacity_label = f"{current_count}/{max_space}"

        if self.capacity_text is None:
            self.capacity_text = arcade.Text(
                capacity_label,
                window.width - capacity_x_offset,
                capacity_y_offset,
                settings.INVENTORY_COLOR_TEXT_CAPACITY,
                font_size=capacity_font_size,
                anchor_x="right",
                anchor_y="bottom",
            )
        else:
            self.capacity_text.text = capacity_label
            self.capacity_text.x = window.width - capacity_x_offset
            self.capacity_text.y = capacity_y_offset
            self.capacity_text.color = settings.INVENTORY_COLOR_TEXT_CAPACITY
            self.capacity_text.font_size = capacity_font_size

        self.capacity_text.draw()

    def _draw_photo_view(self, window: arcade.Window) -> None:
        """Draw the photo viewing overlay."""
        if not self.current_photo_texture:
            return

        design = settings.INVENTORY_DESIGN

        # Compute scale factor
        ui_scale = compute_ui_scale(
            window.width,
            window.height,
            min_scale=settings.INVENTORY_UI_SCALE_MIN,
            max_scale=settings.INVENTORY_UI_SCALE_MAX,
        )

        # Scale design values
        text_area_height = scale(design["photo_text_area_height"], ui_scale)
        photo_title_y_offset = scale(design["photo_title_y_offset"], ui_scale)
        photo_description_y_offset = scale(design["photo_description_y_offset"], ui_scale)

        # Scale fonts
        photo_title_font_size = scale_font(
            settings.UI_FONT_LARGE, ui_scale, settings.INVENTORY_UI_SCALE_MIN, settings.INVENTORY_UI_SCALE_MAX
        )
        photo_description_font_size = scale_font(
            settings.UI_FONT_SMALL, ui_scale, settings.INVENTORY_UI_SCALE_MIN, settings.INVENTORY_UI_SCALE_MAX
        )

        # Draw solid background
        arcade.draw_lrbt_rectangle_filled(0, window.width, 0, window.height, settings.INVENTORY_COLOR_PHOTO_BACKGROUND)

        # Get selected item
        selected_index = self.selected_row * settings.INVENTORY_GRID_COLS + self.selected_col
        if 0 <= selected_index < len(self.all_items):
            item = self.all_items[selected_index]

            # Calculate photo display size
            max_width = window.width * design["photo_max_width_fraction"]
            max_height = (window.height - text_area_height) * design["photo_max_height_fraction"]

            # Calculate scale to fit
            width_scale = max_width / self.current_photo_texture.width
            height_scale = max_height / self.current_photo_texture.height
            photo_scale = min(width_scale, height_scale)

            # Calculate final dimensions
            final_width = self.current_photo_texture.width * photo_scale
            final_height = self.current_photo_texture.height * photo_scale

            # Center the photo vertically in the space above the text area
            available_vertical_space = window.height - text_area_height
            photo_center_y = text_area_height + available_vertical_space / 2
            photo_center_x = window.width / 2

            # Draw photo
            arcade.draw_texture_rect(
                self.current_photo_texture,
                arcade.LRBT(
                    photo_center_x - final_width / 2,
                    photo_center_x + final_width / 2,
                    photo_center_y - final_height / 2,
                    photo_center_y + final_height / 2,
                ),
            )

            # Draw photo title
            if self.photo_title_text is None:
                self.photo_title_text = arcade.Text(
                    item.name,
                    window.width / 2,
                    photo_title_y_offset,
                    settings.INVENTORY_COLOR_TEXT_PHOTO_TITLE,
                    font_size=photo_title_font_size,
                    anchor_x="center",
                )
            else:
                self.photo_title_text.text = item.name
                self.photo_title_text.x = window.width / 2
                self.photo_title_text.y = photo_title_y_offset
                self.photo_title_text.color = settings.INVENTORY_COLOR_TEXT_PHOTO_TITLE
                self.photo_title_text.font_size = photo_title_font_size

            self.photo_title_text.draw()

            # Draw photo description
            if self.photo_description_text is None:
                self.photo_description_text = arcade.Text(
                    item.description,
                    window.width / 2,
                    photo_description_y_offset,
                    settings.INVENTORY_COLOR_TEXT_PHOTO_DESCRIPTION,
                    font_size=photo_description_font_size,
                    anchor_x="center",
                )
            else:
                self.photo_description_text.text = item.description
                self.photo_description_text.x = window.width / 2
                self.photo_description_text.y = photo_description_y_offset
                self.photo_description_text.color = settings.INVENTORY_COLOR_TEXT_PHOTO_DESCRIPTION
                self.photo_description_text.font_size = photo_description_font_size

            self.photo_description_text.draw()

    def get_save_state(self) -> dict[str, Any]:
        """Return serializable state for saving (BasePlugin interface)."""
        return {"inventory_items": self.to_dict()}

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Restore state from save data (BasePlugin interface)."""
        if "inventory_items" in state:
            self.from_dict(state["inventory_items"])

    def _initialize_default_items(self) -> None:
        """Initialize default inventory items from JSON data file."""
        try:
            items_file = asset_path(settings.INVENTORY_ITEMS_FILE)

            with Path(items_file).open("r", encoding="utf-8") as f:
                data = json.load(f)

            for item_data in data.get("items", []):
                item = InventoryItem(
                    id=item_data["id"],
                    name=item_data["name"],
                    description=item_data["description"],
                    image_path=item_data.get("image_path"),
                    icon_path=item_data.get("icon_path"),
                    category=item_data.get("category", "general"),
                    acquired=item_data.get("acquired", False),
                    consumable=item_data.get("consumable", False),
                )
                self.items[item.id] = item

            logger.info("Loaded %d inventory items from JSON", len(self.items))

        except FileNotFoundError as e:
            logger.warning(
                "Inventory items file not found: %s",
                e.filename if hasattr(e, "filename") else "data/inventory_items.json",
            )
        except json.JSONDecodeError:
            logger.exception("Failed to parse inventory items JSON")
        except KeyError:
            logger.exception("Missing required field in inventory item data")
        except OSError as e:
            if "No such file or directory" in str(e):
                logger.warning("Assets directory or inventory items file not found, continuing with empty inventory")
            else:
                logger.warning("Failed to load inventory items (continuing with empty inventory): %s", str(e))

    def add_item(self, item: InventoryItem) -> bool:
        """Add a new item to the inventory plugin and optionally acquire it.

        This method allows dynamically adding items that aren't defined in inventory_items.json.
        This is useful for consumable items (like potions) that can be obtained through gameplay
        actions rather than being part of the static item definitions.

        If an item with the same ID already exists, this method will not overwrite it and will
        return False. Use acquire_item() to mark existing items as acquired.

        The item's acquired flag determines whether it's immediately added to the player's
        inventory or just registered in the plugin. Set acquired=True for items that should
        be immediately available (e.g., picking up a potion), or acquired=False for items
        that need to be acquired later.

        Note: When using AddItemAction from scripts, you can omit the item_id to have a UUID
        automatically generated. This is useful for consumable items where you want to add
        multiple instances without worrying about ID conflicts.

        Args:
            item: The InventoryItem to add to the plugin. Must have a unique ID.

        Returns:
            True if the item was successfully added, False if an item with that ID already exists
            or if adding it would exceed inventory capacity.

        Example:
            # Add a health potion that's immediately available
            potion = InventoryItem(
                id=str(uuid.uuid4()),  # Generate unique ID
                name="Health Potion",
                description="Restores 50 HP",
                icon_path="items/potion.png",
                category="consumable",
                acquired=True
            )
            if inventory_mgr.add_item(potion):
                show_notification("Found: Health Potion!")
        """
        if item.id in self.items:
            logger.warning("Attempted to add item with existing ID: %s", item.id)
            return False

        self.items[item.id] = item
        self.dynamic_items.add(item.id)  # Track as dynamically added
        logger.info("Added new dynamically created item to inventory plugin: %s (%s)", item.id, item.name)

        # If the item is already marked as acquired, publish the event and check capacity
        if item.acquired:
            current_count = len(self._get_acquired_items())
            if current_count > settings.INVENTORY_MAX_SPACE:
                logger.warning(
                    "Item %s added exceeds inventory capacity (%d/%d)",
                    item.id,
                    current_count,
                    settings.INVENTORY_MAX_SPACE,
                )
                # Don't publish event if capacity is exceeded
                self.context.event_bus.publish(ItemAcquisitionFailedEvent(item_id=item.id, reason="capacity"))
                logger.info("Published ItemAcquisitionFailedEvent (item_id=%s, reason=capacity)", item.id)
                # Remove the item since it exceeds capacity
                del self.items[item.id]
                return False

            self.context.event_bus.publish(ItemAcquiredEvent(item_id=item.id, item_name=item.name))
            logger.info("Published ItemAcquiredEvent (item_id=%s, item_name=%s)", item.id, item.name)

        return True

    def acquire_item(self, item_id: str) -> bool:
        """Mark an item as acquired by the player.

        Gives the specified item to the player by setting its acquired flag to True. This
        method is typically called when the player finds, picks up, or earns an item through
        gameplay actions.

        The method enforces inventory capacity limits. If the inventory is at maximum capacity
        (INVENTORY_MAX_SPACE setting), the acquisition will fail and False is returned.

        The method includes logic to detect whether the item is being acquired for the first
        time or was already in the player's possession. This distinction is useful for:
        - Showing "item acquired" notifications only on first pickup
        - Preventing duplicate acquisition sound effects or animations
        - Tracking which items are newly acquired vs previously owned
        - Publishing ItemAcquiredEvent only for new acquisitions

        If the item ID doesn't exist in the registry, a warning is logged and False is
        returned. This helps catch typos or missing item definitions during development.

        When an item is newly acquired, an ItemAcquiredEvent is published to the event bus
        (if one was provided during initialization), allowing scripts to react to item
        acquisition.

        Args:
            item_id: The unique identifier of the item to acquire (e.g., "rusty_key",
                    "photo_01"). Must match an item previously added to the plugin.

        Returns:
            True if the item was newly acquired (transitioned from unacquired to acquired),
            False if the item was not found, was already acquired, or inventory is at capacity.
            Use this return value to trigger "new item" feedback to the player.

        Example:
            # When player picks up an item
            if inventory_mgr.acquire_item("ancient_scroll"):
                # Item was newly acquired
                show_notification("Found: Ancient Scroll!")
                audio_mgr.play_sfx("item_get.wav")
                particle_mgr.emit_sparkles(player.center_x, player.center_y)
            else:
                # Item was already owned, doesn't exist, or inventory is full
                pass
        """
        if item_id not in self.items:
            logger.warning("Attempted to acquire unknown item: %s", item_id)
            self.context.event_bus.publish(ItemAcquisitionFailedEvent(item_id=item_id, reason="unknown_item"))
            logger.info("Published ItemAcquisitionFailedEvent (item_id=%s, reason=unknown_item)", item_id)
            return False

        if not self.items[item_id].acquired:
            # Check inventory capacity before acquiring
            current_count = len(self._get_acquired_items())
            if current_count >= settings.INVENTORY_MAX_SPACE:
                logger.warning(
                    "Cannot acquire item %s: inventory is at maximum capacity (%d/%d)",
                    item_id,
                    current_count,
                    settings.INVENTORY_MAX_SPACE,
                )
                self.context.event_bus.publish(ItemAcquisitionFailedEvent(item_id=item_id, reason="capacity"))
                logger.info("Published ItemAcquisitionFailedEvent (item_id=%s, reason=capacity)", item_id)
                return False

            item = self.items[item_id]
            item.acquired = True
            logger.info("Player acquired item: %s (%s)", item_id, item.name)

            # Publish event if event bus is available
            self.context.event_bus.publish(ItemAcquiredEvent(item_id=item_id, item_name=item.name))
            logger.info("Published ItemAcquiredEvent (item_id=%s, item_name=%s)", item_id, item.name)

            return True

        # Item already owned
        self.context.event_bus.publish(ItemAcquisitionFailedEvent(item_id=item_id, reason="already_owned"))
        logger.info("Published ItemAcquisitionFailedEvent (item_id=%s, reason=already_owned)", item_id)
        return False

    def consume_item(self, item_id: str) -> bool:
        """Mark an item as consumed by the player.

        Consumes a specified item by setting its consumed flag to True. This method can only
        consume items that have been acquired and not already consumed. Once consumed, items
        will no longer appear in the inventory display.

        Args:
            item_id: The unique identifier of the item to consume (e.g., "health_potion",
                    "key_card"). Must match an item previously added to the plugin.

        Returns:
            True if the item was successfully consumed (was acquired and not already consumed),
            False if the item doesn't exist, hasn't been acquired, or was already consumed.

        Example:
            # When player uses a consumable item
            if inventory_mgr.consume_item("health_potion"):
                # Item was consumed successfully
                restore_player_health(50)
            else:
                # Item couldn't be consumed (not available)
                show_message("You don't have that item!")
        """
        if item_id not in self.items:
            logger.warning("Attempted to consume unknown item: %s", item_id)
            return False

        item = self.items[item_id]
        if item.acquired and not item.consumed:
            item.consumed = True
            logger.info("Player consumed item: %s (%s)", item_id, item.name)
            return True

        return False

    def has_item(self, item_id: str) -> bool:
        """Check if the player has acquired a specific item.

        Queries whether the player currently possesses the specified item. This is commonly
        used for conditional logic in gameplay, such as checking if the player has the key
        needed to unlock a door or if they've found a quest item.

        The method returns False if the item ID doesn't exist in the registry OR if the
        item exists but hasn't been acquired. This unified False response simplifies
        conditional logic where you only care whether the player can proceed.

        This is a pure query method with no side effects - it doesn't modify any state
        or trigger any events.

        Args:
            item_id: The unique identifier of the item to check (e.g., "tower_key",
                    "quest_token"). Case-sensitive and must match exactly.

        Returns:
            True if the player has acquired the item (item exists and acquired=True),
            False if the item doesn't exist or hasn't been acquired yet.

        Example:
            # Check for key before allowing door interaction
            if inventory_mgr.has_item("tower_key"):
                unlock_door("tower_entrance")
                dialog_mgr.show_dialog("Info", ["The key fits perfectly!"])
            else:
                dialog_mgr.show_dialog("Info", ["The door is locked."])

            # Quest condition check
            if inventory_mgr.has_item("herb_1") and inventory_mgr.has_item("herb_2"):
                complete_alchemy_quest()
        """
        return item_id in self.items and self.items[item_id].acquired

    def _get_acquired_items(self, category: str | None = None) -> list[InventoryItem]:
        """Get all items the player has acquired and not consumed, optionally filtered by category.

        Returns a list of all items where acquired=True and consumed=False, maintaining the
        insertion order from when items were added to the plugin. This method is commonly used
        to display the player's inventory in UI screens.

        Consumed items are excluded from the results, so only available (usable) items are returned.

        The optional category filter allows for displaying specific types of items, such
        as showing only photos in a gallery view or only keys in a key ring interface.

        Items are returned in insertion order, which is important for chronological display
        (e.g., photos in the order they were collected) or logical grouping (e.g., quest
        items in story order).

        Args:
            category: Optional category string to filter results (e.g., "photo", "key",
                     "note"). If None, returns all acquired, unconsumed items regardless of
                     category. Category matching is exact and case-sensitive.

        Returns:
            List of InventoryItem instances where acquired=True and consumed=False, filtered
            by category if specified. Returns empty list if no items match the criteria.
            The list maintains insertion order from the items dictionary.
        """
        acquired = [item for item in self.items.values() if item.acquired and not item.consumed]

        if category:
            acquired = [item for item in acquired if item.category == category]

        return acquired

    def _get_acquired_count(self, category: str | None = None) -> int:
        """Get the count of items the player has acquired.

        Convenience method that returns the number of acquired items, optionally filtered
        by category. Equivalent to len(get_acquired_items(category)).

        Args:
            category: Optional category filter. If None, counts all acquired items.

        Returns:
            Integer count of acquired items matching the filter.
        """
        return len(self._get_acquired_items(category))

    def has_been_accessed(self) -> bool:
        """Check if inventory has been accessed."""
        return self.accessed

    def to_dict(self) -> dict[str, Any]:
        """Convert inventory state to dictionary for save data serialization.

        Exports the acquisition and consumption status of all items as a dictionary mapping
        item IDs to state dictionaries. This dictionary can be serialized to JSON or other
        formats for persistent storage.

        For items loaded from the JSON file, only acquired and consumed status is saved.
        For dynamically added items (via add_item()), the full item data is saved to restore them.

        Returns:
            Dictionary with two keys:
            - "item_states": Maps item IDs to {acquired, consumed} for JSON-loaded items
            - "dynamic_items": List of full item data dicts for dynamically added items

        Example:
            # Save to JSON file
            import json
            save_data = {
                "inventory": inventory_mgr.to_dict(),
                "player_position": (x, y),
                # ... other save data
            }
            with open("save.json", "w") as f:
                json.dump(save_data, f)
        """
        # Save state for all items
        item_states = {
            item_id: {"acquired": item.acquired, "consumed": item.consumed} for item_id, item in self.items.items()
        }

        # Save full data for dynamically added items
        dynamic_item_data = []
        for item_id in self.dynamic_items:
            if item_id in self.items:
                item = self.items[item_id]
                dynamic_item_data.append(
                    {
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "image_path": item.image_path,
                        "icon_path": item.icon_path,
                        "category": item.category,
                        "acquired": item.acquired,
                        "consumed": item.consumed,
                        "consumable": item.consumable,
                    }
                )

        return {
            "item_states": item_states,
            "dynamic_items": dynamic_item_data,
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        """Load inventory state from saved dictionary data.

        Restores the acquisition and consumption status of items from a previously saved
        dictionary. This method updates the acquired and consumed flags of existing items
        and recreates dynamically added items.

        Args:
            data: Dictionary containing:
                 - "item_states": Maps item IDs to {acquired, consumed} state
                 - "dynamic_items": List of full item data for dynamically added items

        Example:
            # Load from JSON file
            import json
            with open("save.json", "r") as f:
                save_data = json.load(f)

            inventory_mgr.from_dict(save_data["inventory"])
            # Player's inventory is now restored
        """
        item_states = data.get("item_states", {})
        dynamic_items_data = data.get("dynamic_items", [])

        # Restore states for existing items
        for item_id, state in item_states.items():
            if item_id in self.items:
                self.items[item_id].acquired = state.get("acquired", False)
                self.items[item_id].consumed = state.get("consumed", False)
            else:
                logger.warning("Unknown item in save data: %s", item_id)

        # Restore dynamically added items
        for item_data in dynamic_items_data:
            item_id = item_data["id"]
            # Only add if not already present (avoid duplicates)
            if item_id not in self.items:
                item = InventoryItem(
                    id=item_id,
                    name=item_data["name"],
                    description=item_data["description"],
                    image_path=item_data.get("image_path"),
                    icon_path=item_data.get("icon_path"),
                    category=item_data.get("category", "general"),
                    acquired=item_data.get("acquired", False),
                    consumed=item_data.get("consumed", False),
                    consumable=item_data.get("consumable", False),
                )
                self.items[item_id] = item
                self.dynamic_items.add(item_id)
                logger.info("Restored dynamically added item from save: %s (%s)", item_id, item.name)
