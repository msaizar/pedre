# Scripting System

Arcade Tiled RPG uses a powerful JSON-based scripting system for creating cutscenes, interactive sequences, and event-driven gameplay. Scripts enable you to create rich, interactive storytelling experiences without writing code.

## What Can You Do With Scripts?

Scripts let you:

- Create interactive conversations with NPCs
- Build cinematic cutscenes with movement and timing
- Design multi-stage quests and storylines
- Trigger sound effects and music
- Show particle effects and visual feedback
- Control NPC behavior and pathfinding
- Create conditional gameplay based on player actions

## Quick Example

Here's a simple script that shows a greeting when the player talks to a merchant:

```json
{
  "greet_merchant": {
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
        "text": ["Welcome to my shop!"]
      },
      {
        "type": "play_sfx",
        "file": "greeting.wav"
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

This script:

1. Triggers when the player interacts with the merchant
2. Shows a dialog message
3. Plays a greeting sound
4. Displays heart particles above the merchant
5. Only runs once

## How Scripts Work

A script is a JSON object that defines:

1. **When** to trigger (event type)
2. **If** it should run (conditions)
3. **What** to do (action sequence)

Scripts are organized by scene/map and automatically loaded when a scene starts.

## Learn More

- **[Script Basics](basics.md)** - Learn script structure, file organization, and core concepts
- **[Event Types](events.md)** - Understand all available triggers for your scripts
- **[Conditions](conditions.md)** - Control when scripts run with conditional logic
- **[Actions](actions.md)** - Explore all available actions for creating gameplay
- **[Advanced Patterns](advanced.md)** - Master complex techniques like cutscenes and quest chains
- **[Examples](examples.md)** - Browse a cookbook of complete script examples

## File Organization

Scripts are stored in the `assets/scripts/` directory, organized by scene:

```text
assets/scripts/
  ├── village_scripts.json
  ├── forest_scripts.json
  └── castle_scripts.json
```

Each file contains multiple scripts related to that specific scene or map.
