"""Save and load plugin for game state persistence.

This module provides a comprehensive save plugin that persists game state to disk,
allowing players to save their progress and resume later. The plugin uses JSON files
for human-readable storage and supports multiple save slots plus automatic saving.

The save plugin consists of:
- GameSaveData: Data class representing complete game state snapshot
- SavePlugin: Handles file I/O and save slot management

Key features:
- Multiple save slots (typically 1-3) for manual saves
- Automatic save slot (slot 0) for crash recovery
- JSON format for easy debugging and manual editing if needed
- Timestamp tracking for save file metadata
- Version tracking for future save format migrations
- Safe file operations with exception handling
- Pluggable save providers for extensible state management

What gets saved:
- Player position (x, y coordinates)
- Current map filename
- All state from configured save providers (via installed_saves)
- Save timestamp and version metadata

Note: Active scripts in progress are NOT saved - interrupted scripts will restart
from the beginning when the game is loaded.

The save plugin uses pluggable save providers configured via installed_saves in
settings.py. Each provider handles its own state serialization.

File structure:
- Save files are stored in a designated saves/ directory
- Each slot gets its own file: save_slot_1.json, save_slot_2.json, etc.
- Auto-save uses autosave.json
- JSON format with 2-space indentation for readability

Example usage:
    # Create save plugin
    save_plugin = SavePlugin()

    # Save to slot 1
    success = save_plugin.save_game(slot=1, context=context)

    # Load from slot 1
    save_data = save_plugin.load_game(slot=1)
    if save_data:
        save_plugin.restore_game_data(save_data, context)
"""

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, ClassVar

from pedre.conf import settings
from pedre.helpers import get_app_data_dir, matches_key
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.save.base import GameSaveData, SaveBasePlugin

if TYPE_CHECKING:
    from pathlib import Path


logger = logging.getLogger(__name__)


@PluginRegistry.register
class SavePlugin(SaveBasePlugin):
    """Manages game save and load operations.

    The SavePlugin coordinates all save/load functionality, handling file I/O, slot
    management, and state serialization via SaveLoader.

    Attributes:
        saves_dir: Path to directory containing save files.
        current_slot: Most recently used save slot number, or None if no saves yet.
        settings: Game settings for resolving asset paths.
    """

    name: ClassVar[str] = "save"

    def __init__(self) -> None:
        """Initialize the save plugin."""
        self.saves_dir = get_app_data_dir(settings.SAVE_FOLDER)
        self.saves_dir.mkdir(parents=True, exist_ok=True)

        self.current_slot: int | None = None

    def cleanup(self) -> None:
        """Clean up save plugin resources."""
        return

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle quick save/load hotkeys.

        Args:
            symbol: Keyboard symbol.
            modifiers: Key modifiers.

        Returns:
            True if hotkey was handled.
        """
        if matches_key(symbol, settings.SAVE_QUICK_SAVE_KEY):
            self._handle_quick_save()
            return True
        if matches_key(symbol, settings.SAVE_QUICK_LOAD_KEY):
            self._handle_quick_load()
            return True
        return False

    def _handle_quick_save(self) -> None:
        """Perform a quick save using current context state."""
        success = self.auto_save()

        audio_plugin = self.context.audio_plugin
        if success:
            audio_plugin.play_sfx(settings.SAVE_SFX_FILE)
            logger.info("Quick save completed")
        else:
            logger.warning("Quick save failed")

    def _handle_quick_load(self) -> None:
        """Perform a quick load from auto-save."""
        save_data = self.load_auto_save()
        if not save_data:
            logger.warning("No auto-save found for quick load")
            return

        # Restore state from save providers
        self.restore_game_data(save_data)

        audio_plugin = self.context.audio_plugin
        audio_plugin.play_sfx(settings.SAVE_SFX_FILE)
        logger.info("Quick load completed")

    def save_game(self, slot: int) -> bool:
        """Save game to a slot.

        Creates a complete snapshot of the current game state and writes it to a JSON
        file in the specified slot.

        The save process:
        1. Gathers state from all save providers via SaveLoader
        2. Creates GameSaveData with current state and UTC timestamp
        3. Serializes to JSON with 2-space indentation
        4. Writes to slot-specific file (overwrites if exists)
        5. Updates current_slot tracker

        Args:
            slot: Save slot number (0 for auto-save, 1-3 for manual saves).

        Returns:
            True if save succeeded and file was written, False if any error occurred.
        """
        scene_plugin = self.context.scene_plugin

        try:
            # Gather state from all plugins
            save_states: dict[str, Any] = {}
            for plugin in self.context.get_plugins().values():
                state = plugin.get_save_state()
                if state:
                    save_states[plugin.name] = state
                    logger.debug("Gathered save state from plugin: %s", plugin.name)

            # Cache the current active scene before saving (in case we never left it)
            cache_plugin = self.context.cache_plugin
            cache_plugin.cache_scene(scene_plugin.get_current_scene())

            # Create save data
            player_sprite = self.context.player_plugin.get_player_sprite()
            if player_sprite:
                save_data = GameSaveData(
                    save_states=save_states,
                    save_timestamp=datetime.now(UTC).timestamp(),
                )

                # Write to file
                save_path = self._get_save_path(slot)
                with save_path.open("w") as f:
                    json.dump(save_data.to_dict(), f, indent=2)

                self.current_slot = slot

        except Exception:
            logger.exception("Failed to save game")
            return False
        else:
            logger.info("Game saved to slot %d", slot)
            return True

    def load_game(self, slot: int) -> GameSaveData | None:
        """Load game from a slot.

        Reads a save file from the specified slot and deserializes it into a GameSaveData
        object.

        Args:
            slot: Save slot number (0 for auto-save, 1-3 for manual saves).

        Returns:
            GameSaveData object containing all saved state if successful, None if the
            save file doesn't exist or if loading failed.
        """
        try:
            save_path = self._get_save_path(slot)

            if not save_path.exists():
                logger.warning("No save file found in slot %d", slot)
                return None

            with save_path.open() as f:
                data = json.load(f)

            save_data = GameSaveData.from_dict(data)
            self.current_slot = slot

        except Exception:
            logger.exception("Failed to load game")
            return None
        else:
            logger.info("Game loaded from slot %d", slot)
            return save_data

    def restore_game_data(self, save_data: GameSaveData) -> None:
        """Phase 1: Restore metadata state from save data before sprites exist.

        This restores non-entity state (settings, flags, which map to load).
        Entity-specific state (positions, visibility) is applied later via
        apply_entity_states() after load_from_tiled() creates sprites.

        Args:
            save_data: The GameSaveData object loaded from a save file.
        """
        # Store save data for Phase 2 (entity state restoration)
        self.context.set_pending_save_data(save_data)

        # Restore each plugin's metadata state
        for plugin in self.context.get_plugins().values():
            if plugin.name in save_data.save_states:
                plugin.restore_save_state(save_data.save_states[plugin.name])
                logger.debug("Restored metadata state to plugin: %s", plugin.name)

        logger.info("Phase 1: Restored metadata state from save data")

    def apply_entity_states(self) -> None:
        """Phase 2: Apply entity-specific state after sprites exist.

        Called by ScenePlugin after load_from_tiled() has created all sprites.
        This applies positions, visibility, and other state that requires
        sprites to exist.
        """
        save_data = self.context.get_pending_save_data()
        if not save_data:
            return

        for plugin in self.context.get_plugins().values():
            if plugin.name in save_data.save_states:
                plugin.apply_entity_state(save_data.save_states[plugin.name])
                logger.debug("Applied entity state to plugin: %s", plugin.name)

        self.context.clear_pending_save_data()
        logger.info("Phase 2: Applied entity state from save data")

    def delete_save(self, slot: int) -> bool:
        """Delete a save file.

        Args:
            slot: Save slot number (0 for auto-save, 1-3 for manual saves).

        Returns:
            True if save file existed and was deleted successfully, False otherwise.
        """
        try:
            save_path = self._get_save_path(slot)

            if save_path.exists():
                save_path.unlink()
            else:
                logger.warning("No save file to delete in slot %d", slot)
                return False

        except Exception:
            logger.exception("Failed to delete save")
            return False
        else:
            logger.info("Deleted save in slot %d", slot)
            return True

    def save_exists(self, slot: int) -> bool:
        """Check if a save file exists in a slot.

        Args:
            slot: Save slot number (0 for auto-save, 1-3 for manual saves).

        Returns:
            True if a save file exists in the slot, False otherwise.
        """
        return self._get_save_path(slot).exists()

    def get_save_info(self, slot: int) -> dict[str, Any] | None:
        """Get basic info about a save file without fully loading it.

        Args:
            slot: Save slot number (0 for auto-save, 1-3 for manual saves).

        Returns:
            Dictionary with save metadata if the file exists and is readable,
            None if the file doesn't exist or if an error occurred.
        """
        try:
            save_path = self._get_save_path(slot)

            if not save_path.exists():
                return None

            with save_path.open() as f:
                data = json.load(f)

            # Return summary info
            timestamp = data.get("save_timestamp", 0)
            dt = datetime.fromtimestamp(timestamp, UTC)

        except Exception:
            logger.exception("Failed to get save info")
            return None
        else:
            return {
                "slot": slot,
                "map": data["save_states"]["scene"].get("current_map", "Unknown"),
                "timestamp": timestamp,
                "date_string": dt.strftime("%Y-%m-%d %H:%M"),
                "version": data.get("save_version", "Unknown"),
            }

    def auto_save(self) -> bool:
        """Auto-save to a special auto-save slot.

        Returns:
            True if auto-save succeeded, False if it failed.
        """
        return self.save_game(0)

    def load_auto_save(self) -> GameSaveData | None:
        """Load from auto-save slot.

        Returns:
            GameSaveData object with auto-save state if successful, None otherwise.
        """
        return self.load_game(0)

    def _get_save_path(self, slot: int) -> Path:
        """Get the file path for a save slot.

        Args:
            slot: Save slot number (0 for auto-save, 1+ for manual saves).

        Returns:
            Path object pointing to the save file for the specified slot.
        """
        if slot == 0:
            return self.saves_dir / "autosave.json"
        return self.saves_dir / f"save_slot_{slot}.json"
