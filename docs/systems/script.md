# ScriptManager

Event-driven scripting system for cutscenes and interactive sequences.

## Location

- Implementation: [src/pedre/systems/script/manager.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/script/manager.py)
- Base class: [src/pedre/systems/script/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/script/base.py)
- Events: [src/pedre/systems/script/events.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/script/events.py)
- Conditions: [src/pedre/systems/script/conditions.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/script/conditions.py)

## Configuration

The ScriptManager uses the following setting from `pedre.conf.settings`:

- `ASSETS_HANDLE` - Base path for asset loading (default: "assets")

## Public API

### Script Loading

All scripts are loaded globally during system setup. The ScriptManager automatically scans the scripts directory for all `*_scripts.json` files and loads them at initialization time. This makes scripts available for condition checking across all scenes, with the `scene` field in each script definition controlling when it can actually execute.

**Automatic Loading:**

Scripts are loaded automatically when ScriptManager initializes:

```python
# Scripts are loaded during setup
script_manager = ScriptManager()
script_manager.setup(context)  # Loads all scripts from scripts directory
```

**Script File Naming:**

Script files should follow the naming pattern `*_scripts.json`:

```text
assets/scripts/
  ├── village_scripts.json
  ├── forest_scripts.json
  └── castle_scripts.json
```

**Notes:**

- All scripts from all files are loaded into a single global registry
- The `scene` field in each script controls when it can execute
- Scripts are available for condition checking regardless of current scene
- Scripts are reloaded on reset (new game or load game)

### Script Execution

#### update

`update(delta_time: float) -> None`

Update active action sequences (called every frame).

**Parameters:**

- `delta_time` - Time since last update in seconds

**Example:**

```python
def on_update(self, delta_time):
    self.script_manager.update(delta_time)
```

**Notes:**

- Called automatically by SystemLoader each frame
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
all_scripts = script_manager.get_scripts()
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
    "script": script_manager.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Saves lists of completed scripts and run-once scripts that have executed
- Active running scripts are NOT saved and will restart on load

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Restore script system state from save file.

**Parameters:**

- `state` - Dictionary containing saved script state

**Example:**

```python
script_manager.restore_save_state(save_data["script"])
```

**Notes:**

- Restores completion flags and run-once history
- Critical for preventing one-time events from re-running

### System Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the script system with game context.

**Parameters:**

- `context` - Game context providing access to other systems

**Notes:**

- Called automatically by SystemLoader
- Loads all scripts globally from scripts directory
- Registers event handlers for all script triggers

#### cleanup

`cleanup() -> None`

Clean up script system resources.

**Notes:**

- Unregisters all event handlers
- Clears scripts and active sequences
- Called automatically by SystemLoader

#### reset

`reset() -> None`

Reset script system for new game.

**Notes:**

- Clears all runtime state (active sequences, completion flags)
- Reloads all scripts from disk
- Re-registers event handlers
- Called when starting a new game or loading a saved game

## Script Data Structures

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
        {"type": "dialog", "speaker": "martin", "text": ["Hello!"]},
        {"type": "wait_for_dialog_close"},
        {"type": "move_npc", "npcs": ["martin"], "waypoint": "town_square"}
    ]
)
```

## Script System

### Script JSON Format

Scripts are defined in JSON files located in `assets/scripts/` with the naming pattern `*_scripts.json`:

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
      {"type": "dialog", "speaker": "merchant", "text": ["Hello!"]},
      {"type": "wait_for_dialog_close"},
      {"type": "advance_dialog", "npc": "merchant"}
    ],
    "on_condition_fail": [
      {"type": "dialog", "speaker": "merchant", "text": ["Check your inventory first!"]}
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

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `trigger` | object | Yes | Event specification that triggers this script |
| `conditions` | array | No | Conditions to check before running |
| `scene` | string | No | Only run in this scene/map (omit for global scripts that run anywhere) |
| `run_once` | bool | No | Only execute once (default: false) |
| `actions` | array | Yes | Sequence of actions to execute |
| `on_condition_fail` | array | No | Actions to execute when conditions fail |

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

All scripts are loaded globally during system initialization:

1. ScriptManager scans `assets/scripts/` for all `*_scripts.json` files
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
      {"type": "change_scene", "target_map": "throne_room.tmx"}
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
      {"type": "reveal_npcs", "npcs": ["guard"]}
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
      {"type": "dialog", "speaker": "Merchant", "text": ["Welcome!"]},
      {"type": "wait_for_dialog_close"},
      {"type": "advance_dialog", "npc": "merchant"}
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
      {"type": "dialog", "speaker": "Merchant", "text": ["Good! You found your inventory!"]}
    ],
    "on_condition_fail": [
      {"type": "dialog", "speaker": "Merchant", "text": ["Please check your inventory first."]}
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
      {"type": "play_sfx", "file": "magic.wav"},
      {"type": "reveal_npcs", "npcs": ["spirit"]},
      {"type": "wait_npcs_appear", "npcs": ["spirit"]}
    ]
  },
  "cutscene_part2": {
    "trigger": {
      "event": "script_complete",
      "script": "cutscene_part1"
    },
    "actions": [
      {"type": "dialog", "speaker": "Spirit", "text": ["Who dares summon me?"]},
      {"type": "wait_for_dialog_close"},
      {"type": "start_disappear_animation", "npcs": ["spirit"]}
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
      {"type": "change_scene", "target_map": "forest.tmx", "spawn_waypoint": "from_village"}
    ],
    "on_condition_fail": [
      {"type": "dialog", "speaker": "Narrator", "text": ["The path is blocked."]}
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
      {"type": "play_music", "file": "village_theme.ogg"},
      {"type": "dialog", "speaker": "Narrator", "text": ["Welcome to the village!"]}
    ]
  }
}
```

## Custom Script Implementation

If you need to replace the script system with a custom implementation, you can extend the `ScriptBaseManager` abstract base class.

### ScriptBaseManager

**Location:** [src/pedre/systems/script/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/script/base.py)

The `ScriptBaseManager` class defines the minimum interface that any script manager must implement.

#### Required Methods

Your custom script manager must implement these abstract methods:

```python
from pedre.systems.script.base import ScriptBaseManager, Script

class CustomScriptManager(ScriptBaseManager):
    """Custom script implementation."""

    name = "script"
    dependencies = []

    def get_scripts(self) -> dict[str, Script]:
        """Get all loaded scripts."""
        ...
```

#### Registration

Register your custom script manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.script.base import ScriptBaseManager

@SystemRegistry.register
class CustomScriptManager(ScriptBaseManager):
    name = "script"
    dependencies = []

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `ScriptBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"script_manager"` in the base class
- Your implementation can use any script storage or execution system
- Register your custom script manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.script"` to replace it

**Example Custom Implementation:**

```python
# In myproject/systems/custom_script.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.script.base import ScriptBaseManager

@SystemRegistry.register
class DatabaseScriptManager(ScriptBaseManager):
    """Script manager that stores state in a database."""

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
INSTALLED_SYSTEMS = [
    "myproject.systems.custom_script",  # Load custom script first
    "pedre.systems.camera",
    "pedre.systems.audio",
    # ... rest of systems (omit "pedre.systems.script") ...
]
```

## See Also

- [Scripting Guide](../scripting/index.md) - Event-driven scripting documentation
- [Scripting Basics](../scripting/basics.md) - Script structure and organization
- [Event Types](../scripting/events.md) - Available event triggers
- [Conditions](../scripting/conditions.md) - Script condition system
- [Actions](../scripting/actions.md) - Available script actions
- [NPCManager](npc.md) - NPC interactions and dialog
- [DialogManager](dialog.md) - Conversation system
