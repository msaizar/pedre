"""Pause menu plugin implementation with inline save/load slot selection."""

import logging
from typing import TYPE_CHECKING, ClassVar

import arcade

from pedre.conf import settings
from pedre.plugins.dialog.events import DialogClosedEvent
from pedre.plugins.pause_menu.base import PauseMenuBasePlugin, PauseMenuOption, PauseMenuState
from pedre.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext
    from pedre.plugins.save.base import GameSaveData

logger = logging.getLogger(__name__)


@PluginRegistry.register
class PauseMenuPlugin(PauseMenuBasePlugin):
    """Provides an in-game pause menu overlay.

    This plugin creates a centered overlay menu that appears when ESC is pressed,
    offering options like Resume, New Game, Load Game, Save Game, and Exit.
    It includes inline slot selection for loading and saving games.
    """

    name: ClassVar[str] = "pause_menu"
    dependencies: ClassVar[list[str]] = ["dialog"]  # Process after dialog

    def __init__(self) -> None:
        """Initialize the pause menu plugin."""
        super().__init__()
        self._showing = False
        self.menu_state = PauseMenuState.MAIN_MENU
        self.selected_option = 0  # Index of selected option/slot
        self.context: GameContext | None = None
        self.save_feedback_message: str | None = None
        self.save_feedback_timer: float = 0.0
        self._awaiting_new_game_confirmation = False

    def setup(self, context: GameContext) -> None:
        """Setup the pause menu plugin.

        Args:
            context: Game context providing access to other plugins.
        """
        self.context = context

        # Subscribe to DialogClosedEvent for New Game confirmation
        context.event_bus.subscribe(DialogClosedEvent, self._on_dialog_closed)
        logger.debug("PauseMenuPlugin: setup() called")

    def cleanup(self) -> None:
        """Clean up the pause menu plugin."""
        logger.debug("PauseMenuPlugin: cleanup() called")
        self._showing = False

    def update(self, delta_time: float) -> None:
        """Update the pause menu plugin (handle timers).

        Args:
            delta_time: Time elapsed since the last frame, in seconds.
        """
        # Update save feedback timer
        if self.save_feedback_timer > 0:
            self.save_feedback_timer -= delta_time
            if self.save_feedback_timer <= 0:
                self.save_feedback_message = None

    @property
    def showing(self) -> bool:
        """Whether the pause menu overlay is currently visible."""
        return self._showing

    def show(self) -> None:
        """Show the pause menu overlay."""
        self._showing = True
        self.menu_state = PauseMenuState.MAIN_MENU
        self.selected_option = 0
        logger.debug("Pause menu shown")

    def hide(self) -> None:
        """Hide the pause menu overlay."""
        self._showing = False
        logger.debug("Pause menu hidden")

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle key presses when pause menu is showing.

        Args:
            symbol: The key that was pressed.
            modifiers: Bitwise AND of all modifiers (shift, ctrl, num lock) pressed.

        Returns:
            True if input was consumed, False otherwise.
        """
        if not self._showing:
            return False

        # ESC key handling
        if symbol == arcade.key.ESCAPE:
            if self.menu_state == PauseMenuState.MAIN_MENU:
                # Close pause menu
                self.hide()
            else:
                # Return to main menu from slot selection
                self.menu_state = PauseMenuState.MAIN_MENU
                self.selected_option = 0
            return True

        # Navigation in main menu
        if self.menu_state == PauseMenuState.MAIN_MENU:
            if symbol == arcade.key.UP:
                self.selected_option = (self.selected_option - 1) % len(PauseMenuOption)
                return True
            if symbol == arcade.key.DOWN:
                self.selected_option = (self.selected_option + 1) % len(PauseMenuOption)
                return True
            if symbol == arcade.key.ENTER:
                self._execute_main_menu_option()
                return True

        # Navigation in load slots
        elif self.menu_state == PauseMenuState.LOAD_SLOTS:
            num_slots = 4  # Slots 0-3 (autosave + 3 manual)
            if symbol == arcade.key.UP:
                self.selected_option = (self.selected_option - 1) % num_slots
                return True
            if symbol == arcade.key.DOWN:
                self.selected_option = (self.selected_option + 1) % num_slots
                return True
            if symbol == arcade.key.ENTER:
                self._execute_load_slot()
                return True

        # Navigation in save slots
        elif self.menu_state == PauseMenuState.SAVE_SLOTS:
            num_slots = 3  # Slots 1-3 (manual only)
            if symbol == arcade.key.UP:
                self.selected_option = (self.selected_option - 1) % num_slots
                return True
            if symbol == arcade.key.DOWN:
                self.selected_option = (self.selected_option + 1) % num_slots
                return True
            if symbol == arcade.key.ENTER:
                self._execute_save_slot()
                return True

        # All other input is consumed when pause menu is showing
        return True

    def _execute_load_slot(self) -> None:
        """Load the game from the selected slot."""
        if not self.context or not self.context.save_plugin:
            logger.error("SavePlugin not available")
            return

        slot = self.selected_option  # Slots 0-3
        save_plugin = self.context.save_plugin

        # Check if save exists
        if not save_plugin.save_exists(slot=slot):
            logger.warning("No save data in slot %d", slot)
            return

        # Load the save data
        save_data: GameSaveData | None = save_plugin.load_game(slot=slot)
        if not save_data:
            logger.error("Failed to load save from slot %d", slot)
            return

        # Hide pause menu
        self.hide()

        # Load the game via context facade
        self.context.load_game(save_data)
        logger.info("Loaded game from slot %d", slot)

    def _execute_save_slot(self) -> None:
        """Save the game to the selected slot."""
        if not self.context or not self.context.save_plugin:
            logger.error("SavePlugin not available")
            return

        # Slots 1-3 for manual saves (selected_option 0-2 maps to slots 1-3)
        slot = self.selected_option + 1
        save_plugin = self.context.save_plugin

        # Save the game
        success = save_plugin.save_game(slot=slot)
        if success:
            logger.info("Game saved to slot %d", slot)
            # Show feedback message
            self.save_feedback_message = "Game Saved!"
            self.save_feedback_timer = 2.0  # Show for 2 seconds
            # Return to main menu after brief delay
            self.menu_state = PauseMenuState.MAIN_MENU
            self.selected_option = 0
        else:
            logger.error("Failed to save game to slot %d", slot)

    def _execute_main_menu_option(self) -> None:
        """Execute the currently selected main menu option."""
        option = PauseMenuOption(self.selected_option)

        if option == PauseMenuOption.RESUME:
            self.hide()
        elif option == PauseMenuOption.NEW_GAME:
            self._show_new_game_confirmation()
        elif option == PauseMenuOption.LOAD_GAME:
            # Switch to load slots view
            self.menu_state = PauseMenuState.LOAD_SLOTS
            self.selected_option = 0
        elif option == PauseMenuOption.SAVE_GAME:
            # Switch to save slots view
            self.menu_state = PauseMenuState.SAVE_SLOTS
            self.selected_option = 0
        elif option == PauseMenuOption.EXIT:
            # Exit the game
            if self.context and hasattr(self.context, "window"):
                arcade.close_window()
            logger.debug("Exit game")

    def _show_new_game_confirmation(self) -> None:
        """Show confirmation dialog for starting a new game."""
        if not self.context or not self.context.dialog_plugin:
            logger.error("DialogPlugin not available")
            return

        # Hide pause menu temporarily
        self.hide()

        # Mark that we're awaiting confirmation
        self._awaiting_new_game_confirmation = True

        # Show confirmation dialog
        self.context.dialog_plugin.show_dialog(
            npc_name="Confirm",
            text=[settings.PAUSE_MENU_CONFIRM_NEW_GAME],
            instant=True,
            auto_close=False,
        )
        logger.debug("Showing new game confirmation dialog")

    def _on_dialog_closed(self, event: DialogClosedEvent) -> None:
        """Handle dialog closed event for new game confirmation.

        Args:
            event: DialogClosedEvent instance.
        """
        if not event:
            return

        # Only handle if we're awaiting new game confirmation
        if not self._awaiting_new_game_confirmation:
            return

        # Check if it's our confirmation dialog
        if event.npc_name != "Confirm":
            return

        # Reset confirmation flag
        self._awaiting_new_game_confirmation = False

        # Start new game via context facade
        if self.context:
            self.context.start_new_game()
            logger.info("Starting new game after confirmation")

    def on_draw_ui(self) -> None:
        """Draw the pause menu overlay in screen coordinates.

        This is called after all world rendering is complete, so the overlay
        appears on top of everything else.
        """
        if not self._showing:
            return

        if not self.context or not self.context.window:
            return

        window = self.context.window

        # Draw semi-transparent full-screen overlay
        arcade.draw_lrbt_rectangle_filled(
            0,
            window.width,
            0,
            window.height,
            (*arcade.color.BLACK[:3], settings.PAUSE_MENU_OVERLAY_ALPHA),
        )

        # Calculate responsive menu box dimensions
        box_width = min(
            settings.PAUSE_MENU_BOX_MAX_WIDTH,
            max(settings.PAUSE_MENU_BOX_MIN_WIDTH, int(window.width * settings.PAUSE_MENU_BOX_WIDTH_PERCENT)),
        )
        box_height = max(
            settings.PAUSE_MENU_BOX_MIN_HEIGHT,
            int(window.height * settings.PAUSE_MENU_BOX_HEIGHT_PERCENT),
        )
        center_x = window.width // 2
        center_y = window.height // 2

        # Menu box background
        arcade.draw_lrbt_rectangle_filled(
            center_x - box_width // 2,
            center_x + box_width // 2,
            center_y - box_height // 2,
            center_y + box_height // 2,
            arcade.color.DARK_BLUE_GRAY,
        )

        # Menu box border
        arcade.draw_lrbt_rectangle_outline(
            center_x - box_width // 2,
            center_x + box_width // 2,
            center_y - box_height // 2,
            center_y + box_height // 2,
            arcade.color.WHITE,
            border_width=2,
        )

        # Calculate box bounds for positioning
        box_top = center_y + box_height // 2
        box_bottom = center_y - box_height // 2

        # Title positioning (with padding from top)
        title_padding = 20
        title_y = box_top - title_padding - settings.PAUSE_MENU_TITLE_FONT_SIZE // 2

        arcade.draw_text(
            settings.PAUSE_MENU_TITLE,
            center_x,
            title_y,
            arcade.color.WHITE,
            settings.PAUSE_MENU_TITLE_FONT_SIZE,
            anchor_x="center",
            bold=True,
        )

        # Render appropriate menu based on state (pass box dimensions)
        if self.menu_state == PauseMenuState.MAIN_MENU:
            self._draw_main_menu(center_x, center_y, box_width, box_height, box_top, box_bottom)
        elif self.menu_state == PauseMenuState.LOAD_SLOTS:
            self._draw_load_slots(center_x, center_y, box_width, box_height, box_top, box_bottom)
        elif self.menu_state == PauseMenuState.SAVE_SLOTS:
            self._draw_save_slots(center_x, center_y, box_width, box_height, box_top, box_bottom)

        # Draw save feedback message if present
        if self.save_feedback_message:
            arcade.draw_text(
                self.save_feedback_message,
                center_x,
                center_y - box_height // 2 - 40,
                arcade.color.GREEN,
                settings.PAUSE_MENU_OPTION_FONT_SIZE + 4,
                anchor_x="center",
                bold=True,
            )

    def _draw_main_menu(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Draw the main menu options.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        menu_options = [
            settings.PAUSE_MENU_TEXT_RESUME,
            settings.PAUSE_MENU_TEXT_NEW_GAME,
            settings.PAUSE_MENU_TEXT_LOAD_GAME,
            settings.PAUSE_MENU_TEXT_SAVE_GAME,
            settings.PAUSE_MENU_TEXT_EXIT,
        ]

        # Calculate content area (excluding title at top)
        title_area_height = 60  # Space reserved for title
        content_top = box_top - title_area_height
        content_height = content_top - box_bottom

        # Starting Y position for menu options (centered in content area)
        num_options = len(menu_options)
        total_height = (num_options - 1) * settings.PAUSE_MENU_SPACING
        start_y = box_bottom + content_height // 2 + total_height // 2

        # Calculate selector position based on box width
        selector_offset = min(box_width // 3, 100)  # Max 100px or 1/3 of box width

        for i, option_text in enumerate(menu_options):
            y_pos = start_y - (i * settings.PAUSE_MENU_SPACING)

            # Selected option in yellow, others in white
            color = arcade.color.YELLOW if i == self.selected_option else arcade.color.WHITE

            # Draw selection indicator (inside the box)
            if i == self.selected_option:
                arcade.draw_text(
                    ">",
                    center_x - selector_offset,
                    y_pos,
                    color,
                    settings.PAUSE_MENU_OPTION_FONT_SIZE,
                    anchor_x="center",
                    bold=True,
                )

            # Draw option text
            arcade.draw_text(
                option_text,
                center_x,
                y_pos,
                color,
                settings.PAUSE_MENU_OPTION_FONT_SIZE,
                anchor_x="center",
                bold=(i == self.selected_option),
            )

    def _draw_load_slots(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Draw the load game slot selection menu.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        # Draw subtitle
        subtitle_y = box_top - 60
        arcade.draw_text(
            settings.PAUSE_MENU_TEXT_LOAD_GAME,
            center_x,
            subtitle_y,
            arcade.color.WHITE,
            settings.PAUSE_MENU_OPTION_FONT_SIZE + 4,
            anchor_x="center",
            bold=True,
        )

        # Draw slots 0-3
        slots = [0, 1, 2, 3]

        # Calculate content area and positioning
        content_top = subtitle_y - 40
        content_bottom = box_bottom + 40  # Leave room for instructions
        content_height = content_top - content_bottom

        # Starting Y position for slots (centered in content area)
        num_slots = len(slots)
        total_height = (num_slots - 1) * settings.PAUSE_MENU_SPACING
        start_y = content_bottom + content_height // 2 + total_height // 2

        # Calculate text positioning based on box width
        text_offset = min(box_width // 2 - 20, 200)  # Stay inside box with padding
        selector_offset = text_offset + 20

        for i, slot in enumerate(slots):
            y_pos = start_y - (i * settings.PAUSE_MENU_SPACING)

            # Get save info
            save_info = None
            if self.context and self.context.save_plugin:
                save_info = self.context.save_plugin.get_save_info(slot)

            # Format slot text
            slot_prefix = "Slot 0 (Autosave)" if slot == 0 else f"Slot {slot}"

            if save_info:
                slot_text = f"{slot_prefix}: {save_info['map']} - {save_info['date_string']}"
            else:
                slot_text = f"{slot_prefix}: {settings.PAUSE_MENU_TEXT_EMPTY_SLOT}"

            # Color based on selection and availability
            if i == self.selected_option:
                color = arcade.color.YELLOW
            elif save_info:
                color = arcade.color.WHITE
            else:
                color = arcade.color.GRAY

            # Draw selection indicator (inside the box)
            if i == self.selected_option:
                arcade.draw_text(
                    ">",
                    center_x - selector_offset,
                    y_pos,
                    color,
                    settings.PAUSE_MENU_SLOT_FONT_SIZE,
                    anchor_x="left",
                    bold=True,
                )

            # Draw slot text
            arcade.draw_text(
                slot_text,
                center_x - text_offset,
                y_pos,
                color,
                settings.PAUSE_MENU_SLOT_FONT_SIZE,
                anchor_x="left",
                bold=(i == self.selected_option),
            )

    def _draw_save_slots(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Draw the save game slot selection menu.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        # Draw subtitle
        subtitle_y = box_top - 60
        arcade.draw_text(
            settings.PAUSE_MENU_TEXT_SAVE_GAME,
            center_x,
            subtitle_y,
            arcade.color.WHITE,
            settings.PAUSE_MENU_OPTION_FONT_SIZE + 4,
            anchor_x="center",
            bold=True,
        )

        # Draw slots 1-3 (manual saves only)
        slots = [1, 2, 3]

        # Calculate content area and positioning
        content_top = subtitle_y - 40
        content_bottom = box_bottom + 40  # Leave room for instructions
        content_height = content_top - content_bottom

        # Starting Y position for slots (centered in content area)
        num_slots = len(slots)
        total_height = (num_slots - 1) * settings.PAUSE_MENU_SPACING
        start_y = content_bottom + content_height // 2 + total_height // 2

        # Calculate text positioning based on box width
        text_offset = min(box_width // 2 - 20, 200)  # Stay inside box with padding
        selector_offset = text_offset + 20

        for i, slot in enumerate(slots):
            y_pos = start_y - (i * settings.PAUSE_MENU_SPACING)

            # Get save info
            save_info = None
            if self.context and self.context.save_plugin:
                save_info = self.context.save_plugin.get_save_info(slot)

            # Format slot text
            slot_prefix = f"Slot {slot}"

            if save_info:
                slot_text = f"{slot_prefix}: {save_info['map']} - {save_info['date_string']}"
            else:
                slot_text = f"{slot_prefix}: {settings.PAUSE_MENU_TEXT_EMPTY_SLOT}"

            # Color based on selection
            color = arcade.color.YELLOW if i == self.selected_option else arcade.color.WHITE

            # Draw selection indicator (inside the box)
            if i == self.selected_option:
                arcade.draw_text(
                    ">",
                    center_x - selector_offset,
                    y_pos,
                    color,
                    settings.PAUSE_MENU_SLOT_FONT_SIZE,
                    anchor_x="left",
                    bold=True,
                )

            # Draw slot text
            arcade.draw_text(
                slot_text,
                center_x - text_offset,
                y_pos,
                color,
                settings.PAUSE_MENU_SLOT_FONT_SIZE,
                anchor_x="left",
                bold=(i == self.selected_option),
            )
