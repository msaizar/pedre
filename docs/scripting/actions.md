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
- `instant` (boolean, optional) - If true, text appears immediately without letter-by-letter reveal (default: false)
- `auto_close` (boolean, optional) - If true, dialog automatically closes after configured duration (default: false)

**Example:**

```json
{
  "type": "dialog",
  "speaker": "Merchant",
  "text": ["Welcome!", "Take a look around."]
}
```

**With auto-close for cutscenes:**

```json
{
  "type": "dialog",
  "speaker": "Narrator",
  "text": ["The story begins..."],
  "auto_close": true
}
```

**Details:**

- Each string in the `text` array is a separate page
- When `auto_close` is false (default), player presses a key to advance to next page
- When `auto_close` is true, dialog automatically advances and closes after the configured duration (see `DIALOG_AUTO_CLOSE_DURATION` in `settings.py`)
- The auto-close timer starts after text is fully revealed
- Dialog window automatically sizes to fit text

**Use Cases:**

- NPC conversations (manual advance)
- Story narration (auto-close for cutscenes)
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

Make NPCs visible with appear animation.

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

- Makes sprite.visible = True
- Starts appear animation for AnimatedNPCs
- Adds NPCs to collision wall list
- Use for dramatic entrances
- Publishes `NPCAppearCompleteEvent` when animation done

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

- Starts disappear animation for AnimatedNPCs
- Waits for all animations to complete before finishing
- Publishes `NPCDisappearCompleteEvent` when animation done
- Automatically removes NPCs from collision walls when animation completes
- Only AnimatedNPC sprites have disappear animations

**Use Cases:**

- Dramatic exits
- Quest completion
- Teleportation effects
- Death or transformation scenes

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

## Scene Actions

### change_scene

Transition to a different map/scene with fade effects.

**Parameters:**

- `target_map` (string) - Destination map filename (relative to assets/maps/)
- `spawn_waypoint` (string, optional) - Waypoint name in destination map where player spawns

**Example:**

```json
{
  "type": "change_scene",
  "target_map": "forest.tmx",
  "spawn_waypoint": "from_village"
}
```

**Details:**

- Triggers a scene transition with fade out/in effects
- Player spawns at the specified waypoint in the target map
- If `spawn_waypoint` is not specified, uses the target map's default spawn point
- Typically used in response to `portal_entered` events

**Use Cases:**

- Portal transitions
- Story-driven map changes
- Conditional area access
- Cutscenes that end with map transition

**Portal Script Example:**

```json
{
  "forest_portal": {
    "trigger": {"event": "portal_entered", "portal": "to_forest"},
    "actions": [
      {"type": "change_scene", "target_map": "forest.tmx", "spawn_waypoint": "entrance"}
    ]
  }
}
```

**Cutscene with Transition:**

```json
{
  "dungeon_entrance": {
    "trigger": {"event": "portal_entered", "portal": "dungeon_gate"},
    "run_once": true,
    "actions": [
      {"type": "dialog", "speaker": "Narrator", "text": ["A cold wind blows..."]},
      {"type": "wait_for_dialog_close"},
      {"type": "play_sfx", "file": "wind.wav"},
      {"type": "change_scene", "target_map": "dungeon.tmx", "spawn_waypoint": "entrance"}
    ]
  }
}
```

## Visual Actions

### emit_particles

Spawn particle effects at an NPC, player, or interactive object location.

**Parameters:**

- `particle_type` (string) - Effect type: "hearts", "sparkles", "burst", or "trail"
- **Exactly one of:**
  - `npc` (string) - NPC identifier
  - `player` (boolean) - Set to true for player location
  - `interactive_object` (string) - Interactive object name
- `color` (array[int, int, int], optional) - RGB color tuple to override default color

**Option 1 - At NPC Location:**

```json
{
  "type": "emit_particles",
  "particle_type": "hearts",
  "npc": "merchant"
}
```

**Option 2 - At Player Location:**

```json
{
  "type": "emit_particles",
  "particle_type": "sparkles",
  "player": true
}
```

**Option 3 - At Interactive Object Location:**

```json
{
  "type": "emit_particles",
  "particle_type": "burst",
  "interactive_object": "treasure_chest"
}
```

**Option 4 - With Custom Color:**

```json
{
  "type": "emit_particles",
  "particle_type": "hearts",
  "npc": "yema",
  "color": [255, 0, 0]
}
```

**Particle Types:**

- `"hearts"` - Pink heart particles floating up (affection, happiness)
  - Default color: (255, 105, 180) - hot pink
  - Configurable via `PARTICLE_COLOR_HEARTS`
- `"sparkles"` - Glittering yellow particles (magic, discovery)
  - Default color: (255, 255, 100) - yellow
  - Configurable via `PARTICLE_COLOR_SPARKLES`
- `"burst"` - Explosive orange particles (impact, emphasis)
  - Default color: (255, 200, 0) - orange
  - Configurable via `PARTICLE_COLOR_BURST`
- `"trail"` - Subtle blue trail particles (movement)
  - Default color: (200, 200, 255) - light blue
  - Configurable via `PARTICLE_COLOR_TRAIL`

**Details:**

- Default colors can be changed globally in `settings.py`
- Per-action custom colors override the defaults
- Colors are specified as `[R, G, B]` arrays with values 0-255

**Use Cases:**

- Item discoveries at chest/object locations
- NPC reactions and emotions
- Player achievement celebrations
- Quest completion effects
- Magic effects at specific objects
- Custom-colored particles for different moods/themes

## Inventory Actions

### acquire_item

Give an item to the player's inventory.

**Parameters:**

- `item_id` (string) - Unique identifier of the item to acquire

**Example:**

```json
{
  "type": "acquire_item",
  "item_id": "rusty_key"
}
```

**In a script after finding a treasure chest:**

```json
{
  "actions": [
    {
      "type": "dialog",
      "speaker": "Narrator",
      "text": ["You found a key!"]
    },
    {
      "type": "acquire_item",
      "item_id": "tower_key"
    },
    {
      "type": "wait_for_dialog_close"
    }
  ]
}
```

**Details:**

- The item must already be defined in the inventory plugin
- Publishes `ItemAcquiredEvent` on success
- Publishes `ItemAcquisitionFailedEvent` on failure
- Returns `False` and blocks script progression if acquisition fails

**Use Cases:**

- Giving items when player finds treasure
- Quest rewards
- Item pickups from objects
- Story progression items

### add_item

Add a new item to the inventory plugin.

**Parameters:**

- `name` (string, required) - Display name of the item
- `description` (string, required) - Description text for the item
- `item_id` (string, optional) - Unique identifier (auto-generates UUID if omitted)
- `image_path` (string, optional) - Path to full-size image
- `icon_path` (string, optional) - Path to icon/thumbnail
- `category` (string, optional) - Item category (default: "general")
- `acquired` (boolean, optional) - Whether item is immediately acquired (default: true)
- `consumable` (boolean, optional) - Whether item can be consumed (default: false)

**Example without item_id (UUID auto-generated):**

```json
{
  "type": "add_item",
  "name": "Health Potion",
  "description": "Restores 50 HP",
  "icon_path": "items/potion.png",
  "category": "potion",
  "consumable": true,
  "acquired": true
}
```

**Example with explicit item_id:**

```json
{
  "type": "add_item",
  "item_id": "rusty_key",
  "name": "Rusty Key",
  "description": "Opens an old door",
  "icon_path": "items/key.png",
  "category": "key",
  "acquired": true
}
```

**Details:**

- Dynamically creates items without requiring JSON definition
- Useful for consumable items obtained through gameplay
- Auto-generates UUID if `item_id` is omitted (prevents conflicts)
- Publishes `ItemAcquiredEvent` if `acquired=true`
- Can fail if inventory is at capacity

**Use Cases:**

- Adding consumable items (potions, food)
- Dynamic loot generation
- Quest items created on the fly
- Multiple instances of same item type

### consume_item

Consume an item from the player's inventory.

**Parameters:**

- `item_id` (string) - Unique identifier of the item to consume

**Example:**

```json
{
  "type": "consume_item",
  "item_id": "health_potion"
}
```

**In a script for using a consumable:**

```json
{
  "actions": [
    {
      "type": "consume_item",
      "item_id": "ancient_key"
    },
    {
      "type": "dialog",
      "speaker": "Narrator",
      "text": ["The key dissolves into dust..."]
    },
    {
      "type": "wait_for_dialog_close"
    }
  ]
}
```

**Details:**

- Item must be acquired and not already consumed
- Publishes `ItemConsumedEvent` when successful
- Action completes immediately regardless of success

**Use Cases:**

- One-time-use keys
- Quest items that get used
- Story progression requirements
- Item-based puzzles

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

### wait_for_npcs_disappear

Pause until NPCs finish their disappear animation.

**Parameters:**

- `npcs` (array of strings) - List of NPC identifiers

**Example:**

```json
{
  "type": "wait_for_npcs_disappear",
  "npcs": ["ghost", "spirit"]
}
```

**Use Case:**

```json
{
  "actions": [
    {
      "type": "start_disappear_animation",
      "npcs": ["ghost"]
    },
    {
      "type": "wait_for_npcs_disappear",
      "npcs": ["ghost"]
    },
    {
      "type": "dialog",
      "speaker": "Narrator",
      "text": ["The ghost has vanished..."]
    }
  ]
}
```

**When to Use:**

- After starting disappear animations
- Timing dramatic exits
- Coordinating disappearance effects
- Before scene transitions

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
      "interactive_object": "treasure_chest"
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
{"particle_type": "sparkles", "player": true}

// Impact
{"particle_type": "burst", "interactive_object": "explosion_point"}
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
      "interactive_object": "item_chest"
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
