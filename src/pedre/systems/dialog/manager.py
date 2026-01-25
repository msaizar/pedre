"""Dialog system for managing game dialogs and conversations.

This module provides the dialog display system used throughout the game for
NPC conversations, narration, and player communication. It handles dialog
pagination, visual presentation, and user interaction.

The dialog system is typically used through:
- Direct NPC interaction (player presses E near an NPC)
- Scripted sequences (actions triggered by game events)
- Tutorial and story moments

Dialog Configuration:
    Dialogs are typically loaded from JSON files in assets/dialogs/ directory.
    Each file follows the pattern <scene>_dialogs.json (e.g., casa_dialogs.json).

    JSON structure:
        {
            "npc_name": {
                "0": {
                    "name": "Display Name",
                    "text": [
                        "First page of dialog",
                        "Second page of dialog"
                    ]
                },
                "1": {
                    "name": "Display Name",
                    "text": ["Next dialog level"],
                    "conditions": [
                        {
                            "check": "inventory_accessed",
                            "equals": true
                        }
                    ],
                    "on_condition_fail": [
                        {
                            "type": "dialog",
                            "speaker": "Display Name",
                            "text": ["Alternative text if condition fails"]
                        }
                    ]
                }
            }
        }

    The "name" field is optional - if provided, it will be displayed as the speaker name
    in the dialog box instead of the NPC's key name (e.g., "Merchant" instead of "merchant").

Example usage from code:
    dialog_manager.show_dialog("Martin", [
        "Welcome to the game!",
        "Press E to interact with NPCs.",
        "Have fun exploring!"
    ])
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, cast

import arcade

from pedre.conf import settings
from pedre.systems.dialog.base import DialogBaseManager, DialogPage
from pedre.systems.dialog.events import DialogClosedEvent, DialogOpenedEvent
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.systems.npc.base import NPCBaseManager

logger = logging.getLogger(__name__)


@SystemRegistry.register
class DialogManager(DialogBaseManager):
    """Manages dialog display and pagination.

    The DialogManager is the core system for displaying conversations in the game.
    It handles:
    - Converting multi-page text into individual dialog pages
    - Tracking the current page being displayed
    - Advancing through pages or closing the dialog
    - Rendering the dialog UI with a semi-transparent overlay and styled dialog box

    The manager maintains state about whether a dialog is currently showing and
    which page the player is viewing. Players advance through pages by pressing
    SPACE, and the dialog automatically closes after the last page.

    Visual Design:
    - Semi-transparent black overlay covers the game world
    - Dark blue-gray dialog box in the lower portion of the screen
    - Yellow NPC name at the top of the box
    - White dialog text with multiline support
    - Page indicator for multi-page dialogs
    - Context-sensitive instructions (next page vs close)

    Integration:
    - Called by the game view when players interact with NPCs
    - Used by DialogAction in the scripting system for cutscenes
    - Publishes DialogClosedEvent when dialogs are dismissed
    - Works with WaitForDialogCloseAction to pause scripts until player reads

    Scripted Dialog Example:
        # In a script, you can chain dialogs and actions:
        [
            {"type": "dialog", "speaker": "Martin", "text": ["Hello!"]},
            {"type": "wait_for_dialog_close"},  # Pauses until player presses SPACE
            {"type": "move_npc", "npcs": ["martin"], "waypoint": "door"},
            {"type": "wait_for_movement", "npc": "martin"},
            {"type": "dialog", "speaker": "Martin", "text": ["I'm leaving now!"]}
        ]

    This system has no dependencies on other systems.
    """

    name: ClassVar[str] = "dialog"
    # Depends on npc/interaction so dialog is loaded later and
    # processed first in reversed order (to consume SPACE when showing)
    dependencies: ClassVar[list[str]] = ["npc", "interaction"]

    def __init__(self) -> None:
        """Initialize the dialog manager.

        Creates an empty dialog manager ready to display conversations.
        Initially no dialog is showing.
        """
        self.showing = False
        self.pages: list[DialogPage] = []
        self.current_page_index = 0

        # Track current NPC for event emission
        self.current_npc_name: str | None = None
        self.current_dialog_level: int | None = None

        # Text reveal animation state
        self.revealed_chars = 0
        self.char_reveal_speed = 20  # characters per second
        self.char_timer = 0.0
        self.text_fully_revealed = False

        # Auto-close state
        self.auto_close_enabled = False
        self.auto_close_timer = 0.0

        # Text objects for dialog (created on first draw)
        self.npc_name_text: arcade.Text | None = None
        self.dialog_text: arcade.Text | None = None
        self.page_indicator_text: arcade.Text | None = None
        self.instruction_text: arcade.Text | None = None

        # Game context for event publishing
        self.context: GameContext | None = None

    def is_showing(self) -> bool:
        """Verify if dialog is showing."""
        return self.showing

    def set_current_dialog_level(self, dialog_level: int) -> None:
        """Set current dialog level."""
        self.current_dialog_level = dialog_level

    def set_current_npc_name(self, npc_name: str) -> None:
        """Set current dialog level."""
        self.current_npc_name = npc_name

    def setup(self, context: GameContext) -> None:
        """Initialize the dialog system with game settings.

        This method is called by the SystemLoader after all systems have been
        instantiated. Stores the game context for event publishing.

        Args:
            context: Game context for accessing the event bus.
        """
        self.context = context
        logger.debug("DialogManager setup complete")

    def on_key_press(self, symbol: int, modifiers: int, context: GameContext) -> bool:
        """Handle input for dialog advancement.

        Args:
            symbol: Arcade key constant.
            modifiers: Modifier key bitfield.
            context: Game context.

        Returns:
            True if dialog is showing and event was consumed.
        """
        if self.showing and symbol == arcade.key.SPACE:
            closed = self.advance_page()
            if closed and self.current_npc_name is not None and hasattr(context, "event_bus") and context.event_bus:
                # Get actual current level from NPC manager if available
                current_level = self.current_dialog_level or 0
                npc_manager = cast("NPCBaseManager", context.get_system("npc"))
                if npc_manager and hasattr(npc_manager, "npcs"):
                    npc_state = npc_manager.npcs.get(self.current_npc_name)
                    if npc_state:
                        current_level = npc_state.dialog_level

                context.event_bus.publish(DialogClosedEvent(npc_name=self.current_npc_name, dialog_level=current_level))
                logger.debug("Published DialogClosedEvent for %s at level %s", self.current_npc_name, current_level)
            return True
        return False

    def cleanup(self) -> None:
        """Clean up dialog resources when the scene unloads.

        Closes any open dialog and clears text objects.
        """
        self.close_dialog()
        self.npc_name_text = None
        self.dialog_text = None
        self.page_indicator_text = None
        self.instruction_text = None
        logger.debug("DialogManager cleanup complete")

    def show_dialog(
        self,
        npc_name: str,
        text: list[str],
        *,
        instant: bool = False,
        auto_close: bool | None = None,
        dialog_level: int | None = None,
        npc_key: str | None = None,
    ) -> None:
        """Show a dialog from an NPC.

        This method initiates a new dialog sequence, replacing any currently
        showing dialog. It converts the text list into pages and displays the
        first page immediately.

        Each string in the text list becomes one page of dialog. Players will
        advance through pages sequentially by pressing SPACE.

        This method is called by:
        - NPCManager when player interacts with an NPC (presses E nearby)
        - DialogAction when scripted sequences trigger dialog
        - Game systems for tutorials or story moments

        Args:
            npc_name: Display name of the character speaking (shown at top of dialog box).
            text: List of dialog text strings, one per page. Each string can contain
                multiple lines and will be wrapped automatically to fit the dialog box.
            instant: If True, text appears immediately without letter-by-letter reveal.
                Useful for narration, system messages, or cutscenes where the reveal
                animation would be distracting.
            auto_close: If True, dialog automatically closes after configured duration.
                If False, player must manually close. If None, uses the default from
                settings.DIALOG_AUTO_CLOSE_DEFAULT. Useful for cutscenes and
                scripted sequences. The timer starts after text is fully revealed.
            dialog_level: Optional dialog level for event tracking. Used when emitting
                DialogClosedEvent.
            npc_key: Optional NPC key name for event tracking. If provided, this is used
                in DialogClosedEvent instead of npc_name. Use this when the display name
                differs from the NPC's key name in the dialog system.

        Example from code:
            dialog_manager.show_dialog("Martin", [
                "Hello! I'm Martin, the village elder.",
                "Welcome to our humble town.",
                "Feel free to explore and talk to the other villagers!"
            ], dialog_level=0)

        Example from JSON config (assets/dialogs/casa_dialogs.json):
            {
                "martin": {
                    "0": {
                        "text": [
                            "Buenos días mi amor! Feliz cumpleaños!",
                            "Te hice un café, me acompañas a tomarlo?"
                        ]
                    }
                }
            }

            When player interacts with martin at dialog level 0, NPCManager automatically calls:

            show_dialog("Martin", ["Buenos días...", "Te hice..."], dialog_level=0, npc_key="martin")
        """
        self.pages = self._create_pages(npc_name, text)
        self.current_page_index = 0
        self.showing = True
        self.current_npc_name = npc_key or npc_name
        self.current_dialog_level = dialog_level
        # Use default from settings if auto_close not explicitly specified
        if auto_close is None:
            self.auto_close_enabled = settings.DIALOG_AUTO_CLOSE_DEFAULT
        else:
            self.auto_close_enabled = auto_close
        self.auto_close_timer = 0.0
        self._reset_text_reveal()

        # Publish DialogOpenedEvent
        if self.context and hasattr(self.context, "event_bus") and self.context.event_bus:
            self.context.event_bus.publish(
                DialogOpenedEvent(
                    npc_name=self.current_npc_name,
                    dialog_level=dialog_level or 0,
                )
            )
            logger.debug(
                "Published DialogOpenedEvent for %s at level %s",
                self.current_npc_name,
                dialog_level or 0,
            )

        # If instant mode, immediately reveal all text
        if instant:
            self.speed_up_text()

    def close_dialog(self) -> None:
        """Close the currently showing dialog.

        This method dismisses the dialog overlay and clears all dialog state.
        The dialog box will disappear and the game world will be fully visible again.

        This is typically called:
        - When the player advances past the last page of a dialog
        - By the game view when handling dialog closed events
        - When a dialog needs to be forcefully dismissed

        After closing, the dialog manager is ready to show a new dialog.
        """
        self.showing = False
        self.pages = []
        self.current_page_index = 0
        self.auto_close_enabled = False
        self.auto_close_timer = 0.0

    def advance_page(self) -> bool:
        """Advance to the next page or close dialog if on last page.

        This method is called when the player presses SPACE while viewing a dialog.
        If text is still being revealed, it instantly completes the reveal animation.
        Otherwise, it advances to the next page if there are more pages remaining,
        or closes the dialog if the player is on the last page.

        The return value indicates whether the dialog was closed, which is used
        by the game view to emit DialogClosedEvent for triggering scripted sequences.

        Returns:
            True if dialog was closed (was on last page), False if text was revealed
            or advanced to next page.

        Example flow:
            - Player sees page 1 (text revealing), presses SPACE -> completes text reveal, returns False
            - Player sees page 1 (text complete), presses SPACE -> advances to page 2, returns False
            - Player sees page 2 (text complete), presses SPACE -> advances to page 3, returns False
            - Player sees page 3 (text complete), presses SPACE -> closes dialog, returns True
        """
        # If text is still revealing, complete it instead of advancing
        if not self.text_fully_revealed:
            self.speed_up_text()
            return False

        # Text is fully revealed, advance to next page or close
        if self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
            self._reset_text_reveal()
            self.auto_close_timer = 0.0  # Reset timer for new page
            return False
        # Last page, close dialog
        self.close_dialog()
        return True

    def get_current_page(self) -> DialogPage | None:
        """Get the currently displayed page.

        This method retrieves the DialogPage object for the page that should
        currently be shown to the player. It's used primarily by the draw()
        method to know what content to render.

        Returns:
            Current DialogPage with text and metadata, or None if no dialog is showing.

        Note:
            Returns None if the dialog system is not currently showing a dialog or
            if the pages list is empty. This prevents errors when rendering.
        """
        if not self.showing or not self.pages:
            return None
        return self.pages[self.current_page_index]

    def _create_pages(self, npc_name: str, text: list[str]) -> list[DialogPage]:
        """Create dialog pages from a list of text strings.

        This internal method converts a simple list of strings into properly
        structured DialogPage objects with metadata like page numbers and total
        count. Each page knows its position in the sequence, which is displayed
        to the player as "Page X/Y".

        Args:
            npc_name: Name of the NPC speaking (applied to all pages).
            text: List of dialog text strings, one per page.

        Returns:
            List of DialogPage objects with sequential page numbering starting at 0.
        """
        total_pages = len(text)
        return [DialogPage(npc_name, page_text, i, total_pages) for i, page_text in enumerate(text)]

    def _reset_text_reveal(self) -> None:
        """Reset text reveal animation state for the current page."""
        self.revealed_chars = 0
        self.char_timer = 0.0
        self.text_fully_revealed = False

    def speed_up_text(self) -> None:
        """Instantly reveal all text on the current page.

        Called when the player presses SPACE while text is still being revealed.
        This allows players to skip the letter-by-letter animation.
        """
        current_page = self.get_current_page()
        if current_page and not self.text_fully_revealed:
            self.revealed_chars = len(current_page.text)
            self.text_fully_revealed = True

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update the dialog text reveal animation and auto-close timer.

        This method should be called every frame with the time elapsed since
        the last frame. It progressively reveals characters in the current
        dialog page at a rate controlled by char_reveal_speed, and handles
        auto-close countdown when enabled.

        Args:
            delta_time: Time elapsed since last update, in seconds.
            context: Game context (not used by DialogManager).
        """
        if not self.showing:
            return

        current_page = self.get_current_page()
        if not current_page:
            return

        # Handle text reveal animation
        if not self.text_fully_revealed:
            self.char_timer += delta_time
            chars_to_reveal = int(self.char_timer * self.char_reveal_speed)

            if chars_to_reveal > 0:
                self.char_timer -= chars_to_reveal / self.char_reveal_speed
                self.revealed_chars = min(self.revealed_chars + chars_to_reveal, len(current_page.text))

                if self.revealed_chars >= len(current_page.text):
                    self.text_fully_revealed = True

        # Handle auto-close countdown
        if self.auto_close_enabled and self.text_fully_revealed:
            self.auto_close_timer += delta_time
            if self.auto_close_timer >= settings.DIALOG_AUTO_CLOSE_DURATION:
                closed = self.advance_page()
                if (
                    closed
                    and self.current_npc_name
                    and self.context
                    and hasattr(self.context, "event_bus")
                    and self.context.event_bus
                ):
                    # Publish DialogClosedEvent (similar to on_key_press)
                    current_level = self.current_dialog_level or 0
                    npc_manager = cast("NPCBaseManager", self.context.get_system("npc"))
                    if npc_manager and hasattr(npc_manager, "npcs"):
                        npc_state = npc_manager.npcs.get(self.current_npc_name)
                        if npc_state:
                            current_level = npc_state.dialog_level

                    self.context.event_bus.publish(
                        DialogClosedEvent(npc_name=self.current_npc_name, dialog_level=current_level)
                    )
                    logger.debug(
                        "Auto-closed dialog for %s at level %s",
                        self.current_npc_name,
                        current_level,
                    )

    def on_draw_ui(self, context: GameContext) -> None:
        """Draw the dialog overlay in screen coordinates.

        This method is called automatically by the system loader during the UI
        draw phase. It renders the complete dialog UI on top of the game world.

        Args:
            context: Game context providing access to the window.
        """
        if not self.showing:
            return

        window = context.window
        current_page = self.get_current_page()
        if not current_page:
            return

        # Draw semi-transparent overlay
        arcade.draw_lrbt_rectangle_filled(
            0,
            window.width,
            0,
            window.height,
            (0, 0, 0, 128),
        )

        # Dialog box dimensions
        box_width = min(600, window.width - 100)
        box_height = 200
        box_x = window.width // 2
        box_y = window.height // 4

        # Calculate box corners
        left = box_x - box_width // 2
        right = box_x + box_width // 2
        bottom = box_y - box_height // 2
        top = box_y + box_height // 2

        # Draw dialog box background
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.DARK_BLUE_GRAY)

        # Draw dialog box border
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, arcade.color.WHITE, border_width=3)

        # Create or update NPC name text
        if self.npc_name_text is None:
            self.npc_name_text = arcade.Text(
                current_page.npc_name,
                box_x,
                top - 30,
                arcade.color.YELLOW,
                font_size=20,
                anchor_x="center",
                bold=True,
            )
        else:
            self.npc_name_text.text = current_page.npc_name
            self.npc_name_text.x = box_x
            self.npc_name_text.y = top - 30

        # Draw NPC name
        self.npc_name_text.draw()

        # Draw dialog text (only revealed portion)
        text_to_show = current_page.text[: self.revealed_chars]

        # Create or update dialog text
        if self.dialog_text is None:
            self.dialog_text = arcade.Text(
                text_to_show,
                left + 20,
                box_y,
                arcade.color.WHITE,
                font_size=16,
                width=box_width - 40,
                multiline=True,
            )
        else:
            self.dialog_text.text = text_to_show
            self.dialog_text.x = left + 20
            self.dialog_text.y = box_y
            self.dialog_text.width = box_width - 40

        # Draw dialog text
        self.dialog_text.draw()

        # Draw page indicator if multiple pages
        if current_page.total_pages > 1:
            page_indicator = f"Page {current_page.page_num + 1}/{current_page.total_pages}"

            # Create or update page indicator text
            if self.page_indicator_text is None:
                self.page_indicator_text = arcade.Text(
                    page_indicator,
                    right - 10,
                    bottom + 20,
                    arcade.color.LIGHT_GRAY,
                    font_size=10,
                    anchor_x="right",
                )
            else:
                self.page_indicator_text.text = page_indicator
                self.page_indicator_text.x = right - 10
                self.page_indicator_text.y = bottom + 20

            # Draw page indicator
            self.page_indicator_text.draw()

        # Draw instruction
        if self.current_page_index < len(self.pages) - 1:
            instruction = "Press SPACE for next page"
        else:
            instruction = "Press SPACE to close"

        # Create or update instruction text
        if self.instruction_text is None:
            self.instruction_text = arcade.Text(
                instruction,
                box_x,
                bottom + 20,
                arcade.color.LIGHT_GRAY,
                font_size=12,
                anchor_x="center",
            )
        else:
            self.instruction_text.text = instruction
            self.instruction_text.x = box_x
            self.instruction_text.y = bottom + 20

        # Draw instruction
        self.instruction_text.draw()

    def get_state(self) -> dict[str, Any]:
        """Return serializable state for saving (BaseSystem interface).

        DialogManager doesn't need to persist state between saves, so this
        returns an empty dictionary.

        Returns:
            Empty dictionary (no state to save).
        """
        return {}

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restore state from save data (BaseSystem interface).

        DialogManager doesn't persist state, so this method does nothing.

        Args:
            state: Previously saved state dictionary (ignored).
        """
