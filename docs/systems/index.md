# Systems Reference

This documentation provides detailed information about each manager/system in the Pedre framework. Each system is responsible for a specific aspect of game functionality and can be used independently or combined to create rich interactive experiences.

## Overview

The Pedre framework follows a manager-based architecture where each system encapsulates specific functionality. Systems communicate through an event bus for loose coupling and maintainability.

## Core Systems

### [DialogManager](dialog.md)
Manages dialog display with multi-page support and pagination. Handles NPC conversations and text-based interactions.

**Key Features:**
- Multi-page dialog support
- Automatic pagination
- Dialog overlay rendering
- Event integration

### [NPCManager](npc.md)
Manages NPC state, movement, pathfinding, and interactions. Controls all non-player character behavior and conversations.

**Key Features:**
- NPC registration and tracking
- Dialog level progression
- Pathfinding integration
- JSON-based dialog configuration
- Event-driven interactions

### [ScriptManager](script.md)
Event-driven scripting system for cutscenes and interactive sequences. Enables complex game logic without code changes.

**Key Features:**
- JSON-based scripting
- Event-triggered actions
- Conditional execution
- Action sequencing
- Script reusability

### [PortalManager](portal.md)
Handles map transitions and portal collision detection. Manages seamless movement between different game areas.

**Key Features:**
- Portal registration
- Collision detection
- Conditional portals
- Target positioning

### [InventoryManager](inventory.md)
Manages item collection and categorization. Tracks player possessions and supports various item types.

**Key Features:**
- Item storage by category
- Inventory queries
- Item validation
- Category management

## Media & Effects

### [AudioManager](audio.md)
Manages background music and sound effects with caching. Provides audio playback and volume control.

**Key Features:**
- Music playback with looping
- Sound effect caching
- Volume control
- Multiple audio format support

### [ParticleManager](particle.md)
Visual effects and particle systems. Creates visual feedback for game events.

**Key Features:**
- Particle emission
- Effect types
- Duration control
- Automatic cleanup

## Persistence & State

### [SaveManager](save.md)
Handles game state persistence with auto-save and manual save slots. Manages game progress across sessions.

**Key Features:**
- Multiple save slots
- JSON-based storage
- Save/load operations
- Auto-save support

## Camera & Movement

### [CameraManager](camera.md)
Smooth camera following with optional bounds. Controls viewport positioning and movement.

**Key Features:**
- Sprite following
- Smooth transitions
- Boundary constraints
- Configurable smoothing

### [PathfindingManager](pathfinding.md)
A* pathfinding for NPC navigation. Enables intelligent movement around obstacles.

**Key Features:**
- A* algorithm
- Grid-based navigation
- Collision avoidance
- Waypoint generation

## Interaction & Input

### [InteractionManager](interaction.md)
Manages interactive objects that players can interact with. Handles object-based interactions.

**Key Features:**
- Object registration
- Proximity detection
- Multiple interaction types
- Property-based configuration

### [InputManager](input.md)
Keyboard input handling and movement vector calculation. Processes player input.

**Key Features:**
- Key state tracking
- Movement vector calculation
- Action mapping
- Normalized input

## Communication

### [EventBus](event-bus.md)
Publish-subscribe event system for loose coupling. Enables decoupled communication between systems.

**Key Features:**
- Event publishing
- Subscriber management
- Custom event support
- Type-safe events

## Best Practices

### Manager Coordination

Use `GameContext` to pass managers to actions and systems:

```python
from pedre.systems.game_context import GameContext

game_context = GameContext(
    event_bus=event_bus,
    npc_manager=npc_manager,
    dialog_manager=dialog_manager,
    inventory_manager=inventory_manager,
    # ... other managers
)
```

### Event-Driven Design

Prefer events over direct manager calls:

```python
# Don't: Direct coupling
def close_dialog():
    dialog_manager.close()
    npc_manager.increment_level("merchant")

# Do: Event-driven
def close_dialog():
    dialog_manager.close()
    event_bus.publish(DialogClosedEvent(npc_name="merchant"))
    # ScriptManager handles the rest
```

### Update Order

Call manager updates in the correct order:

```python
def on_update(self, delta_time):
    # 1. Input
    dx, dy = self.input_manager.get_movement_vector()

    # 2. Physics
    self.player.update_physics(dx, dy, delta_time)

    # 3. NPCs
    self.npc_manager.update(delta_time)

    # 4. Scripts
    self.script_manager.update(delta_time, self.game_context)

    # 5. Particles
    self.particle_manager.update(delta_time)

    # 6. Camera
    self.camera_manager.update(delta_time)
```

## Next Steps

- [Scripting Guide](../scripting/index.md) - Detailed scripting documentation
- [API Reference](../api-reference.md) - Complete API documentation
