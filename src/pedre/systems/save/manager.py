"""Save and load system for game state persistence.

This module provides a comprehensive save system that persists game state to disk,
allowing players to save their progress and resume later. The system uses JSON files
for human-readable storage and supports multiple save slots plus automatic saving.

The save system consists of:
- GameSaveData: Data class representing complete game state snapshot
- SaveManager: Handles file I/O and save slot management

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

The save system uses pluggable save providers configured via installed_saves in
settings.py. Each provider handles its own state serialization.

File structure:
- Save files are stored in a designated saves/ directory
- Each slot gets its own file: save_slot_1.json, save_slot_2.json, etc.
- Auto-save uses autosave.json
- JSON format with 2-space indentation for readability

Example usage:
    # Create save manager
    save_manager = SaveManager()

    # Save to slot 1
    success = save_manager.save_game(slot=1, context=context)

    # Load from slot 1
    save_data = save_manager.load_game(slot=1)
    if save_data:
        save_manager.restore_game_data(save_data, context)
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, cast

import arcade

from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.systems.audio import AudioManager
    from pedre.systems.game_context import GameContext
    from pedre.systems.scene import SceneManager

logger = logging.getLogger(__name__)


@dataclass
class GameSaveData:
    """Complete game save state.

    This data class represents a snapshot of the entire game state at a moment in time.
    It contains player position, current map, and all state from save providers.

    State categories:
    1. Player state: Physical location in the world
    2. World state: Which map the player is currently in
    3. Save states: All state from configured save providers
    4. Metadata: When the save was created and what format version

    The save_version field enables future migration if the save format needs to change.

    Attributes:
        player_x: Player's X position in pixel coordinates.
        player_y: Player's Y position in pixel coordinates.
        current_map: Filename of the current map (e.g., "village.tmx").
        save_states: Dictionary mapping save provider names to their serialized state.
        save_timestamp: Unix timestamp when save was created (seconds since epoch).
        save_version: Save format version string for future compatibility.
    """

    # Player state
    player_x: float
    player_y: float
    current_map: str

    # All state from save providers
    save_states: dict[str, Any] = field(default_factory=dict)

    # Metadata
    save_timestamp: float = 0.0
    save_version: str = "2.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation with all save data fields as key-value pairs.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameSaveData:
        """Create from dictionary loaded from JSON.

        Args:
            data: Dictionary loaded from JSON save file.

        Returns:
            New GameSaveData instance with values from the dictionary.
        """
        return cls(
            player_x=data["player_x"],
            player_y=data["player_y"],
            current_map=data["current_map"],
            save_states=data.get("save_states", {}),
            save_timestamp=data.get("save_timestamp", 0.0),
            save_version=data.get("save_version", "2.0"),
        )


@SystemRegistry.register
class SaveManager(BaseSystem):
    """Manages game save and load operations.

    The SaveManager coordinates all save/load functionality, handling file I/O, slot
    management, and state serialization via SaveLoader.

    Attributes:
        saves_dir: Path to directory containing save files.
        current_slot: Most recently used save slot number, or None if no saves yet.
        settings: Game settings for resolving asset paths.
    """

    name: ClassVar[str] = "save"

    def __init__(self, saves_dir: Path | None = None) -> None:
        """Initialize the save manager.

        Args:
            saves_dir: Optional custom path to save files directory. If None, uses
                      default 'saves' directory in project root.
        """
        if saves_dir is None:
            # Default to saves/ directory in project root
            saves_dir = Path.cwd() / "saves"

        self.saves_dir = saves_dir
        self.saves_dir.mkdir(exist_ok=True)

        self.current_slot: int | None = None

    def setup(self, context: GameContext) -> None:
        """Initialize the save system with settings."""
        return

    def cleanup(self) -> None:
        """Clean up save system resources."""
        return

    def on_key_press(self, symbol: int, modifiers: int, context: GameContext) -> bool:
        """Handle quick save/load hotkeys.

        Args:
            symbol: Keyboard symbol.
            modifiers: Key modifiers.
            context: Game context.

        Returns:
            True if hotkey was handled.
        """
        if symbol == arcade.key.F5:
            self._handle_quick_save(context)
            return True
        if symbol == arcade.key.F9:
            self._handle_quick_load(context)
            return True
        return False

    def _handle_quick_save(self, context: GameContext) -> None:
        """Perform a quick save using current context state."""
        if not context.player_sprite:
            return

        scene_manager = context.get_system("scene")
        if not scene_manager or not hasattr(scene_manager, "current_map"):
            return

        success = self.auto_save(context)

        audio_manager = cast("AudioManager | None", context.get_system("audio"))
        if success:
            if audio_manager:
                audio_manager.play_sfx("save.wav")
            logger.info("Quick save completed")
        else:
            logger.warning("Quick save failed")

    def _handle_quick_load(self, context: GameContext) -> None:
        """Perform a quick load from auto-save."""
        # Note: game_view check removed - quick load handled by ViewManager.load_game()
        save_data = self.load_auto_save()
        if not save_data:
            logger.warning("No auto-save found for quick load")
            return

        # Reload map if different
        scene_manager = cast("SceneManager | None", context.get_system("scene"))
        current_map = ""
        if scene_manager and hasattr(scene_manager, "current_map"):
            current_map = scene_manager.current_map

        if save_data.current_map != current_map:
            if scene_manager and hasattr(scene_manager, "load_level"):
                scene_manager.load_level(save_data.current_map, None, context)
            else:
                logger.warning("Cannot reload map: SceneManager.load_level not available")
                return

        # Restore state from save providers
        self.restore_game_data(save_data, context)

        # Reposition player
        if context.player_sprite:
            context.player_sprite.center_x = save_data.player_x
            context.player_sprite.center_y = save_data.player_y

        audio_manager = cast("AudioManager | None", context.get_system("audio"))
        if audio_manager:
            audio_manager.play_sfx("save.wav")
        logger.info("Quick load completed")

    def save_game(self, slot: int, context: GameContext) -> bool:
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
            context: Game context providing access to game state.

        Returns:
            True if save succeeded and file was written, False if any error occurred.
        """
        if not context.player_sprite:
            logger.error("No player sprite in context")
            return False

        scene_manager = cast("SceneManager | None", context.get_system("scene"))
        if not scene_manager or not hasattr(scene_manager, "current_map"):
            logger.error("SceneManager not available")
            return False

        try:
            # Gather state from all systems
            save_states: dict[str, Any] = {}
            for system in context.get_systems().values():
                state = system.get_save_state()
                if state:
                    save_states[system.name] = state
                    logger.debug("Gathered save state from system: %s", system.name)

            # Also include cache manager state
            cache_state = scene_manager.get_cache_state_dict()
            if cache_state:
                save_states["_scene_caches"] = cache_state

            # Create save data
            save_data = GameSaveData(
                player_x=context.player_sprite.center_x,
                player_y=context.player_sprite.center_y,
                current_map=scene_manager.current_map,
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

    def restore_game_data(self, save_data: GameSaveData, context: GameContext) -> None:
        """Restore all state from save data to save providers.

        Args:
            save_data: The GameSaveData object loaded from a save file.
            context: Game context for accessing managers.
        """
        # Restore cache manager state first
        if "_scene_caches" in save_data.save_states:
            scene_manager = cast("SceneManager | None", context.get_system("scene"))
            if scene_manager:
                scene_manager.restore_cache_state(save_data.save_states["_scene_caches"])
                logger.debug("Restored cache manager state")

        # Restore each system's state
        for system in context.get_systems().values():
            if system.name in save_data.save_states:
                system.restore_save_state(save_data.save_states[system.name])
                logger.debug("Restored save state to system: %s", system.name)

        logger.info("Restored all state from save data")

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
                "map": data.get("current_map", "Unknown"),
                "timestamp": timestamp,
                "date_string": dt.strftime("%Y-%m-%d %H:%M"),
                "version": data.get("save_version", "Unknown"),
            }

    def auto_save(self, context: GameContext) -> bool:
        """Auto-save to a special auto-save slot.

        Args:
            context: Game context providing access to game state.

        Returns:
            True if auto-save succeeded, False if it failed.
        """
        return self.save_game(0, context)

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
