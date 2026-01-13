# Advanced Patterns

This guide covers advanced scripting techniques for creating complex gameplay sequences, quest chains, and dynamic NPC behaviors.

## Sequential Cutscenes

Chain multiple scripts using `script_complete` to create multi-part cutscenes.

```json
{
  "cutscene_part1": {
    "scene": "temple",
    "trigger": {
      "event": "npc_interacted",
      "npc": "elder"
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Elder",
        "text": ["Behold the ancient altar!"]
      },
      {
        "type": "wait_for_dialog_close"
      }
    ]
  },
  "cutscene_part2": {
    "scene": "temple",
    "trigger": {
      "event": "script_complete",
      "script_name": "cutscene_part1"
    },
    "actions": [
      {
        "type": "move_npc",
        "npcs": ["elder"],
        "waypoint": "altar"
      },
      {
        "type": "wait_for_movement",
        "npc": "elder"
      },
      {
        "type": "reveal_npcs",
        "npcs": ["spirit"]
      }
    ]
  },
  "cutscene_part3": {
    "scene": "temple",
    "trigger": {
      "event": "script_complete",
      "script_name": "cutscene_part2"
    },
    "actions": [
      {
        "type": "dialog",
        "speaker": "Spirit",
        "text": ["I have been summoned..."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "play_music",
        "file": "mysterious.ogg"
      }
    ]
  }
}
```

**Key Techniques:**

- Each part triggers when the previous completes
- Use `run_once` on the first script to prevent replaying the sequence
- Break long sequences into manageable chunks
- Each part can have different timing and actions

## Conditional Progression

Create branching paths based on player actions and game state.

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

**Key Techniques:**

- First script has conditions, second is fallback
- Both trigger on same event
- First script changes dialog level to prevent future triggers
- Creates "gated" progression requiring specific actions

## NPC Patrol Routes

Create looping movement patterns for guards, merchants, or other NPCs.

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

**Key Techniques:**

- Each waypoint arrival triggers next movement
- Forms a continuous loop
- Add delays or dialog at specific waypoints
- Can have multiple NPCs with different routes

**Enhanced Version with Pauses:**

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
        "type": "dialog",
        "speaker": "Guard",
        "text": ["Hmm, all quiet here..."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "move_npc",
        "npcs": ["guard"],
        "waypoint": "point_b"
      }
    ]
  }
}
```

## Multi-Stage Quests

Track quest progress through dialog levels and object interactions.

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
        "text": ["Bring me the ancient artifact..."]
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
  "quest_progress": {
    "scene": "temple",
    "trigger": {
      "event": "object_interacted",
      "object_name": "ancient_artifact"
    },
    "run_once": true,
    "actions": [
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
        "text": ["You found it! The quest is complete!"]
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
        "x": 400,
        "y": 300
      }
    ]
  }
}
```

**Quest State Tracking:**

- Level 0: Quest not started
- Level 1: Quest given, in progress
- Level 2: Objective completed, ready to turn in

**Key Techniques:**

- Use dialog levels to track quest state
- Object interaction advances quest
- Different scripts for each quest stage
- Audio and visual feedback on completion

## Timed Sequences

Create dramatic timing with coordinated movement, dialog, and effects.

```json
{
  "dramatic_entrance": {
    "scene": "throne_room",
    "trigger": {
      "event": "object_interacted",
      "object_name": "throne"
    },
    "run_once": true,
    "actions": [
      {
        "type": "play_music",
        "file": "ominous.ogg"
      },
      {
        "type": "reveal_npcs",
        "npcs": ["villain"]
      },
      {
        "type": "wait_for_npcs_appear",
        "npcs": ["villain"]
      },
      {
        "type": "move_npc",
        "npcs": ["villain"],
        "waypoint": "throne"
      },
      {
        "type": "wait_for_movement",
        "npc": "villain"
      },
      {
        "type": "dialog",
        "speaker": "Villain",
        "text": ["You dare approach my throne?!"]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "reveal_npcs",
        "npcs": ["minion_1", "minion_2"]
      }
    ]
  }
}
```

**Timing Elements:**

1. Music sets mood immediately
2. Villain appears with animation
3. Wait for appearance to complete
4. Villain walks to throne
5. Wait for movement to complete
6. Dialog plays at dramatic moment
7. Minions appear as reinforcements

## Complex Multi-NPC Choreography

Coordinate multiple NPCs with precise timing.

```json
{
  "council_meeting": {
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
        "text": ["Let me call the council."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "reveal_npcs",
        "npcs": ["guard", "merchant", "healer"]
      },
      {
        "type": "wait_for_npcs_appear",
        "npcs": ["guard", "merchant", "healer"]
      },
      {
        "type": "move_npc",
        "npcs": ["guard"],
        "waypoint": "council_spot_1"
      },
      {
        "type": "move_npc",
        "npcs": ["merchant"],
        "waypoint": "council_spot_2"
      },
      {
        "type": "move_npc",
        "npcs": ["healer"],
        "waypoint": "council_spot_3"
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
        "type": "wait_for_movement",
        "npc": "healer"
      },
      {
        "type": "dialog",
        "speaker": "Elder",
        "text": ["Now that we're all here..."]
      }
    ]
  }
}
```

**Key Techniques:**

- Reveal all NPCs simultaneously
- Wait for all appearances to complete
- Move NPCs to positions (parallel movement)
- Wait for all movements to complete
- Continue with scene dialog

## Dialog-Driven State Machines

Use dialog levels as state machine for complex NPC behaviors.

```json
{
  "blacksmith_state_idle": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "blacksmith",
      "dialog_level": 0
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Blacksmith",
        "text": ["I need iron ore to work."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "advance_dialog",
        "npc": "blacksmith"
      }
    ]
  },
  "blacksmith_state_waiting": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "blacksmith",
      "dialog_level": 1
    },
    "actions": [
      {
        "type": "dialog",
        "speaker": "Blacksmith",
        "text": ["Have you found the iron ore yet?"]
      }
    ]
  },
  "blacksmith_receive_ore": {
    "scene": "village",
    "trigger": {
      "event": "object_interacted",
      "object_name": "iron_ore"
    },
    "run_once": true,
    "actions": [
      {
        "type": "set_dialog_level",
        "npc": "blacksmith",
        "dialog_level": 2
      }
    ]
  },
  "blacksmith_state_working": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "blacksmith",
      "dialog_level": 2
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Blacksmith",
        "text": ["Excellent! Let me forge this into a sword."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "play_sfx",
        "file": "hammer.wav"
      },
      {
        "type": "advance_dialog",
        "npc": "blacksmith"
      }
    ]
  },
  "blacksmith_state_complete": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "blacksmith",
      "dialog_level": 3
    },
    "actions": [
      {
        "type": "dialog",
        "speaker": "Blacksmith",
        "text": ["Your sword is ready!"]
      }
    ]
  }
}
```

**States:**

- 0: Initial - needs ore
- 1: Waiting - player searching for ore
- 2: Working - received ore, forging
- 3: Complete - sword ready

## Dynamic Scene Population

Reveal NPCs based on quest progress or conditions.

```json
{
  "populate_market": {
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
        "text": ["The market is now open!"]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "reveal_npcs",
        "npcs": ["merchant_1", "merchant_2", "merchant_3", "buyer_1", "buyer_2"]
      }
    ]
  }
}
```

## Tutorial Sequences

Guide players through game mechanics interactively.

```json
{
  "tutorial_movement": {
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
        "text": ["Use WASD to move around."]
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
        "text": ["Great job! Tutorial complete."]
      },
      {
        "type": "wait_for_dialog_close"
      },
      {
        "type": "advance_dialog",
        "npc": "guide"
      }
    ]
  }
}
```

## Best Practices for Advanced Scripts

### 1. Plan Your State Machine

Draw out dialog levels and transitions before scripting:

```text
Level 0: First meeting → Level 1
Level 1: Quest given → (on item found) → Level 2
Level 2: Quest complete → Level 3
Level 3: Repeating thank you dialog
```

### 2. Use Meaningful Names

```json
// Bad
{"cutscene_1": {...}}

// Good
{"throne_room_villain_entrance": {...}}
```

### 3. Break Complex Sequences

Split into 3-5 scripts maximum per sequence:

```json
// Instead of one 30-action script:
"intro_part1", "intro_part2", "intro_part3"
```

### 4. Test Edge Cases

- What if player walks away during cutscene?
- What if NPC can't reach waypoint?
- What if player triggers same script twice?

### 5. Add Audio and Visual Feedback

Every major action should have:

- Sound effect
- Particle effect (optional)
- Dialog confirmation

### 6. Document State Machines

```json
{
  "quest_state_0": {
    // STATE 0: Quest not started
    // TRANSITION: Player talks to quest giver → STATE 1
    "trigger": {...}
  }
}
```

### 7. Use Consistent Naming Conventions

```text
{npc_name}_{action}_{state}
quest_{quest_name}_{stage}
cutscene_{scene}_{part}
```

## Performance Considerations

### Avoid Infinite Loops

```json
// Bad - Creates infinite loop
{
  "bad_script_1": {
    "trigger": {
      "event": "script_complete",
      "script_name": "bad_script_2"
    },
    "actions": [...]
  },
  "bad_script_2": {
    "trigger": {
      "event": "script_complete",
      "script_name": "bad_script_1"
    },
    "actions": [...]
  }
}
```

### Limit Concurrent Scripts

- Don't trigger too many scripts simultaneously
- Use `wait_for_*` actions to sequence properly
- Consider performance with many NPCs moving

### Clean Up After Cutscenes

Remove NPCs that are no longer needed:

```json
{
  "actions": [
    {
      "type": "start_disappear_animation",
      "npcs": ["temporary_npc"]
    }
  ]
}
```

## Next Steps

- Browse [Examples](examples.md) for complete implementations
- Review [Actions](actions.md) for all available commands
- Study [Events](events.md) for trigger options
