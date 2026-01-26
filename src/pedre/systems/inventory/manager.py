"""Inventory system for managing collectible items.

This module provides the InventoryManager class, which manages the player's collection
of items throughout the game. Items can represent various collectibles like photos,
notes, keys, or quest items that the player discovers and acquires during gameplay.

The inventory system supports:
- Defining items with metadata (name, description, image, category)
- Tracking which items the player has acquired
- Filtering items by category for organized display
- Persistence through save/load functionality
- Tracking first-time inventory access for tutorial/achievement systems
- Publishing events when items are acquired

Items are organized into categories to allow for different types of collectibles:
- "photo": Visual memories and photographs
- "note": Written documents, letters, clues
- "key": Items that unlock doors or areas
- "general": Miscellaneous items

The manager maintains a master list of all possible items, each with an 'acquired'
flag that tracks whether the player has collected it. This approach supports both
showing acquired items to the player and tracking completion progress.

Example usage:
    # Initialize manager with event bus
    inventory_mgr = InventoryManager(event_bus)

    # Add a custom item
    key_item = InventoryItem(
        id="secret_key",
        name="Rusty Key",
        description="A key that might open something...",
        image_path="items/rusty_key.png",
        icon_path="items/icons/key_icon.png",
        category="key"
    )
    inventory_mgr.add_item(key_item)

    # Acquire item when player finds it (publishes ItemAcquiredEvent)
    if inventory_mgr.acquire_item("secret_key"):
        show_notification("Found: Rusty Key")

    # Check if player has item (for puzzle logic)
    if inventory_mgr.has_item("secret_key"):
        unlock_door()

    # Display acquired photos in UI
    photos = inventory_mgr.get_acquired_items(category="photo")
    for photo in photos:
        display_photo(photo)

    # Save/load support
    save_data = inventory_mgr.to_dict()
    # ... later ...
    inventory_mgr.from_dict(save_data)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import arcade

from pedre.conf import settings
from pedre.constants import asset_path
from pedre.systems.inventory.base import InventoryBaseManager, InventoryItem
from pedre.systems.inventory.events import InventoryClosedEvent, ItemAcquiredEvent
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from typing import Any

    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@SystemRegistry.register
class InventoryManager(InventoryBaseManager):
    """Manages player's inventory and item collection.

    The InventoryManager acts as a central registry for all collectible items in game.
    It maintains a master list of possible items, tracks which ones player has acquired,
    and provides methods for querying, filtering, and persisting inventory state.

    This manager supports multiple gameplay patterns:
    - **Collectathon**: Track progress toward collecting all items in a category
    - **Key items**: Gate progression behind acquiring specific items
    - **Gallery/album**: Display acquired photos or memories in a collection view
    - **Achievement tracking**: Monitor first-time inventory access for tutorials

    The manager uses a dictionary-based storage where items are indexed by their unique ID
    for O(1) lookups. Items maintain insertion order (Python 3.7+), which is important for
    displaying items in a consistent, meaningful order (e.g., chronological for photos).

    The inventory state is designed to be serializable to/from dictionaries, making it
    compatible with JSON-based save systems. The get_save_state() and restore_save_state() methods handle
    conversion between manager's internal state and save data format.

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
        """Initialize inventory manager with default items.

        Creates a new InventoryManager with an empty items dictionary and unaccessed status.
        Items will be loaded in setup() method.

        This initialization approach separates the manager's setup (empty state) from
        the game's content (default items), making it easier to modify starting items
        or load from save data without changing the manager's core initialization.
        """
        # Asset paths are resolved via resource handles - no need to store them

        # All available items
        self.items: dict[str, InventoryItem] = {}

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

    def setup(self, context: GameContext) -> None:
        """Initialize the inventory system with game context and settings.

        Args:
            context: Game context providing access to event bus.
        """
        self.context = context

        # Initialize default items
        self._initialize_default_items()

        logger.debug("InventoryManager setup complete")

    def cleanup(self) -> None:
        """Clean up inventory resources when the scene unloads."""
        self.items.clear()
        self.accessed = False
        logger.debug("InventoryManager cleanup complete")

    def reset(self) -> None:
        """Reset inventory state for new game."""
        self.items.clear()
        self.accessed = False
        self.showing = False
        self.viewing_photo = False
        self.current_photo_texture = None
        self.all_items = []
        self.icon_textures.clear()
        self._initialize_default_items()
        logger.debug("InventoryManager reset complete")

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle key presses for inventory overlay."""
        # Toggle inventory with I key
        if symbol == arcade.key.I and not self.showing:
            self._show_inventory()
            return True

        # Handle input when overlay is showing
        if self.showing:
            if self.viewing_photo:
                # Close photo view
                if symbol in (arcade.key.ESCAPE, arcade.key.ENTER, arcade.key.RETURN):
                    self.viewing_photo = False
                    self.current_photo_texture = None
                    return True
            # Grid navigation
            elif symbol == arcade.key.ESCAPE:
                self._hide_inventory()
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
            elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
                self._view_selected_item()
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
        self.mark_as_accessed()

        # Get only acquired items for grid display
        self.all_items = self.get_acquired_items()

        # Load icon textures for acquired items
        self._load_icon_textures()

        logger.debug("Inventory overlay shown")

    def _hide_inventory(self) -> None:
        """Hide the inventory overlay and emit closed event."""
        self.showing = False
        self.viewing_photo = False
        self.current_photo_texture = None
        self.emit_closed_event()
        logger.debug("Inventory overlay hidden")

    def _move_selection(self, delta_col: int, delta_row: int) -> None:
        """Move selection in the grid with wrapping."""
        self.selected_col = (self.selected_col + delta_col) % settings.INVENTORY_GRID_COLS
        self.selected_row = (self.selected_row + delta_row) % settings.INVENTORY_GRID_ROWS

    def _view_selected_item(self) -> None:
        """View the currently selected item (photo) in full-screen mode."""
        selected_index = self.selected_row * settings.INVENTORY_GRID_COLS + self.selected_col

        if selected_index >= len(self.all_items):
            return

        item = self.all_items[selected_index]

        # Get image path
        image_path = self.get_image_path(item)

        if not image_path:
            logger.warning("No image path configured for item: %s", item.id)
            return

        try:
            # Load and display photo
            self.current_photo_texture = arcade.load_texture(image_path)
            self.viewing_photo = True
            logger.info("Loaded photo: %s", item.name)
        except Exception:
            logger.exception("Failed to load photo: %s", image_path)

    def _load_icon_textures(self) -> None:
        """Load icon textures for all acquired items."""
        self.icon_textures.clear()

        for item in self.all_items:
            icon_path = self.get_icon_path(item)
            if icon_path:
                try:
                    self.icon_textures[item.id] = arcade.load_texture(icon_path)
                    logger.debug("Loaded icon for item: %s", item.id)
                except (FileNotFoundError, OSError):
                    logger.warning("Failed to load icon for item: %s at %s", item.id, icon_path)

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
        # Draw semi-transparent overlay
        arcade.draw_lrbt_rectangle_filled(0, window.width, 0, window.height / 2, (0, 0, 0, 200))

        # Draw background image if loaded
        if self.background_texture:
            arcade.draw_texture_rect(
                self.background_texture,
                arcade.LBWH(0, 0, window.width, window.height),
            )

        # Calculate grid positioning (centered within the overlay area - bottom half of screen)
        grid_width = (
            settings.INVENTORY_GRID_COLS * settings.INVENTORY_BOX_SIZE
            + (settings.INVENTORY_GRID_COLS - 1) * settings.INVENTORY_BOX_SPACING
        )
        grid_height = (
            settings.INVENTORY_GRID_ROWS * settings.INVENTORY_BOX_SIZE
            + (settings.INVENTORY_GRID_ROWS - 1) * settings.INVENTORY_BOX_SPACING
        )

        overlay_height = window.height / 2  # Overlay covers bottom half of screen
        start_x = (window.width - grid_width) / 2
        start_y = (overlay_height - grid_height) / 2 + 20  # Center within overlay, slight offset up

        # Draw grid boxes
        for row in range(settings.INVENTORY_GRID_ROWS):
            for col in range(settings.INVENTORY_GRID_COLS):
                item_index = row * settings.INVENTORY_GRID_COLS + col

                # Calculate box position (top-left corner)
                x = start_x + col * (settings.INVENTORY_BOX_SIZE + settings.INVENTORY_BOX_SPACING)
                y = start_y + (settings.INVENTORY_GRID_ROWS - 1 - row) * (
                    settings.INVENTORY_BOX_SIZE + settings.INVENTORY_BOX_SPACING
                )

                # Determine if this slot has an item
                has_item = item_index < len(self.all_items)
                item = self.all_items[item_index] if has_item else None
                is_selected = row == self.selected_row and col == self.selected_col

                # Draw box background and border based on slot state
                if item:
                    # FILLED SLOT: Draw solid background with item icon
                    bg_color = arcade.color.DARK_SLATE_GRAY

                    arcade.draw_lrbt_rectangle_filled(
                        x, x + settings.INVENTORY_BOX_SIZE, y, y + settings.INVENTORY_BOX_SIZE, bg_color
                    )

                    # Draw border (yellow if selected, white otherwise)
                    if is_selected:
                        border_color = arcade.color.YELLOW
                        border_width = settings.INVENTORY_BOX_BORDER_WIDTH + 1
                    else:
                        border_color = arcade.color.WHITE
                        border_width = settings.INVENTORY_BOX_BORDER_WIDTH

                    arcade.draw_lrbt_rectangle_outline(
                        x,
                        x + settings.INVENTORY_BOX_SIZE,
                        y,
                        y + settings.INVENTORY_BOX_SIZE,
                        border_color,
                        border_width,
                    )

                    # Draw icon if available
                    icon_texture = self.icon_textures.get(item.id)
                    if icon_texture:
                        # Scale icon to fit box with padding
                        padding = 4
                        max_icon_size = settings.INVENTORY_BOX_SIZE - (padding * 2)

                        # Calculate scale to fit
                        scale_x = max_icon_size / icon_texture.width
                        scale_y = max_icon_size / icon_texture.height
                        scale = min(scale_x, scale_y)

                        # Draw centered icon
                        icon_width = icon_texture.width * scale
                        icon_height = icon_texture.height * scale
                        icon_center_x = x + settings.INVENTORY_BOX_SIZE / 2
                        icon_center_y = y + settings.INVENTORY_BOX_SIZE / 2

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
                    empty_bg_color = (30, 30, 35, 180)
                    arcade.draw_lrbt_rectangle_filled(
                        x, x + settings.INVENTORY_BOX_SIZE, y, y + settings.INVENTORY_BOX_SIZE, empty_bg_color
                    )

                    # Draw subdued border (yellow if selected, dim gray otherwise)
                    if is_selected:
                        border_color = arcade.color.YELLOW
                        border_width = settings.INVENTORY_BOX_BORDER_WIDTH + 1
                    else:
                        border_color = arcade.color.DIM_GRAY
                        border_width = 2

                    arcade.draw_lrbt_rectangle_outline(
                        x,
                        x + settings.INVENTORY_BOX_SIZE,
                        y,
                        y + settings.INVENTORY_BOX_SIZE,
                        border_color,
                        border_width,
                    )

        # Draw selected item name at bottom
        selected_index = self.selected_row * settings.INVENTORY_GRID_COLS + self.selected_col
        if selected_index < len(self.all_items):
            selected_item = self.all_items[selected_index]

            if self.selected_item_text is None:
                self.selected_item_text = arcade.Text(
                    selected_item.name,
                    window.width / 2,
                    10,
                    arcade.color.WHITE,
                    font_size=16,
                    anchor_x="center",
                    anchor_y="bottom",
                    bold=True,
                )
            else:
                self.selected_item_text.text = selected_item.name
                self.selected_item_text.x = window.width / 2

            self.selected_item_text.draw()

    def _draw_photo_view(self, window: arcade.Window) -> None:
        """Draw the photo viewing overlay."""
        if not self.current_photo_texture:
            return

        # Draw black background
        arcade.draw_lrbt_rectangle_filled(0, window.width, 0, window.height, arcade.color.BLACK)

        # Get selected item
        selected_index = self.selected_row * settings.INVENTORY_GRID_COLS + self.selected_col
        if 0 <= selected_index < len(self.all_items):
            item = self.all_items[selected_index]

            # Reserve space for text at bottom
            text_area_height = 120

            # Calculate photo display size
            max_width = window.width * 0.7
            max_height = (window.height - text_area_height) * 0.7

            # Calculate scale to fit
            width_scale = max_width / self.current_photo_texture.width
            height_scale = max_height / self.current_photo_texture.height
            scale = min(width_scale, height_scale)

            # Calculate final dimensions
            final_width = self.current_photo_texture.width * scale
            final_height = self.current_photo_texture.height * scale

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
                    90,
                    arcade.color.WHITE,
                    font_size=settings.MENU_TITLE_SIZE,
                    anchor_x="center",
                )
            else:
                self.photo_title_text.text = item.name
                self.photo_title_text.x = window.width / 2

            self.photo_title_text.draw()

            # Draw photo description
            if self.photo_description_text is None:
                self.photo_description_text = arcade.Text(
                    item.description,
                    window.width / 2,
                    60,
                    arcade.color.LIGHT_GRAY,
                    font_size=14,
                    anchor_x="center",
                )
            else:
                self.photo_description_text.text = item.description
                self.photo_description_text.x = window.width / 2

            self.photo_description_text.draw()

    def get_save_state(self) -> dict[str, Any]:
        """Return serializable state for saving (BaseSystem interface)."""
        return {"inventory_items": self.to_dict()}

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Restore state from save data (BaseSystem interface)."""
        if "inventory_items" in state:
            self.from_dict(state["inventory_items"])

    def _initialize_default_items(self) -> None:
        """Initialize default inventory items from JSON data file."""
        try:
            items_file = asset_path("data/inventory_items.json")

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

    def add_item(self, item: InventoryItem) -> None:
        """Add an item to the manager's registry of available items.

        Registers a new item in the inventory system, making it available for acquisition
        and display. This method is used to dynamically add items beyond the default set,
        such as items defined in game data files or created programmatically.

        Items are stored by their unique ID. Adding an item with an ID that already exists
        will overwrite the previous item, which can be used to update item properties.

        This method does NOT automatically acquire the item for the player - it only makes
        the item definition available. Use acquire_item() to actually give the item to
        the player.

        Args:
            item: The InventoryItem instance to add. The item's ID will be used as the
                 dictionary key for storage and lookups.

        Example:
            # Add a quest item dynamically
            quest_item = InventoryItem(
                id="magic_amulet",
                name="Ancient Amulet",
                description="Glows with mysterious power.",
                category="key"
            )
            inventory_mgr.add_item(quest_item)
        """
        self.items[item.id] = item
        logger.debug("Added item to inventory: %s", item.id)

    def acquire_item(self, item_id: str) -> bool:
        """Mark an item as acquired by the player.

        Gives the specified item to the player by setting its acquired flag to True. This
        method is typically called when the player finds, picks up, or earns an item through
        gameplay actions.

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
                    "photo_01"). Must match an item previously added to the manager.

        Returns:
            True if the item was newly acquired (transitioned from unacquired to acquired),
            False if the item was not found or was already acquired. Use this return value
            to trigger "new item" feedback to the player.

        Example:
            # When player picks up an item
            if inventory_mgr.acquire_item("ancient_scroll"):
                # Item was newly acquired
                show_notification("Found: Ancient Scroll!")
                audio_mgr.play_sfx("item_get.wav")
                particle_mgr.emit_sparkles(player.center_x, player.center_y)
            else:
                # Item was already owned or doesn't exist
                pass
        """
        if item_id not in self.items:
            logger.warning("Attempted to acquire unknown item: %s", item_id)
            return False

        if not self.items[item_id].acquired:
            item = self.items[item_id]
            item.acquired = True
            logger.info("Player acquired item: %s (%s)", item_id, item.name)

            # Publish event if event bus is available
            if self.context.event_bus:
                self.context.event_bus.publish(ItemAcquiredEvent(item_id=item_id, item_name=item.name))

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

    def get_acquired_items(self, category: str | None = None) -> list[InventoryItem]:
        """Get all items the player has acquired, optionally filtered by category.

        Returns a list of all items where acquired=True, maintaining the insertion order
        from when items were added to the manager. This method is commonly used to display
        the player's inventory in UI screens.

        The optional category filter allows for displaying specific types of items, such
        as showing only photos in a gallery view or only keys in a key ring interface.

        Items are returned in insertion order, which is important for chronological display
        (e.g., photos in the order they were collected) or logical grouping (e.g., quest
        items in story order).

        Args:
            category: Optional category string to filter results (e.g., "photo", "key",
                     "note"). If None, returns all acquired items regardless of category.
                     Category matching is exact and case-sensitive.

        Returns:
            List of InventoryItem instances where acquired=True, filtered by category if
            specified. Returns empty list if no items match the criteria. The list maintains
            insertion order from the items dictionary.

        Example:
            # Display all acquired photos in a gallery
            photos = inventory_mgr.get_acquired_items(category="photo")
            for i, photo in enumerate(photos):
                display_photo_thumbnail(photo, position=i)

            # Show all acquired items
            all_items = inventory_mgr.get_acquired_items()
            show_notification(f"Inventory: {len(all_items)} items")

            # Check quest completion progress
            notes_found = len(inventory_mgr.get_acquired_items(category="note"))
            total_notes = len(inventory_mgr.get_all_items(category="note"))
            print(f"Notes collected: {notes_found}/{total_notes}")
        """
        acquired = [item for item in self.items.values() if item.acquired]

        if category:
            acquired = [item for item in acquired if item.category == category]

        return acquired

    def get_all_items(self, category: str | None = None) -> list[InventoryItem]:
        """Get all items regardless of acquisition status, optionally filtered by category.

        Returns a list of all items in the registry, including both acquired and unacquired
        items. This is useful for showing completion tracking ("5/10 photos found") or
        displaying locked/grayed-out items that the player hasn't found yet.

        Args:
            category: Optional category string to filter results. If None, returns all items.

        Returns:
            List of all InventoryItem instances in insertion order, filtered by category
            if specified.

        Example:
            # Show completion percentage
            total = len(inventory_mgr.get_all_items(category="photo"))
            found = len(inventory_mgr.get_acquired_items(category="photo"))
            completion = (found / total) * 100
            print(f"Photo album: {completion:.0f}% complete")
        """
        all_items = list(self.items.values())

        if category:
            all_items = [item for item in all_items if item.category == category]

        return all_items

    def get_item(self, item_id: str) -> InventoryItem | None:
        """Get an item by its unique ID.

        Direct lookup of an item by ID, useful when you need the full item object to
        access its properties (name, description, image path, etc.).

        Args:
            item_id: The unique identifier of the item to retrieve.

        Returns:
            The InventoryItem instance if found, None if the ID doesn't exist.

        Example:
            item = inventory_mgr.get_item("ancient_scroll")
            if item and item.acquired:
                display_item_details(item.name, item.description, item.image_path)
        """
        return self.items.get(item_id)

    def get_image_path(self, item: InventoryItem) -> str | None:
        """Get the full absolute path to an item's full-size image file.

        Resolves the item's relative image path to an absolute filesystem path using
        the asset_path() helper. This handles the asset directory structure so callers
        don't need to know where assets are stored.

        Args:
            item: The InventoryItem instance to get the image path for.

        Returns:
            Full absolute path to the image file (e.g., "/path/to/assets/images/photos/beach.jpg"),
            or None if the item has no image (image_path is None).

        Example:
            item = inventory_mgr.get_item("memory_photo")
            if item:
                img_path = inventory_mgr.get_image_path(item)
                if img_path:
                    texture = arcade.load_texture(img_path)
                    display_texture(texture)
        """
        if not item.image_path:
            return None

        return asset_path(f"{item.image_path}")

    def get_icon_path(self, item: InventoryItem) -> str | None:
        """Get the full absolute path to an item's icon/thumbnail image file.

        Resolves the item's relative icon path to an absolute filesystem path using
        the asset_path() helper. Icons are smaller preview images displayed in the
        inventory grid.

        Args:
            item: The InventoryItem instance to get the icon path for.

        Returns:
            Full absolute path to the icon file (e.g., "/path/to/assets/images/icons/key_icon.png"),
            or None if the item has no icon (icon_path is None).

        Example:
            item = inventory_mgr.get_item("rusty_key")
            if item:
                icon_path = inventory_mgr.get_icon_path(item)
                if icon_path:
                    icon_texture = arcade.load_texture(icon_path)
                    display_icon(icon_texture)
        """
        if not item.icon_path:
            return None

        return asset_path(f"{item.icon_path}")

    def get_acquired_count(self, category: str | None = None) -> int:
        """Get the count of items the player has acquired.

        Convenience method that returns the number of acquired items, optionally filtered
        by category. Equivalent to len(get_acquired_items(category)).

        Args:
            category: Optional category filter. If None, counts all acquired items.

        Returns:
            Integer count of acquired items matching the filter.

        Example:
            photos_collected = inventory_mgr.get_acquired_count(category="photo")
            print(f"You've collected {photos_collected} photos!")
        """
        return len(self.get_acquired_items(category))

    def get_total_count(self, category: str | None = None) -> int:
        """Get the total count of all items in the registry.

        Convenience method that returns the total number of items (acquired and unacquired),
        optionally filtered by category. Equivalent to len(get_all_items(category)).

        Args:
            category: Optional category filter. If None, counts all items.

        Returns:
            Integer count of all items matching the filter.

        Example:
            total_photos = inventory_mgr.get_total_count(category="photo")
            found_photos = inventory_mgr.get_acquired_count(category="photo")
            print(f"Photo Album: {found_photos}/{total_photos}")
        """
        return len(self.get_all_items(category))

    def has_been_accessed(self) -> bool:
        """Check if inventory has been accessed."""
        return self.accessed

    def mark_as_accessed(self) -> None:
        """Mark the inventory as having been accessed by the player.

        Sets the accessed flag to True, indicating the player has opened the
        inventory view at least once. This is typically called by the inventory UI when
        it's first displayed.

        This flag is useful for:
        - Tutorial systems that wait for the player to check their inventory
        - Achievement tracking ("Opened inventory for the first time")
        - Quest progression that requires viewing collected items
        - First-time help tooltips that shouldn't show after initial access

        The method is idempotent - calling it multiple times has no additional effect
        beyond the first call. Only the first access is logged.

        Example:
            # In inventory view's on_show_view() method
            def on_show_view(self):
                self.inventory_mgr.mark_as_accessed()
                # ... rest of UI setup
        """
        if not self.accessed:
            self.accessed = True
            logger.info("Inventory accessed for the first time")

    def emit_closed_event(self) -> None:
        """Emit InventoryClosedEvent when inventory view closes.

        This allows the script system to react when the player finishes browsing
        their items.

        Args:
            context: Game context for accessing event bus.
        """
        self.context.event_bus.publish(InventoryClosedEvent(has_been_accessed=self.accessed))
        logger.info("Published InventoryClosedEvent (accessed=%s)", self.accessed)

    def to_dict(self) -> dict[str, bool]:
        """Convert inventory state to dictionary for save data serialization.

        Exports the acquisition status of all items as a dictionary mapping item IDs to
        boolean acquired flags. This dictionary can be serialized to JSON or other formats
        for persistent storage.

        Only the acquired status is saved - item definitions (name, description, image)
        are considered part of the game's code/data and are loaded via _initialize_default_items()
        or add_item() when the game starts.

        Returns:
            Dictionary mapping item ID strings to boolean acquired status. Example:
            {"photo_01": True, "secret_key": False, "quest_note": True}

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
        return {item_id: item.acquired for item_id, item in self.items.items()}

    def from_dict(self, data: dict[str, bool]) -> None:
        """Load inventory state from saved dictionary data.

        Restores the acquisition status of items from a previously saved dictionary.
        This method updates the acquired flags of existing items but doesn't create
        new items - items must already exist in the registry (from initialization or
        add_item() calls).

        If the save data contains item IDs that don't exist in the current registry,
        those entries are skipped with a warning. This handles cases where items were
        added/removed between game versions.

        Args:
            data: Dictionary mapping item ID strings to boolean acquired status, typically
                 loaded from a JSON save file. Example: {"photo_01": True, "key_02": False}

        Example:
            # Load from JSON file
            import json
            with open("save.json", "r") as f:
                save_data = json.load(f)

            inventory_mgr.from_dict(save_data["inventory"])
            # Player's inventory is now restored
        """
        for item_id, acquired in data.items():
            if item_id in self.items:
                self.items[item_id].acquired = acquired
            else:
                logger.warning("Unknown item in save data: %s", item_id)
