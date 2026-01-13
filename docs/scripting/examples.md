# Script Examples

A cookbook of complete, ready-to-use script examples for common gameplay scenarios.

## Example 1: First Meeting

A simple first-time conversation with an NPC that advances dialog progression.

```json
{
  "meet_merchant_first_time": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "merchant",
      "dialog_level": 0
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Merchant",
        "text": ["Hello, traveler! Welcome to my shop."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "advance_dialog",
        "npc": "merchant"
      },
      {
        "type": "play_sfx",
        "file": "greeting.wav"
      }
    ]
  }
}
```

**What It Does:**

- Triggers on first interaction with merchant (dialog_level 0)
- Shows greeting dialog
- Waits for player to close dialog
- Advances merchant's dialog level to 1
- Plays greeting sound
- Only runs once

## Example 2: Item Collection

Opening a chest and receiving an item with visual and audio feedback.

```json
{
  "collect_golden_key": {
    "scene": "dungeon",
    "trigger": {
      "event": "object_interacted",
      "object_name": "golden_chest"
    },
    "run_once": true,
    "actions": [
      {
        "type": "play_sfx",
        "file": "chest_open.wav"
      },
      {
        "type": "dialog",
        "speaker": "Info",
        "text": ["You found the Golden Key!"]
      },
      {
        "type": "emit_particles",
        "particle_type": "sparkles",
        "x": 500,
        "y": 400
      }
    ]
  }
}
```

**What It Does:**

- Triggers when golden_chest is interacted with
- Plays chest opening sound immediately
- Shows item acquisition message
- Spawns sparkle particles at chest location
- Only runs once (chest can't be opened again)

## Example 3: Multi-NPC Cutscene

Coordinating multiple NPCs with movement and dialog.

```json
{
  "village_meeting": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "elder"
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Elder",
        "text": ["Let me call the others."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "reveal_npcs",
        "npcs": ["guard", "merchant"]
      },
      {
        "type": "wait_for_npcs_appear",
        "npcs": ["guard", "merchant"]
      },
      {
        "type": "move_npc",
        "npcs": ["guard"],
        "waypoint": "meeting_spot"
      },
      {
        "type": "move_npc",
        "npcs": ["merchant"],
        "waypoint": "meeting_spot"
      },
      {
        "type": "wait_for_movement",
        "npc": "guard"
      },
      {
        "type": "wait_for_movement",
        "npc": "merchant"
      },
      {
        "type": "dialog",
        "speaker": "Guard",
        "text": ["You called, Elder?"]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "dialog",
        "speaker": "Merchant",
        "text": ["What seems to be the matter?"]
      }
    ]
  }
}
```

**What It Does:**

- Elder announces calling others
- Reveals guard and merchant with appear animation
- Waits for both to fully appear
- Moves both NPCs to meeting spot simultaneously
- Waits for both to arrive
- Guard speaks first
- Merchant speaks second
- Only runs once

## Example 4: Object Interaction Sequence

Examining an object with atmospheric effects.

```json
{
  "examine_altar": {
    "scene": "temple",
    "trigger": {
      "event": "object_interacted",
      "object_name": "altar"
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Info",
        "text": ["The altar glows with ancient power..."]
      },
      {
        "type": "play_sfx",
        "file": "magic_glow.wav"
      },
      {
        "type": "emit_particles",
        "particle_type": "sparkles",
        "x": 700,
        "y": 100
      }
    ]
  }
}
```

**What It Does:**

- Triggers when altar is examined
- Shows atmospheric description
- Plays magical sound effect
- Emits sparkles at altar location
- Only happens once

## Example 5: Boss Encounter

Dramatic boss appearance with music and effects.

```json
{
  "boss_appear": {
    "scene": "boss_room",
    "trigger": {
      "event": "object_interacted",
      "object_name": "altar"
    },
    "run_once": true,
    "actions": [
      {
        "type": "play_music",
        "file": "boss_theme.ogg"
      },
      {
        "type": "emit_particles",
        "particle_type": "burst",
        "x": 400,
        "y": 300
      },
      {
        "type": "reveal_npcs",
        "npcs": ["boss"]
      },
      {
        "type": "wait_for_npcs_appear",
        "npcs": ["boss"]
      },
      {
        "type": "dialog",
        "speaker": "Boss",
        "text": ["You dare disturb my slumber?!"]
      },
      {
        "type": "wait_for_dialog_close"
      }
    ]
  }
}
```

**What It Does:**

- Activates when player touches altar
- Immediately plays boss music
- Creates explosion particle effect
- Reveals boss with appear animation
- Waits for boss to fully appear
- Boss delivers threatening dialog
- Only happens once

## Example 6: Guard Patrol Route

Looping NPC movement pattern.

```json
{
  "guard_patrol_1": {
    "scene": "castle",
    "trigger": {
      "event": "npc_movement_complete",
      "npc": "guard",
      "waypoint": "point_a"
    },
    "actions": [
      {
        "type": "move_npc",
        "npcs": ["guard"],
        "waypoint": "point_b"
      }
    ]
  },
  "guard_patrol_2": {
    "scene": "castle",
    "trigger": {
      "event": "npc_movement_complete",
      "npc": "guard",
      "waypoint": "point_b"
    },
    "actions": [
      {
        "type": "move_npc",
        "npcs": ["guard"],
        "waypoint": "point_c"
      }
    ]
  },
  "guard_patrol_3": {
    "scene": "castle",
    "trigger": {
      "event": "npc_movement_complete",
      "npc": "guard",
      "waypoint": "point_c"
    },
    "actions": [
      {
        "type": "move_npc",
        "npcs": ["guard"],
        "waypoint": "point_a"
      }
    ]
  }
}
```

**What It Does:**

- Creates triangle patrol route (A → B → C → A)
- Each waypoint arrival triggers next movement
- Loops continuously
- Guard appears to patrol the area

## Example 7: Quest Chain

Multi-stage quest with progress tracking.

```json
{
  "quest_start": {
    "scene": "temple",
    "trigger": {
      "event": "npc_interacted",
      "npc": "elder",
      "dialog_level": 0
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Elder",
        "text": ["Bring me the ancient artifact from the ruins."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "advance_dialog",
        "npc": "elder"
      }
    ]
  },
  "quest_reminder": {
    "scene": "temple",
    "trigger": {
      "event": "npc_interacted",
      "npc": "elder",
      "dialog_level": 1
    },
    "actions": [
      {
        "type": "dialog",
        "speaker": "Elder",
        "text": ["Have you found the artifact yet?"]
      }
    ]
  },
  "quest_progress": {
    "scene": "ruins",
    "trigger": {
      "event": "object_interacted",
      "object_name": "ancient_artifact"
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Info",
        "text": ["You found the ancient artifact!"]
      },
      {
        "type": "play_sfx",
        "file": "item_get.wav"
      },
      {
        "type": "emit_particles",
        "particle_type": "sparkles",
        "x": 600,
        "y": 400
      },
      {
        "type": "set_dialog_level",
        "npc": "elder",
        "dialog_level": 2
      }
    ]
  },
  "quest_complete": {
    "scene": "temple",
    "trigger": {
      "event": "npc_interacted",
      "npc": "elder",
      "dialog_level": 2
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Elder",
        "text": ["You found it! Thank you, brave adventurer!"]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "play_sfx",
        "file": "quest_complete.wav"
      },
      {
        "type": "emit_particles",
        "particle_type": "burst",
        "npc": "elder"
      },
      {
        "type": "advance_dialog",
        "npc": "elder"
      }
    ]
  },
  "quest_thanks": {
    "scene": "temple",
    "trigger": {
      "event": "npc_interacted",
      "npc": "elder",
      "dialog_level": 3
    },
    "actions": [
      {
        "type": "dialog",
        "speaker": "Elder",
        "text": ["Thank you again for your help!"]
      }
    ]
  }
}
```

**Quest Flow:**

1. Level 0: Quest given, advances to level 1
2. Level 1: Reminder dialog (repeatable)
3. Finding artifact: Sets level to 2
4. Level 2: Turn in quest, advances to level 3
5. Level 3: Thank you message (repeatable)

## Example 8: Conditional Dialog Branching

Different responses based on whether player has required item.

```json
{
  "talk_with_key": {
    "scene": "castle",
    "trigger": {
      "event": "npc_interacted",
      "npc": "guard",
      "dialog_level": 0
    },
    "conditions": [
      {
        "check": "object_interacted",
        "object": "castle_key",
        "equals": true
      }
    ],
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Guard",
        "text": ["You have the key! You may enter."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "advance_dialog",
        "npc": "guard"
      },
      {
        "type": "reveal_npcs",
        "npcs": ["king"]
      }
    ]
  },
  "talk_without_key": {
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
        "text": ["You need the castle key to enter."]
      }
    ]
  }
}
```

**What It Does:**

- First script checks if player has key
- If yes: Grants entry, reveals king
- If no: Second script runs with rejection message
- Creates gated progression

## Example 9: Tutorial Sequence

Interactive tutorial teaching game mechanics.

```json
{
  "tutorial_start": {
    "scene": "tutorial",
    "trigger": {
      "event": "npc_interacted",
      "npc": "guide"
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Guide",
        "text": ["Welcome! Let me teach you the basics."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "advance_dialog",
        "npc": "guide"
      }
    ]
  },
  "tutorial_inventory": {
    "scene": "tutorial",
    "trigger": {
      "event": "npc_interacted",
      "npc": "guide",
      "dialog_level": 1
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Guide",
        "text": ["Press I to open your inventory."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "wait_for_inventory_access"
      },
      {
        "type": "dialog",
        "speaker": "Guide",
        "text": ["Great! Now you know how to check your items."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "advance_dialog",
        "npc": "guide"
      },
      {
        "type": "play_sfx",
        "file": "success.wav"
      }
    ]
  },
  "tutorial_complete": {
    "scene": "tutorial",
    "trigger": {
      "event": "npc_interacted",
      "npc": "guide",
      "dialog_level": 2
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Guide",
        "text": ["Tutorial complete! Good luck on your adventure!"]
      }
    ]
  }
}
```

**What It Does:**

- Level 0: Welcome message
- Level 1: Asks player to open inventory
- Waits until inventory is opened
- Confirms success with dialog and sound
- Level 2: Completion message

## Example 10: Dramatic Story Event

Complex cutscene with multiple stages.

```json
{
  "betrayal_part1": {
    "scene": "throne_room",
    "trigger": {
      "event": "npc_interacted",
      "npc": "advisor"
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Advisor",
        "text": ["At last, I can reveal my true intentions!"]
      },
      {
        "type": "wait_for_dialog_close"
      }
    ]
  },
  "betrayal_part2": {
    "scene": "throne_room",
    "trigger": {
      "event": "script_complete",
      "script_name": "betrayal_part1"
    },
    "actions": [
      {
        "type": "play_music",
        "file": "betrayal.ogg"
      },
      {
        "type": "start_disappear_animation",
        "npcs": ["king"]
      },
      {
        "type": "emit_particles",
        "particle_type": "burst",
        "npc": "king"
      }
    ]
  },
  "betrayal_part3": {
    "scene": "throne_room",
    "trigger": {
      "event": "npc_disappear_complete",
      "npc": "king"
    },
    "actions": [
      {
        "type": "dialog",
        "speaker": "Advisor",
        "text": ["The king is gone! I now rule this kingdom!"]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "reveal_npcs",
        "npcs": ["dark_knight_1", "dark_knight_2"]
      }
    ]
  }
}
```

**What It Does:**

- Part 1: Advisor reveals betrayal
- Part 2: Music changes, king disappears with effects
- Part 3: After king vanishes, advisor proclaims victory
- Dark knights appear as new threat
- Creates dramatic story moment

## Example 11: Shop Opening Event

Time-gated event that unlocks new NPCs.

```json
{
  "market_opens": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "elder",
      "dialog_level": 5
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Elder",
        "text": ["Thanks to your help, the market can now open!"]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "reveal_npcs",
        "npcs": ["merchant_1", "merchant_2", "merchant_3"]
      },
      {
        "type": "play_sfx",
        "file": "celebration.wav"
      },
      {
        "type": "emit_particles",
        "particle_type": "hearts",
        "npc": "elder"
      },
      {
        "type": "advance_dialog",
        "npc": "elder"
      }
    ]
  }
}
```

**What It Does:**

- Unlocks after multiple conversations with elder (level 5)
- Spawns three new merchant NPCs
- Plays celebration sound
- Shows hearts on elder
- Advances elder's dialog

## Example 12: Ghost NPC Interaction

Special NPC that can be walked through.

```json
{
  "meet_ghost": {
    "scene": "graveyard",
    "trigger": {
      "event": "npc_interacted",
      "npc": "ghost"
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Ghost",
        "text": ["I am but a spirit now...", "Walk through me if you must."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "remove_npc_from_walls",
        "npcs": ["ghost"]
      },
      {
        "type": "emit_particles",
        "particle_type": "sparkles",
        "npc": "ghost"
      }
    ]
  },
  "ghost_vanish": {
    "scene": "graveyard",
    "trigger": {
      "event": "object_interacted",
      "object_name": "tombstone"
    },
    "run_once": true,
    "actions": [
      {
        "type": "start_disappear_animation",
        "npcs": ["ghost"]
      },
      {
        "type": "play_sfx",
        "file": "ghost_vanish.wav"
      }
    ]
  }
}
```

**What It Does:**

- Ghost introduces itself
- Removes collision so player can walk through
- Adds ethereal sparkle effect
- Second script makes ghost vanish when tombstone is examined

## Tips for Using These Examples

### Customization

All examples can be customized by changing:

- NPC names
- Object names
- Scene names
- Dialog text
- Audio files
- Particle effects
- Waypoint names

### Combining Examples

Mix and match patterns:

- Quest chain + Conditional branching
- Boss encounter + Multi-NPC choreography
- Patrol route + Dialog on waypoint arrival

### Testing

Always test your scripts:

1. Does it trigger correctly?
2. Do NPCs move to right places?
3. Is dialog timing good?
4. Do audio and effects play?
5. Does run_once work as expected?

## Next Steps

- Adapt these examples to your game
- Learn more in [Advanced Patterns](advanced.md)
- Understand the details in [Actions](actions.md)
- Review triggers in [Events](events.md)
