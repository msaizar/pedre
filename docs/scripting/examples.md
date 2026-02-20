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
        "name": "dialog",
        "speaker": "Merchant",
        "text": ["Hello, traveler! Welcome to my shop."]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "advance_dialog",
        "npc": "merchant"
      },
      {
        "name": "play_sfx",
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
        "name": "play_sfx",
        "file": "chest_open.wav"
      },
      {
        "name": "dialog",
        "speaker": "Info",
        "text": ["You found the Golden Key!"]
      },
      {
        "name": "emit_particles",
        "particle_type": "sparkles",
        "interactive_object": "golden_chest"
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
        "name": "dialog",
        "speaker": "Elder",
        "text": ["Let me call the others."]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "start_appear_animation",
        "npcs": ["guard", "merchant"]
      },
      {
        "name": "wait_for_npcs_appear",
        "npcs": ["guard", "merchant"]
      },
      {
        "name": "move_npc",
        "npcs": ["guard"],
        "waypoint": "meeting_spot"
      },
      {
        "name": "move_npc",
        "npcs": ["merchant"],
        "waypoint": "meeting_spot"
      },
      {
        "name": "wait_for_movement",
        "npc": "guard"
      },
      {
        "name": "wait_for_movement",
        "npc": "merchant"
      },
      {
        "name": "dialog",
        "speaker": "Guard",
        "text": ["You called, Elder?"]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "dialog",
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
        "name": "dialog",
        "speaker": "Info",
        "text": ["The altar glows with ancient power..."]
      },
      {
        "name": "play_sfx",
        "file": "magic_glow.wav"
      },
      {
        "name": "emit_particles",
        "particle_type": "sparkles",
        "interactive_object": "altar"
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
        "name": "play_music",
        "file": "boss_theme.ogg"
      },
      {
        "name": "emit_particles",
        "particle_type": "burst",
        "interactive_object": "altar"
      },
      {
        "name": "start_appear_animation",
        "npcs": ["boss"]
      },
      {
        "name": "wait_for_npcs_appear",
        "npcs": ["boss"]
      },
      {
        "name": "dialog",
        "speaker": "Boss",
        "text": ["You dare disturb my slumber?!"]
      },
      {
        "name": "wait_for_dialog_close"
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
        "name": "move_npc",
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
        "name": "move_npc",
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
        "name": "move_npc",
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
        "name": "dialog",
        "speaker": "Elder",
        "text": ["Bring me the ancient artifact from the ruins."]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "advance_dialog",
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
        "name": "dialog",
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
        "name": "dialog",
        "speaker": "Info",
        "text": ["You found the ancient artifact!"]
      },
      {
        "name": "play_sfx",
        "file": "item_get.wav"
      },
      {
        "name": "emit_particles",
        "particle_type": "sparkles",
        "interactive_object": "ancient_artifact"
      },
      {
        "name": "set_dialog_level",
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
        "name": "dialog",
        "speaker": "Elder",
        "text": ["You found it! Thank you, brave adventurer!"]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "play_sfx",
        "file": "quest_complete.wav"
      },
      {
        "name": "emit_particles",
        "particle_type": "burst",
        "npc": "elder"
      },
      {
        "name": "advance_dialog",
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
        "name": "dialog",
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
        "name": "object_interacted",
        "object": "castle_key",
        "equals": true
      }
    ],
    "run_once": true,
    "actions": [
      {
        "name": "dialog",
        "speaker": "Guard",
        "text": ["You have the key! You may enter."]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "advance_dialog",
        "npc": "guard"
      },
      {
        "name": "start_appear_animation",
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
        "name": "dialog",
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
        "name": "dialog",
        "speaker": "Guide",
        "text": ["Welcome! Let me teach you the basics."]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "advance_dialog",
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
        "name": "dialog",
        "speaker": "Guide",
        "text": ["Press I to open your inventory."]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "wait_for_inventory_access"
      },
      {
        "name": "dialog",
        "speaker": "Guide",
        "text": ["Great! Now you know how to check your items."]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "advance_dialog",
        "npc": "guide"
      },
      {
        "name": "play_sfx",
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
        "name": "dialog",
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
        "name": "dialog",
        "speaker": "Advisor",
        "text": ["At last, I can reveal my true intentions!"]
      },
      {
        "name": "wait_for_dialog_close"
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
        "name": "play_music",
        "file": "betrayal.ogg"
      },
      {
        "name": "start_disappear_animation",
        "npcs": ["king"]
      },
      {
        "name": "emit_particles",
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
        "name": "dialog",
        "speaker": "Advisor",
        "text": ["The king is gone! I now rule this kingdom!"]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "start_appear_animation",
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
        "name": "dialog",
        "speaker": "Elder",
        "text": ["Thanks to your help, the market can now open!"]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "start_appear_animation",
        "npcs": ["merchant_1", "merchant_2", "merchant_3"]
      },
      {
        "name": "play_sfx",
        "file": "celebration.wav"
      },
      {
        "name": "emit_particles",
        "particle_type": "hearts",
        "npc": "elder"
      },
      {
        "name": "advance_dialog",
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

Ghost NPC that vanishes after interaction.

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
        "name": "dialog",
        "speaker": "Ghost",
        "text": ["I am but a spirit now...", "Farewell, mortal..."]
      },
      {
        "name": "wait_for_dialog_close"
      },
      {
        "name": "emit_particles",
        "particle_type": "sparkles",
        "npc": "ghost"
      },
      {
        "name": "start_disappear_animation",
        "npcs": ["ghost"]
      },
      {
        "name": "play_sfx",
        "file": "ghost_vanish.wav"
      }
    ]
  }
}
```

**What It Does:**

- Ghost introduces itself
- Adds ethereal sparkle effect
- Ghost fades away with disappear animation
- Collision is automatically removed when animation completes

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
