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
        "type": "dialog",
        "speaker": "Merchant",
        "text": ["Hello, traveler!"]
      },
      {
        "type": "play_sfx",
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
- If omitted, script can run in any scene
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
- Each action has a `"type"` and type-specific parameters

## File Location

Scripts are organized by scene/map in the `assets/scripts/` directory:

```text
assets/scripts/
  ├── village_scripts.json
  ├── forest_scripts.json
  └── castle_scripts.json
```

### File Organization Tips

You can organize scripts by:

- **Scene/Map:** One file per location (recommended)
- **Feature:** Main quest, side quests, NPCs, events
- **Quest Line:** Group related story scripts together

Example organization:

```text
assets/scripts/
  ├── village_main_quest.json
  ├── village_side_quests.json
  ├── village_npcs.json
  └── village_events.json
```

## Loading Scripts

Scripts are automatically loaded when a scene starts. The game's `GameView.setup()` method loads the appropriate script file:

```python
# In GameView.setup()
script_manager.load_scripts(
    script_path=f"assets/scripts/{scene_name}_scripts.json",
    npc_dialogs=npc_manager.dialogs
)
```

You don't need to manually load scripts - the system handles this automatically based on the current scene name.

## How Scripts Execute

1. **Event Occurs:** Player interacts with NPC, closes dialog, etc.
2. **Matching:** Script manager finds all scripts with matching event type
3. **Filtering:** Checks if conditions are met (scene, trigger fields, condition checks)
4. **Execution:** Runs the actions array sequentially
5. **Completion:** Emits `script_complete` event when finished

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
    {"type": "dialog", ...},
    {"type": "move_npc", ...},
    {"type": "play_music", ...},
    {"type": "reveal_npcs", ...}
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
      "script_name": "part1"
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

- Verify action type spelling
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
