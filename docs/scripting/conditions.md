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
      "check": "npc_dialog_level",
      "npc": "merchant",
      "equals": 2
    }
  ]
}
```

## Trigger Conditions

Basic event matching goes in the `trigger` object. These fields depend on the event type:

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

### object_interacted

```json
{
  "trigger": {
    "event": "object_interacted",
    "object_name": "chest"       // Required: which object
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
    "script_name": "intro"       // Required: which script
  }
}
```

## Additional Conditions

For more complex checks, use the `conditions` array. All conditions must be true for the script to run.

### Available Condition Checks

| Check Type | Fields | Description | Example |
| ---------- | ------ | ----------- | ------- |
| `npc_dialog_level` | `npc`, `equals` | Match NPC conversation level | `{"check": "npc_dialog_level", "npc": "merchant", "equals": 2}` |
| `inventory_accessed` | `equals` | Check if inventory was opened | `{"check": "inventory_accessed", "equals": true}` |
| `object_interacted` | `object`, `equals` | Check if object was interacted with | `{"check": "object_interacted", "object": "sink", "equals": true}` |

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
      "check": "npc_dialog_level",
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
      "check": "inventory_accessed",
      "equals": true
    }
  ]
}
```

**Use Cases:**

- Tutorial completion
- Achievement triggers
- First-time inventory checks

### object_interacted

Check if a specific object has been interacted with.

**Parameters:**

- `check`: `"object_interacted"`
- `object`: Object name
- `equals`: `true` or `false`

**Example:**

```json
{
  "trigger": {
    "event": "npc_interacted",
    "npc": "guard"
  },
  "conditions": [
    {
      "check": "object_interacted",
      "object": "royal_seal",
      "equals": true
    }
  ]
}
```

**Use Cases:**

- Requiring items for dialog
- Quest prerequisite checks
- Conditional NPC responses

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
      "check": "npc_dialog_level",
      "npc": "merchant",
      "equals": 2
    },
    {
      "check": "inventory_accessed",
      "equals": true
    },
    {
      "check": "object_interacted",
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
          "check": "object_interacted",
          "object": "letter",
          "equals": true
        }
      ],
      "on_condition_fail": [
        {
          "type": "dialog",
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
        "check": "object_interacted",
        "object": "royal_seal",
        "equals": true
      }
    ],
    "actions": [
      {
        "type": "set_dialog_level",
        "npc": "guard",
        "dialog_level": 2
      },
      {
        "type": "dialog",
        "speaker": "Guard",
        "text": ["You have the royal seal! Enter."]
      },
      {
        "type": "reveal_npcs",
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
        "type": "dialog",
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
      "check": "object_interacted",
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
      "check": "inventory_accessed",  // Secondary: extra requirement
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

## Next Steps

- Learn about [Actions](actions.md) to see what happens when conditions are met
- Explore [Advanced Patterns](advanced.md) for complex conditional sequences
- Browse [Examples](examples.md) for practical conditional script examples
