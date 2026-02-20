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
        "name": "dialog",
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
        "name": "play_sfx",
        "file": "dialog_open.wav"
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
        "name": "advance_dialog",
        "npc": "merchant"
      },
      {
        "name": "emit_particles",
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
        "name": "dialog",
        "speaker": "Info",
        "text": ["You checked your inventory!"]
      },
      {
        "name": "play_sfx",
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

### item_acquired

Triggered when player acquires an inventory item for the first time.

**Available Trigger Fields:**

- `item_id` - Which item was acquired (optional)

**Example:**

```json
{
  "found_key": {
    "scene": "dungeon",
    "trigger": {
      "event": "item_acquired",
      "item_id": "rusty_key"
    },
    "actions": [
      {
        "name": "dialog",
        "speaker": "Narrator",
        "text": ["This key might unlock something..."]
      },
      {
        "name": "play_sfx",
        "file": "item_get.wav"
      }
    ]
  }
}
```

**Example without item_id filter (triggers for any item):**

```json
{
  "any_item_found": {
    "scene": "village",
    "trigger": {
      "event": "item_acquired"
    },
    "actions": [
      {
        "name": "play_sfx",
        "file": "item_pickup.wav"
      }
    ]
  }
}
```

**Use Cases:**

- Playing sound effects on item pickup
- Showing notifications or messages
- Triggering quest progression
- Unlocking new areas or features
- Achievement tracking

### item_consumed

Triggered when player consumes an inventory item.

**Available Trigger Fields:**

- `item_id` - Which item was consumed (optional)
- `category` - Category of consumed item (optional)

**Example filtering by item_id:**

```json
{
  "used_health_potion": {
    "scene": "dungeon",
    "trigger": {
      "event": "item_consumed",
      "item_id": "health_potion_1"
    },
    "actions": [
      {
        "name": "dialog",
        "speaker": "Narrator",
        "text": ["You feel refreshed!"]
      },
      {
        "name": "play_sfx",
        "file": "potion_drink.wav"
      }
    ]
  }
}
```

**Example filtering by category:**

```json
{
  "consumed_any_potion": {
    "scene": "dungeon",
    "trigger": {
      "event": "item_consumed",
      "category": "consumable"
    },
    "actions": [
      {
        "name": "play_sfx",
        "file": "consume.wav"
      }
    ]
  }
}
```

**Use Cases:**

- Applying item effects (healing, buffs)
- Playing consumption sound effects
- Tracking item usage statistics
- Quest objectives requiring item use
- Achievement triggers

### item_acquisition_failed

Triggered when an attempt to acquire an item fails.

**Available Trigger Fields:**

- `item_id` - Which item failed to be acquired (optional)
- `reason` - Reason for failure: `"capacity"`, `"unknown_item"`, or `"already_owned"` (optional)

**Example showing inventory full message:**

```json
{
  "inventory_full": {
    "scene": "village",
    "trigger": {
      "event": "item_acquisition_failed",
      "reason": "capacity"
    },
    "actions": [
      {
        "name": "dialog",
        "speaker": "Narrator",
        "text": ["Your inventory is full! You can't carry any more items."]
      },
      {
        "name": "play_sfx",
        "file": "error.wav"
      }
    ]
  }
}
```

**Example for specific item:**

```json
{
  "key_already_owned": {
    "scene": "dungeon",
    "trigger": {
      "event": "item_acquisition_failed",
      "item_id": "dungeon_key",
      "reason": "already_owned"
    },
    "actions": [
      {
        "name": "dialog",
        "speaker": "Narrator",
        "text": ["You already have this key."]
      }
    ]
  }
}
```

**Use Cases:**

- Showing "inventory full" messages
- Handling duplicate item pickups
- Error feedback to player
- Tutorial hints about inventory management
- Preventing progression until inventory space available

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
        "name": "dialog",
        "speaker": "Info",
        "text": ["You found a Silver Key!"]
      },
      {
        "name": "play_sfx",
        "file": "chest_open.wav"
      },
      {
        "name": "emit_particles",
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

- `npc` - Which NPC finished moving (optional, omit to trigger for any NPC)

**Example:**

```json
{
  "merchant_arrives": {
    "scene": "village",
    "trigger": {
      "event": "npc_movement_complete",
      "npc": "merchant"
    },
    "actions": [
      {
        "name": "dialog",
        "speaker": "Merchant",
        "text": ["I've arrived at the market!"]
      },
      {
        "name": "play_sfx",
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

### npc_appear_complete

Triggered when an NPC's appear animation finishes.

**Available Trigger Fields:**

- `npc` - Which NPC appeared (optional, omit to trigger for any NPC)

**Example:**

```json
{
  "spirit_materialized": {
    "scene": "forest",
    "trigger": {
      "event": "npc_appear_complete",
      "npc": "spirit"
    },
    "actions": [
      {
        "name": "play_sfx",
        "file": "materialize.wav"
      },
      {
        "name": "dialog",
        "speaker": "Spirit",
        "text": ["I have been summoned!"]
      }
    ]
  }
}
```

**Use Cases:**

- Triggering dialog after dramatic entrances
- Playing sound effects when NPCs fully appear
- Chaining actions after reveal sequences
- Coordinating multiple NPC appearances

### npc_disappear_complete

Triggered when an NPC's disappear animation finishes.

**Available Trigger Fields:**

- `npc` - Which NPC disappeared (optional, omit to trigger for any NPC)

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
        "name": "play_sfx",
        "file": "vanish.wav"
      },
      {
        "name": "emit_particles",
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

- `portal` - Which portal was entered (optional, omit entirely to trigger for any portal)

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
        "name": "change_scene",
        "target_map": "forest.tmx",
        "spawn_waypoint": "from_village"
      }
    ]
  }
}
```

**Example without portal filter (triggers for ANY portal):**

```json
{
  "any_portal_sfx": {
    "trigger": {
      "event": "portal_entered"
    },
    "actions": [
      {
        "name": "play_sfx",
        "file": "portal_whoosh.wav"
      }
    ]
  }
}
```

**Notes:**

- Events only fire when player enters the portal zone (not while standing in it)
- Won't re-fire until player leaves and re-enters
- Uses `PORTAL_INTERACTION_DISTANCE` setting
- For more details, see the [Portal Plugin Documentation](../plugins/portal.md)

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
    "conditions": [{"check": "npc_dialog_level", "npc": "guard", "equals": 2}],
    "actions": [
      {"name": "change_scene", "target_map": "Tower.tmx", "spawn_waypoint": "entrance"}
    ]
  },
  "tower_gate_locked": {
    "trigger": {
      "event": "portal_entered",
      "portal": "tower_gate"
    },
    "conditions": [{"check": "npc_dialog_level", "npc": "guard", "equals": 0}],
    "actions": [
      {"name": "dialog", "speaker": "Narrator", "text": ["The gate is locked..."]}
    ]
  }
}
```

### scene_start

Triggered when a new scene/map finishes loading.

**Available Trigger Fields:**

- `scene` - Which scene started loading (optional, omit to trigger for any scene)

**Example:**

```json
{
  "forest_intro": {
    "scene": "forest",
    "trigger": {
      "event": "scene_start"
    },
    "actions": [
      {
        "name": "play_music",
        "file": "forest_ambience.ogg"
      },
      {
        "name": "dialog",
        "speaker": "Narrator",
        "text": ["The forest is dark and mysterious..."]
      }
    ]
  }
}
```

**Example with scene filter:**

```json
{
  "village_welcome": {
    "trigger": {
      "event": "scene_start",
      "scene": "village"
    },
    "run_once": true,
    "actions": [
      {
        "name": "dialog",
        "speaker": "Narrator",
        "text": ["Welcome to the village!"]
      }
    ]
  }
}
```

**Notes:**

- Fires after all plugins are loaded and initialized
- Fires on every map transition and when starting new game
- Useful for scene-specific initialization like music, cutscenes, or tutorial messages
- For more details, see the [Scene Plugin Documentation](../plugins/scene.md)

**Use Cases:**

- Playing scene-specific music
- Opening cutscenes when entering new areas
- Tutorial messages for first-time visits
- Quest state checks when returning to areas
- Spawning or revealing NPCs based on game state

**Scene-Specific Quest Example:**

```json
{
  "castle_return": {
    "trigger": {
      "event": "scene_start",
      "scene": "castle"
    },
    "conditions": [
      {"check": "quest_complete", "quest": "gather_herbs"}
    ],
    "run_once": true,
    "actions": [
      {
        "name": "start_appear_animation",
        "npcs": ["king", "advisor"]
      },
      {
        "name": "dialog",
        "speaker": "King",
        "text": ["You've returned! Did you find the herbs?"]
      }
    ]
  }
}
```

### script_complete

Triggered when another script finishes executing.

**Available Trigger Fields:**

- `script` - Which script completed

**Example:**

```json
{
  "followup_action": {
    "scene": "castle",
    "trigger": {
      "event": "script_complete",
      "script": "cutscene_intro"
    },
    "actions": [
      {
        "name": "start_appear_animation",
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

When an event occurs, the script plugin:

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
      "script": "part1"
    },
    "actions": [...]
  }
}
```

## Next Steps

- Learn about [Conditions](conditions.md) for more complex trigger logic
- Explore [Actions](actions.md) to see what happens when events trigger
- Check [Advanced Patterns](advanced.md) for complex event sequences
