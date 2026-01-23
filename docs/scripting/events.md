# Event Types

Events trigger scripts when specific game actions occur. This guide covers all available event types and how to use them.

## Overview

Every script has a `trigger` object that specifies:

- Which event type activates the script
- Additional conditions that must match

```json
{
  "trigger": {
    "event": "npc_interacted",
    "npc": "merchant",
    "dialog_level": 0
  }
}
```

## Available Events

### npc_interacted

Triggered when the player interacts with an NPC (presses SPACE nearby).

**Available Trigger Fields:**

- `npc` - Which NPC was interacted with
- `dialog_level` - NPC's current conversation level (optional)

**Example:**

```json
{
  "greet_merchant": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "merchant",
      "dialog_level": 0
    },
    "actions": [
      {
        "type": "dialog",
        "speaker": "Merchant",
        "text": ["Welcome to my shop!"]
      }
    ]
  }
}
```

**Use Cases:**

- Starting conversations
- Quest initiation
- Shop interactions
- Triggering cutscenes

### dialog_opened

Triggered when a dialog window is opened and shown to the player.

**Available Trigger Fields:**

- `npc` - Which NPC's dialog was opened
- `dialog_level` - Dialog level being shown (optional)

**Example:**

```json
{
  "dialog_begins": {
    "scene": "village",
    "trigger": {
      "event": "dialog_opened",
      "npc": "merchant",
      "dialog_level": 0
    },
    "actions": [
      {
        "type": "play_sfx",
        "file": "dialog_open.wav"
      },
      {
        "type": "pause_music"
      }
    ]
  }
}
```

**Use Cases:**

- Playing sound effects when conversations start
- Pausing background music during important dialogs
- Triggering visual effects or UI changes
- Tracking conversation metrics or analytics

### dialog_closed

Triggered when a dialog window is closed.

**Available Trigger Fields:**

- `npc` - Which NPC's dialog was closed
- `dialog_level` - Dialog level that was shown (optional)

**Example:**

```json
{
  "after_first_talk": {
    "scene": "village",
    "trigger": {
      "event": "dialog_closed",
      "npc": "merchant",
      "dialog_level": 0
    },
    "actions": [
      {
        "type": "advance_dialog",
        "npc": "merchant"
      },
      {
        "type": "emit_particles",
        "particle_type": "hearts",
        "npc": "merchant"
      }
    ]
  }
}
```

**Use Cases:**

- Advancing dialog progression
- Triggering follow-up actions
- Starting next phase of a quest
- Playing reactions or animations

### inventory_closed

Triggered when the inventory screen is closed.

**Available Conditions:**

Use the `conditions` array for checking inventory state.

**Example:**

```json
{
  "check_key_acquired": {
    "scene": "village",
    "trigger": {
      "event": "inventory_closed"
    },
    "conditions": [
      {
        "check": "inventory_accessed",
        "equals": true
      }
    ],
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Info",
        "text": ["You checked your inventory!"]
      },
      {
        "type": "play_sfx",
        "file": "quest_complete.wav"
      }
    ]
  }
}
```

**Use Cases:**

- Tutorial prompts
- Quest progress checks
- Item verification
- Inventory-related achievements

### object_interacted

Triggered when the player interacts with an interactive object.

**Available Trigger Fields:**

- `object_name` - Which object was interacted with

**Example:**

```json
{
  "open_chest": {
    "scene": "forest",
    "trigger": {
      "event": "object_interacted",
      "object_name": "treasure_chest"
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Info",
        "text": ["You found a Silver Key!"]
      },
      {
        "type": "play_sfx",
        "file": "chest_open.wav"
      },
      {
        "type": "emit_particles",
        "particle_type": "sparkles",
        "interactive_object": "treasure_chest"
      }
    ]
  }
}
```

**Use Cases:**

- Opening chests or containers
- Examining objects
- Activating switches or levers
- Collecting items

### npc_movement_complete

Triggered when an NPC finishes moving to a waypoint.

**Available Trigger Fields:**

- `npc` - Which NPC finished moving
- `waypoint` - Waypoint name that was reached (optional)

**Example:**

```json
{
  "merchant_arrives": {
    "scene": "village",
    "trigger": {
      "event": "npc_movement_complete",
      "npc": "merchant",
      "waypoint": "market_spot"
    },
    "actions": [
      {
        "type": "dialog",
        "speaker": "Merchant",
        "text": ["I've arrived at the market!"]
      },
      {
        "type": "play_sfx",
        "file": "arrive.wav"
      }
    ]
  }
}
```

**Use Cases:**

- Sequencing cutscene movement
- NPC patrol routes
- Timed reactions
- Multi-stage animations

### npc_disappear_complete

Triggered when an NPC's disappear animation finishes.

**Available Trigger Fields:**

- `npc` - Which NPC disappeared

**Example:**

```json
{
  "ghost_vanished": {
    "scene": "castle",
    "trigger": {
      "event": "npc_disappear_complete",
      "npc": "ghost"
    },
    "actions": [
      {
        "type": "play_sfx",
        "file": "vanish.wav"
      },
      {
        "type": "emit_particles",
        "particle_type": "burst",
        "player": true
      }
    ]
  }
}
```

**Use Cases:**

- Cleanup after NPC removal
- Dramatic disappearance effects
- Spawning new NPCs after others leave
- Quest progression markers

### portal_entered

Triggered when the player enters a portal zone.

**Available Trigger Fields:**

- `portal` - Which portal was entered (optional, omit to trigger for any portal)

**Example:**

```json
{
  "forest_portal": {
    "trigger": {
      "event": "portal_entered",
      "portal": "to_forest"
    },
    "actions": [
      {
        "type": "change_scene",
        "target_map": "forest.tmx",
        "spawn_waypoint": "from_village"
      }
    ]
  }
}
```

**Use Cases:**

- Map transitions
- Conditional portal access
- Cutscenes before transitions
- Locked doors with failure messages

**Conditional Portal Example:**

```json
{
  "tower_gate_open": {
    "trigger": {
      "event": "portal_entered",
      "portal": "tower_gate"
    },
    "conditions": [{"check": "npc_dialog_level", "npc": "guard", "gte": 2}],
    "actions": [
      {"type": "change_scene", "target_map": "Tower.tmx", "spawn_waypoint": "entrance"}
    ]
  },
  "tower_gate_locked": {
    "trigger": {
      "event": "portal_entered",
      "portal": "tower_gate"
    },
    "conditions": [{"check": "npc_dialog_level", "npc": "guard", "lt": 2}],
    "actions": [
      {"type": "dialog", "speaker": "Narrator", "text": ["The gate is locked..."]}
    ]
  }
}
```

### script_complete

Triggered when another script finishes executing.

**Available Trigger Fields:**

- `script_name` - Which script completed

**Example:**

```json
{
  "followup_action": {
    "scene": "castle",
    "trigger": {
      "event": "script_complete",
      "script_name": "cutscene_intro"
    },
    "actions": [
      {
        "type": "reveal_npcs",
        "npcs": ["guard", "captain"]
      }
    ]
  }
}
```

**Use Cases:**

- Chaining cutscene sequences
- Multi-part story events
- Complex timed actions
- Sequential quest phases

## Event Matching

When an event occurs, the script manager:

1. Finds all scripts with matching `event` type
2. Checks if additional trigger fields match (e.g., `npc`, `dialog_level`)
3. Verifies conditions in the `conditions` array
4. Confirms `scene` matches current scene (if specified)
5. Executes matching scripts that haven't been disabled by `run_once`

## Combining Events with Conditions

For more complex triggers, combine event types with conditions:

```json
{
  "trigger": {
    "event": "dialog_closed",
    "npc": "merchant"
  },
  "conditions": [
    {
      "check": "npc_dialog_level",
      "npc": "merchant",
      "equals": 2
    },
    {
      "check": "inventory_accessed",
      "equals": true
    }
  ]
}
```

This script only runs when:

- Dialog with merchant is closed AND
- Merchant's dialog level is 2 AND
- Player has accessed their inventory

## Best Practices

### Be Specific with Trigger Fields

```json
// Less specific - triggers on any merchant interaction
{
  "trigger": {
    "event": "npc_interacted",
    "npc": "merchant"
  }
}

// More specific - only triggers on first interaction
{
  "trigger": {
    "event": "npc_interacted",
    "npc": "merchant",
    "dialog_level": 0
  }
}
```

### Use run_once for One-Time Events

```json
{
  "open_chest": {
    "trigger": {
      "event": "object_interacted",
      "object_name": "treasure_chest"
    },
    "run_once": true,  // Chest can only be opened once
    "actions": [...]
  }
}
```

### Chain Scripts with script_complete

```json
{
  "part1": {
    "trigger": {
      "event": "npc_interacted",
      "npc": "elder"
    },
    "run_once": true,
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

## Next Steps

- Learn about [Conditions](conditions.md) for more complex trigger logic
- Explore [Actions](actions.md) to see what happens when events trigger
- Check [Advanced Patterns](advanced.md) for complex event sequences
