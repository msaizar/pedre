"""Debug manager for rendering debug overlays."""

import logging
from typing import TYPE_CHECKING, ClassVar, cast

import arcade

from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.systems.game_context import GameContext
    from pedre.systems.npc import NPCManager

logger = logging.getLogger(__name__)


@SystemRegistry.register
class DebugManager(BaseSystem):
    """System for rendering debug information.

    Handles the debug overlay showing player and NPC positions in tile coordinates.
    Toggled with Shift+D.
    """

    name: ClassVar[str] = "debug"
    dependencies: ClassVar[list[str]] = ["npc"]

    def __init__(self) -> None:
        """Initialize the debug manager with default state."""
        self.debug_mode = False
        self.debug_text_objects: list[arcade.Text] = []
        self.settings: GameSettings | None = None

    def setup(self, context: GameContext, settings: GameSettings) -> None:
        """Initialize the debug system.

        Args:
            context: Game context.
            settings: Game settings.
        """
        self.settings = settings
        self.debug_text_objects = []

    def on_key_press(self, symbol: int, modifiers: int, context: GameContext) -> bool:
        """Handle debug toggle input.

        Args:
            symbol: Key symbol.
            modifiers: Key modifiers.
            context: Game context.

        Returns:
            True if handled.
        """
        if symbol == arcade.key.D and (modifiers & arcade.key.MOD_SHIFT):
            self.debug_mode = not self.debug_mode
            logger.info("Debug mode toggled: %s", self.debug_mode)
            # Clear text objects when toggling off
            if not self.debug_mode:
                self.debug_text_objects.clear()
            return True
        return False

    def on_draw_ui(self, context: GameContext) -> None:
        """Draw debug information overlay in screen coordinates.

        Args:
            context: Game context.
        """
        if not self.debug_mode or not self.settings:
            return

        # Build debug text content
        debug_lines = []
        y_offset = 30
        tile_size = self.settings.tile_size

        # Collect player position (from context)
        if context.player_sprite:
            player_tile_x = int(context.player_sprite.center_x / tile_size)
            player_tile_y = int(context.player_sprite.center_y / tile_size)
            debug_lines.append((f"Player: tile ({player_tile_x}, {player_tile_y})", arcade.color.GREEN))

        # Collect NPC positions
        npc_manager = cast("NPCManager", context.get_system("npc"))
        if npc_manager:
            for npc_name, npc_state in npc_manager.npcs.items():
                if npc_state.sprite and npc_state.sprite.visible:
                    tile_x = int(npc_state.sprite.center_x / tile_size)
                    tile_y = int(npc_state.sprite.center_y / tile_size)
                    debug_lines.append(
                        (f"{npc_name}: tile ({tile_x}, {tile_y}) level {npc_state.dialog_level}", arcade.color.YELLOW)
                    )

        # Create or update text objects
        num_needed = len(debug_lines)
        num_existing = len(self.debug_text_objects)

        # Remove extra text objects if we have too many
        if num_existing > num_needed:
            self.debug_text_objects = self.debug_text_objects[:num_needed]

        # Update or create text objects
        for i, (text, color) in enumerate(debug_lines):
            if i < len(self.debug_text_objects):
                # Update existing text object
                self.debug_text_objects[i].text = text
                self.debug_text_objects[i].color = color
                self.debug_text_objects[i].y = y_offset
            else:
                # Create new text object
                text_obj = arcade.Text(
                    text,
                    10,
                    y_offset,
                    color,
                    font_size=12,
                )
                self.debug_text_objects.append(text_obj)

            y_offset += 20

        # Draw all text objects
        for text_obj in self.debug_text_objects:
            text_obj.draw()

    def cleanup(self) -> None:
        """Clean up debug resources."""
        self.debug_text_objects.clear()
        self.debug_mode = False
