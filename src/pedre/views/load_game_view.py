"""Load game view for selecting and loading saved games.

This module provides the LoadGameView class, which displays a menu interface
for browsing available save slots and loading previously saved games. Players
can view save information (date, map) and select which save to load.

Key features:
- Display up to 4 save slots (auto-save + 3 manual slots)
- Show save metadata (map name, date/time saved)
- Visual distinction between empty and occupied slots
- Keyboard navigation with arrow keys
- Return to main menu option

Save slot organization:
- Slot 0: Auto-save (F5 quick save, automatic on cleanup)
- Slots 1-3: Manual save slots for future manual save feature
- Slot -1: Back to menu (special navigation option)

User interface flow:
1. Player selects "Load Game" from main menu
2. View displays all available save slots with metadata
3. Player navigates with arrow keys and selects with ENTER
4. Game loads from selected save, or returns to menu if back selected
5. Empty slots do nothing when selected (could show error in future)

Example usage:
    # Create load game view
    load_view = LoadGameView(view_manager)

    # Show the view (typically called by view_manager)
    view_manager.show_load_game()
"""

from typing import TYPE_CHECKING

import arcade

from pedre.systems import SaveManager

if TYPE_CHECKING:
    from pedre.view_manager import ViewManager


class LoadGameView(arcade.View):
    """Load game view for browsing and loading save slots.

    The LoadGameView displays a menu interface showing all available save slots
    with their metadata (map name, save date/time). Players can navigate through
    slots and load a saved game or return to the main menu.

    The view queries the save manager to get information about each slot without
    fully loading the save data until a selection is confirmed.

    Attributes:
        view_manager: ViewManager instance for handling view transitions.
        save_manager: SaveManager instance for loading save data and metadata.
        selected_slot: Currently selected slot index (0=auto-save, 1-3=manual, -1=back).
        save_info: Dictionary mapping slot numbers to save metadata (or None if empty).
    """

    def __init__(self, view_manager: ViewManager) -> None:
        """Initialize the load game view.

        Creates the view with a view manager reference and initializes the save
        manager for querying save data.

        Args:
            view_manager: ViewManager for handling transitions to game or menu.
        """
        super().__init__()
        self.view_manager = view_manager
        self.save_manager = SaveManager()
        self.selected_slot = 1  # Slots 1-3, plus 0 for back
        self.save_info: dict[int, dict | None] = {}

        # Text objects (created on first draw)
        self.title_text: arcade.Text | None = None
        self.slot_text_objects: list[arcade.Text] = []
        self.back_text: arcade.Text | None = None
        self.instructions_text: arcade.Text | None = None

    def on_show_view(self) -> None:
        """Called when this view becomes active (arcade lifecycle callback).

        Initializes the view by loading metadata for all save slots. This queries
        each slot's save file to get date and map information without loading the
        full game state.

        Slot loading order:
        1. Slots 1-3 (manual save slots)
        2. Slot 0 (auto-save slot)

        Side effects:
            - Sets background color to black
            - Populates self.save_info with metadata for slots 0-3
            - Reads save files from disk (metadata only, not full game state)
        """
        arcade.set_background_color(arcade.color.BLACK)

        # Load save slot information
        self.save_info = {}
        for slot in range(1, 4):  # Slots 1-3
            self.save_info[slot] = self.save_manager.get_save_info(slot)

        # Check auto-save
        self.save_info[0] = self.save_manager.get_save_info(0)

    def on_draw(self) -> None:
        """Render the load game menu (arcade lifecycle callback).

        Draws the load game interface showing:
        - "Load Game" title at top
        - Auto-save slot with metadata or "(Empty)"
        - Manual save slots 1-3 with metadata or "(Empty)"
        - "Back to Menu" option at bottom
        - Control instructions at very bottom

        Visual states:
        - Selected slot: Yellow color with ">" prefix
        - Empty slot: Gray color
        - Occupied slot: White color
        - Selected back: Yellow with ">" prefix

        Metadata format: "Slot X: MapName - Date/Time"

        Side effects:
            - Clears the screen
            - Draws text to window
        """
        self.clear()

        # Create or update title text
        settings = self.window.settings
        if self.title_text is None:
            self.title_text = arcade.Text(
                "Load Game",
                self.window.width / 2,
                self.window.height * 0.75,
                arcade.color.WHITE,
                font_size=settings.menu_title_size,
                anchor_x="center",
            )
        else:
            self.title_text.x = self.window.width / 2
            self.title_text.y = self.window.height * 0.75

        # Draw title
        self.title_text.draw()

        # Draw save slots
        settings = self.window.settings
        start_y = self.window.height * 0.55
        slot_order = [0, 1, 2, 3]  # Auto-save first, then slots 1-3

        # Ensure we have enough text objects
        while len(self.slot_text_objects) < len(slot_order):
            text_obj = arcade.Text(
                "",
                self.window.width / 2,
                0,
                arcade.color.WHITE,
                font_size=settings.menu_option_size,
                anchor_x="center",
            )
            self.slot_text_objects.append(text_obj)

        for i, slot in enumerate(slot_order):
            y_position = start_y - (i * settings.menu_spacing)
            is_selected = slot == self.selected_slot

            # Determine slot name and info
            slot_name = "Auto-Save" if slot == 0 else f"Slot {slot}"

            # Get save info
            info = self.save_info.get(slot)

            # Determine color
            if is_selected:
                color = arcade.color.YELLOW
            elif info is None:
                color = arcade.color.GRAY
            else:
                color = arcade.color.WHITE

            # Add selection indicator
            prefix = "> " if is_selected else "  "

            # Format display text
            if info is None:
                text = f"{prefix}{slot_name}: (Empty)"
            else:
                date_str = info.get("date_string", "Unknown")
                map_name = info.get("map", "Unknown")
                text = f"{prefix}{slot_name}: {map_name} - {date_str}"

            # Update text object
            text_obj = self.slot_text_objects[i]
            text_obj.text = text
            text_obj.x = self.window.width / 2
            text_obj.y = y_position
            text_obj.color = color

            # Draw slot text
            text_obj.draw()

        # Draw back option
        settings = self.window.settings
        back_y = start_y - (len(slot_order) * settings.menu_spacing)
        is_back_selected = self.selected_slot == -1
        back_color = arcade.color.YELLOW if is_back_selected else arcade.color.WHITE
        back_prefix = "> " if is_back_selected else "  "

        # Create or update back text
        if self.back_text is None:
            self.back_text = arcade.Text(
                f"{back_prefix}Back to Menu",
                self.window.width / 2,
                back_y,
                back_color,
                font_size=settings.menu_option_size,
                anchor_x="center",
            )
        else:
            self.back_text.text = f"{back_prefix}Back to Menu"
            self.back_text.x = self.window.width / 2
            self.back_text.y = back_y
            self.back_text.color = back_color

        # Draw back text
        self.back_text.draw()

        # Create or update instructions text
        if self.instructions_text is None:
            self.instructions_text = arcade.Text(
                "Arrow keys to navigate | ENTER to select | ESC to go back",
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

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        """Handle keyboard input (arcade lifecycle callback).

        Processes keyboard input for menu navigation and selection:
        - UP: Move selection up (wraps to bottom)
        - DOWN: Move selection down (wraps to top)
        - ENTER: Load selected save or go back to menu
        - ESC: Return to main menu

        Args:
            symbol: Arcade key constant (e.g., arcade.key.ENTER).
            modifiers: Bitfield of modifier keys held (unused).

        Returns:
            None to allow other handlers to process the key.

        Side effects:
            - May change selected_slot
            - May load game from save file
            - May trigger view transition to game or menu
        """
        if symbol == arcade.key.UP:
            self._move_selection(-1)
        elif symbol == arcade.key.DOWN:
            self._move_selection(1)
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._execute_selection()
        elif symbol == arcade.key.ESCAPE:
            self.view_manager.show_menu()

        return None

    def _move_selection(self, direction: int) -> None:
        """Move selection up or down in the menu (internal implementation).

        Updates the selected slot index with wrapping. The selection cycles through
        available slots (0=auto-save, 1-3=manual slots, -1=back) in display order.

        If selected_slot has an invalid value, defaults to first slot (0).

        Args:
            direction: Direction to move selection. -1 for up, 1 for down.

        Side effects:
            - Updates self.selected_slot with wrapping through available options
        """
        # Available selections: 0 (auto-save), 1, 2, 3 (slots), -1 (back)
        selections = [0, 1, 2, 3, -1]
        try:
            current_index = selections.index(self.selected_slot)
        except ValueError:
            current_index = 0

        new_index = (current_index + direction) % len(selections)
        self.selected_slot = selections[new_index]

    def _execute_selection(self) -> None:
        """Execute the action for the currently selected option (internal implementation).

        Handles the ENTER key action based on selected slot:
        - Slot -1: Return to main menu
        - Slot 0-3: Load game from selected save slot (if not empty)

        If the selected slot is empty (save_data is None), no action is taken.
        This could be enhanced to show an error message to the user.

        Side effects:
            - May call view_manager.show_menu() for back option
            - May call view_manager.load_game() with save data
            - Loads full game state from disk if save exists
        """
        # Back to menu
        if self.selected_slot == -1:
            self.view_manager.show_menu()
            return

        # Try to load the selected save
        save_data = self.save_manager.load_game(self.selected_slot)

        if save_data is None:
            # No save in this slot, do nothing (or could show error message)
            return

        # Load the game with this save data
        self.view_manager.load_game(save_data)
