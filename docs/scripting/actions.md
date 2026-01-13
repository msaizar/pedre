# Actions

Actions are the commands executed when a script runs. This guide covers all available action types and how to use them.

## Overview

Actions are defined in the `actions` array of a script. They execute sequentially in the order specified.

```json
{
  "actions": [
    {
      "type": "dialog",
      "speaker": "Merchant",
      "text": ["Hello!"]
    },
    {
      "type": "play_sfx",
      "file": "greeting.wav"
    }
  ]
}
```

## Dialog Actions

### dialog

Display dialog with a speaker and text.

**Parameters:**

- `speaker` (string) - Speaker name to display
- `text` (array of strings) - Dialog text pages

**Example:**

```json
{
  "type": "dialog",
  "speaker": "Merchant",
  "text": ["Welcome!", "Take a look around."]
}
```

**Details:**

- Each string in the `text` array is a separate page
- Player presses a key to advance to next page
- Dialog window automatically sizes to fit text

**Use Cases:**

- NPC conversations
- Story narration
- Tutorial messages
- Quest instructions

### advance_dialog

Increment an NPC's dialog level by 1.

**Parameters:**

- `npc` (string) - NPC identifier

**Example:**

```json
{
  "type": "advance_dialog",
  "npc": "merchant"
}
```

**Details:**

- Dialog level tracks conversation progress
- Use after first-time conversations
- Enables different dialog on next interaction

**Use Cases:**

- Progressing conversations
- Quest state tracking
- Unlocking new dialog options

### set_dialog_level

Set an NPC's conversation progress to a specific level.

**Parameters:**

- `npc` (string) - NPC identifier
- `dialog_level` (int) - New dialog level

**Example:**

```json
{
  "type": "set_dialog_level",
  "npc": "merchant",
  "dialog_level": 2
}
```

**Details:**

- Jump to any dialog level directly
- Useful for quest completion
- Can skip or reset conversation states

**Use Cases:**

- Completing quest stages
- Resetting conversations
- Conditional dialog branching

## NPC Actions

### move_npc

Move NPC(s) to a waypoint using pathfinding.

**Parameters:**

- `npcs` (array of strings) - List of NPC identifiers
- `waypoint` (string) - Waypoint name from Tiled map

**Example:**

```json
{
  "type": "move_npc",
  "npcs": ["merchant"],
  "waypoint": "well"
}
```

**Details:**

- NPCs use A* pathfinding to reach waypoint
- Waypoints must be defined in your Tiled map
- NPCs walk around obstacles automatically
- Triggers `npc_movement_complete` event when done

**Use Cases:**

- Cutscene choreography
- NPC patrol routes
- Dynamic positioning
- Timed sequences

### reveal_npcs

Make NPCs visible with appear animation and particle effects.

**Parameters:**

- `npcs` (array of strings) - List of NPC identifiers

**Example:**

```json
{
  "type": "reveal_npcs",
  "npcs": ["guard", "captain", "merchant"]
}
```

**Details:**

- NPCs fade in over time
- Plays sparkle particle effect
- Use for dramatic entrances
- Triggers `npc_appear_complete` event when done

**Use Cases:**

- Spawning NPCs mid-scene
- Dramatic reveals
- Cutscene sequences
- Quest completion rewards

### start_disappear_animation

Play disappear animation for NPC(s).

**Parameters:**

- `npcs` (array of strings) - List of NPC identifiers

**Example:**

```json
{
  "type": "start_disappear_animation",
  "npcs": ["ghost"]
}
```

**Details:**

- NPCs fade out over time
- Can trigger particle effects
- Triggers `npc_disappear_complete` event when done
- NPC still exists until animation completes

**Use Cases:**

- Dramatic exits
- Quest completion
- Teleportation effects
- Death or transformation scenes

### remove_npc_from_walls

Remove NPC collision (allows player to walk through).

**Parameters:**

- `npcs` (array of strings) - List of NPC identifiers

**Example:**

```json
{
  "type": "remove_npc_from_walls",
  "npcs": ["ghost"]
}
```

**Details:**

- Removes NPC from collision detection
- Player can walk through the NPC
- Useful for ghosts, spirits, or non-solid entities

**Use Cases:**

- Ghost NPCs
- Background characters
- Non-interactive NPCs
- Special effects

### set_current_npc

Set the current context NPC (for dialog event attribution).

**Parameters:**

- `npc` (string) - NPC identifier

**Example:**

```json
{
  "type": "set_current_npc",
  "npc": "merchant"
}
```

**Details:**

- Sets which NPC is considered "active" for dialog events
- Affects dialog_closed event attribution
- Rarely needed in most scripts

**Use Cases:**

- Complex multi-NPC dialog sequences
- Switching conversation context
- Advanced cutscene control

## Audio Actions

### play_sfx

Play a sound effect.

**Parameters:**

- `file` (string) - Sound filename (relative to `assets/audio/sfx/`)

**Example:**

```json
{
  "type": "play_sfx",
  "file": "door_open.wav"
}
```

**Details:**

- Plays immediately
- Does not loop
- Supports WAV, OGG, MP3 formats
- Volume controlled by game settings

**Use Cases:**

- Item pickups
- Door sounds
- Footsteps
- UI feedback
- Environmental effects

### play_music

Play background music.

**Parameters:**

- `file` (string) - Music filename (relative to `assets/audio/music/`)
- `loop` (boolean, optional) - Whether to loop the music (default: true)
- `volume` (float, optional) - Volume level 0.0-1.0 (default: 0.8)

**Example:**

```json
{
  "type": "play_music",
  "file": "village_theme.ogg",
  "loop": true,
  "volume": 0.8
}
```

**Details:**

- Fades out previous music
- Fades in new music
- Best format: OGG Vorbis for file size
- Music controlled by game settings

**Use Cases:**

- Scene transitions
- Boss battles
- Emotional moments
- Atmosphere changes

## Visual Actions

### emit_particles

Spawn particle effects at a location or on an NPC.

**Option 1 - At Coordinates:**

**Parameters:**

- `x` (float) - X coordinate
- `y` (float) - Y coordinate
- `particle_type` (string) - Effect type: "hearts", "sparkles", or "burst"

**Example:**

```json
{
  "type": "emit_particles",
  "particle_type": "sparkles",
  "x": 400,
  "y": 300
}
```

**Option 2 - On NPC:**

**Parameters:**

- `npc` (string) - NPC identifier
- `particle_type` (string) - Effect type: "hearts", "sparkles", or "burst"

**Example:**

```json
{
  "type": "emit_particles",
  "particle_type": "hearts",
  "npc": "merchant"
}
```

**Particle Types:**

- `"hearts"` - Pink heart particles floating up (affection, happiness)
- `"sparkles"` - Glittering golden particles (magic, discovery)
- `"burst"` - Explosive outward particles (impact, emphasis)

**Use Cases:**

- Item discoveries
- NPC reactions
- Quest completion
- Magic effects
- Emotional moments

## Wait Actions

Wait actions pause script execution until a condition is met. This allows for timing and sequencing.

### wait_for_dialog_close

Pause script execution until dialog is closed.

**Parameters:** None

**Example:**

```json
{
  "type": "wait_for_dialog_close"
}
```

**Use Case:**

```json
{
  "actions": [
    {
      "type": "dialog",
      "speaker": "Merchant",
      "text": ["Welcome!"]
    },
    {
      "type": "wait_for_dialog_close"
    },
    {
      "type": "move_npc",
      "npcs": ["merchant"],
      "waypoint": "shop"
    }
  ]
}
```

**When to Use:**

- After showing dialog before next action
- Sequencing cutscenes
- Waiting for player acknowledgment

### wait_for_movement

Pause until an NPC reaches their destination.

**Parameters:**

- `npc` (string) - NPC identifier

**Example:**

```json
{
  "type": "wait_for_movement",
  "npc": "merchant"
}
```

**Use Case:**

```json
{
  "actions": [
    {
      "type": "move_npc",
      "npcs": ["guard"],
      "waypoint": "gate"
    },
    {
      "type": "wait_for_movement",
      "npc": "guard"
    },
    {
      "type": "dialog",
      "speaker": "Guard",
      "text": ["I've reached the gate."]
    }
  ]
}
```

**When to Use:**

- Choreographing NPC movement
- Timing dialog after movement
- Coordinating multiple NPCs

### wait_for_npcs_appear

Pause until NPCs finish their appear animation.

**Parameters:**

- `npcs` (array of strings) - List of NPC identifiers

**Example:**

```json
{
  "type": "wait_for_npcs_appear",
  "npcs": ["guard", "captain"]
}
```

**Use Case:**

```json
{
  "actions": [
    {
      "type": "reveal_npcs",
      "npcs": ["villain"]
    },
    {
      "type": "wait_for_npcs_appear",
      "npcs": ["villain"]
    },
    {
      "type": "dialog",
      "speaker": "Villain",
      "text": ["Surprise!"]
    }
  ]
}
```

**When to Use:**

- After revealing NPCs
- Timing dramatic entrances
- Coordinating appearance effects

### wait_for_inventory_access

Pause until the inventory screen is opened.

**Parameters:** None

**Example:**

```json
{
  "type": "wait_for_inventory_access"
}
```

**Use Case:**

```json
{
  "actions": [
    {
      "type": "dialog",
      "speaker": "Tutorial",
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
      "speaker": "Tutorial",
      "text": ["Great! You opened your inventory!"]
    }
  ]
}
```

**When to Use:**

- Tutorial sequences
- Waiting for player actions
- Interactive teaching moments

## Action Sequencing

Actions execute in order. Use wait actions to control timing:

```json
{
  "actions": [
    // 1. Show dialog
    {
      "type": "dialog",
      "speaker": "Elder",
      "text": ["Watch this!"]
    },
    // 2. Wait for player to close dialog
    {
      "type": "wait_for_dialog_close"
    },
    // 3. Reveal NPC
    {
      "type": "reveal_npcs",
      "npcs": ["spirit"]
    },
    // 4. Wait for appear animation
    {
      "type": "wait_for_npcs_appear",
      "npcs": ["spirit"]
    },
    // 5. Move NPC
    {
      "type": "move_npc",
      "npcs": ["spirit"],
      "waypoint": "altar"
    },
    // 6. Wait for movement
    {
      "type": "wait_for_movement",
      "npc": "spirit"
    },
    // 7. Final dialog
    {
      "type": "dialog",
      "speaker": "Spirit",
      "text": ["I have arrived."]
    }
  ]
}
```

## Best Practices

### 1. Always Wait After Dialog

```json
{
  "actions": [
    {
      "type": "dialog",
      "speaker": "Merchant",
      "text": ["Hello!"]
    },
    {
      "type": "wait_for_dialog_close"  // Always include this
    },
    {
      "type": "advance_dialog",
      "npc": "merchant"
    }
  ]
}
```

### 2. Add Audio Feedback

```json
{
  "actions": [
    {
      "type": "dialog",
      "speaker": "Info",
      "text": ["You found a key!"]
    },
    {
      "type": "play_sfx",
      "file": "item_get.wav"  // Audio cue
    },
    {
      "type": "emit_particles",
      "particle_type": "sparkles",  // Visual cue
      "x": 400,
      "y": 300
    }
  ]
}
```

### 3. Use Descriptive File Names

```json
// Bad
{"file": "sound1.wav"}

// Good
{"file": "chest_open.wav"}
```

### 4. Coordinate Multiple NPCs

```json
{
  "actions": [
    // Move both NPCs simultaneously
    {
      "type": "move_npc",
      "npcs": ["guard"],
      "waypoint": "left"
    },
    {
      "type": "move_npc",
      "npcs": ["merchant"],
      "waypoint": "right"
    },
    // Wait for both to finish
    {
      "type": "wait_for_movement",
      "npc": "guard"
    },
    {
      "type": "wait_for_movement",
      "npc": "merchant"
    },
    // Continue...
  ]
}
```

### 5. Match Particles to Mood

```json
// Happy moment
{"particle_type": "hearts", "npc": "lover"}

// Discovery
{"particle_type": "sparkles", "x": 400, "y": 300}

// Impact
{"particle_type": "burst", "x": 500, "y": 400}
```

## Common Action Patterns

### Item Pickup

```json
{
  "actions": [
    {
      "type": "play_sfx",
      "file": "item_get.wav"
    },
    {
      "type": "dialog",
      "speaker": "Info",
      "text": ["You found a Silver Key!"]
    },
    {
      "type": "emit_particles",
      "particle_type": "sparkles",
      "x": 500,
      "y": 400
    }
  ]
}
```

### First Meeting

```json
{
  "actions": [
    {
      "type": "dialog",
      "speaker": "Merchant",
      "text": ["Hello, traveler!"]
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
```

### Dramatic Entrance

```json
{
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
      "type": "dialog",
      "speaker": "Villain",
      "text": ["You dare approach?!"]
    }
  ]
}
```

## Next Steps

- See [Advanced Patterns](advanced.md) for complex action sequences
- Browse [Examples](examples.md) for complete script examples
- Learn about [Events](events.md) to understand what triggers actions
