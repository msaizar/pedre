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

What gets saved:
- Player position (x, y coordinates)
- Current map filename
- NPC dialog progression levels for all NPCs
- NPC positions and visibility (for scripted movement/appearances)
- Inventory item states (collected/not collected)
- Inventory accessed flag (for tutorial/dialog triggers)
- Audio settings (volumes and enable/disable states)
- Interacted objects set (for puzzle/dialog state)
- Completed run_once scripts (prevents re-triggering)
- Save timestamp and version metadata

Note: Active scripts in progress are NOT saved - interrupted scripts will restart
from the beginning when the game is loaded.

The save system is designed to be extensible - new state can be added by updating
GameSaveData and modifying save_game()/load_game() to handle the new fields.

File structure:
- Save files are stored in a designated saves/ directory
- Each slot gets its own file: save_slot_1.json, save_slot_2.json, etc.
- Auto-save uses autosave.json
- JSON format with 2-space indentation for readability

Integration with other systems:
- NPCManager provides dialog level state and restores via restore_state()
- InventoryManager provides item collection state and restores via from_dict()
- AudioManager provides user settings and restores via from_dict()
- ScriptManager provides interacted_objects set for dialog conditions
- Game view coordinates the save/load process
- Map loading system uses saved map name and position

Example usage:
    # Create save manager
    save_manager = SaveManager()

    # Save to slot 1
    success = save_manager.save_game(
        slot=1,
        player_x=player.center_x,
        player_y=player.center_y,
        current_map="village.tmx",
        npc_manager=npc_manager,
        inventory_manager=inventory_manager,
        audio_manager=audio_manager,
        interacted_objects=script_manager.interacted_objects
    )

    # Load from slot 1
    save_data = save_manager.load_game(slot=1)
    if save_data:
        # Restore game state
        player.center_x = save_data.player_x
        player.center_y = save_data.player_y
        load_map(save_data.current_map)

        # Restore all manager states
        interacted_objects = save_manager.restore_all_state(
            save_data,
            npc_manager,
            inventory_manager,
            audio_manager
        )

    # Auto-save periodically
    save_manager.auto_save(
        player_x, player_y, current_map,
        npc_manager, inventory_manager,
        audio_manager, interacted_objects
    )
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pedre.systems.audio import AudioManager
    from pedre.systems.inventory import InventoryManager
    from pedre.systems.npc import NPCManager
    from pedre.systems.script import ScriptManager

logger = logging.getLogger(__name__)


@dataclass
class GameSaveData:
    """Complete game save state.

    This data class represents a snapshot of the entire game state at a moment in time.
    It contains all information needed to restore the player's progress, including position,
    current location, NPC interaction history, and collected items.

    The class uses Python's dataclass for automatic initialization and provides serialization
    methods for converting to/from JSON format for file storage.

    State categories:
    1. Player state: Physical location in the world
    2. World state: Which map the player is currently in
    3. NPC state: Dialog progression for each NPC
    4. Inventory state: Which items have been collected
    5. Metadata: When the save was created and what format version

    The save_version field enables future migration if the save format needs to change.
    For example, if new fields are added in version 2.0, the load code can detect version
    1.0 saves and provide default values for missing fields.

    Attributes:
        player_x: Player's X position in pixel coordinates.
        player_y: Player's Y position in pixel coordinates.
        current_map: Filename of the current map (e.g., "village.tmx").
        npc_dialog_levels: Dictionary mapping NPC names to their current dialog level.
        npc_positions: Optional dictionary mapping NPC names to their position and visibility state.
                      Each NPC entry contains: {"x": float, "y": float, "visible": bool}.
                      None if NPC positions should use map defaults.
        inventory_items: Optional dictionary mapping item names to collection state (True/False).
                        None if inventory system not used.
        inventory_accessed: Whether the player has opened their inventory at least once.
                           Used for dialog conditions and tutorials.
        audio_settings: Optional dictionary with audio preferences (volumes, enabled states).
                       None if audio settings should use defaults.
        interacted_objects: Optional list of interactive object names that have been used.
                          Used for dialog conditions and puzzle state tracking.
        completed_scripts: Optional list of run_once script names that have completed.
                          Scripts in this list won't trigger again. None if no scripts completed.
        scene_states: Optional dictionary storing NPC states per scene for persistence across
                     scene transitions. Maps scene names to NPC states (position, visibility,
                     dialog level). None if no scenes have been visited yet.
        save_timestamp: Unix timestamp when save was created (seconds since epoch).
        save_version: Save format version string for future compatibility.
    """

    # Player state
    player_x: float
    player_y: float
    current_map: str

    # NPC dialog states
    npc_dialog_levels: dict[str, int]
    npc_positions: dict[str, dict[str, float | bool]] | None = None

    # Inventory state
    inventory_items: dict[str, bool] | None = None
    inventory_accessed: bool = False

    # Audio settings
    audio_settings: dict[str, bool | float] | None = None

    # Game state
    interacted_objects: list[str] | None = None
    completed_scripts: list[str] | None = None

    # Scene state cache (NPC states per scene for persistence across transitions)
    scene_states: dict[str, dict[str, dict[str, float | bool | int]]] | None = None

    # Metadata
    save_timestamp: float = 0.0
    save_version: str = "1.0"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Uses the dataclass asdict() helper to convert all fields to a dictionary
        suitable for JSON encoding. This handles nested structures like the
        npc_dialog_levels and inventory_items dictionaries automatically.

        The resulting dictionary can be directly passed to json.dump() for writing
        to a save file.

        Returns:
            Dictionary representation with all save data fields as key-value pairs.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> GameSaveData:
        """Create from dictionary loaded from JSON.

        Class method that reconstructs a GameSaveData instance from a dictionary
        loaded from a JSON save file. This is the reverse operation of to_dict().

        The method uses dictionary unpacking (**data) to pass all fields to the
        dataclass constructor, which handles type conversion and validation.

        This is typically called after json.load() to convert the raw dictionary
        data into a properly typed GameSaveData object.

        Args:
            data: Dictionary loaded from JSON save file, containing all required
                 and optional fields.

        Returns:
            New GameSaveData instance with values from the dictionary.
        """
        return cls(**data)


class SaveManager:
    """Manages game save and load operations.

    The SaveManager coordinates all save/load functionality, handling file I/O, slot
    management, and state serialization. It provides a high-level interface for the
    game to persist and restore player progress.

    The manager uses a slot-based system:
    - Slots 1-3: Manual player saves (accessible from save/load menu)
    - Slot 0: Auto-save (automatic periodic saves for crash recovery)

    Each slot is an independent save file stored in JSON format. The manager ensures
    the save directory exists and handles all file operations safely with exception
    handling to prevent data corruption.

    Save file lifecycle:
    1. Game calls save_game() with current state
    2. Manager gathers state from various managers (NPCs, inventory)
    3. Creates GameSaveData snapshot with timestamp
    4. Serializes to JSON and writes to appropriate slot file
    5. On load, reads JSON, deserializes to GameSaveData
    6. Game restores state from returned data

    The manager tracks the current_slot to remember which save was last used,
    useful for quick-save/quick-load functionality.

    Error handling:
    All file operations are wrapped in try-except blocks. Errors are logged and
    methods return False/None to indicate failure, allowing the game to show
    appropriate error messages to the player.

    Attributes:
        saves_dir: Path to directory containing save files.
        current_slot: Most recently used save slot number, or None if no saves yet.
    """

    def __init__(self, saves_dir: Path | None = None) -> None:
        """Initialize the save manager.

        Creates the save manager and ensures the save directory exists. If no directory
        is specified, defaults to a 'saves' folder in the project root (four levels up
        from this file's location).

        The directory is created if it doesn't exist (mkdir with exist_ok=True), so
        the manager is ready to save immediately after initialization.

        Args:
            saves_dir: Optional custom path to save files directory. If None, uses
                      default 'saves' directory in project root.
        """
        if saves_dir is None:
            # Default to saves/ directory in project root
            saves_dir = Path(__file__).parent.parent.parent.parent / "saves"

        self.saves_dir = saves_dir
        self.saves_dir.mkdir(exist_ok=True)

        # Track current save slot
        self.current_slot: int | None = None

    def save_game(
        self,
        slot: int,
        player_x: float,
        player_y: float,
        current_map: str,
        npc_manager: NPCManager | None = None,
        inventory_manager: InventoryManager | None = None,
        audio_manager: AudioManager | None = None,
        script_manager: ScriptManager | None = None,
        scene_states: dict[str, dict[str, dict[str, float | bool | int]]] | None = None,
    ) -> bool:
        """Save game to a slot.

        Creates a complete snapshot of the current game state and writes it to a JSON
        file in the specified slot. This includes player position, map location, NPC
        interaction history, and inventory state.

        The save process:
        1. Extracts dialog levels from all NPCs in npc_manager
        2. Optionally extracts inventory state from inventory_manager
        3. Creates GameSaveData with current state and UTC timestamp
        4. Serializes to JSON with 2-space indentation
        5. Writes to slot-specific file (overwrites if exists)
        6. Updates current_slot tracker

        File location:
        - Slots 1-3 write to: saves/save_slot_N.json
        - Slot 0 writes to: saves/autosave.json

        The method is safe to call repeatedly - it overwrites existing saves in the
        slot, ensuring the save file always reflects the latest state.

        Error handling:
        If any exception occurs during save (file I/O errors, serialization issues),
        the error is logged and False is returned. The game should check the return
        value and notify the player if the save failed.

        Args:
            slot: Save slot number (0 for auto-save, 1-3 for manual saves).
            player_x: Player's current X position in pixel coordinates.
            player_y: Player's current Y position in pixel coordinates.
            current_map: Filename of the current map (e.g., "village.tmx").
            npc_manager: Optional NPC manager containing all NPC dialog progression states.
            inventory_manager: Optional inventory manager with item collection states.
                              If None, inventory_items will be saved as None.
            audio_manager: Optional audio manager with volume and enable/disable settings.
                          If None, audio_settings will be saved as None.
            script_manager: Optional script manager with interacted_objects and completed scripts.
                           If None, interacted_objects and completed_scripts will be saved as None.
            scene_states: Optional dictionary of per-scene NPC states from SceneStateCache.
                         If None, scene_states will be saved as None.

        Returns:
            True if save succeeded and file was written, False if any error occurred.
        """
        try:
            # Gather NPC dialog states
            npc_states = (
                {name: npc_state.dialog_level for name, npc_state in npc_manager.npcs.items()} if npc_manager else {}
            )

            # Gather NPC positions and visibility
            npc_positions = npc_manager.get_npc_positions() if npc_manager else None

            # Gather inventory states
            inventory_items = inventory_manager.to_dict() if inventory_manager else None
            inventory_accessed = inventory_manager.has_been_accessed if inventory_manager else False

            # Gather audio settings
            audio_settings = audio_manager.to_dict() if audio_manager else None

            # Gather script state
            interacted_objects_list = list(script_manager.interacted_objects) if script_manager else None
            completed_scripts = script_manager.get_completed_scripts() if script_manager else None

            # Create save data
            save_data = GameSaveData(
                player_x=player_x,
                player_y=player_y,
                current_map=current_map,
                npc_dialog_levels=npc_states,
                npc_positions=npc_positions,
                inventory_items=inventory_items,
                inventory_accessed=inventory_accessed,
                audio_settings=audio_settings,
                interacted_objects=interacted_objects_list,
                completed_scripts=completed_scripts,
                scene_states=scene_states,
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
        object. The caller is responsible for applying the loaded state to the game
        (restoring player position, loading the map, updating NPC states, etc.).

        The load process:
        1. Constructs file path for the slot
        2. Checks if save file exists
        3. Reads and parses JSON file
        4. Deserializes into GameSaveData object
        5. Updates current_slot tracker
        6. Returns the loaded data

        Missing save handling:
        If no save file exists in the slot, a warning is logged and None is returned.
        This allows the game to distinguish between "no save exists" and "load failed".

        Error handling:
        If any exception occurs during load (file I/O errors, JSON parsing errors,
        invalid data format), the error is logged and None is returned. The game should
        check for None and handle appropriately (show error message, return to menu, etc.).

        After loading:
        The game typically needs to:
        - Load the specified map
        - Position the player at the saved coordinates
        - Restore NPC dialog levels via npc_manager.restore_state()
        - Restore inventory via inventory_manager.restore_state()

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

    def delete_save(self, slot: int) -> bool:
        """Delete a save file.

        Permanently removes a save file from the specified slot. This operation cannot
        be undone - the save data is lost permanently.

        The method is safe to call even if no save exists in the slot - it will log a
        warning and return False but won't raise an exception.

        Typical use cases:
        - Player explicitly deletes a save from the save management menu
        - Clearing corrupted save files
        - Resetting a save slot during development/testing

        The current_slot tracker is NOT modified by this method. If the deleted slot
        was the current slot, current_slot will still reference it even though the
        file is gone.

        Args:
            slot: Save slot number (0 for auto-save, 1-3 for manual saves).

        Returns:
            True if save file existed and was deleted successfully, False if the file
            didn't exist or if deletion failed.
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

        Quick check to determine if a save file is present in the specified slot
        without actually loading or parsing the file.

        This is useful for:
        - Populating save/load menu UI (showing which slots have saves)
        - Enabling/disabling load buttons based on save availability
        - Checking if auto-save exists before offering to load it
        - Validating before attempting to load or delete

        The check only verifies file existence, not validity. A corrupt or invalid
        save file will still return True. Use load_game() or get_save_info() to
        validate the file contents.

        Args:
            slot: Save slot number (0 for auto-save, 1-3 for manual saves).

        Returns:
            True if a save file exists in the slot, False otherwise.
        """
        return self._get_save_path(slot).exists()

    def get_save_info(self, slot: int) -> dict | None:
        """Get basic info about a save file without fully loading it.

        Reads minimal information from a save file for display purposes without fully
        deserializing the entire game state. This is more efficient than load_game()
        when you only need to show save metadata in a menu.

        The method reads the JSON file and extracts key fields to create a summary
        dictionary. The timestamp is converted to a human-readable date string in
        "YYYY-MM-DD HH:MM" format.

        Returned info includes:
        - slot: The slot number (echoed back for convenience)
        - map: The map the save was created on
        - timestamp: Unix timestamp (seconds since epoch)
        - date_string: Formatted date/time for display
        - version: Save format version

        This is typically used to populate a save/load menu showing:
        "Slot 1: Village - 2024-01-15 14:30 (v1.0)"

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

    def auto_save(
        self,
        player_x: float,
        player_y: float,
        current_map: str,
        npc_manager: NPCManager | None = None,
        inventory_manager: InventoryManager | None = None,
        audio_manager: AudioManager | None = None,
        script_manager: ScriptManager | None = None,
        scene_states: dict[str, dict[str, dict[str, float | bool | int]]] | None = None,
    ) -> bool:
        """Auto-save to a special auto-save slot.

        Convenience method for automatic periodic saves. Uses slot 0, which is separate
        from the manual save slots (1-3). This allows the game to auto-save without
        overwriting the player's manual saves.

        Auto-save is typically triggered:
        - Periodically on a timer (e.g., every 5 minutes)
        - When transitioning between maps
        - After completing major story events
        - Before potentially dangerous encounters

        The auto-save serves as a safety net for crash recovery. If the game crashes,
        the player can load the auto-save to recover recent progress without losing
        much playtime.

        This method is functionally identical to calling save_game(0, ...) but provides
        a clearer semantic meaning in the calling code.

        Args:
            player_x: Player's current X position in pixel coordinates.
            player_y: Player's current Y position in pixel coordinates.
            current_map: Filename of the current map.
            npc_manager: Optional NPC manager containing dialog progression states.
            inventory_manager: Optional inventory manager with item collection states.
            audio_manager: Optional audio manager with volume and enable/disable settings.
            script_manager: Optional script manager with interacted_objects and completed scripts.
            scene_states: Optional dictionary of per-scene NPC states from SceneStateCache.

        Returns:
            True if auto-save succeeded, False if it failed.
        """
        # Use slot 0 for auto-save
        return self.save_game(
            0,
            player_x,
            player_y,
            current_map,
            npc_manager,
            inventory_manager,
            audio_manager,
            script_manager,
            scene_states,
        )

    def load_auto_save(self) -> GameSaveData | None:
        """Load from auto-save slot.

        Convenience method for loading the automatic save. Uses slot 0, which is
        the dedicated auto-save slot separate from manual saves.

        This is typically used:
        - When offering "Continue" option on the main menu
        - For crash recovery after unexpected game termination
        - Testing/debugging to quickly load recent game state

        The method checks if an auto-save exists and loads it if present. If no
        auto-save exists (first launch) or if loading fails, returns None.

        This method is functionally identical to calling load_game(0) but provides
        clearer semantic meaning in the calling code.

        Returns:
            GameSaveData object with auto-save state if successful, None if no
            auto-save exists or if loading failed.
        """
        return self.load_game(0)

    def restore_all_state(
        self,
        save_data: GameSaveData,
        npc_manager: NPCManager | None = None,
        inventory_manager: InventoryManager | None = None,
        audio_manager: AudioManager | None = None,
        script_manager: ScriptManager | None = None,
    ) -> tuple[set[str], dict[str, dict[str, dict[str, float | bool | int]]] | None]:
        """Restore all manager states from save data.

        Convenience method that applies loaded save data to all game managers.
        This centralizes the restoration logic to ensure all state is properly
        restored in the correct order.

        The method restores:
        - NPC dialog levels via npc_manager.restore_state()
        - NPC positions and visibility via npc_manager.restore_positions()
        - Inventory items via inventory_manager.from_dict()
        - Inventory accessed flag via inventory_manager.has_been_accessed
        - Audio settings via audio_manager.from_dict()
        - Completed scripts via script_manager.restore_completed_scripts()
        - Interacted objects set (returned for game to use)
        - Scene states (returned for game to restore to SceneStateCache)

        Args:
            save_data: The GameSaveData object loaded from a save file.
            npc_manager: Optional NPC manager to restore dialog levels to.
            inventory_manager: Optional inventory manager to restore items to.
            audio_manager: Optional audio manager to restore settings to.
            script_manager: Optional script manager to restore completed scripts to.

        Returns:
            Tuple of (interacted_objects set, scene_states dict or None).
            The scene_states should be passed to SceneStateCache.from_dict().

        Example:
            # Load and restore a save
            save_data = save_manager.load_game(slot=1)
            if save_data:
                interacted_objects, scene_states = save_manager.restore_all_state(
                    save_data,
                    npc_manager,
                    inventory_manager,
                    audio_manager
                )
                if scene_states:
                    scene_state_cache.from_dict(scene_states)
                # Now all managers have their state restored
        """
        # Restore NPC dialog levels
        if npc_manager:
            npc_manager.restore_state(save_data.npc_dialog_levels)

        # Restore NPC positions and visibility
        if npc_manager and save_data.npc_positions:
            npc_manager.restore_positions(save_data.npc_positions)

        # Restore inventory state
        if inventory_manager and save_data.inventory_items:
            inventory_manager.from_dict(save_data.inventory_items)

        # Restore inventory accessed flag
        if inventory_manager:
            inventory_manager.has_been_accessed = save_data.inventory_accessed

        # Restore audio settings
        if audio_manager and save_data.audio_settings:
            audio_manager.from_dict(save_data.audio_settings)

        # Restore completed scripts
        if script_manager and save_data.completed_scripts:
            script_manager.restore_completed_scripts(save_data.completed_scripts)

        # Restore interacted objects (convert list back to set)
        interacted_objects = set(save_data.interacted_objects) if save_data.interacted_objects else set()

        logger.info("Restored all manager states from save data")
        return interacted_objects, save_data.scene_states

    def _get_save_path(self, slot: int) -> Path:
        """Get the file path for a save slot.

        Internal helper method that constructs the file path for a given save slot.
        This centralizes the file naming logic so it's consistent across all save
        operations.

        File naming convention:
        - Slot 0: "autosave.json" (dedicated auto-save)
        - Slots 1+: "save_slot_N.json" (manual saves)

        All paths are relative to self.saves_dir. The returned Path object can be
        used directly with file operations like open(), exists(), unlink(), etc.

        This is a private method (marked with _ prefix) and should only be called
        internally by other SaveManager methods.

        Args:
            slot: Save slot number (0 for auto-save, 1+ for manual saves).

        Returns:
            Path object pointing to the save file for the specified slot.
        """
        if slot == 0:
            return self.saves_dir / "autosave.json"
        return self.saves_dir / f"save_slot_{slot}.json"
