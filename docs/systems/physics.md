# PhysicsManager

Manages collision detection and physics simulation for the player sprite using Arcade's built-in physics engine.

## Location

- Implementation: [src/pedre/systems/physics/manager.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/physics/manager.py)
- Base class: [src/pedre/systems/physics/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/physics/base.py)

## Overview

The PhysicsManager wraps Arcade's `PhysicsEngineSimple` to provide collision handling between the player sprite and the environment (walls, obstacles). It automatically manages the physics engine lifecycle and provides an invalidation mechanism to rebuild the engine when the player or collision layers change.

## Public API

### Physics Engine Control

#### invalidate

`invalidate() -> None`

Mark the physics engine for recreation on the next update cycle.

**Example:**

```python
# After spawning a new player sprite
player_manager.spawn_player(x=100, y=100)
physics_manager.invalidate()
```

**Notes:**

- Called automatically when the player sprite changes
- Sets internal flag to recreate engine on next `update()` call
- Useful when the wall list or player sprite changes during gameplay

### System Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the physics system with game context and create the physics engine.

**Parameters:**

- `context` - Game context providing access to player and scene managers

**Notes:**

- Called automatically by SystemLoader
- Creates the initial physics engine with current player and walls
- Stores reference to game context for future engine recreation

#### update

`update(delta_time: float) -> None`

Update the physics simulation.

**Parameters:**

- `delta_time` - Time elapsed since last update in seconds

**Notes:**

- Called automatically every frame by the game loop
- Recreates physics engine if invalidation flag is set
- Updates Arcade physics engine to handle collisions and movement
- Does nothing if physics engine is not initialized

## Physics Engine Behavior

### Collision Detection

The PhysicsManager uses Arcade's `PhysicsEngineSimple`, which provides:

- **Simple collision response** - Prevents player from moving through walls
- **Sliding along walls** - Player can slide along diagonal walls smoothly
- **Solid obstacles** - Any sprite in the wall list acts as an impassable barrier

### Wall List

The physics engine uses the wall list from the SceneManager:

```python
wall_list = context.scene_manager.get_wall_list()
```

**Notes:**

- Wall list typically comes from Tiled map layers marked as collision layers
- SceneManager automatically extracts wall sprites from map data
- Walls must be present in the Arcade scene for collision to work

### Engine Recreation

The physics engine is recreated when:

1. **Initial setup** - When the system is first initialized
2. **Player sprite changes** - When `invalidate()` is called
3. **Scene transitions** - After loading a new map with different walls

**Automatic Recreation:**

```python
# Triggered automatically during update if needed
if self._needs_recreate:
    self._create_engine()
```

## Implementation Details

### Physics Engine Creation

The physics engine is created with:

```python
self.physics_engine = arcade.PhysicsEngineSimple(
    player_sprite,
    wall_list
)
```

**Requirements:**

- Player sprite must exist (from PlayerManager)
- Wall list must be available (from SceneManager)

**Fallback:**

- If player sprite doesn't exist, engine is not created
- System gracefully handles missing sprites and walls

### Invalidation Pattern

The invalidation pattern allows deferred engine recreation:

```python
def invalidate(self) -> None:
    """Mark for recreation."""
    self._needs_recreate = True

def update(self, delta_time: float) -> None:
    """Recreate if needed."""
    if self._needs_recreate:
        self._create_engine()

    if self.physics_engine:
        self.physics_engine.update()
```

**Benefits:**

- Avoids recreating engine multiple times in same frame
- Allows systems to invalidate without direct access to sprites
- Defers expensive operations until necessary

## System Dependencies

The PhysicsManager depends on:

- `player` - PlayerManager for player sprite access

The system also requires:

- `scene_manager` - Via game context for wall list access
- Player sprite must exist before physics can work
- Wall list should be populated from Tiled map

## Usage Examples

### Basic Physics Setup

The physics system is automatically initialized by the SystemLoader:

```python
# In GameView initialization
# PhysicsManager is loaded and setup automatically
# No manual initialization needed
```

### Invalidating After Player Spawn

When the player sprite is recreated or repositioned:

```python
# In PlayerManager after spawning new player
def spawn_player(self, x: float, y: float):
    self.player_sprite = AnimatedPlayer(...)
    self.player_sprite.center_x = x
    self.player_sprite.center_y = y

    # Tell physics system to rebuild engine
    self.context.physics_manager.invalidate()
```

### Scene Transition

After loading a new scene with different walls:

```python
# In SceneManager after loading new map
def load_level(self, map_file: str):
    # Load new Tiled map
    self.tile_map = arcade.load_tilemap(map_file)
    self.scene = arcade.Scene.from_tilemap(self.tile_map)

    # Physics engine will be invalidated and recreated
    # automatically by PlayerManager or scene loading
    self.context.physics_manager.invalidate()
```

### Checking Physics State

```python
# Check if physics engine is active
if physics_manager.physics_engine is not None:
    print("Physics engine is running")
else:
    print("Physics engine not initialized")
```

## Configuration

The PhysicsManager has no direct configuration settings. Physics behavior is controlled by:

- **Player movement speed** - `PLAYER_MOVEMENT_SPEED` in settings
- **Tile size** - `TILE_SIZE` in settings (affects collision precision)
- **Map collision layers** - Defined in Tiled map editor

## Integration with Other Systems

### PlayerManager Integration

The PlayerManager provides the player sprite:

```python
player_sprite = context.player_manager.get_player_sprite()
```

**Important:**

- PlayerManager should call `invalidate()` when player sprite changes
- Player must exist before physics engine can be created

### SceneManager Integration

The SceneManager provides the wall list:

```python
wall_list = context.scene_manager.get_wall_list()
```

**Wall List Contents:**

- Sprites from collision layers in Tiled map
- Typically includes walls, obstacles, barriers
- Updated automatically when new scene loads

### InputManager Integration

The InputManager provides movement input, which the physics engine applies:

```python
# In game update loop
dx, dy = input_manager.get_movement_vector()

# Player sprite position updated
player_sprite.change_x = dx
player_sprite.change_y = dy

# Physics engine prevents collision
physics_manager.update(delta_time)
```

## Custom PhysicsManager Implementation

If you need advanced physics behavior, you can extend the `PhysicsBaseManager` abstract base class.

### PhysicsBaseManager

**Location:** [src/pedre/systems/physics/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/physics/base.py)

The `PhysicsBaseManager` class defines the minimum interface for physics systems.

#### Required Methods

Your custom physics manager must implement:

```python
from pedre.systems.physics.base import PhysicsBaseManager
from pedre.systems.registry import SystemRegistry

@SystemRegistry.register
class CustomPhysicsManager(PhysicsBaseManager):
    """Custom physics implementation."""

    name = "physics"

    def invalidate(self) -> None:
        """Mark physics engine for recreation."""
        ...

    # Also implement BaseSystem methods:
    # - setup(context: GameContext)
    # - update(delta_time: float)
    # - cleanup() (optional)
```

#### Example Custom Implementation

```python
# In myproject/systems/advanced_physics.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.physics.base import PhysicsBaseManager
import arcade

@SystemRegistry.register
class PlatformerPhysicsManager(PhysicsBaseManager):
    """Physics with gravity and jumping."""

    name = "physics"
    dependencies = ["player"]

    def __init__(self):
        self.physics_engine = None
        self._needs_recreate = True
        self.gravity_constant = 1.0

    def setup(self, context: GameContext) -> None:
        self.context = context
        self._create_engine()

    def invalidate(self) -> None:
        self._needs_recreate = True

    def update(self, delta_time: float) -> None:
        if self._needs_recreate:
            self._create_engine()

        if self.physics_engine:
            self.physics_engine.update()

    def _create_engine(self) -> None:
        player = self.context.player_manager.get_player_sprite()
        walls = self.context.scene_manager.get_wall_list()
        platforms = self.context.scene_manager.get_platform_list()

        if player:
            # Use platformer physics with gravity
            self.physics_engine = arcade.PhysicsEnginePlatformer(
                player,
                walls=walls,
                platforms=platforms,
                gravity_constant=self.gravity_constant
            )

        self._needs_recreate = False
```

```python
# In myproject/settings.py
INSTALLED_SYSTEMS = [
    "myproject.systems.advanced_physics",  # Load custom physics first
    "pedre.systems.camera",
    "pedre.systems.player",
    # ... rest of systems (omit "pedre.systems.physics") ...
]
```

## Troubleshooting

### Physics Not Working

If the player passes through walls:

1. **Check player sprite exists** - `player_manager.get_player_sprite()` should not be None
2. **Check wall list** - `scene_manager.get_wall_list()` should contain wall sprites
3. **Verify invalidation** - Call `physics_manager.invalidate()` after spawning player
4. **Check collision layers** - Ensure Tiled map has properly configured collision layers

### Engine Not Updating

If the physics engine seems frozen:

1. **Check update loop** - Ensure `physics_manager.update(delta_time)` is called every frame
2. **Verify setup** - Ensure `physics_manager.setup(context)` was called during initialization
3. **Check for errors** - Review logs for physics-related warnings

### Performance Issues

If physics is causing lag:

1. **Reduce wall sprites** - Combine smaller wall tiles into larger collision areas
2. **Optimize collision layers** - Use simple rectangular collision shapes
3. **Consider spatial partitioning** - For very large maps, use Arcade's spatial hash

## See Also

- [PlayerManager](player.md) - Player sprite management
- [SceneManager](scene.md) - Map loading and wall list management
- [InputManager](input.md) - Movement input handling
- [Arcade Physics Documentation](https://api.arcade.academy/en/latest/programming_guide/physics_engines.html) - Underlying physics engine
