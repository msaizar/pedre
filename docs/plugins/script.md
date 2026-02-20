# ScriptPlugin

Event-driven scripting plugin for cutscenes and interactive sequences.

## Location

- Implementation: [src/pedre/plugins/script/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/script/plugin.py)
- Base class: [src/pedre/plugins/script/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/script/base.py)
- Events: [src/pedre/plugins/script/events.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/script/events.py)
- Conditions: [src/pedre/plugins/script/conditions.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/script/conditions.py)

## Configuration

The ScriptPlugin uses the following settings from `pedre.conf.settings`:

| Setting              | Type   | Default         | Description                                                  |
| -------------------- | ------ | --------------- | ------------------------------------------------------------ |
| `SCRIPTS_DIRECTORY`  | string | "data/scripts"  | Directory where script files are stored (relative to assets) |
| `ASSETS_HANDLE`      | string | "assets"        | Base path for asset loading                                  |

## Public API

### Script Loading

All scripts are loaded globally during plugin setup. The ScriptPlugin automatically scans the scripts directory for all `*_scripts.json` files and loads them at initialization time. This makes scripts available for condition checking across all scenes, with the `scene` field in each script definition controlling when it can actually execute.

**Automatic Loading:**

Scripts are loaded automatically when ScriptPlugin initializes:

```python
# Scripts are loaded during setup
script_plugin = ScriptPlugin()
script_plugin.setup(context)  # Loads all scripts from scripts directory
```

**Script File Naming:**

Script files should follow the naming pattern `*_scripts.json` and be placed in the directory specified by `SCRIPTS_DIRECTORY` (default: `data/scripts`):

```text
assets/data/scripts/
  ├── village_scripts.json
  ├── forest_scripts.json
  └── castle_scripts.json
```

You can customize the scripts directory in your `settings.py`:

```python
SCRIPTS_DIRECTORY = "custom_scripts"  # Relative to assets directory
```

**Notes:**

- All scripts from all files are loaded into a single global registry
- The `scene` field in each script controls when it can execute
- Scripts are available for condition checking regardless of current scene
- Scripts are reloaded on reset (new game or load game)

### Script Validation

All scripts are validated after loading to catch configuration errors early. Validation checks:

- **Trigger Events**: All `event` values in triggers must be registered in EventRegistry
- **Conditions**: All `check` types in conditions must be registered in ConditionRegistry
- **Actions**: All action `name` values must be registered in ActionRegistry
- **Required Fields**: Scripts must have required keys (`trigger`, `actions`) and valid structure
- **Unknown Keys**: Scripts cannot have unrecognized top-level keys
- **Non-Empty Actions**: The `actions` list must contain at least one action
- **Type Validation**: All action, event, and condition parameters are validated for correct types (strings, booleans, integers, lists, etc.)

**Validation Errors:**

If validation fails, a `ScriptValidationError` is raised with detailed error messages listing all problems found:

```python
# Example validation error output
ScriptValidationError: 5 script validation error(s):
  - Script 'intro_cutscene': unknown event 'scene_loaded' (registered events: scene_start, npc_interacted, ...)
  - Script 'merchant_greeting': unknown action type 'show_dialog' (registered actions: dialog, move_npc, ...)
  - Script 'broken_script': unknown keys ['conditions_fail'] (valid keys: actions, conditions, on_condition_fail, run_once, scene, trigger)
  - Script 'npc_move': action 'move_npc': 'waypoint' must be a string
  - Script 'dialog_test': action 'dialog': 'text' must be a list
```

This validation helps catch typos, type errors, and configuration errors before they cause runtime issues. All referenced events, conditions, and actions must be properly registered with their respective registries, and all parameters must be the correct types.

### Script Execution

#### update

`update(delta_time: float) -> None`

Update active action sequences (called every frame).

**Parameters:**

- `delta_time` - Time since last update in seconds

**Example:**

```python
def on_update(self, delta_time):
    self.script_plugin.update(delta_time)
```

**Notes:**

- Called automatically by PluginLoader each frame
- Updates all currently executing script action sequences
- Removes completed sequences and publishes ScriptCompleteEvent

### State Queries

#### get_scripts

`get_scripts() -> dict[str, Script]`

Get all loaded scripts.

**Returns:**

- Dictionary mapping script names to Script instances

**Example:**

```python
all_scripts = script_plugin.get_scripts()
for name, script in all_scripts.items():
    print(f"{name}: completed={script.completed}, has_run={script.has_run}")
```

### Save/Load Support

#### get_save_state

`get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing completed scripts and run-once execution history

**Example:**

```python
save_data = {
    "player_position": (x, y),
    "script": script_plugin.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Saves lists of completed scripts and run-once scripts that have executed
- Saves currently active script sequences with their execution progress
- On load, active scripts resume from where they left off

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Restore script plugin state from save file.

**Parameters:**

- `state` - Dictionary containing saved script state

**Example:**

```python
script_plugin.restore_save_state(save_data["script"])
```

**Notes:**

- Restores completion flags and run-once history
- Resumes active script sequences from where they were when saved
- For actions like NPC movement, backs up to re-initiate the operation from saved entity state
- Critical for preventing one-time events from re-running

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the script plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Loads all scripts globally from scripts directory
- Registers event handlers for all script triggers

#### cleanup

`cleanup() -> None`

Clean up script plugin resources.

**Notes:**

- Unregisters all event handlers
- Clears scripts and active sequences
- Called automatically by PluginLoader

#### reset

`reset() -> None`

Reset script plugin for new game.

**Notes:**

- Clears all runtime state (active sequences, completion flags)
- Reloads all scripts from disk
- Re-registers event handlers
- Called when starting a new game or loading a saved game

## Script Data Structures

### ScriptValidationError

Exception raised when script validation fails during loading.

**Attributes:**

- `errors: list[str]` - List of validation error messages

**Example:**

```python
try:
    script_plugin.load_all_scripts()
except ScriptValidationError as e:
    print(f"Script validation failed with {len(e.errors)} errors:")
    for error in e.errors:
        print(f"  - {error}")
```

**Raised When:**

- Unknown event types in triggers
- Unknown condition types in conditions
- Unknown action types in actions or on_condition_fail
- Missing required fields (event, check, type)
- Unknown top-level script keys
- Empty actions list
- Invalid parameter types (e.g., string where bool expected, list where string expected)

This exception is typically raised during plugin setup when scripts are loaded, ensuring all scripts are valid before the game runs.

### Script

Container for action sequences with trigger conditions and metadata.

**Attributes:**

- `trigger: dict[str, Any] | None` - Event specification that triggers this script
- `conditions: list[dict[str, Any]]` - List of condition dictionaries that must all be true
- `scene: str | None` - Optional scene name where this script can run
- `run_once: bool` - If True, script only executes once per game session
- `actions: list[dict[str, Any]]` - List of action dictionaries to execute in sequence
- `on_condition_fail: list[dict[str, Any]]` - Optional actions to execute when conditions fail
- `has_run: bool` - Tracks if this script has started (for run_once prevention)
- `completed: bool` - Tracks if this script has fully completed all actions

**Example:**

```python
script = Script(
    trigger={"event": "dialog_closed", "npc": "martin", "dialog_level": 1},
    conditions=[{"check": "inventory_accessed", "equals": True}],
    scene="village",
    run_once=True,
    actions=[
        {"name": "dialog", "speaker": "martin", "text": ["Hello!"]},
        {"name": "wait_for_dialog_close"},
        {"name": "move_npc", "npcs": ["martin"], "waypoint": "town_square"}
    ]
)
```

## Script Plugin

### Script JSON Format

Scripts are defined in JSON files located in `assets/data/scripts/` with the naming pattern `*_scripts.json`:

```json
{
  "script_name": {
    "trigger": {
      "event": "npc_interacted",
      "npc": "merchant",
      "dialog_level": 0
    },
    "conditions": [
      {"check": "inventory_accessed", "equals": true}
    ],
    "scene": "village",
    "run_once": true,
    "actions": [
      {"name": "dialog", "speaker": "merchant", "text": ["Hello!"]},
      {"name": "wait_for_dialog_close"},
      {"name": "advance_dialog", "npc": "merchant"}
    ],
    "on_condition_fail": [
      {"name": "dialog", "speaker": "merchant", "text": ["Check your inventory first!"]}
    ]
  }
}
```

**Structure:**

- Top level: Script name (unique identifier)
- `trigger`: Event specification with filters
- `conditions`: Optional array of condition checks
- `scene`: Optional scene restriction
- `run_once`: Optional one-time execution flag
- `actions`: Array of actions to execute
- `on_condition_fail`: Optional fallback actions

### Script Fields

| Field               | Type   | Required | Description                                                            |
| ------------------- | ------ | -------- | ---------------------------------------------------------------------- |
| `trigger`           | object | Yes      | Event specification that triggers this script                          |
| `conditions`        | array  | No       | Conditions to check before running                                     |
| `scene`             | string | No       | Only run in this scene/map (omit for global scripts that run anywhere) |
| `run_once`          | bool   | No       | Only execute once (default: false)                                     |
| `actions`           | array  | Yes      | Sequence of actions to execute (must not be empty)                     |
| `on_condition_fail` | array  | No       | Actions to execute when conditions fail                                |

**Note:** Only the keys listed above are valid. Using unknown keys will cause a validation error during script loading.

### Trigger Object

The trigger object specifies which event activates the script:

```json
{
  "trigger": {
    "event": "npc_interacted",
    "npc": "merchant",
    "dialog_level": 0
  }
}
```

**Fields:**

- `event` (required) - Event type name (e.g., "npc_interacted", "dialog_closed")
- Additional fields act as filters (all must match for trigger to fire)

**Available Event Types:**

- `npc_interacted` - Player interacts with NPC
- `dialog_opened` - Dialog window opens
- `dialog_closed` - Dialog window closes
- `inventory_closed` - Inventory closes
- `item_acquired` - Item added to inventory
- `item_consumed` - Item consumed from inventory
- `item_acquisition_failed` - Item acquisition failed
- `object_interacted` - Player interacts with object
- `npc_movement_complete` - NPC finishes moving
- `npc_appear_complete` - NPC appear animation finishes
- `npc_disappear_complete` - NPC disappear animation finishes
- `portal_entered` - Player enters portal zone
- `scene_start` - Scene/map finishes loading
- `script_complete` - Another script finishes

For detailed information on each event type, see [Event Types](../scripting/events.md).

### Condition Checking

Conditions must all evaluate to true for the script to execute:

```json
{
  "conditions": [
    {"check": "inventory_accessed", "equals": true},
    {"check": "npc_dialog_level", "npc": "merchant", "equals": 2}
  ]
}
```

When conditions fail and `on_condition_fail` is defined:

1. Script's main actions are skipped
2. `on_condition_fail` actions execute instead
3. Useful for feedback messages or alternative paths

For available condition types, see [Conditions](../scripting/conditions.md).

### Global Script Loading

All scripts are loaded globally during plugin initialization:

1. ScriptPlugin scans the `SCRIPTS_DIRECTORY` (default: `assets/data/scripts/`) for all `*_scripts.json` files
2. All scripts are loaded into a single registry
3. Event triggers are registered with the EventBus
4. Scripts can be referenced in conditions across all scenes

**Scene Restriction:**

The optional `scene` field controls when a script can execute:

```json
{
  "village_only_script": {
    "scene": "village",
    "trigger": {"event": "npc_interacted", "npc": "merchant"},
    "actions": [...]
  },
  "global_script": {
    "trigger": {"event": "item_acquired", "item_id": "key"},
    "actions": [...]
  }
}
```

- **Scene-specific scripts** (with `scene` field): Only execute in the specified scene
- **Global scripts** (without `scene` field): Can execute in any scene
- Conditions can reference scripts from any scene, regardless of where they're defined

**Example - Cross-Scene Condition:**

```json
{
  "castle_gate": {
    "scene": "castle",
    "trigger": {"event": "portal_entered", "portal": "gate"},
    "conditions": [
      {"check": "script_completed", "script": "village_quest_complete"}
    ],
    "actions": [
      {"name": "change_scene", "target_map": "throne_room.tmx"}
    ]
  }
}
```

This allows checking if a script from another scene has completed.

## Events

### ScriptCompleteEvent

Published when a script completes execution.

**Attributes:**

- `script_name: str` - Name of the script that completed

**Script Trigger Example:**

```json
{
  "followup": {
    "trigger": {
      "event": "script_complete",
      "script": "intro_cutscene"
    },
    "actions": [
      {"name": "start_appear_animation", "npcs": ["guard"]}
    ]
  }
}
```

**Notes:**

- Fires when all actions in a script have finished executing
- The `script` filter is optional (omit to trigger for any script completion)
- Useful for chaining complex multi-stage sequences

## Conditions

### script_completed

Check if a specific script has fully completed all its actions.

**Parameters:**

- `check`: `"script_completed"`
- `script`: Name of the script to check

**Example:**

```json
{
  "trigger": {
    "event": "portal_entered",
    "portal": "exit"
  },
  "conditions": [
    {
      "check": "script_completed",
      "script": "main_quest_finale"
    }
  ]
}
```

**Use Cases:**

- Gating progression behind script completion
- Quest prerequisites
- Story progression tracking
- Conditional scene transitions

## Usage Examples

### Basic Script Trigger

```json
{
  "greet_merchant": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "merchant",
      "dialog_level": 0
    },
    "run_once": true,
    "actions": [
      {"name": "dialog", "speaker": "Merchant", "text": ["Welcome!"]},
      {"name": "wait_for_dialog_close"},
      {"name": "advance_dialog", "npc": "merchant"}
    ]
  }
}
```

### Conditional Script with Fallback

```json
{
  "check_inventory": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "merchant",
      "dialog_level": 1
    },
    "conditions": [
      {"check": "inventory_accessed", "equals": true}
    ],
    "actions": [
      {"name": "dialog", "speaker": "Merchant", "text": ["Good! You found your inventory!"]}
    ],
    "on_condition_fail": [
      {"name": "dialog", "speaker": "Merchant", "text": ["Please check your inventory first."]}
    ]
  }
}
```

### Chained Scripts

```json
{
  "cutscene_part1": {
    "scene": "forest",
    "trigger": {
      "event": "object_interacted",
      "object_name": "altar"
    },
    "run_once": true,
    "actions": [
      {"name": "play_sfx", "file": "magic.wav"},
      {"name": "start_appear_animation", "npcs": ["spirit"]},
      {"name": "wait_npcs_appear", "npcs": ["spirit"]}
    ]
  },
  "cutscene_part2": {
    "trigger": {
      "event": "script_complete",
      "script": "cutscene_part1"
    },
    "actions": [
      {"name": "dialog", "speaker": "Spirit", "text": ["Who dares summon me?"]},
      {"name": "wait_for_dialog_close"},
      {"name": "start_disappear_animation", "npcs": ["spirit"]}
    ]
  }
}
```

### Portal Transition

```json
{
  "forest_portal": {
    "trigger": {
      "event": "portal_entered",
      "portal": "to_forest"
    },
    "conditions": [
      {"check": "npc_interacted", "npc": "guard", "equals": true}
    ],
    "actions": [
      {"name": "change_scene", "target_map": "forest.tmx", "spawn_waypoint": "from_village"}
    ],
    "on_condition_fail": [
      {"name": "dialog", "speaker": "Narrator", "text": ["The path is blocked."]}
    ]
  }
}
```

### Scene Initialization

```json
{
  "village_intro": {
    "scene": "village",
    "trigger": {
      "event": "scene_start"
    },
    "run_once": true,
    "actions": [
      {"name": "play_music", "file": "village_theme.ogg"},
      {"name": "dialog", "speaker": "Narrator", "text": ["Welcome to the village!"]}
    ]
  }
}
```

## Custom Script Implementation

If you need to replace the script plugin with a custom implementation, you can extend the `ScriptBasePlugin` abstract base class.

### ScriptBasePlugin

**Location:** [src/pedre/plugins/script/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/script/base.py)

The `ScriptBasePlugin` class defines the minimum interface that any script plugin must implement.

#### Required Methods

Your custom script plugin must implement these abstract methods:

```python
from pedre.plugins.script.base import ScriptBasePlugin, Script

class CustomScriptPlugin(ScriptBasePlugin):
    """Custom script implementation."""

    name = "script"
    dependencies = []

    def get_scripts(self) -> dict[str, Script]:
        """Get all loaded scripts."""
        ...
```

#### Registration

Register your custom script plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.script.base import ScriptBasePlugin

@PluginRegistry.register
class CustomScriptPlugin(ScriptBasePlugin):
    name = "script"
    dependencies = []

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom plugin inherits from `BasePlugin` (via `ScriptBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"script_plugin"` in the base class
- Your implementation can use any script storage or execution plugin
- Register your custom script plugin in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.script"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_script.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.script.base import ScriptBasePlugin

@PluginRegistry.register
class DatabaseScriptPlugin(ScriptBasePlugin):
    """Script plugin that stores state in a database."""

    name = "script"
    dependencies = []

    def __init__(self):
        self.db = Database()
        # ... rest of initialization ...

    def get_scripts(self) -> dict[str, Script]:
        # Query database for scripts
        return self.db.query("SELECT * FROM scripts")

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_script",  # Load custom script first
    "pedre.plugins.camera",
    "pedre.plugins.audio",
    # ... rest of plugins (omit "pedre.plugins.script") ...
]
```

## See Also

- [NPCPlugin](npc.md) - NPC interactions and dialog
- [DialogPlugin](dialog.md) - Conversation plugin
- [Scripting Guide](../scripting/index.md) - Event-driven scripting documentation
- [Scripting Basics](../scripting/basics.md) - Script structure and organization
- [Event Types](../scripting/events.md) - Available event triggers
- [Conditions](../scripting/conditions.md) - Script condition plugin
- [Actions](../scripting/actions.md) - Available script actions
