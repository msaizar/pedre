# ScriptManager

Event-driven scripting system for cutscenes and interactive sequences.

## Location

`src/pedre/systems/script.py`

## Initialization

```python
from pedre.systems.script import ScriptManager

script_manager = ScriptManager(event_bus=event_bus)
```

## Key Methods

### `load_scripts(script_path: str, npc_dialogs: dict) -> None`

Load scripts from a JSON file.

**Parameters:**

- `script_path` - Path to script JSON file
- `npc_dialogs` - NPC dialog data (from NPCManager)

**Example:**

```python
script_manager.load_scripts(
    script_path="assets/scripts/village_scripts.json",
    npc_dialogs=npc_manager.dialogs
)
```

### `update(delta_time: float, context: GameContext) -> None`

Update active action sequences (call every frame).

**Parameters:**

- `delta_time` - Time since last update in seconds
- `context` - GameContext with all managers

**Example:**

```python
def on_update(self, delta_time):
    self.script_manager.update(delta_time, self.game_context)
```

### `reset_script(script_name: str) -> None`

Reset a script to allow it to run again.

**Parameters:**

- `script_name` - Name of the script to reset

**Example:**

```python
# Allow a "run_once" script to execute again
script_manager.reset_script("first_meeting")
```

## Script JSON Format

```json
{
  "script_name": {
    "event_type": "npc_interacted",
    "condition": {
      "npc_name": "merchant",
      "dialog_level": 0
    },
    "scene": "village",
    "run_once": true,
    "defer_conditions": false,
    "actions": [
      {
        "type": "show_dialog",
        "params": {"npc_name": "merchant"}
      },
      {
        "type": "set_dialog_level",
        "params": {"npc_name": "merchant", "level": 1}
      }
    ]
  }
}
```

## Script Fields

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `event_type` | string | Yes | Event that triggers this script |
| `condition` | object | No | Conditions to check before running |
| `scene` | string | No | Only run in this scene/map |
| `run_once` | bool | No | Only execute once (default: false) |
| `defer_conditions` | bool | No | Check conditions after update (default: false) |
| `actions` | array | Yes | Sequence of actions to execute |

## Available Event Types

- `npc_interacted` - Player interacts with NPC
- `dialog_closed` - Dialog window closes
- `inventory_closed` - Inventory closes
- `object_interacted` - Player interacts with object
- `npc_movement_complete` - NPC finishes moving
- `npc_disappear_complete` - NPC disappear animation finishes
- `script_complete` - Another script finishes

## Available Actions

| Action Type | Parameters | Description |
| ----------- | ---------- | ----------- |
| `show_dialog` | `npc_name` | Display NPC dialog |
| `set_dialog_level` | `npc_name`, `level` | Update conversation progress |
| `move_npc` | `npc_name`, `waypoint` | Move NPC to position |
| `reveal_npcs` | `npc_names` (array) | Make NPCs visible |
| `start_disappear_animation` | `npc_name` | Play disappear animation |
| `remove_npc_from_walls` | `npc_name` | Remove NPC collision |
| `set_current_npc` | `npc_name` | Set context NPC |
| `emit_particles` | `x`, `y`, `duration` | Spawn particles |
| `play_sfx` | `audio_file` | Play sound effect |
| `play_music` | `audio_file` | Play background music |
| `wait_for_dialog_close` | - | Pause until dialog closes |
| `wait_for_inventory_access` | - | Pause until inventory closes |
| `wait_for_npc_movement` | `npc_name` | Pause until NPC arrives |
| `wait_for_npcs_appear` | `npc_names` (array) | Pause until NPCs appear |

## Condition Checking

Conditions can check:

- `npc_name` - Match NPC identifier
- `dialog_level` - Match conversation level
- `object_name` - Match interacted object
- `has_item` - Check inventory for item

**Example:**

```json
{
  "condition": {
    "npc_name": "merchant",
    "dialog_level": 0,
    "has_item": "golden_key"
  }
}
```
