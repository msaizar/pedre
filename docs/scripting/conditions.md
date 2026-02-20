# Conditions

Conditions determine if a script should run when its event is triggered. This guide covers all types of conditions and how to use them effectively.

## Overview

Conditions can be specified in two places:

1. **Trigger Object:** Basic event matching (required)
2. **Conditions Array:** Additional checks (optional)

```json
{
  "trigger": {
    "event": "dialog_closed",
    "npc": "merchant"
  },
  "conditions": [
    {
      "name": "npc_dialog_level",
      "npc": "merchant",
      "equals": 2
    }
  ]
}
```

## Trigger Conditions

The `trigger` object specifies which event to react to and can include fields to match specific event data. These fields filter the event when it fires and depend on the event type:

### npc_interacted

```json
{
  "trigger": {
    "event": "npc_interacted",
    "npc": "merchant",           // Required: which NPC
    "dialog_level": 0            // Optional: current dialog level
  }
}
```

### dialog_closed

```json
{
  "trigger": {
    "event": "dialog_closed",
    "npc": "merchant",           // Optional: which NPC's dialog
    "dialog_level": 0            // Optional: what level was shown
  }
}
```

### object_interacted (event)

```json
{
  "trigger": {
    "event": "object_interacted",
    "object_name": "chest"       // Required: which object was just interacted with
  }
}
```

### npc_movement_complete

```json
{
  "trigger": {
    "event": "npc_movement_complete",
    "npc": "guard",              // Required: which NPC
    "waypoint": "gate"           // Optional: destination waypoint
  }
}
```

### npc_disappear_complete

```json
{
  "trigger": {
    "event": "npc_disappear_complete",
    "npc": "ghost"               // Required: which NPC
  }
}
```

### script_complete

```json
{
  "trigger": {
    "event": "script_complete",
    "script": "intro"            // Required: which script
  }
}
```

## Additional Conditions

For checking game state beyond event matching, use the `conditions` array. These conditions check persistent state (what has happened before, current values, etc.) rather than the event that just fired. All conditions must be true for the script to run.

### Available Condition Checks

| Check Type           | Fields                                | Description                                            | Example                                                            |
| -------------------- | ------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------ |
| `npc_interacted`     | `npc`, `scene`, `equals`              | Check if NPC was interacted with in a scene            | `{"name": "npc_interacted", "npc": "guard", "equals": true}`      |
| `npc_dialog_level`   | `npc`, `equals`                       | Match NPC conversation level                           | `{"name": "npc_dialog_level", "npc": "merchant", "equals": 2}`    |
| `inventory_accessed` | `equals`                              | Check if inventory was ever opened                     | `{"name": "inventory_accessed", "equals": true}`                  |
| `object_interacted`  | `object`, `equals`                    | Check if object was ever interacted with (state check) | `{"name": "object_interacted", "object": "sink", "equals": true}` |
| `script_completed`   | `script`                              | Check if a run_once script has completed               | `{"name": "script_completed", "script": "intro_cutscene"}`        |
| `item_acquired`      | `item_id`                             | Check if an item was acquired                          | `{"name": "item_acquired", "item_id": "golden_key"}`              |

### npc_interacted (state check)

Check if an NPC has been interacted with in a specific scene. This is different from the `npc_interacted` event trigger, which fires when an interaction happens. This condition checks persistent state.

**Parameters:**

- `check`: `"npc_interacted"`
- `npc`: NPC identifier
- `scene`: Optional scene name (defaults to current scene)
- `equals`: `true` (has been interacted with) or `false` (has not been interacted with)

**Example:**

```json
{
  "trigger": {
    "event": "portal_entered",
    "portal": "exit"
  },
  "conditions": [
    {
      "name": "npc_interacted",
      "npc": "guard"
    }
  ]
}
```

**Check if NOT interacted:**

```json
{
  "name": "npc_interacted",
  "npc": "guard",
  "equals": false
}
```

**Check interaction in specific scene:**

```json
{
  "name": "npc_interacted",
  "npc": "guard",
  "scene": "castle"
}
```

**Use Cases:**

- Gating progression behind conversations
- Quest prerequisites
- Conditional scene transitions
- Ensuring player talked to key NPCs

### npc_dialog_level

Check if an NPC's conversation progress matches a specific level.

**Parameters:**

- `check`: `"npc_dialog_level"`
- `npc`: NPC identifier
- `equals`: Expected dialog level (integer)

**Example:**

```json
{
  "trigger": {
    "event": "dialog_closed",
    "npc": "merchant"
  },
  "conditions": [
    {
      "name": "npc_dialog_level",
      "npc": "merchant",
      "equals": 2
    }
  ]
}
```

**Use Cases:**

- Triggering events after multiple conversations
- Quest progression tracking
- Unlocking new dialog options

### inventory_accessed

Check if the player has opened their inventory.

**Parameters:**

- `check`: `"inventory_accessed"`
- `equals`: `true` or `false`

**Example:**

```json
{
  "trigger": {
    "event": "inventory_closed"
  },
  "conditions": [
    {
      "name": "inventory_accessed",
      "equals": true
    }
  ]
}
```

**Use Cases:**

- Tutorial completion
- Achievement triggers
- First-time inventory checks

### object_interacted (state check)

Check if a specific object has been interacted with at any point in the past. This is different from the `object_interacted` event trigger, which fires when an interaction happens. This condition checks persistent state.

**Parameters:**

- `check`: `"object_interacted"`
- `object`: Object name
- `equals`: `true` (has been interacted with) or `false` (has not been interacted with)

**Example:**

```json
{
  "trigger": {
    "event": "npc_interacted",
    "npc": "guard"
  },
  "conditions": [
    {
      "name": "object_interacted",
      "object": "royal_seal",
      "equals": true
    }
  ],
  "actions": [
    {
      "name": "dialog",
      "speaker": "Guard",
      "text": ["I see you found the royal seal. You may pass."]
    }
  ]
}
```

This script triggers when talking to the guard, but only if the player has previously interacted with the royal seal object.

**Use Cases:**

- Requiring prior object interactions for dialog
- Quest prerequisite checks
- Conditional NPC responses based on exploration

### script_completed

Check if a run_once script has completed execution. This is useful for creating follow-up scripts that only run after another script has finished, or for portal scripts that should behave differently after an initial cutscene.

**Parameters:**

- `check`: `"script_completed"`
- `script`: Script name

**Example:**

```json
{
  "trigger": {
    "event": "portal_entered",
    "portal": "dungeon_gate"
  },
  "conditions": [
    {
      "name": "script_completed",
      "script": "dungeon_intro_cutscene"
    }
  ],
  "actions": [
    {"name": "change_scene", "target_map": "dungeon.tmx", "spawn_waypoint": "entrance"}
  ]
}
```

**Use Cases:**

- Portal scripts that skip cutscenes on subsequent visits
- Chained cutscene sequences
- Unlocking features after tutorials
- Quest progression gating

**Portal Pattern Example:**

```json
{
  "dungeon_first_entry": {
    "trigger": {"event": "portal_entered", "portal": "dungeon_gate"},
    "run_once": true,
    "actions": [
      {"name": "dialog", "speaker": "Narrator", "text": ["A cold wind blows..."]},
      {"name": "wait_for_dialog_close"},
      {"name": "change_scene", "target_map": "dungeon.tmx", "spawn_waypoint": "entrance"}
    ]
  },
  "dungeon_return": {
    "trigger": {"event": "portal_entered", "portal": "dungeon_gate"},
    "conditions": [{"name": "script_completed", "script": "dungeon_first_entry"}],
    "actions": [
      {"name": "change_scene", "target_map": "dungeon.tmx", "spawn_waypoint": "entrance"}
    ]
  }
}
```

### item_acquired

Check if an inventory item was acquired.

**Parameters:**

- `check`: `"item_acquired"`
- `item_id`: Item id

**Example:**

```json
{
  "trigger": {
    "event": "portal_entered",
    "portal": "dungeon_gate"
  },
  "conditions": [
    {
      "name": "item_acquired",
      "item_id": "dungeon_key"
    }
  ],
  "actions": [
    {"name": "change_scene", "target_map": "dungeon.tmx", "spawn_waypoint": "entrance"}
  ]
}
```

## Multiple Conditions

You can combine multiple conditions. ALL must be true for the script to run.

```json
{
  "trigger": {
    "event": "dialog_closed",
    "npc": "merchant"
  },
  "conditions": [
    {
      "name": "npc_dialog_level",
      "npc": "merchant",
      "equals": 2
    },
    {
      "name": "inventory_accessed",
      "equals": true
    },
    {
      "name": "object_interacted",
      "object": "letter",
      "equals": true
    }
  ]
}
```

This script runs only when:

- Dialog with merchant closes AND
- Merchant's dialog level is 2 AND
- Player has accessed inventory AND
- Player has interacted with the letter

## Conditional Dialog

NPCs can have dialog-level conditions in their dialog JSON files. This allows different dialog based on game state.

**Dialog File Example:**

```json
{
  "merchant": {
    "0": {
      "text": ["Hello, stranger! I see you have the letter."],
      "conditions": [
        {
          "name": "object_interacted",
          "object": "letter",
          "equals": true
        }
      ],
      "on_condition_fail": [
        {
          "name": "dialog",
          "speaker": "Merchant",
          "text": ["Come back with a letter of introduction."]
        }
      ]
    }
  }
}
```

**How It Works:**

1. Player talks to merchant (dialog level 0)
2. System checks conditions
3. If conditions pass: Shows main dialog
4. If conditions fail: Runs `on_condition_fail` actions

**Use Cases:**

- Gated conversations requiring items
- Different responses based on game state
- Quest requirement checks

## Conditional Progression Example

Create branching paths based on player actions:

```json
{
  "talk_with_seal": {
    "scene": "castle",
    "trigger": {
      "event": "npc_interacted",
      "npc": "guard",
      "dialog_level": 0
    },
    "conditions": [
      {
        "name": "object_interacted",
        "object": "royal_seal",
        "equals": true
      }
    ],
    "actions": [
      {
        "name": "set_dialog_level",
        "npc": "guard",
        "dialog_level": 2
      },
      {
        "name": "dialog",
        "speaker": "Guard",
        "text": ["You have the royal seal! Enter."]
      },
      {
        "name": "start_appear_animation",
        "npcs": ["king"]
      }
    ]
  },
  "talk_without_seal": {
    "scene": "castle",
    "trigger": {
      "event": "npc_interacted",
      "npc": "guard",
      "dialog_level": 0
    },
    "actions": [
      {
        "name": "dialog",
        "speaker": "Guard",
        "text": ["You need the royal seal to enter."]
      }
    ]
  }
}
```

The first script runs if player has the seal, otherwise the second runs.

## Best Practices

### 1. Use Specific Conditions

More specific conditions prevent unwanted triggers:

```json
// Less specific
{
  "trigger": {
    "event": "npc_interacted",
    "npc": "merchant"
  }
}

// More specific
{
  "trigger": {
    "event": "npc_interacted",
    "npc": "merchant",
    "dialog_level": 0
  },
  "conditions": [
    {
      "name": "object_interacted",
      "object": "quest_item",
      "equals": true
    }
  ]
}
```

### 2. Consider Fallback Scripts

Provide alternative scripts for failed conditions:

```json
{
  "main_path": {
    "trigger": {...},
    "conditions": [{...}],
    "actions": [...]
  },
  "fallback_path": {
    "trigger": {...},
    "actions": [...]  // No conditions - catches all other cases
  }
}
```

### 3. Test Edge Cases

Always test:

- What happens if conditions are never met?
- What if player interacts in wrong order?
- What if required objects don't exist?

### 4. Use Dialog Level for Quest Tracking

Dialog levels make excellent quest progress trackers:

```json
// Level 0: Quest not started
// Level 1: Quest given
// Level 2: Quest in progress
// Level 3: Quest complete
{
  "trigger": {
    "event": "npc_interacted",
    "npc": "quest_giver",
    "dialog_level": 3
  }
}
```

### 5. Combine Trigger and Conditions

Use trigger fields for primary matching, conditions for secondary checks:

```json
{
  "trigger": {
    "event": "dialog_closed",
    "npc": "merchant",        // Primary: which NPC
    "dialog_level": 1         // Primary: which conversation
  },
  "conditions": [
    {
      "name": "inventory_accessed",  // Secondary: extra requirement
      "equals": true
    }
  ]
}
```

## Debugging Conditions

### Script Not Triggering?

Check:

1. Event type matches actual event
2. All trigger fields match exactly
3. All conditions in array are true
4. Scene matches if specified
5. run_once hasn't disabled the script

### Enable Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Look for condition check messages in console output.

## Creating Custom Conditions

 Pedre supports adding custom condition logic using the `ConditionRegistry`.

### 1. Define the Checker Function

 Create a function that initiates the check. It receives the condition parameters (from JSON) and the `GameContext`.

 ```python
 from typing import Any
 from pedre.plugins.game_context import GameContext
 from pedre.conditions.registry import ConditionRegistry

 @ConditionRegistry.register("is_weather")
 def check_weather(data: dict[str, Any], context: GameContext) -> bool:
     required_weather = data.get("weather")

     weather_plugin = context.get_plugin("weather")
     if not weather_plugin:
         return False

     return weather_plugin.current_weather == required_weather
 ```

### 2. Use in Scripts

 ```json
 {
   "trigger": {
     "event": "npc_interacted",
     "npc": "farmer"
   },
   "conditions": [
     {
       "name": "is_weather",
       "weather": "rain"
     }
   ]
 }
 ```

## Next Steps

- Learn about [Actions](../extending/custom-actions.md) to see what happens when conditions are met
- Explore [Advanced Patterns](advanced.md) for complex conditional sequences
- Browse [Examples](examples.md) for practical conditional script examples
