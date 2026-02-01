# PhysicsPlugin

Manages collision detection and physics simulation for the player sprite using Arcade's built-in physics engine.

## Location

- Implementation: [src/pedre/plugins/physics/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/physics/plugin.py)
- Base class: [src/pedre/plugins/physics/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/physics/base.py)

## Configuration

The PhysicsPlugin uses the following settings from `pedre.conf.settings`:

### Movement and Collision Settings

- `PLAYER_MOVEMENT_SPEED` - Player movement speed in pixels per second (affects physics response)
- `TILE_SIZE` - Size of tiles in the map (affects collision precision)

These can be overridden in your project's `settings.py`:

```python
# Custom physics settings
PLAYER_MOVEMENT_SPEED = 200.0
TILE_SIZE = 32
```

**Additional Configuration:**

- **Map collision layers** - Defined in Tiled map editor, determines which sprites act as walls

## Public API

### Physics Engine Control

#### invalidate

`invalidate() -> None`

Mark the physics engine for recreation on the next update cycle.

**Example:**

```python
# After spawning a new player sprite
player_plugin.spawn_player(x=100, y=100)
physics_plugin.invalidate()
```

**Notes:**

- Called automatically when the player sprite changes
- Sets internal flag to recreate engine on next `update()` call
- Useful when the wall list or player sprite changes during gameplay

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the physics plugin with game context and create the physics engine.

**Parameters:**

- `context` - Game context providing access to player and scene plugins

**Notes:**

- Called automatically by PluginLoader
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

The PhysicsPlugin uses Arcade's `PhysicsEngineSimple`, which provides:

- **Simple collision response** - Prevents player from moving through walls
- **Sliding along walls** - Player can slide along diagonal walls smoothly
- **Solid obstacles** - Any sprite in the wall list acts as an impassable barrier

### Wall List

The physics engine uses the wall list from the ScenePlugin:

```python
wall_list = context.scene_plugin.get_wall_list()
```

**Notes:**

- Wall list typically comes from Tiled map layers marked as collision layers
- ScenePlugin automatically extracts wall sprites from map data
- Walls must be present in the Arcade scene for collision to work

### Engine Recreation

The physics engine is recreated when:

1. **Initial setup** - When the plugin is first initialized
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

- Player sprite must exist (from PlayerPlugin)
- Wall list must be available (from ScenePlugin)

**Fallback:**

- If player sprite doesn't exist, engine is not created
- Plugin gracefully handles missing sprites and walls

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
- Allows plugins to invalidate without direct access to sprites
- Defers expensive operations until necessary

## Plugin Dependencies

The PhysicsPlugin depends on:

- `player` - PlayerPlugin for player sprite access

The plugin also requires:

- `scene_plugin` - Via game context for wall list access
- Player sprite must exist before physics can work
- Wall list should be populated from Tiled map

## Usage Examples

### Basic Physics Setup

The physics plugin is automatically initialized by the PluginLoader:

```python
# In GameView initialization
# PhysicsPlugin is loaded and setup automatically
# No manual initialization needed
```

### Invalidating After Player Spawn

When the player sprite is recreated or repositioned:

```python
# In PlayerPlugin after spawning new player
def spawn_player(self, x: float, y: float):
    self.player_sprite = AnimatedPlayer(...)
    self.player_sprite.center_x = x
    self.player_sprite.center_y = y

    # Tell physics plugin to rebuild engine
    self.context.physics_plugin.invalidate()
```

### Scene Transition

After loading a new scene with different walls:

```python
# In ScenePlugin after loading new map
def load_level(self, map_file: str):
    # Load new Tiled map
    self.tile_map = arcade.load_tilemap(map_file)
    self.scene = arcade.Scene.from_tilemap(self.tile_map)

    # Physics engine will be invalidated and recreated
    # automatically by PlayerPlugin or scene loading
    self.context.physics_plugin.invalidate()
```

### Checking Physics State

```python
# Check if physics engine is active
if physics_plugin.physics_engine is not None:
    print("Physics engine is running")
else:
    print("Physics engine not initialized")
```

## Integration with Other Plugins

### PlayerPlugin Integration

The PlayerPlugin provides the player sprite:

```python
player_sprite = context.player_plugin.get_player_sprite()
```

**Important:**

- PlayerPlugin should call `invalidate()` when player sprite changes
- Player must exist before physics engine can be created

### ScenePlugin Integration

The ScenePlugin provides the wall list:

```python
wall_list = context.scene_plugin.get_wall_list()
```

**Wall List Contents:**

- Sprites from collision layers in Tiled map
- Typically includes walls, obstacles, barriers
- Updated automatically when new scene loads

### InputPlugin Integration

The InputPlugin provides movement input, which the physics engine applies:

```python
# In game update loop
dx, dy = input_plugin.get_movement_vector()

# Player sprite position updated
player_sprite.change_x = dx
player_sprite.change_y = dy

# Physics engine prevents collision
physics_plugin.update(delta_time)
```

## Custom PhysicsPlugin Implementation

If you need advanced physics behavior, you can extend the `PhysicsBasePlugin` abstract base class.

### PhysicsBasePlugin

**Location:** [src/pedre/plugins/physics/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/physics/base.py)

The `PhysicsBasePlugin` class defines the minimum interface for physics plugins.

#### Required Methods

Your custom physics plugin must implement:

```python
from pedre.plugins.physics.base import PhysicsBasePlugin
from pedre.plugins.registry import PluginRegistry

@PluginRegistry.register
class CustomPhysicsPlugin(PhysicsBasePlugin):
    """Custom physics implementation."""

    name = "physics"

    def invalidate(self) -> None:
        """Mark physics engine for recreation."""
        ...

    # Also implement BasePlugin methods:
    # - setup(context: GameContext)
    # - update(delta_time: float)
    # - cleanup() (optional)
```

#### Example Custom Implementation

```python
# In myproject/plugins/advanced_physics.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.physics.base import PhysicsBasePlugin
import arcade

@PluginRegistry.register
class PlatformerPhysicsPlugin(PhysicsBasePlugin):
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
        player = self.context.player_plugin.get_player_sprite()
        walls = self.context.scene_plugin.get_wall_list()
        platforms = self.context.scene_plugin.get_platform_list()

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
INSTALLED_PLUGINS = [
    "myproject.plugins.advanced_physics",  # Load custom physics first
    "pedre.plugins.camera",
    "pedre.plugins.player",
    # ... rest of plugins (omit "pedre.plugins.physics") ...
]
```

## Troubleshooting

### Physics Not Working

If the player passes through walls:

1. **Check player sprite exists** - `player_plugin.get_player_sprite()` should not be None
2. **Check wall list** - `scene_plugin.get_wall_list()` should contain wall sprites
3. **Verify invalidation** - Call `physics_plugin.invalidate()` after spawning player
4. **Check collision layers** - Ensure Tiled map has properly configured collision layers

### Engine Not Updating

If the physics engine seems frozen:

1. **Check update loop** - Ensure `physics_plugin.update(delta_time)` is called every frame
2. **Verify setup** - Ensure `physics_plugin.setup(context)` was called during initialization
3. **Check for errors** - Review logs for physics-related warnings

### Performance Issues

If physics is causing lag:

1. **Reduce wall sprites** - Combine smaller wall tiles into larger collision areas
2. **Optimize collision layers** - Use simple rectangular collision shapes
3. **Consider spatial partitioning** - For very large maps, use Arcade's spatial hash

## See Also

- [PlayerPlugin](player.md) - Player sprite management
- [ScenePlugin](scene.md) - Map loading and wall list management
- [InputPlugin](input.md) - Movement input handling
- [Arcade Physics Documentation](https://api.arcade.academy/en/latest/programming_guide/physics_engines.html) - Underlying physics engine
