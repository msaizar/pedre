# Plugins Reference

This documentation provides detailed information about each plugin in the Pedre framework. Each plugin is responsible for a specific aspect of game functionality and can be used independently or combined to create rich interactive experiences.

## Overview

The Pedre framework follows a plugin-based architecture where each plugin encapsulates specific functionality. Plugins communicate through an event bus for loose coupling and maintainability.

For framework architecture and extension points, see:

- [API Reference](../api/index.md) - Core framework components
- [Extending Pedre](../extending/index.md) - Custom actions, events, conditions, and plugins

## Core Plugins

### [DialogPlugin](dialog.md)

Manages dialog display with multi-page support and pagination. Handles NPC conversations and text-based interactions.

**Key Features:**

- Multi-page dialog support
- Automatic pagination
- Dialog overlay rendering
- Event integration

### [NPCPlugin](npc.md)

Manages NPC state, movement, pathfinding, and interactions. Controls all non-player character behavior and conversations.

**Key Features:**

- NPC registration and tracking
- Dialog level progression
- Pathfinding integration
- JSON-based dialog configuration
- Event-driven interactions

### [PlayerPlugin](player.md)

Manages player spawning, movement, animation, and state. Handles player character lifecycle and input processing.

**Key Features:**

- Player sprite management
- 4-directional animation
- Input-based movement
- Portal-based spawning
- Save/load support

### [ScriptPlugin](script.md)

Event-driven scripting plugin for cutscenes and interactive sequences. Enables complex game logic without code changes.

**Key Features:**

- JSON-based scripting
- Event-triggered actions
- Conditional execution
- Action sequencing
- Script reusability

### [PortalPlugin](portal.md)

Handles map transitions and portal collision detection. Manages seamless movement between different game areas.

**Key Features:**

- Portal registration
- Collision detection
- Conditional portals
- Target positioning

### [InventoryPlugin](inventory.md)

Manages item collection and categorization. Tracks player possessions and supports various item types.

**Key Features:**

- Item storage by category
- Inventory queries
- Item validation
- Category management

## Media & Effects

### [AudioPlugin](audio.md)

Manages background music and sound effects with caching. Provides audio playback and volume control.

**Key Features:**

- Music playback with looping
- Sound effect caching
- Volume control
- Multiple audio format support

### [ParticlePlugin](particle.md)

Visual effects and particle plugins. Creates visual feedback for game events.

**Key Features:**

- Particle emission
- Effect types
- Duration control
- Automatic cleanup

## Development Tools

### [DebugPlugin](debug.md)

Displays development information overlays showing player and NPC positions. Helps with debugging and level design.

**Key Features:**

- Toggle with Shift+D
- Player position display (tile and pixel coordinates)
- NPC position display (tile and pixel coordinates)
- Dialog level tracking
- Minimal performance overhead

## Persistence & State

### [CachePlugin](cache.md)

Manages scene state cache to preserve plugin states when the player transitions between scenes.

**Key Features:**

- In-memory scene state storage
- Automatic state preservation during transitions
- Plugin-agnostic caching interface
- Save/load integration

### [SavePlugin](save.md)

Handles game state persistence with auto-save and manual save slots. Manages game progress across sessions.

**Key Features:**

- Multiple save slots
- JSON-based storage
- Save/load operations
- Auto-save support

## Camera & Movement

### [CameraPlugin](camera.md)

Smooth camera following with optional bounds. Controls viewport positioning and movement.

**Key Features:**

- Sprite following
- Smooth transitions
- Boundary constraints
- Configurable smoothing

### [PhysicsPlugin](physics.md)

Collision detection and physics simulation for the player sprite.

**Key Features:**

- Arcade physics engine integration
- Player-wall collision handling
- Automatic engine recreation
- Scene transition support

### [ScenePlugin](scene.md)

Manages map loading and scene transitions. Handles the lifecycle of Tiled maps and connects game plugins to the current level.

**Key Features:**

- Map loading (.tmx)
- Smooth visual transitions (fade in/out)
- Waypoint spawning
- Collision layer extraction

### [PathfindingPlugin](pathfinding.md)

A* pathfinding for NPC navigation. Enables intelligent movement around obstacles.

**Key Features:**

- A* algorithm
- Grid-based navigation
- Collision avoidance
- Waypoint generation

### [WaypointPlugin](waypoint.md)

Named position management for navigation and spawning. Stores map locations used by NPCs and portals.

**Key Features:**

- Named position storage
- Portal destination tracking
- NPC movement targets
- Tiled map integration

## UI & Menus

### [PauseMenuPlugin](pause-menu.md)

Provides an in-game pause menu overlay with save/load functionality. Appears when ESC is pressed.

**Key Features:**

- In-game overlay menu
- Save/load slot selection
- New game confirmation
- Responsive UI scaling
- Customizable appearance

## Interaction & Input

### [InteractionPlugin](interaction.md)

Manages interactive objects that players can interact with. Handles object-based interactions.

**Key Features:**

- Object registration
- Proximity detection
- Multiple interaction types
- Property-based configuration

### [InputPlugin](input.md)

Keyboard input handling and movement vector calculation. Processes player input.

**Key Features:**

- Key state tracking
- Movement vector calculation
- Action mapping
- Normalized input

## Best Practices

### Event-Driven Design

Prefer events over direct plugin calls:

```python
# Good: Event-driven
def close_dialog():
    dialog_plugin.close()
    event_bus.publish(DialogClosedEvent(npc_name="merchant"))
    # ScriptPlugin handles the rest

# Avoid: Direct coupling
def close_dialog():
    dialog_plugin.close()
    npc_plugin.increment_level("merchant")
```

### Update Order

Call plugin updates in the correct order:

```python
def on_update(self, delta_time):
    # 1. Input
    dx, dy = self.input_plugin.get_movement_vector()

    # 2. Physics
    self.player.update_physics(dx, dy, delta_time)

    # 3. NPCs
    self.npc_plugin.update(delta_time)

    # 4. Scripts
    self.script_plugin.update(delta_time, self.game_context)

    # 5. Particles
    self.particle_plugin.update(delta_time)

    # 6. Camera
    self.camera_plugin.update(delta_time)
```

## Next Steps

- [API Reference](../api/index.md) - Framework architecture and core components
- [Scripting Guide](../scripting/index.md) - Event-driven scripting system
- [Extending Pedre](../extending/index.md) - Add custom functionality
- [Configuration Guide](../guides/configuration.md) - Plugin settings reference
