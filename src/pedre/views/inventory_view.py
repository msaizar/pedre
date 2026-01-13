"""Inventory view for displaying collected items and photos.

This module provides the InventoryView class, which presents a fullscreen interface
for browsing the player's collected items in a grid-based layout. The view displays
items as a grid of boxes that can be navigated using arrow keys.

Key features:
- Grid-based inventory interface with navigable boxes
- Arrow key navigation between inventory slots
- Visual highlighting of selected slot
- Full-screen photo viewing with automatic scaling
- Integration with inventory manager for item tracking
- Triggers post-inventory dialog events when closing

User interface flow:
1. Player opens inventory (presses I in game)
2. View shows grid of acquired items only
3. Player navigates with arrow keys between items
4. Player views photo with ENTER
5. Photo displays full-screen with title and description
6. Player closes photo or returns to game with ESC

The view marks the inventory as accessed on first show, which can trigger
story progression scripts through the event system.

Example usage:
    # Create inventory view
    inventory_view = InventoryView(view_manager, inventory_manager)

    # Show the view (typically called by view_manager)
    view_manager.show_inventory()
"""

import logging
from typing import TYPE_CHECKING

import arcade

from pedre.constants import asset_path

if TYPE_CHECKING:
    from pedre.systems import InventoryManager
    from pedre.systems.inventory import InventoryItem
    from pedre.view_manager import ViewManager

logger = logging.getLogger(__name__)


class InventoryView(arcade.View):
    """Inventory view for browsing collected items (photos) in a grid layout.

    The InventoryView provides a fullscreen grid-based interface for viewing the player's
    photo collection. Only acquired items are displayed in the grid, with icons/thumbnails
    that can be navigated using arrow keys.

    View modes:
    - Grid mode: Navigable grid showing only acquired items
    - Photo mode: Full-screen photo display with title and description

    The view integrates with the inventory manager to:
    - Mark inventory as accessed (triggers story events)
    - Retrieve acquired items for grid display
    - Get image paths for photo display

    Attributes:
        view_manager: ViewManager instance for transitioning between views.
        inventory_manager: InventoryManager instance containing player's items.
        grid_cols: Number of columns in the inventory grid (default: 3).
        grid_rows: Number of rows in the inventory grid (default: 3).
        selected_row: Currently selected row in the grid (0-based).
        selected_col: Currently selected column in the grid (0-based).
        all_items: List of acquired InventoryItem objects only.
        viewing_photo: Whether currently viewing a photo full-screen (vs grid mode).
        current_photo_texture: Loaded texture for currently viewed photo, or None.
        background_texture: Loaded background image texture, or None if not loaded.
    """

    def __init__(self, view_manager: ViewManager, inventory_manager: InventoryManager) -> None:
        """Initialize the inventory view.

        Creates the view with references to the view manager and inventory manager,
        and initializes view state for grid navigation and photo viewing.

        Args:
            view_manager: ViewManager for handling view transitions back to game.
            inventory_manager: InventoryManager containing player's collected items.
        """
        super().__init__()
        self.view_manager = view_manager
        self.inventory_manager = inventory_manager

        # Grid navigation state
        self.selected_row = 0
        self.selected_col = 0

        self.all_items: list[InventoryItem] = []
        self.viewing_photo = False
        self.current_photo_texture: arcade.Texture | None = None

        # Cache for item icon textures
        self.icon_textures: dict[str, arcade.Texture] = {}

        # Load background image
        self.background_texture: arcade.Texture | None = None

        # Text objects (created on first draw)
        self.title_text: arcade.Text | None = None
        self.selected_item_text: arcade.Text | None = None
        self.instructions_text: arcade.Text | None = None
        self.photo_title_text: arcade.Text | None = None
        self.photo_description_text: arcade.Text | None = None
        self.photo_instructions_text: arcade.Text | None = None

    def on_show_view(self) -> None:
        """Called when this view becomes active (arcade lifecycle callback).

        Initializes the view state when the inventory is opened:
        1. Sets background color to black
        2. Loads background image (if configured and not already loaded)
        3. Marks inventory as accessed (triggers InventoryClosedEvent later)
        4. Retrieves all photo items (acquired and unacquired) from inventory manager
        5. Resets selection to first slot
        6. Ensures photo viewing mode is closed

        The inventory accessed flag is important for story progression - scripts can
        wait for the player to open their inventory before continuing.

        Side effects:
            - Sets background color to black
            - Loads background texture if not cached
            - Calls inventory_manager.mark_as_accessed()
            - Populates self.all_items with photo category items
            - Resets selection to (0, 0)
            - Sets self.viewing_photo to False
            - Clears self.current_photo_texture
            - Logs background image loading status
        """
        arcade.set_background_color(arcade.color.BLACK)

        # Load background image if not already loaded
        settings = self.window.settings
        if self.background_texture is None and settings.inventory_background_image:
            background_path = asset_path(settings.inventory_background_image, settings.assets_handle)
            try:
                self.background_texture = arcade.load_texture(background_path)
                logger.info("Loaded inventory background: %s", background_path)
            except FileNotFoundError:
                logger.warning("Background image not found: %s", background_path)

        # Mark inventory as accessed
        self.inventory_manager.mark_as_accessed()

        # Get only acquired items for grid display
        self.all_items = self.inventory_manager.get_acquired_items(category="photo")
        self.selected_row = 0
        self.selected_col = 0
        self.viewing_photo = False
        self.current_photo_texture = None

        # Load icon textures for acquired items
        self._load_icon_textures()

    def on_draw(self) -> None:
        """Render the inventory (arcade lifecycle callback).

        Draws either the grid view or full-screen photo view depending on viewing_photo
        state. Called automatically by arcade each frame.

        Rendering modes:
        - Grid mode: Shows grid of item boxes with collection progress
        - Photo mode: Shows full-screen photo with title and description

        Side effects:
            - Clears the screen
            - Draws UI elements to window
        """
        self.clear()

        if self.viewing_photo and self.current_photo_texture:
            self._draw_photo_view()
        else:
            self._draw_inventory_grid()

    def _draw_inventory_grid(self) -> None:
        """Draw the inventory grid view (internal implementation).

        Renders the grid-based inventory interface showing:
        - Background image (if loaded)
        - Title ("Inventory")
        - Grid of acquired items only (3x3 by default)
        - Items show with colored background and icons
        - Selected item highlighted with yellow border
        - Selected item name displayed below grid
        - Control instructions at bottom

        Only acquired items are drawn - unacquired items are not displayed at all.
        Grid navigation wraps at edges.

        Side effects:
            - Draws shapes and text to screen
        """
        # Draw background image if loaded
        if self.background_texture:
            arcade.draw_texture_rect(
                self.background_texture,
                arcade.LBWH(0, 0, self.window.width, self.window.height),
            )

        # Create or update title text
        settings = self.window.settings
        if self.title_text is None:
            self.title_text = arcade.Text(
                "Inventory",
                self.window.width / 2,
                self.window.height - 60,
                arcade.color.WHITE,
                font_size=settings.menu_title_size,
                anchor_x="center",
            )
        else:
            self.title_text.x = self.window.width / 2
            self.title_text.y = self.window.height - 60

        # Draw title
        self.title_text.draw()

        # Calculate grid positioning (centered on screen)
        settings = self.window.settings
        grid_width = (
            settings.inventory_grid_cols * settings.inventory_box_size
            + (settings.inventory_grid_cols - 1) * settings.inventory_box_spacing
        )
        grid_height = (
            settings.inventory_grid_rows * settings.inventory_box_size
            + (settings.inventory_grid_rows - 1) * settings.inventory_box_spacing
        )

        start_x = (self.window.width - grid_width) / 2
        start_y = (self.window.height - grid_height) / 2 + 20  # Slight offset up

        # Draw grid boxes
        for row in range(settings.inventory_grid_rows):
            for col in range(settings.inventory_grid_cols):
                item_index = row * settings.inventory_grid_cols + col

                # Calculate box position (top-left corner)
                x = start_x + col * (settings.inventory_box_size + settings.inventory_box_spacing)
                y = start_y + (settings.inventory_grid_rows - 1 - row) * (
                    settings.inventory_box_size + settings.inventory_box_spacing
                )

                # Determine if this slot has an item
                has_item = item_index < len(self.all_items)
                item = self.all_items[item_index] if has_item else None
                is_selected = row == self.selected_row and col == self.selected_col

                # Only draw slots that have items (skip empty slots entirely)
                if not item:
                    continue

                # Draw box background (all items in list are acquired)
                bg_color = arcade.color.DARK_SLATE_GRAY

                arcade.draw_lrbt_rectangle_filled(
                    x, x + settings.inventory_box_size, y, y + settings.inventory_box_size, bg_color
                )

                # Draw border (yellow if selected, white otherwise)
                if is_selected:
                    border_color = arcade.color.YELLOW
                    border_width = settings.inventory_box_border_width + 1
                else:
                    border_color = arcade.color.WHITE
                    border_width = settings.inventory_box_border_width

                arcade.draw_lrbt_rectangle_outline(
                    x, x + settings.inventory_box_size, y, y + settings.inventory_box_size, border_color, border_width
                )

                # Draw icon if available
                icon_texture = self.icon_textures.get(item.id)
                if icon_texture:
                    # Scale icon to fit box with padding
                    padding = 4
                    max_icon_size = settings.inventory_box_size - (padding * 2)

                    # Calculate scale to fit
                    scale_x = max_icon_size / icon_texture.width
                    scale_y = max_icon_size / icon_texture.height
                    scale = min(scale_x, scale_y)

                    # Draw centered icon
                    icon_width = icon_texture.width * scale
                    icon_height = icon_texture.height * scale
                    icon_center_x = x + settings.inventory_box_size / 2
                    icon_center_y = y + settings.inventory_box_size / 2

                    arcade.draw_texture_rect(
                        icon_texture,
                        arcade.LRBT(
                            icon_center_x - icon_width / 2,  # left
                            icon_center_x + icon_width / 2,  # right
                            icon_center_y - icon_height / 2,  # bottom
                            icon_center_y + icon_height / 2,  # top
                        ),
                    )

        # Draw selected item name at bottom (below grid)
        settings = self.window.settings
        selected_index = self.selected_row * settings.inventory_grid_cols + self.selected_col
        if selected_index < len(self.all_items):
            selected_item = self.all_items[selected_index]

            # Create or update selected item text
            if self.selected_item_text is None:
                self.selected_item_text = arcade.Text(
                    selected_item.name,
                    self.window.width / 2,
                    80,
                    arcade.color.WHITE,
                    font_size=16,
                    anchor_x="center",
                    bold=True,
                )
            else:
                self.selected_item_text.text = selected_item.name
                self.selected_item_text.x = self.window.width / 2

            self.selected_item_text.draw()

        # Create or update instructions text
        if self.instructions_text is None:
            self.instructions_text = arcade.Text(
                "Arrow keys to navigate | ENTER to view | ESC to close",
                self.window.width / 2,
                30,
                arcade.color.WHITE,
                font_size=12,
                anchor_x="center",
            )
        else:
            self.instructions_text.x = self.window.width / 2

        # Draw instructions
        self.instructions_text.draw()

    def _draw_photo_view(self) -> None:
        """Draw the photo viewing screen (internal implementation).

        Renders the full-screen photo display with:
        - Photo scaled to fit window (70% of width and available height)
        - Maintains original aspect ratio
        - Centers photo vertically in space above text area
        - Photo title at bottom (white, large font)
        - Photo description below title (light gray)
        - Control instructions at very bottom

        The photo is scaled using the smaller of width_scale or height_scale to ensure
        it fits within the display area without distortion. A text area of 120px is
        reserved at the bottom for title, description, and instructions.

        Side effects:
            - Draws texture and text to screen
            - Logs photo dimensions and scaling info at debug level
        """
        if not self.current_photo_texture:
            return

        # Get selected item
        settings = self.window.settings
        selected_index = self.selected_row * settings.inventory_grid_cols + self.selected_col
        if 0 <= selected_index < len(self.all_items):
            item = self.all_items[selected_index]

            # Reserve space for text at bottom (title, description, instructions)
            text_area_height = 120

            # Calculate photo display size - make images smaller with padding
            max_width = self.window.width * 0.7  # Use only 70% of width
            max_height = (self.window.height - text_area_height) * 0.7  # 70% of height

            # Calculate scale to fit
            width_scale = max_width / self.current_photo_texture.width
            height_scale = max_height / self.current_photo_texture.height
            scale = min(width_scale, height_scale)

            # Calculate final dimensions
            final_width = self.current_photo_texture.width * scale
            final_height = self.current_photo_texture.height * scale

            # Center the photo vertically in the space above the text area
            available_vertical_space = self.window.height - text_area_height
            photo_center_y = text_area_height + available_vertical_space / 2

            # Calculate center position
            photo_center_x = self.window.width / 2

            logger.debug(
                "Photo: orig=%dx%d scale=%.2f final=%dx%d center=(%.1f,%.1f)",
                self.current_photo_texture.width,
                self.current_photo_texture.height,
                scale,
                final_width,
                final_height,
                photo_center_x,
                photo_center_y,
            )

            # Draw using LRBT (left, right, bottom, top) for proper centering
            arcade.draw_texture_rect(
                self.current_photo_texture,
                arcade.LRBT(
                    photo_center_x - final_width / 2,  # left
                    photo_center_x + final_width / 2,  # right
                    photo_center_y - final_height / 2,  # bottom
                    photo_center_y + final_height / 2,  # top
                ),
            )

            # Create or update photo title text
            if self.photo_title_text is None:
                self.photo_title_text = arcade.Text(
                    item.name,
                    self.window.width / 2,
                    90,
                    arcade.color.WHITE,
                    font_size=settings.menu_title_size,
                    anchor_x="center",
                )
            else:
                self.photo_title_text.text = item.name
                self.photo_title_text.x = self.window.width / 2

            # Draw title
            self.photo_title_text.draw()

            # Create or update photo description text
            if self.photo_description_text is None:
                self.photo_description_text = arcade.Text(
                    item.description,
                    self.window.width / 2,
                    60,
                    arcade.color.LIGHT_GRAY,
                    font_size=14,
                    anchor_x="center",
                )
            else:
                self.photo_description_text.text = item.description
                self.photo_description_text.x = self.window.width / 2

            # Draw description
            self.photo_description_text.draw()

            # Create or update photo instructions text
            if self.photo_instructions_text is None:
                self.photo_instructions_text = arcade.Text(
                    "ESC or ENTER to close",
                    self.window.width / 2,
                    30,
                    arcade.color.WHITE,
                    font_size=12,
                    anchor_x="center",
                )
            else:
                self.photo_instructions_text.x = self.window.width / 2

            # Draw instructions
            self.photo_instructions_text.draw()

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        """Handle keyboard input (arcade lifecycle callback).

        Processes keyboard input differently depending on viewing mode:

        Photo viewing mode (viewing_photo=True):
        - ESC/ENTER: Close photo and return to grid

        Grid mode (viewing_photo=False):
        - ESC: Close inventory and return to game (triggers post-inventory dialog)
        - UP: Move selection up in grid (wraps to bottom)
        - DOWN: Move selection down in grid (wraps to top)
        - LEFT: Move selection left in grid (wraps to right)
        - RIGHT: Move selection right in grid (wraps to left)
        - ENTER: View selected photo (if acquired)

        The ESC key in grid mode triggers a post-inventory dialog event, allowing
        scripts to react to the player checking their inventory.

        Args:
            symbol: Arcade key constant (e.g., arcade.key.ESCAPE).
            modifiers: Bitfield of modifier keys held (unused).

        Returns:
            None to allow other handlers to process the key.

        Side effects:
            - May close photo view or entire inventory
            - May change selected_row/selected_col
            - May load and display photo
            - May trigger view transition back to game
        """
        if self.viewing_photo:
            # Close photo view
            if symbol in (arcade.key.ESCAPE, arcade.key.ENTER, arcade.key.RETURN):
                self.viewing_photo = False
                self.current_photo_texture = None
        # Grid navigation
        elif symbol == arcade.key.ESCAPE:
            logger.info("ESC pressed in inventory, calling show_game with trigger=True")
            self.view_manager.show_game(trigger_post_inventory_dialog=True)
        elif symbol == arcade.key.UP:
            self._move_selection(0, -1)
        elif symbol == arcade.key.DOWN:
            self._move_selection(0, 1)
        elif symbol == arcade.key.LEFT:
            self._move_selection(-1, 0)
        elif symbol == arcade.key.RIGHT:
            self._move_selection(1, 0)
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._view_selected_item()

        return None

    def _move_selection(self, delta_col: int, delta_row: int) -> None:
        """Move selection in the grid with wrapping (internal implementation).

        Updates the selected grid position based on the direction deltas. Navigation
        wraps at the edges - moving up from the top row wraps to the bottom row,
        moving right from the rightmost column wraps to the leftmost column, etc.

        Args:
            delta_col: Column direction to move. -1 for left, 1 for right, 0 for no change.
            delta_row: Row direction to move. -1 for up, 1 for down, 0 for no change.

        Side effects:
            - Updates self.selected_row and self.selected_col with wrapping
        """
        settings = self.window.settings
        self.selected_col = (self.selected_col + delta_col) % settings.inventory_grid_cols
        self.selected_row = (self.selected_row + delta_row) % settings.inventory_grid_rows

    def _view_selected_item(self) -> None:
        """View the currently selected item (photo) in full-screen mode (internal implementation).

        Loads the photo image from disk and switches to photo viewing mode. All items in the
        list are acquired, so they can all be viewed.

        The image path is retrieved from the inventory manager, which resolves it from
        the item's image_file property.

        If the image fails to load (missing file, invalid path, etc.), the error is
        logged but the view remains in grid mode.

        Error handling:
        - No item at selected position: Returns silently
        - No image path configured: Logs warning
        - Image load failure: Logs exception

        Side effects:
            - Loads texture into memory (arcade.load_texture)
            - Sets self.current_photo_texture with loaded texture
            - Sets self.viewing_photo to True
            - Logs photo name on success or errors on failure
        """
        settings = self.window.settings
        selected_index = self.selected_row * settings.inventory_grid_cols + self.selected_col

        if selected_index >= len(self.all_items):
            return

        item = self.all_items[selected_index]

        # Get image path
        image_path = self.inventory_manager.get_image_path(item)

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
        """Load icon textures for all acquired items (internal implementation).

        Iterates through all items (which are all acquired) and loads icon textures for
        items that have an icon_path defined. Textures are cached in self.icon_textures
        for reuse during rendering.

        Icons that fail to load are silently skipped (error is logged but doesn't
        prevent the inventory from displaying).

        Side effects:
            - Populates self.icon_textures dictionary with loaded textures
            - Logs errors for icons that fail to load
        """
        self.icon_textures.clear()

        for item in self.all_items:
            icon_path = self.inventory_manager.get_icon_path(item)
            if icon_path:
                try:
                    self.icon_textures[item.id] = arcade.load_texture(icon_path)
                    logger.debug("Loaded icon for item: %s", item.id)
                except (FileNotFoundError, OSError):
                    logger.warning("Failed to load icon for item: %s at %s", item.id, icon_path)
