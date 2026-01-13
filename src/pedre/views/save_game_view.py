"""Save game view for selecting a slot to save the current game.

This module provides the SaveGameView class, which displays a menu interface
for browsing available save slots and saving the current game state. Players
can view existing save information and choose which slot to overwrite.

Key features:
- Display 3 manual save slots
- Show save metadata (map name, date/time saved) for occupied slots
- Visual distinction between empty and occupied slots
- Keyboard navigation with arrow keys
- Return to menu option
- Confirmation before overwriting existing saves

Save slot organization:
- Slots 1-3: Manual save slots for player-initiated saves
- Slot 0 (auto-save) is not shown - handled automatically
- Slot -1: Back to menu (special navigation option)

User interface flow:
1. Player pauses game (ESC) and selects "Save Game" from pause menu
2. View displays available save slots with metadata
3. Player navigates with arrow keys and selects with ENTER
4. Game saves to selected slot and returns to pause menu
5. If slot occupied, overwrites existing save (future: could add confirmation)

Example usage:
    # Create save game view
    save_view = SaveGameView(view_manager)

    # Show the view (typically called by view_manager)
    view_manager.show_save_game()
"""

from typing import TYPE_CHECKING

import arcade

from pedre.systems import SaveManager

if TYPE_CHECKING:
    from pedre.view_manager import ViewManager


class SaveGameView(arcade.View):
    """Save game view for selecting a slot to save the current game.

    The SaveGameView displays a menu interface showing manual save slots 1-3
    with their metadata (map name, save date/time). Players can navigate through
    slots and save the current game or return to the pause menu.

    The view queries the save manager to get information about each slot to
    show whether it's empty or contains an existing save.

    Attributes:
        view_manager: ViewManager instance for handling view transitions.
        save_manager: SaveManager instance for saving game data and querying metadata.
        selected_slot: Currently selected slot index (1-3=manual, -1=back).
        save_info: Dictionary mapping slot numbers to save metadata (or None if empty).
    """

    def __init__(self, view_manager: ViewManager) -> None:
        """Initialize the save game view.

        Creates the view with a view manager reference and initializes the save
        manager for querying and saving data.

        Args:
            view_manager: ViewManager for handling transitions back to menu.
        """
        super().__init__()
        self.view_manager = view_manager
        self.save_manager = SaveManager()
        self.selected_slot = 1  # Default to slot 1
        self.save_info: dict[int, dict | None] = {}

        # Text objects (created on first draw)
        self.title_text: arcade.Text | None = None
        self.slot_text_objects: list[arcade.Text] = []
        self.back_text: arcade.Text | None = None
        self.instructions_text: arcade.Text | None = None

    def on_show_view(self) -> None:
        """Called when this view becomes active (arcade lifecycle callback).

        Initializes the view by loading metadata for all manual save slots (1-3).
        This queries each slot's save file to get date and map information without
        loading the full game state.

        Side effects:
            - Sets background color to black
            - Populates self.save_info with metadata for slots 1-3
            - Reads save files from disk (metadata only, not full game state)
        """
        arcade.set_background_color(arcade.color.BLACK)

        # Load save slot information for manual slots only
        self.save_info = {}
        for slot in range(1, 4):  # Slots 1-3
            self.save_info[slot] = self.save_manager.get_save_info(slot)

    def on_draw(self) -> None:
        """Render the save game menu (arcade lifecycle callback).

        Draws the save game interface showing:
        - "Save Game" title at top
        - Manual save slots 1-3 with metadata or "(Empty)"
        - "Back to Menu" option at bottom
        - Control instructions at very bottom

        Visual states:
        - Selected slot: Yellow color with ">" prefix
        - Empty slot: White color
        - Occupied slot: White color with metadata
        - Selected back: Yellow with ">" prefix

        Metadata format: "Slot X: MapName - Date/Time" or "Slot X: (Empty)"

        Side effects:
            - Clears the screen
            - Draws text to window
        """
        self.clear()

        # Create or update title text
        settings = self.window.settings
        if self.title_text is None:
            self.title_text = arcade.Text(
                "Save Game",
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
        slot_order = [1, 2, 3]  # Manual slots only

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

            # Get save info
            info = self.save_info.get(slot)

            # Determine color
            color = arcade.color.YELLOW if is_selected else arcade.color.WHITE

            # Add selection indicator
            prefix = "> " if is_selected else "  "

            # Format display text
            if info is None:
                text = f"{prefix}Slot {slot}: (Empty)"
            else:
                date_str = info.get("date_string", "Unknown")
                map_name = info.get("map", "Unknown")
                text = f"{prefix}Slot {slot}: {map_name} - {date_str}"

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
        - ENTER: Save to selected slot or go back to menu
        - ESC: Return to pause menu

        Args:
            symbol: Arcade key constant (e.g., arcade.key.ENTER).
            modifiers: Bitfield of modifier keys held (unused).

        Returns:
            None to allow other handlers to process the key.

        Side effects:
            - May change selected_slot
            - May save game to selected slot
            - May trigger view transition back to pause menu
        """
        if symbol == arcade.key.UP:
            self._move_selection(-1)
        elif symbol == arcade.key.DOWN:
            self._move_selection(1)
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._execute_selection()
        elif symbol == arcade.key.ESCAPE:
            self.view_manager.show_menu(from_game_pause=True)

        return None

    def _move_selection(self, direction: int) -> None:
        """Move selection up or down in the menu (internal implementation).

        Updates the selected slot index with wrapping. The selection cycles through
        available slots (1-3=manual slots, -1=back) in display order.

        If selected_slot has an invalid value, defaults to first slot (1).

        Args:
            direction: Direction to move selection. -1 for up, 1 for down.

        Side effects:
            - Updates self.selected_slot with wrapping through available options
        """
        # Available selections: 1, 2, 3 (manual slots), -1 (back)
        selections = [1, 2, 3, -1]
        try:
            current_index = selections.index(self.selected_slot)
        except ValueError:
            current_index = 0

        new_index = (current_index + direction) % len(selections)
        self.selected_slot = selections[new_index]

    def _execute_selection(self) -> None:
        """Execute the action for the currently selected option (internal implementation).

        Handles the ENTER key action based on selected slot:
        - Slot -1: Return to pause menu
        - Slot 1-3: Save current game to selected slot

        When saving, retrieves the current game state from the game view and calls
        save_manager.save_game() with all necessary state (player position, NPCs,
        inventory, audio settings, script state).

        Side effects:
            - May call view_manager.show_menu() to return to pause menu
            - May call save_manager.save_game() to write save file to disk
            - Returns to pause menu after successful save
        """
        # Back to menu
        if self.selected_slot == -1:
            self.view_manager.show_menu(from_game_pause=True)
            return

        # Get game view to access current game state
        game_view = self.view_manager.game_view
        if not game_view or not game_view.player_sprite or not game_view.map_file:
            # No active game to save
            return

        # Save the game to the selected slot
        success = self.save_manager.save_game(
            slot=self.selected_slot,
            player_x=game_view.player_sprite.center_x,
            player_y=game_view.player_sprite.center_y,
            current_map=game_view.map_file,
            npc_manager=game_view.npc_manager,
            inventory_manager=game_view.inventory_manager,
            audio_manager=game_view.audio_manager,
            script_manager=game_view.script_manager,
        )

        if success:
            # Return to pause menu after successful save
            self.view_manager.show_menu(from_game_pause=True)
