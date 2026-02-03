"""Pause menu plugin implementation with inline save/load slot selection."""

import logging
from typing import TYPE_CHECKING, ClassVar

import arcade

from pedre.conf import settings
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
    dependencies: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """Initialize the pause menu plugin."""
        super().__init__()
        self._showing = False
        self.menu_state = PauseMenuState.MAIN_MENU
        self.selected_option = 0  # Index of selected option/slot (or confirmation option: 0=Yes, 1=No)
        self.context: GameContext | None = None
        self.save_feedback_message: str | None = None
        self.save_feedback_timer: float = 0.0
        self.confirmation_message: str = ""  # Message to show in confirmation overlay
        self.confirmation_action: str = ""  # Action to perform if confirmed (e.g., "new_game")

        # Text objects for better performance
        self.title_text: arcade.Text | None = None
        self.main_menu_texts: list[arcade.Text] = []
        self.slot_texts: list[arcade.Text] = []
        self.confirmation_message_text: arcade.Text | None = None
        self.confirmation_option_texts: list[arcade.Text] = []
        self.feedback_text: arcade.Text | None = None

    def setup(self, context: GameContext) -> None:
        """Setup the pause menu plugin.

        Args:
            context: Game context providing access to other plugins.
        """
        self.context = context
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

        # Navigation in confirmation overlay
        elif self.menu_state == PauseMenuState.CONFIRMATION:
            num_options = 2  # Yes/No
            if symbol == arcade.key.UP:
                self.selected_option = (self.selected_option - 1) % num_options
                return True
            if symbol == arcade.key.DOWN:
                self.selected_option = (self.selected_option + 1) % num_options
                return True
            if symbol == arcade.key.ENTER:
                self._execute_confirmation()
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

    def _execute_confirmation(self) -> None:
        """Execute the confirmation action based on selected option."""
        # selected_option: 0 = Yes, 1 = No
        if self.selected_option == 0:  # Yes
            if self.confirmation_action == "new_game" and self.context:
                # Start new game via context facade
                self.hide()  # Hide pause menu
                self.context.start_new_game()
                logger.info("Starting new game after confirmation")
            # Add more confirmation actions here as needed
        else:  # No
            # Return to main menu
            self.menu_state = PauseMenuState.MAIN_MENU
            self.selected_option = 0
            logger.debug("Confirmation cancelled")

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
            # Auto-save before exit
            if self.context:
                success = self.context.save_plugin.auto_save()
                if success:
                    logger.info("Auto-saved game before exit")
                else:
                    logger.warning("Auto-save failed before exit")

            # Exit the game
            if self.context and hasattr(self.context, "window"):
                arcade.close_window()
            logger.debug("Exit game")

    def _show_new_game_confirmation(self) -> None:
        """Show confirmation overlay for starting a new game."""
        # Switch to confirmation state
        self.menu_state = PauseMenuState.CONFIRMATION
        self.confirmation_message = settings.PAUSE_MENU_CONFIRM_NEW_GAME
        self.confirmation_action = "new_game"
        self.selected_option = 1  # Default to "No" for safety
        logger.debug("Showing new game confirmation overlay")

    def _prepare_text_objects(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Prepare Text objects for the current menu state.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        # Determine title based on menu state
        if self.menu_state == PauseMenuState.LOAD_SLOTS:
            title = settings.PAUSE_MENU_TEXT_LOAD_GAME
        elif self.menu_state == PauseMenuState.SAVE_SLOTS:
            title = settings.PAUSE_MENU_TEXT_SAVE_GAME
        elif self.menu_state == PauseMenuState.CONFIRMATION:
            title = settings.PAUSE_MENU_TEXT_NEW_GAME
        else:
            title = settings.PAUSE_MENU_TITLE

        # Create title text
        title_padding = 20
        title_y = box_top - title_padding - settings.PAUSE_MENU_TITLE_FONT_SIZE // 2
        self.title_text = arcade.Text(
            title,
            center_x,
            title_y,
            arcade.color.WHITE,
            settings.PAUSE_MENU_TITLE_FONT_SIZE,
            anchor_x="center",
            bold=True,
        )

        # Prepare state-specific text objects
        if self.menu_state == PauseMenuState.MAIN_MENU:
            self._prepare_main_menu_texts(center_x, center_y, box_width, box_height, box_top, box_bottom)
        elif self.menu_state == PauseMenuState.LOAD_SLOTS:
            self._prepare_load_slots_texts(center_x, center_y, box_width, box_height, box_top, box_bottom)
        elif self.menu_state == PauseMenuState.SAVE_SLOTS:
            self._prepare_save_slots_texts(center_x, center_y, box_width, box_height, box_top, box_bottom)
        elif self.menu_state == PauseMenuState.CONFIRMATION:
            self._prepare_confirmation_texts(center_x, center_y, box_width, box_height, box_top, box_bottom)

        # Create feedback text if needed
        if self.save_feedback_message:
            self.feedback_text = arcade.Text(
                self.save_feedback_message,
                center_x,
                center_y - box_height // 2 - 40,
                arcade.color.GREEN,
                settings.PAUSE_MENU_OPTION_FONT_SIZE + 4,
                anchor_x="center",
                bold=True,
            )

    def _prepare_main_menu_texts(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Prepare Text objects for main menu.

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

        # Calculate positions
        title_area_height = 60
        content_top = box_top - title_area_height
        content_height = content_top - box_bottom
        num_options = len(menu_options)
        total_height = (num_options - 1) * settings.PAUSE_MENU_SPACING
        start_y = box_bottom + content_height // 2 + total_height // 2

        # Calculate max width for text (leave padding)
        max_text_width = box_width - 80

        # Create text objects
        self.main_menu_texts = []

        for i, option_text in enumerate(menu_options):
            y_pos = start_y - (i * settings.PAUSE_MENU_SPACING)
            is_selected = i == self.selected_option
            color = arcade.color.YELLOW if is_selected else arcade.color.WHITE

            # Create option text with wrapping
            text_obj = arcade.Text(
                option_text,
                center_x,
                y_pos,
                color,
                settings.PAUSE_MENU_OPTION_FONT_SIZE,
                anchor_x="center",
                bold=is_selected,
                width=max_text_width,
                align="center",
                multiline=True,
            )
            self.main_menu_texts.append(text_obj)

    def _prepare_load_slots_texts(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Prepare Text objects for load slots menu.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        # Calculate positions
        slots = [0, 1, 2, 3]
        title_area_height = 60
        content_top = box_top - title_area_height
        content_bottom = box_bottom + 40
        content_height = content_top - content_bottom
        num_slots = len(slots)
        total_height = (num_slots - 1) * settings.PAUSE_MENU_SPACING
        start_y = content_bottom + content_height // 2 + total_height // 2

        # Calculate max width for slot text (centered with padding)
        max_slot_width = box_width - 80

        # Create text objects
        self.slot_texts = []

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

            # Determine color
            is_selected = i == self.selected_option
            if is_selected:
                color = arcade.color.YELLOW
            elif save_info:
                color = arcade.color.WHITE
            else:
                color = arcade.color.GRAY

            # Create slot text with wrapping, centered
            text_obj = arcade.Text(
                slot_text,
                center_x,
                y_pos,
                color,
                settings.PAUSE_MENU_SLOT_FONT_SIZE,
                anchor_x="center",
                bold=is_selected,
                width=max_slot_width,
                align="center",
                multiline=True,
            )
            self.slot_texts.append(text_obj)

    def _prepare_save_slots_texts(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Prepare Text objects for save slots menu.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        # Calculate positions
        slots = [1, 2, 3]
        title_area_height = 60
        content_top = box_top - title_area_height
        content_bottom = box_bottom + 40
        content_height = content_top - content_bottom
        num_slots = len(slots)
        total_height = (num_slots - 1) * settings.PAUSE_MENU_SPACING
        start_y = content_bottom + content_height // 2 + total_height // 2

        # Calculate max width for slot text (centered with padding)
        max_slot_width = box_width - 80

        # Create text objects
        self.slot_texts = []

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

            # Determine color
            is_selected = i == self.selected_option
            color = arcade.color.YELLOW if is_selected else arcade.color.WHITE

            # Create slot text with wrapping, centered
            text_obj = arcade.Text(
                slot_text,
                center_x,
                y_pos,
                color,
                settings.PAUSE_MENU_SLOT_FONT_SIZE,
                anchor_x="center",
                bold=is_selected,
                width=max_slot_width,
                align="center",
                multiline=True,
            )
            self.slot_texts.append(text_obj)

    def _prepare_confirmation_texts(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Prepare Text objects for confirmation overlay.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        # Create confirmation message with wrapping
        message_y = center_y + 40
        self.confirmation_message_text = arcade.Text(
            self.confirmation_message,
            center_x,
            message_y,
            arcade.color.WHITE,
            settings.PAUSE_MENU_OPTION_FONT_SIZE,
            anchor_x="center",
            width=box_width - 80,
            align="center",
            multiline=True,
        )

        # Calculate positions for options
        options = ["Yes", "No"]
        num_options = len(options)
        total_height = (num_options - 1) * settings.PAUSE_MENU_SPACING
        start_y = center_y - 20 - total_height // 2

        # Calculate max width for option text
        max_option_width = box_width - 80

        # Create text objects
        self.confirmation_option_texts = []

        for i, option_text in enumerate(options):
            y_pos = start_y - (i * settings.PAUSE_MENU_SPACING)
            is_selected = i == self.selected_option
            color = arcade.color.YELLOW if is_selected else arcade.color.WHITE

            # Create option text with wrapping
            text_obj = arcade.Text(
                option_text,
                center_x,
                y_pos,
                color,
                settings.PAUSE_MENU_OPTION_FONT_SIZE,
                anchor_x="center",
                bold=is_selected,
                width=max_option_width,
                align="center",
                multiline=True,
            )
            self.confirmation_option_texts.append(text_obj)

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

        # Prepare all text objects for current state
        self._prepare_text_objects(center_x, center_y, box_width, box_height, box_top, box_bottom)

        # Draw title
        if self.title_text:
            self.title_text.draw()

        # Render appropriate menu based on state
        if self.menu_state == PauseMenuState.MAIN_MENU:
            self._draw_main_menu(center_x, center_y, box_width, box_height, box_top, box_bottom)
        elif self.menu_state == PauseMenuState.LOAD_SLOTS:
            self._draw_load_slots(center_x, center_y, box_width, box_height, box_top, box_bottom)
        elif self.menu_state == PauseMenuState.SAVE_SLOTS:
            self._draw_save_slots(center_x, center_y, box_width, box_height, box_top, box_bottom)
        elif self.menu_state == PauseMenuState.CONFIRMATION:
            self._draw_confirmation(center_x, center_y, box_width, box_height, box_top, box_bottom)

        # Draw save feedback message if present
        if self.feedback_text:
            self.feedback_text.draw()

    def _draw_main_menu(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Draw the main menu options using Text objects.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        for text_obj in self.main_menu_texts:
            text_obj.draw()

    def _draw_load_slots(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Draw the load game slot selection menu using Text objects.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        # Draw slot texts
        for text_obj in self.slot_texts:
            text_obj.draw()

    def _draw_save_slots(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Draw the save game slot selection menu using Text objects.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        # Draw slot texts
        for text_obj in self.slot_texts:
            text_obj.draw()

    def _draw_confirmation(
        self, center_x: int, center_y: int, box_width: int, box_height: int, box_top: int, box_bottom: int
    ) -> None:
        """Draw the confirmation overlay with Yes/No options using Text objects.

        Args:
            center_x: Center X coordinate of the menu box.
            center_y: Center Y coordinate of the menu box.
            box_width: Width of the menu box.
            box_height: Height of the menu box.
            box_top: Top Y coordinate of the menu box.
            box_bottom: Bottom Y coordinate of the menu box.
        """
        # Draw confirmation message
        if self.confirmation_message_text:
            self.confirmation_message_text.draw()

        # Draw Yes/No options
        for text_obj in self.confirmation_option_texts:
            text_obj.draw()
