# SaveManager

Manages game state persistence with auto-save, manual save slots, and quick save/load functionality.

## Location

- Implementation: [src/pedre/systems/save/manager.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/save/manager.py)
- Base class: [src/pedre/systems/save/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/save/base.py)

## Configuration

The SaveManager uses the following settings from `pedre.conf.settings`:

### Save System Settings

- `SAVE_FOLDER` - Directory where save files are stored (default: "saves")
- `SAVE_QUICK_SAVE_KEY` - Keybind for quick save action (default: "F5")
- `SAVE_QUICK_LOAD_KEY` - Keybind for quick load action (default: "F9")
- `SAVE_SFX_FILE` - Sound effect played when saving/loading (default: "save.wav")

These can be overridden in your project's `settings.py`:

```python
# Custom save settings
SAVE_FOLDER = "game_saves"
SAVE_QUICK_SAVE_KEY = "F6"
SAVE_QUICK_LOAD_KEY = "F8"
SAVE_SFX_FILE = "menu_select.wav"
```

## Public API

### Save Operations

#### save_game

`save_game(slot: int) -> bool`

Save game to a specified slot.

**Parameters:**

- `slot` - Save slot number (0 for auto-save, 1-3 for manual saves)

**Returns:**

- `True` if save succeeded and file was written, `False` if any error occurred

**Example:**

```python
# Save to slot 1
success = save_manager.save_game(slot=1)
if success:
    print("Game saved successfully!")
```

**Notes:**

- Creates a complete snapshot of the current game state
- Gathers state from all registered save providers (systems)
- Writes to JSON file with 2-space indentation for readability
- Updates `current_slot` tracker
- Automatically caches current scene before saving

#### auto_save

`auto_save() -> bool`

Auto-save to the special auto-save slot (slot 0).

**Returns:**

- `True` if auto-save succeeded, `False` if it failed

**Example:**

```python
# Perform auto-save
if save_manager.auto_save():
    print("Auto-save completed")
```

**Notes:**

- Uses slot 0 for auto-save
- Intended for crash recovery and quick save/load
- Called automatically by quick save (F5 by default)

### Load Operations

#### load_game

`load_game(slot: int) -> GameSaveData | None`

Load game from a specified slot.

**Parameters:**

- `slot` - Save slot number (0 for auto-save, 1-3 for manual saves)

**Returns:**

- `GameSaveData` object containing all saved state if successful
- `None` if the save file doesn't exist or if loading failed

**Example:**

```python
save_data = save_manager.load_game(slot=1)
if save_data:
    save_manager.restore_game_data(save_data)
    print("Game loaded successfully!")
```

**Notes:**

- Reads save file from specified slot
- Deserializes JSON into GameSaveData object
- Updates `current_slot` tracker
- Does NOT automatically restore state (call `restore_game_data` for that)

#### load_auto_save

`load_auto_save() -> GameSaveData | None`

Load from the auto-save slot (slot 0).

**Returns:**

- `GameSaveData` object with auto-save state if successful
- `None` if no auto-save exists or loading failed

**Example:**

```python
save_data = save_manager.load_auto_save()
if save_data:
    save_manager.restore_game_data(save_data)
```

**Notes:**

- Convenience method for loading slot 0
- Called automatically by quick load (F9 by default)

#### restore_game_data

`restore_game_data(save_data: GameSaveData) -> None`

Phase 1: Restore metadata state from save data before sprites exist.

**Parameters:**

- `save_data` - The GameSaveData object loaded from a save file

**Example:**

```python
save_data = save_manager.load_game(slot=1)
if save_data:
    # Phase 1: Restore metadata (settings, flags, which map to load)
    save_manager.restore_game_data(save_data)

    # Phase 2 happens automatically after SceneManager loads sprites
```

**Notes:**

- Restores non-entity state (settings, flags, which map to load)
- Stores save data for Phase 2 (entity state restoration)
- Entity-specific state (positions, visibility) is applied later via `apply_entity_states()`
- Each system's `restore_save_state()` method is called
- Scene cache state is also restored if present

#### apply_entity_states

`apply_entity_states() -> None`

Phase 2: Apply entity-specific state after sprites exist.

**Example:**

```python
# Called automatically by SceneManager after load_from_tiled()
save_manager.apply_entity_states()
```

**Notes:**

- Called by SceneManager after `load_from_tiled()` has created all sprites
- Applies positions, visibility, and other state that requires sprites to exist
- Each system's `apply_entity_state()` method is called
- Clears pending save data after application

### Save Slot Management

#### save_exists

`save_exists(slot: int) -> bool`

Check if a save file exists in a slot.

**Parameters:**

- `slot` - Save slot number (0 for auto-save, 1-3 for manual saves)

**Returns:**

- `True` if a save file exists in the slot, `False` otherwise

**Example:**

```python
if save_manager.save_exists(1):
    print("Slot 1 has a save")
    info = save_manager.get_save_info(1)
    print(f"Saved at: {info['date_string']}")
```

#### get_save_info

`get_save_info(slot: int) -> dict[str, Any] | None`

Get basic info about a save file without fully loading it.

**Parameters:**

- `slot` - Save slot number (0 for auto-save, 1-3 for manual saves)

**Returns:**

- Dictionary with save metadata if the file exists and is readable
- `None` if the file doesn't exist or if an error occurred

**Example:**

```python
info = save_manager.get_save_info(1)
if info:
    print(f"Slot: {info['slot']}")
    print(f"Map: {info['map']}")
    print(f"Saved: {info['date_string']}")
    print(f"Version: {info['version']}")
```

**Returned Fields:**

- `slot` (int) - The slot number
- `map` (str) - Name of the map when saved
- `timestamp` (float) - Unix timestamp
- `date_string` (str) - Formatted date string (YYYY-MM-DD HH:MM)
- `version` (str) - Save format version

#### delete_save

`delete_save(slot: int) -> bool`

Delete a save file.

**Parameters:**

- `slot` - Save slot number (0 for auto-save, 1-3 for manual saves)

**Returns:**

- `True` if save file existed and was deleted successfully
- `False` if file didn't exist or deletion failed

**Example:**

```python
if save_manager.delete_save(2):
    print("Slot 2 deleted")
```

### Quick Save/Load

The SaveManager automatically handles quick save and quick load via keyboard shortcuts.

**Quick Save (F5 by default):**

```python
# Triggered automatically when player presses F5
# Can be customized via SAVE_QUICK_SAVE_KEY setting
```

**Quick Load (F9 by default):**

```python
# Triggered automatically when player presses F9
# Can be customized via SAVE_QUICK_LOAD_KEY setting
```

**Notes:**

- Quick save uses the auto-save slot (slot 0)
- Plays configured SFX on successful save/load
- Logs warnings/info messages for debugging

### System Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the save system with game context.

**Parameters:**

- `context` - Game context providing access to other systems

**Notes:**

- Called automatically by SystemLoader
- Stores reference to game context

#### cleanup

`cleanup() -> None`

Clean up save system resources.

**Notes:**

- Currently a no-op (no cleanup needed)
- Called automatically by SystemLoader

#### on_key_press

`on_key_press(symbol: int, modifiers: int) -> bool`

Handle quick save/load hotkeys.

**Parameters:**

- `symbol` - Keyboard symbol
- `modifiers` - Key modifiers

**Returns:**

- `True` if hotkey was handled, `False` otherwise

**Notes:**

- Called automatically by SystemLoader
- Checks for configured quick save/load keys
- Uses `matches_key` helper to support custom key bindings

## Save File Format

### Directory Structure

Save files are stored in the configured save directory (default: `saves/`):

```text
saves/
  ├── autosave.json
  ├── save_slot_1.json
  ├── save_slot_2.json
  └── save_slot_3.json
```

### JSON Format

Save files use JSON with 2-space indentation for human readability:

```json
{
  "save_states": {
    "scene": {
      "current_map": "village.tmx",
      "spawn_waypoint": null
    },
    "player": {
      "position": {
        "x": 320.0,
        "y": 240.0
      }
    },
    "npc": {
      "npcs": {
        "merchant": {
          "dialog_level": 2,
          "position": {"x": 400.0, "y": 300.0},
          "visible": true
        }
      },
      "interactions": {
        "village": ["merchant", "guard"]
      }
    },
    "inventory": {
      "items": {
        "health_potion": {
          "acquired": true,
          "consumed": false
        }
      },
      "accessed": true
    },
    "_scene_caches": {
      "village": {
        "npc": { /* cached NPC state */ },
        "player": { /* cached player state */ }
      }
    }
  },
  "save_timestamp": 1704067200.0,
  "save_version": "2.0"
}
```

**Structure:**

- `save_states` - Dictionary mapping system names to their saved state
  - Each system manages its own state structure
  - `_scene_caches` stores cached states for scene transitions
- `save_timestamp` - Unix timestamp when save was created
- `save_version` - Save format version for future migrations

## GameSaveData

Data class representing complete game state snapshot.

**Attributes:**

- `save_states: dict[str, Any]` - Dictionary mapping save provider names to their serialized state
- `save_timestamp: float` - Unix timestamp when save was created (seconds since epoch)
- `save_version: str` - Save format version string (default: "2.0")

**Methods:**

- `to_dict() -> dict[str, Any]` - Convert to dictionary for JSON serialization
- `from_dict(data: dict[str, Any]) -> GameSaveData` - Create from dictionary loaded from JSON

**Example:**

```python
# Create save data
save_data = GameSaveData(
    save_states={
        "player": {"position": {"x": 100.0, "y": 200.0}},
        "inventory": {"items": {}},
    },
    save_timestamp=datetime.now(UTC).timestamp(),
    save_version="2.0"
)

# Serialize to dict
data_dict = save_data.to_dict()

# Deserialize from dict
loaded_data = GameSaveData.from_dict(data_dict)
```

## Save Providers

Any system can participate in the save system by implementing save/load methods.

### Implementing Save Support

```python
from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry

@SystemRegistry.register
class MyCustomSystem(BaseSystem):
    name = "my_system"

    def get_save_state(self) -> dict[str, Any]:
        """Return serializable state for saving."""
        return {
            "my_data": self.some_data,
            "my_flags": self.flags,
        }

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Phase 1: Restore metadata state (before sprites exist)."""
        self.some_data = state.get("my_data", {})
        self.flags = state.get("my_flags", {})

    def apply_entity_state(self, state: dict[str, Any]) -> None:
        """Phase 2: Apply entity state (after sprites exist)."""
        # Restore positions, visibility, etc. that require sprites
        pass
```

**Notes:**

- `get_save_state()` returns a JSON-serializable dictionary
- `restore_save_state()` restores metadata state before sprites exist
- `apply_entity_state()` applies entity state after sprites exist
- Both restore methods receive the same state dict returned by `get_save_state()`
- State is automatically included in save files under the system's name

## Scene Caching

The SaveManager also handles scene caching for smooth transitions.

**Scene Cache Flow:**

1. Player enters portal to new scene
2. SaveManager caches current scene state under `_scene_caches`
3. New scene loads
4. Player returns to previous scene via portal
5. SaveManager restores cached state

**Notes:**

- Scene caching is automatic when using portals
- Cached state is separate from manual save slots
- Cache is preserved across save/load operations
- Each scene's cache includes all system entity states

## Usage Examples

### Basic Save/Load

```python
# Save to slot 1
if save_manager.save_game(slot=1):
    print("Game saved!")

# Load from slot 1
save_data = save_manager.load_game(slot=1)
if save_data:
    save_manager.restore_game_data(save_data)
    # Scene will load and apply entity states automatically
```

### Checking Save Slots

```python
# Check all save slots
for slot in range(1, 4):
    if save_manager.save_exists(slot):
        info = save_manager.get_save_info(slot)
        print(f"Slot {slot}: {info['map']} - {info['date_string']}")
    else:
        print(f"Slot {slot}: Empty")
```

### Auto-save Before Dangerous Action

```python
# Auto-save before boss fight
if save_manager.auto_save():
    audio_manager.play_sfx("save.wav")
    print("Progress auto-saved")

# Start boss fight
```

### Delete Old Save

```python
# Confirm with player first
if player_confirmed_deletion:
    if save_manager.delete_save(slot=2):
        print("Slot 2 cleared")
```

### Custom Quick Save Handler

```python
# In your custom system
def on_key_press(self, symbol: int, modifiers: int) -> bool:
    from pedre.helpers import matches_key
    from pedre.conf import settings

    if matches_key(symbol, settings.SAVE_QUICK_SAVE_KEY):
        # Custom save logic
        if save_manager.auto_save():
            show_save_notification()
        return True

    return False
```

## Custom SaveManager Implementation

If you need to replace the save system with a custom implementation, you can extend the `SaveBaseManager` abstract base class.

### SaveBaseManager

**Location:** [src/pedre/systems/save/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/save/base.py)

The `SaveBaseManager` class defines the minimum interface that any save manager must implement.

#### Required Methods

Your custom save manager must implement these abstract methods:

```python
from pedre.systems.save.base import SaveBaseManager, GameSaveData
from pedre.systems.registry import SystemRegistry

@SystemRegistry.register
class CustomSaveManager(SaveBaseManager):
    """Custom save implementation."""

    name = "save"

    def restore_game_data(self, save_data: GameSaveData) -> None:
        """Restore all state from save data to save providers."""
        ...

    def load_auto_save(self) -> GameSaveData | None:
        """Load from auto-save slot."""
        ...

    def load_game(self, slot: int) -> GameSaveData | None:
        """Load game from a slot."""
        ...

    def get_save_info(self, slot: int) -> dict[str, Any] | None:
        """Get basic info about a save file without fully loading it."""
        ...

    def save_exists(self, slot: int) -> bool:
        """Check if a save file exists in a slot."""
        ...

    def save_game(self, slot: int) -> bool:
        """Save game to a slot."""
        ...

    def apply_entity_states(self) -> None:
        """Phase 2: Apply entity-specific state after sprites exist."""
        ...
```

#### Registration

Register your custom save manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.save.base import SaveBaseManager

@SystemRegistry.register
class CloudSaveManager(SaveBaseManager):
    name = "save"

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `SaveBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `cleanup()`, and potentially `reset()`
- The `role` attribute is set to `"save_manager"` in the base class
- Your implementation can use any storage backend (cloud, database, encrypted files, etc.)
- Register your custom save manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.save"` to replace it

**Example Custom Implementation:**

```python
# In myproject/systems/cloud_save.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.save.base import SaveBaseManager, GameSaveData

@SystemRegistry.register
class CloudSaveManager(SaveBaseManager):
    """Save manager that stores saves in the cloud."""

    name = "save"

    def __init__(self):
        self.cloud_client = CloudStorageClient()
        # ... rest of initialization ...

    def save_game(self, slot: int) -> bool:
        # Upload save to cloud storage
        return self.cloud_client.upload(slot, save_data)

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_SYSTEMS = [
    "myproject.systems.cloud_save",  # Load custom save first
    "pedre.systems.camera",
    "pedre.systems.audio",
    # ... rest of systems (omit "pedre.systems.save") ...
]
```

## See Also

- [Configuration Guide](../configuration.md) - Save system settings
- [GameView](../api-reference.md#gameview) - Main gameplay view
- [SceneManager](scene.md) - Scene transitions and loading
