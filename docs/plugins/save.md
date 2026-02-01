# SavePlugin

Manages game state persistence with auto-save, manual save slots, and quick save/load functionality.

## Location

- Implementation: [src/pedre/plugins/save/manager.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/save/manager.py)
- Base class: [src/pedre/plugins/save/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/save/base.py)

## Configuration

The SavePlugin uses the following settings from `pedre.conf.settings`:

### Save Plugin Settings

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
- Gathers state from all registered save providers (plugins)
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

    # Phase 2 happens automatically after ScenePlugin loads sprites
```

**Notes:**

- Restores non-entity state (settings, flags, which map to load)
- Stores save data for Phase 2 (entity state restoration)
- Entity-specific state (positions, visibility) is applied later via `apply_entity_states()`
- Each plugin's `restore_save_state()` method is called
- Scene cache state is also restored if present

#### apply_entity_states

`apply_entity_states() -> None`

Phase 2: Apply entity-specific state after sprites exist.

**Example:**

```python
# Called automatically by ScenePlugin after load_from_tiled()
save_manager.apply_entity_states()
```

**Notes:**

- Called by ScenePlugin after `load_from_tiled()` has created all sprites
- Applies positions, visibility, and other state that requires sprites to exist
- Each plugin's `apply_entity_state()` method is called
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

The SavePlugin automatically handles quick save and quick load via keyboard shortcuts.

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

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the save plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context

#### cleanup

`cleanup() -> None`

Clean up save plugin resources.

**Notes:**

- Currently a no-op (no cleanup needed)
- Called automatically by PluginLoader

#### on_key_press

`on_key_press(symbol: int, modifiers: int) -> bool`

Handle quick save/load hotkeys.

**Parameters:**

- `symbol` - Keyboard symbol
- `modifiers` - Key modifiers

**Returns:**

- `True` if hotkey was handled, `False` otherwise

**Notes:**

- Called automatically by PluginLoader
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

- `save_states` - Dictionary mapping plugin names to their saved state
  - Each plugin manages its own state structure
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

Any plugin can participate in the save plugin by implementing save/load methods.

### Implementing Save Support

```python
from pedre.plugins.base import BasePlugin
from pedre.plugins.registry import PluginRegistry

@PluginRegistry.register
class MyCustomPlugin(BasePlugin):
    name = "my_plugin"

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
- State is automatically included in save files under the plugin's name

## Scene Caching

The SavePlugin also handles scene caching for smooth transitions.

**Scene Cache Flow:**

1. Player enters portal to new scene
2. SavePlugin caches current scene state under `_scene_caches`
3. New scene loads
4. Player returns to previous scene via portal
5. SavePlugin restores cached state

**Notes:**

- Scene caching is automatic when using portals
- Cached state is separate from manual save slots
- Cache is preserved across save/load operations
- Each scene's cache includes all plugin entity states

## Save Plugin Behavior

### Two-Phase Loading

The save plugin uses a two-phase approach to handle sprite dependencies:

**Phase 1: Metadata Restoration (`restore_save_state`)**

1. Save file loaded from disk
2. Plugin metadata restored (flags, settings, which map to load)
3. Scene begins loading
4. Sprites created via `load_from_tiled()`

**Phase 2: Entity State Application (`apply_entity_state`)**

1. All sprites now exist
2. Entity-specific state applied (positions, visibility, dialog levels)
3. Game resumes with full state restored

**Why Two Phases?**

- Some state (player position, NPC visibility) requires sprites to exist
- Other state (which map to load, inventory flags) doesn't require sprites
- Two-phase approach cleanly separates these concerns

### Save State Gathering

When saving, the SavePlugin collects state from all plugins:

```python
save_states = {}
for plugin in registered_plugins:
    if hasattr(plugin, 'get_save_state'):
        save_states[plugin.name] = plugin.get_save_state()
```

**Automatic Collection:**

- No manual registration required
- Plugins opt-in by implementing `get_save_state()`
- State automatically namespaced by plugin name
- JSON serialization handled automatically

### File Operations

Save files are managed using Python's standard library:

```python
# Save file path
save_path = Path(SAVE_FOLDER) / f"save_slot_{slot}.json"

# Write save
with open(save_path, "w") as f:
    json.dump(save_data.to_dict(), f, indent=2)

# Read save
with open(save_path, "r") as f:
    data = json.load(f)
```

**Error Handling:**

- File I/O errors caught and logged
- Returns `False` or `None` on failure
- Safe to call even if save folder doesn't exist
- Creates save folder automatically on first save

## Implementation Details

### Save Slot Plugin

The SavePlugin uses a simple slot-based plugin:

**Slot 0 (Auto-save):**

- Used for quick save/load
- Overwritten automatically
- Crash recovery
- File: `autosave.json`

**Slots 1-3 (Manual saves):**

- User-controlled saves
- Never overwritten automatically
- Persists between game sessions
- Files: `save_slot_1.json`, `save_slot_2.json`, `save_slot_3.json`

### Current Slot Tracking

The manager tracks which slot was last saved/loaded:

```python
self.current_slot: int | None = None
```

**Usage:**

- Updated on every save/load operation
- Used for "Continue" functionality
- Available via `get_current_slot()`
- `None` if no save/load has occurred

### Quick Save/Load Implementation

Quick save and load are implemented via keyboard handlers:

```python
def on_key_press(self, symbol: int, modifiers: int) -> bool:
    if matches_key(symbol, settings.SAVE_QUICK_SAVE_KEY):
        # Quick save to slot 0
        if self.auto_save():
            self.context.audio_manager.play_sfx(settings.SAVE_SFX_FILE)
        return True

    if matches_key(symbol, settings.SAVE_QUICK_LOAD_KEY):
        # Quick load from slot 0
        save_data = self.load_auto_save()
        if save_data:
            self.restore_game_data(save_data)
        return True

    return False
```

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
# In your custom plugin
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

## Integration with Other Plugins

### ScenePlugin Integration

The ScenePlugin coordinates scene loading during game restoration:

```python
# SavePlugin triggers scene load
scene_name = save_data.save_states["scene"]["current_map"]
context.scene_manager.request_transition(
    map_file=scene_name,
    spawn_waypoint=None  # Position restored via entity state
)

# After scene loads, ScenePlugin calls apply_entity_states()
context.save_manager.apply_entity_states()
```

**Notes:**

- ScenePlugin loads the map specified in save data
- Player position restored after map loads
- Scene caching preserved across save/load
- Spawn waypoints cleared during save restoration

### PlayerPlugin Integration

The PlayerPlugin saves and restores player position:

```python
# Saving player state
def get_save_state(self) -> dict[str, Any]:
    player = self.get_player_sprite()
    return {
        "player_x": player.center_x,
        "player_y": player.center_y
    }

# Restoring player position (Phase 2)
def apply_entity_state(self, state: dict[str, Any]) -> None:
    player = self.get_player_sprite()
    player.center_x = state["player_x"]
    player.center_y = state["player_y"]
```

**Notes:**

- Position only restored in Phase 2 (after sprite exists)
- Player sprite must exist before state can be applied
- Coordinates stored as floats for precision

### NPCPlugin Integration

The NPCPlugin saves NPC states and interaction history:

```python
# NPC state includes positions, dialog levels, visibility
{
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
}
```

**Notes:**

- Dialog progression preserved
- Per-scene interaction tracking saved
- NPC positions and visibility restored
- Interaction history available for conditions

### AudioPlugin Integration

Audio plays feedback for save/load operations:

```python
# Play save sound
if save_manager.auto_save():
    context.audio_manager.play_sfx(settings.SAVE_SFX_FILE)
```

**Notes:**

- Configurable via `SAVE_SFX_FILE` setting
- Audio feedback confirms successful operations
- No sound played on failures

### ScriptPlugin Integration

Script execution state can be saved:

```python
# Script plugin tracks completed scripts
{
  "completed_scripts": ["intro_cutscene", "merchant_greeting"],
  "run_once_scripts": {"boss_defeated": true}
}
```

**Notes:**

- `run_once` scripts tracked for save/load
- Script conditions can check saved state
- Prevents cutscenes from replaying

## Troubleshooting

### Save Not Working

If saves fail silently:

1. **Check save folder** - Verify `SAVE_FOLDER` directory exists or can be created
2. **Check permissions** - Ensure write permissions for save directory
3. **Review logs** - Look for I/O errors or JSON serialization issues
4. **Test manually** - Try `save_game(1)` and check return value
5. **Verify plugins** - Ensure all plugins return JSON-serializable data from `get_save_state()`

### Load Not Restoring State

If load succeeds but state isn't restored:

1. **Check Phase 1** - Verify `restore_save_state()` called for all plugins
2. **Check Phase 2** - Ensure `apply_entity_states()` called after scene loads
3. **Verify save data** - Check save file contains expected plugin states
4. **Review plugin implementations** - Ensure plugins implement both restore methods
5. **Check sprite existence** - Entity state requires sprites to exist

### Quick Save/Load Not Working

If keyboard shortcuts don't trigger saves:

1. **Check key bindings** - Verify `SAVE_QUICK_SAVE_KEY` and `SAVE_QUICK_LOAD_KEY` settings
2. **Test key codes** - Use `matches_key` helper to debug key detection
3. **Check auto-save slot** - Ensure slot 0 is writable
4. **Review on_key_press** - Ensure SavePlugin's key handler is called by PluginLoader

### Save File Corruption

If save files are unreadable:

1. **Check JSON format** - Open save file and verify valid JSON
2. **Check version** - Ensure `save_version` matches expected version
3. **Backup saves** - Keep backups before testing new features
4. **Validate serialization** - Test `get_save_state()` returns JSON-serializable data
5. **Review custom plugins** - Check custom plugins don't save unsupported types

### Missing State After Load

If some state is missing after loading:

1. **Check plugin registration** - Ensure all plugins are registered and loaded
2. **Verify save state** - Check `get_save_state()` returns complete data
3. **Test both phases** - Ensure both `restore_save_state()` and `apply_entity_state()` implemented
4. **Check scene caching** - Verify scene cache includes all necessary state
5. **Review namespacing** - Ensure plugin names match between save and load

## Custom SavePlugin Implementation

If you need to replace the save plugin with a custom implementation, you can extend the `SaveBasePlugin` abstract base class.

### SaveBasePlugin

**Location:** [src/pedre/plugins/save/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/save/base.py)

The `SaveBasePlugin` class defines the minimum interface that any save manager must implement.

#### Required Methods

Your custom save manager must implement these abstract methods:

```python
from pedre.plugins.save.base import SaveBasePlugin, GameSaveData
from pedre.plugins.registry import PluginRegistry

@PluginRegistry.register
class CustomSavePlugin(SaveBasePlugin):
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

Register your custom save manager using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.save.base import SaveBasePlugin

@PluginRegistry.register
class CloudSavePlugin(SaveBasePlugin):
    name = "save"

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BasePlugin` (via `SaveBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and potentially `reset()`
- The `role` attribute is set to `"save_manager"` in the base class
- Your implementation can use any storage backend (cloud, database, encrypted files, etc.)
- Register your custom save manager in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.save"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/cloud_save.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.save.base import SaveBasePlugin, GameSaveData

@PluginRegistry.register
class CloudSavePlugin(SaveBasePlugin):
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
INSTALLED_PLUGINS = [
    "myproject.plugins.cloud_save",  # Load custom save first
    "pedre.plugins.camera",
    "pedre.plugins.audio",
    # ... rest of plugins (omit "pedre.plugins.save") ...
]
```

## See Also

- [ScenePlugin](scene.md) - Scene transitions and loading
- [Configuration Guide](../guides/configuration.md)
- [Views](../api/views.md)
