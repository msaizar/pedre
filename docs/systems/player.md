# PlayerManager

Manages player spawning, movement, animation, and state.

## Location

- Implementation: [src/pedre/systems/player/manager.py](../../src/pedre/systems/player/manager.py)
- Base class: [src/pedre/systems/player/base.py](../../src/pedre/systems/player/base.py)
- Sprites: [src/pedre/systems/player/sprites.py](../../src/pedre/systems/player/sprites.py)
- Types: [src/pedre/systems/player/types.py](../../src/pedre/systems/player/types.py)

## Configuration

The PlayerManager uses the following settings from `pedre.conf.settings`:

### Movement Settings

- `PLAYER_MOVEMENT_SPEED` - Movement speed in pixels per second (default: 180.0)
- `TILE_SIZE` - Size of tiles for grid-based calculations (default: 64)

These can be overridden in your project's `settings.py`:

```python
# Custom player settings
PLAYER_MOVEMENT_SPEED = 200.0
TILE_SIZE = 32
```

## Public API

### Player Access

#### `get_player_sprite() -> AnimatedPlayer | None`

Get the player sprite instance.

**Returns:**

- The AnimatedPlayer sprite or None if not loaded

**Example:**

```python
player_sprite = context.player_manager.get_player_sprite()
if player_sprite:
    print(f"Player at ({player_sprite.center_x}, {player_sprite.center_y})")
```

**Notes:**

- Returns None before scene is loaded
- Player sprite is created during `load_from_tiled()`
- Used by other systems (camera, portals, interactions)

### System Lifecycle

#### `setup(context: GameContext) -> None`

Initialize the player system with game context.

**Parameters:**

- `context` - Game context providing access to other systems

**Notes:**

- Called automatically by SystemLoader
- Stores reference to game context
- Must be called before loading player from Tiled

#### `update(delta_time: float) -> None`

Update player movement and animation.

**Parameters:**

- `delta_time` - Time since last update in seconds

**Example:**

```python
def on_update(self, delta_time):
    self.player_manager.update(delta_time)
```

**Notes:**

- Called automatically by SystemLoader each frame
- Processes input from InputManager
- Blocks movement when dialog is showing
- Updates player position and animation state
- Handles direction changes based on movement

#### `load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load player from Tiled map object layer.

**Parameters:**

- `tile_map` - The loaded Tiled map
- `arcade_scene` - The arcade Scene to add player to

**Notes:**

- Called automatically by SystemLoader
- Looks for "Player" object layer
- Uses first player object in layer
- Creates AnimatedPlayer sprite from object data
- Supports portal-based spawning via waypoints

#### `reset() -> None`

Reset player manager state for new game.

**Notes:**

- Clears player sprite and sprite list
- Called when starting a new game

### Save/Load Support

#### `get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing player position

**Example:**

```python
save_data = {
    "player": player_manager.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Saves player_x and player_y coordinates
- Returns empty dict if no player sprite exists

#### `restore_save_state(state: dict[str, Any]) -> None`

Phase 1: No metadata to restore for player (sprites don't exist yet).

**Parameters:**

- `state` - Dictionary containing saved player state

**Notes:**

- Player sprite doesn't exist during this phase
- Actual restoration happens in `apply_entity_state()`

#### `apply_entity_state(state: dict[str, Any]) -> None`

Phase 2: Apply saved player position after sprite exists.

**Parameters:**

- `state` - Dictionary containing saved player state

**Example:**

```python
player_manager.apply_entity_state(save_data["player"])
```

**Notes:**

- Restores player_x and player_y coordinates
- Must be called after `load_from_tiled()`
- Logs restored position for debugging

### State Serialization

#### `to_dict() -> dict[str, float]`

Serialize player position to dictionary.

**Returns:**

- Dictionary with `player_x` and `player_y` keys

**Example:**

```python
position_data = player_manager.to_dict()
print(f"Player at ({position_data['player_x']}, {position_data['player_y']})")
```

#### `from_dict(data: dict[str, float]) -> None`

Restore player position from dictionary.

**Parameters:**

- `data` - Dictionary with `player_x` and `player_y` keys

**Example:**

```python
player_manager.from_dict({"player_x": 320.0, "player_y": 240.0})
```

**Notes:**

- Only applies position if player sprite exists
- Requires both `player_x` and `player_y` keys

## AnimatedPlayer Sprites

AnimatedPlayer is a specialized sprite for the player character with 4-directional animations.

### Creating AnimatedPlayer

```python
from pedre.systems.player.sprites import AnimatedPlayer

player = AnimatedPlayer(
    sprite_sheet="characters/player.png",
    center_x=320,
    center_y=240,
    scale=2.0,
    tile_size=32,
    # Idle animations (4 directions)
    idle_up_frames=4,
    idle_up_row=0,
    idle_down_frames=4,
    idle_down_row=1,
    idle_left_frames=4,
    idle_left_row=2,
    idle_right_frames=4,
    idle_right_row=3,
    # Walk animations (4 directions)
    walk_up_frames=6,
    walk_up_row=4,
    walk_down_frames=6,
    walk_down_row=5,
    walk_left_frames=6,
    walk_left_row=6,
    walk_right_frames=6,
    walk_right_row=7
)
```

### Animation Properties

**Base Animation Properties (from sprite sheet):**

- `idle_up_frames`, `idle_up_row` - Idle facing up
- `idle_down_frames`, `idle_down_row` - Idle facing down
- `idle_left_frames`, `idle_left_row` - Idle facing left
- `idle_right_frames`, `idle_right_row` - Idle facing right
- `walk_up_frames`, `walk_up_row` - Walk upward animation
- `walk_down_frames`, `walk_down_row` - Walk downward animation
- `walk_left_frames`, `walk_left_row` - Walk left animation
- `walk_right_frames`, `walk_right_row` - Walk right animation

### Key Differences from AnimatedNPC

AnimatedPlayer does not include special animations (appear, disappear, interact) to keep the player character implementation simple and focused on core movement functionality. This reflects the different use cases:

- **Player**: Always visible, user-controlled, focused on movement
- **NPC**: May appear/disappear, has interaction states, AI-controlled

### Tiled Map Integration

The player can be placed in Tiled maps using the "Player" object layer:

1. Create a "Player" object layer
2. Add a point object where the player should spawn
3. Set custom properties on the object:

**Required Properties:**

- `sprite_sheet` (string) - Path to sprite sheet (relative to assets)

**Optional Properties:**

- `tile_size` (int) - Size of each tile in sprite sheet (default: from sheet)
- `scale` (float) - Sprite scale multiplier (default: 1.0)
- `spawn_at_portal` (bool) - Whether to use portal spawn waypoint (default: true)
- Animation properties (see above)

**Example Tiled Properties:**

```yaml
sprite_sheet: characters/player.png
tile_size: 32
scale: 2.0
spawn_at_portal: true
walk_up_frames: 6
walk_up_row: 0
walk_down_frames: 6
walk_down_row: 1
idle_up_frames: 4
idle_up_row: 4
idle_down_frames: 4
idle_down_row: 5
```

### Portal-Based Spawning

When loading a scene, the player can spawn at a waypoint instead of the default position:

**How It Works:**

1. SceneManager stores a `next_spawn_waypoint` when transitioning scenes
2. PlayerManager checks for this waypoint during `load_from_tiled()`
3. If `spawn_at_portal=true` and waypoint exists, player spawns there
4. If waypoint not found or `spawn_at_portal=false`, uses default position from Tiled

**Example:**

```python
# Request scene transition with spawn waypoint
context.scene_manager.request_transition(
    map_file="castle.tmx",
    spawn_waypoint="entrance"
)

# PlayerManager will spawn player at "entrance" waypoint
# instead of default position from Tiled map
```

**Notes:**

- Waypoint must exist in target scene's waypoint system
- Spawn waypoint is cleared after use (one-time)
- Default position from Tiled is used as fallback

## Movement System

The PlayerManager handles movement processing each frame:

### Movement Processing Flow

1. **Input Check** - Get movement vector from InputManager
2. **Dialog Blocking** - Block movement if dialog is showing
3. **Direction Update** - Update player direction based on movement
4. **Animation Update** - Update walk/idle animation state

### Direction Logic

Direction changes are based on movement priority:

```python
if dx > 0:
    direction = "right"
elif dx < 0:
    direction = "left"
elif dy > 0:
    direction = "up"
elif dy < 0:
    direction = "down"
```

**Notes:**

- Horizontal movement (dx) takes precedence over vertical (dy)
- Direction only updates when actually moving
- Last direction is preserved when stopped

### Animation States

The player has two animation states:

- **Idle** - When stationary (dx = 0 and dy = 0)
- **Walk** - When moving (dx != 0 or dy != 0)

Each state has 4 directional variants (up, down, left, right).

## Usage Examples

### Accessing Player Position

```python
# Get player sprite
player_sprite = context.player_manager.get_player_sprite()

if player_sprite:
    # Access position
    x = player_sprite.center_x
    y = player_sprite.center_y
    print(f"Player at ({x}, {y})")
```

### Checking Player Distance

```python
# Check distance to NPC
player_sprite = context.player_manager.get_player_sprite()
npc_sprite = context.npc_manager.get_npc_by_name("merchant").sprite

distance = arcade.get_distance_between_sprites(player_sprite, npc_sprite)
if distance < 50:
    print("Player near merchant")
```

### Following Player with Camera

```python
# Camera automatically follows player
context.camera_manager.set_follow_player(smooth=True)

# Stop following
context.camera_manager.stop_follow()
```

### Spawning at Specific Location

The player spawns at waypoints during scene transitions. This is typically handled by scripts:

```json
{
    "type": "change_scene",
    "target_map": "castle.tmx",
    "spawn_waypoint": "main_entrance"
}
```

## Custom Player Implementation

If you need to replace the player system with a custom implementation, you can extend the `PlayerBaseManager` abstract base class.

### PlayerBaseManager

**Location:** [src/pedre/systems/player/base.py](../../src/pedre/systems/player/base.py)

The `PlayerBaseManager` class defines the minimum interface that any player manager must implement.

#### Required Methods

Your custom player manager must implement these abstract methods:

```python
from pedre.systems.player.base import PlayerBaseManager
from pedre.systems.player.sprites import AnimatedPlayer

class CustomPlayerManager(PlayerBaseManager):
    """Custom player implementation."""

    name = "player"
    dependencies = ["input", "waypoint"]

    def get_player_sprite(self) -> AnimatedPlayer | None:
        """Get the player sprite."""
        ...
```

#### Registration

Register your custom player manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.player.base import PlayerBaseManager

@SystemRegistry.register
class CustomPlayerManager(PlayerBaseManager):
    name = "player"
    dependencies = ["input", "waypoint"]

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `PlayerBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"player_manager"` in the base class
- Your implementation can use any sprite type or movement system
- Register your custom player manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.player"` to replace it

**Example Custom Implementation:**

```python
# In myproject/systems/custom_player.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.player.base import PlayerBaseManager

@SystemRegistry.register
class PhysicsPlayerManager(PlayerBaseManager):
    """Player manager with physics-based movement."""

    name = "player"
    dependencies = ["input", "waypoint", "physics"]

    def __init__(self):
        self.player_sprite = None
        self.velocity = (0, 0)
        # ... rest of initialization ...

    def get_player_sprite(self) -> AnimatedPlayer | None:
        return self.player_sprite

    def update(self, delta_time: float) -> None:
        # Custom physics-based movement
        # ... physics calculations ...
        pass

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_SYSTEMS = [
    "myproject.systems.custom_player",  # Load custom player first
    "pedre.systems.camera",
    "pedre.systems.audio",
    # ... rest of systems (omit "pedre.systems.player") ...
]
```

## See Also

- [InputManager](input.md) - Keyboard input handling
- [CameraManager](camera.md) - Camera following
- [SceneManager](scene.md) - Scene transitions and spawning
- [WaypointManager](waypoint.md) - Waypoint system
- [Configuration Guide](../configuration.md) - Player system settings
- [AnimatedSprite](../sprites/animated-sprite.md) - Base animation system
