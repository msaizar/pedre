# Script Basics

This guide covers the fundamental concepts and structure of scripts in Arcade Tiled RPG.

## What is a Script?

A script is a JSON object that defines:

1. **When** to trigger (event type)
2. **If** it should run (conditions)
3. **What** to do (action sequence)

## Script Structure

Every script follows this basic structure:

```json
{
  "script_name": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "merchant"
    },
    "run_once": true,
    "actions": [
      {
        "name": "dialog",
        "speaker": "Merchant",
        "text": ["Hello, traveler!"]
      },
      {
        "name": "play_sfx",
        "file": "greeting.wav"
      }
    ]
  }
}
```

### Script Components

**Script Name** (`"script_name"`)

- Unique identifier for the script
- Use descriptive names like `"merchant_first_meeting"` or `"quest_start"`

**Scene** (`"scene"`)

- Optional: Which scene/map this script runs in
- If specified, script only runs in that scene (scene-specific)
- If omitted, script can run in any scene (global script)
- Example: `"scene": "village"`

**Trigger** (`"trigger"`)

- Required: Defines what event activates this script
- Contains event type and conditions
- Example: `{"event": "npc_interacted", "npc": "merchant"}`

**Run Once** (`"run_once"`)

- Optional: If `true`, script only executes once then disables
- Default: `false` (script can run multiple times)
- Use for one-time events like first meetings or story moments

**Actions** (`"actions"`)

- Required: Array of actions to execute when script triggers
- Actions run sequentially in order
- Each action has a `"name"` and action-specific parameters

## File Location

Scripts are organized by scene/map in the directory specified by the `SCRIPTS_DIRECTORY` setting (default: `assets/data/scripts/`):

```text
assets/data/scripts/
  ├── village.json
  ├── forest.json
  └── castle.json
```

You can customize the scripts directory in your `settings.py`:

```python
SCRIPTS_DIRECTORY = "custom_scripts"  # Relative to assets directory
```

### File Organization Tips

You can organize scripts by:

- **Scene/Map:** One file per location (recommended)
- **Feature:** Main quest, side quests, NPCs, events
- **Quest Line:** Group related story scripts together

Example organization:

```text
assets/data/scripts/
  ├── village_main_quest.json
  ├── village_side_quests.json
  ├── village_npcs.json
  └── village_events.json
```

## Loading Scripts

All scripts are automatically loaded globally when the ScriptPlugin initializes during plugin setup. The plugin scans the scripts directory (configured via `SCRIPTS_DIRECTORY` setting, default: `assets/data/scripts/`) for all files matching the pattern `*.json` and loads them into a single registry.

**Global Loading:**

```python
# Scripts are loaded during setup
script_plugin = ScriptPlugin()
script_plugin.setup(context)  # Loads all scripts from scripts directory
```

**Key Points:**

- All scripts from all files are loaded at once
- Scripts are available for condition checking across all scenes
- The `scene` field in each script controls when it can execute
- Scripts are reloaded on reset (new game or load game)

You don't need to manually load scripts - the plugin handles this automatically.

## How Scripts Execute

1. **Event Occurs:** Player interacts with NPC, closes dialog, etc.
2. **Event Handling:** EventBus publishes event to all subscribers
3. **Matching:** Script plugin finds all scripts with matching event type in trigger
4. **Filtering:** Checks if trigger fields match, scene matches, and conditions are met
5. **Execution:** Runs the actions array sequentially
6. **Completion:** Emits `script_complete` event when finished

## Script Properties

### scene

**Type:** string (optional)

Only run the script in a specific scene/map.

```json
{
  "village_only": {
    "scene": "village",
    "trigger": {
      "event": "dialog_closed",
      "npc": "merchant"
    },
    "actions": []
  }
}
```

**Use Cases:**

- Scene-specific behaviors
- Map-dependent events
- Location-based triggers

### run_once

**Type:** boolean (default: false)

Execute the script only once, then disable it.

```json
{
  "first_meeting": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "merchant"
    },
    "run_once": true,
    "actions": []
  }
}
```

**Use Cases:**

- First-time conversations
- One-time item pickups
- Story events that shouldn't repeat

## Best Practices

### 1. Use Descriptive Names

```json
// Bad
{"s1": {...}}

// Good
{"merchant_first_meeting": {...}}
```

### 2. Keep Scripts Focused

Break long action sequences into multiple scripts using `script_complete`:

```json
// Bad - Too many unrelated actions
{
  "actions": [
    {"name": "dialog", ...},
    {"name": "move_npc", ...},
    {"name": "play_music", ...},
    {"name": "start_appear_animation", ...}
    // 20 more actions...
  ]
}

// Good - Break into multiple scripts
{
  "part1": {
    "trigger": {...},
    "actions": [...]
  },
  "part2": {
    "trigger": {
      "event": "script_complete",
      "script": "part1"
    },
    "actions": [...]
  }
}
```

### 3. Use run_once for Story Events

```json
{
  "important_story_moment": {
    "scene": "village",
    "trigger": {...},
    "run_once": true,  // Prevents repeating
    "actions": [...]
  }
}
```

### 4. Use Scene Property for Map-Specific Scripts

```json
{
  "village_welcome": {
    "scene": "village",  // Only runs in village
    "trigger": {
      "event": "npc_interacted",
      "npc": "elder"
    },
    "actions": [...]
  },
  "global_item_pickup": {
    // No scene property - runs in ANY scene
    "trigger": {
      "event": "item_acquired"
    },
    "actions": [
      {"name": "play_sfx", "file": "pickup.wav"}
    ]
  }
}
```

### 5. Use Trigger Fields Wisely

```json
// Specific trigger conditions prevent unwanted triggers
{
  "my_script": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "merchant",
      "dialog_level": 0
    },
    "actions": [...]
  }
}
```

### 6. Document Complex Scripts

```json
{
  "complex_cutscene": {
    // This script triggers the main story event where the king reveals
    // the ancient prophecy. Requires player to have talked to king 5 times.
    "scene": "throne_room",
    "trigger": {
      "event": "npc_interacted",
      "npc": "king",
      "dialog_level": 5
    },
    "actions": [...]
  }
}
```

## Debugging Scripts

### Script Validation

All scripts are validated when they're loaded. If there are any errors in your script definitions, you'll get a detailed error message listing all problems:

```text
ScriptValidationError: 5 script validation error(s):
  - Script 'intro_cutscene': unknown event 'scene_loaded' (registered events: scene_start, npc_interacted, ...)
  - Script 'merchant_greeting': unknown action type 'show_dialog' (registered actions: dialog, move_npc, ...)
  - Script 'broken_script': unknown keys ['conditions_fail'] (valid keys: actions, conditions, on_condition_fail, run_once, scene, trigger)
  - Script 'npc_move': action 'move_npc': 'waypoint' must be a string
  - Script 'dialog_test': action 'dialog': 'text' must be a list
```

**Validation Checks:**

- Event types in `trigger.event` must be registered (e.g., "npc_interacted", "dialog_closed")
- Conditions in `conditions[].check` must be registered (e.g., "inventory_accessed", "script_completed")
- Action in `actions[].name` and `on_condition_fail[].name` must be registered (e.g., "dialog", "move_npc")
- Only valid top-level keys are allowed: `trigger`, `conditions`, `scene`, `run_once`, `actions`, `on_condition_fail`
- The `actions` array must contain at least one action
- All action, event, and condition parameters must be the correct types:
  - String fields (like `npc`, `waypoint`, `file`) must be strings, not numbers or booleans
  - Boolean fields (like `loop`, `smooth`, `run_once`) must be true/false, not strings
  - Number fields (like `volume`, `dialog_level`) must be numbers, not strings or booleans
  - List fields (like `npcs`, `text`, `color`) must be arrays with the correct element types

This catches typos, type errors, and configuration errors before they cause runtime issues.

### Check Script Loading

Enable logging to see script load messages:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

**Script not triggering:**

- Check event_type matches the actual event
- Verify all conditions are met
- Ensure scene name matches if scene property is set
- Check if run_once script already executed

**Actions not executing:**

- Verify action name spelling
- Check params match expected format
- Look for console errors
- Ensure required NPCs/objects exist

**NPCs not moving:**

- Verify waypoint exists in Tiled map
- Check pathfinding can find a route
- Ensure NPC isn't already moving

**Dialogs not showing:**

- Check dialog JSON exists and is valid
- Verify npc_name matches dialog file
- Ensure dialog level exists in JSON

## Performance Tips

1. **Limit concurrent scripts:** Too many active scripts can impact performance
2. **Use run_once:** Prevents unnecessary condition checking
3. **Avoid tight loops:** Don't create scripts that trigger each other rapidly
4. **Clean up references:** Remove event listeners when scenes unload

## Next Steps

- Learn about [Event Types](events.md) to understand what can trigger your scripts
- Explore [Conditions](conditions.md) to control when scripts execute
- Browse [Actions](actions.md) to see what your scripts can do
