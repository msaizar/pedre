# PlayerPlugin

Manages player spawning, movement, animation, and state.

## Location

- Implementation: [src/pedre/plugins/player/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/player/plugin.py)
- Base class: [src/pedre/plugins/player/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/player/base.py)

## Configuration

The PlayerPlugin uses the following settings from `pedre.conf.settings`:

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

#### get_player_sprite

`get_player_sprite() -> AnimatedSprite | None`

Get the player sprite instance.

**Returns:**

- The `AnimatedSprite` instance or None if not loaded

**Example:**

```python
player_sprite = context.player_plugin.get_player_sprite()
if player_sprite:
    print(f"Player at ({player_sprite.center_x}, {player_sprite.center_y})")
```

**Notes:**

- Returns None before scene is loaded
- Player sprite is created during `load_from_tiled()`
- Used by other plugins (camera, portals, interactions)

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the player plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context
- Must be called before loading player from Tiled

#### update

`update(delta_time: float) -> None`

Update player movement and animation.

**Parameters:**

- `delta_time` - Time since last update in seconds

**Example:**

```python
def on_update(self, delta_time):
    self.player_plugin.update(delta_time)
```

**Notes:**

- Called automatically by PluginLoader each frame
- Processes input from InputPlugin
- Blocks movement when dialog is showing
- Updates player position and animation state
- Handles direction changes based on movement

#### load_from_tiled

`load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load player from Tiled map object layer.

**Parameters:**

- `tile_map` - The loaded Tiled map
- `arcade_scene` - The arcade Scene to add player to

**Notes:**

- Called automatically by PluginLoader
- Looks for "Player" object layer
- Uses first player object in layer
- Resolves sprite via content registry (`sprites` sub-registry, using `sprite_id` property or `"player"` as default)
- Supports portal-based spawning via waypoints

#### reset

`reset() -> None`

Reset player plugin state for new game.

**Notes:**

- Clears player sprite and sprite list
- Called when starting a new game

### Save/Load Support

#### get_save_state

`get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing player position

**Example:**

```python
save_data = {
    "player": player_plugin.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Saves player_x and player_y coordinates
- Returns empty dict if no player sprite exists

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Phase 1: No metadata to restore for player (sprites don't exist yet).

**Parameters:**

- `state` - Dictionary containing saved player state

**Notes:**

- Player sprite doesn't exist during this phase
- Actual restoration happens in `apply_entity_state()`

#### apply_entity_state

`apply_entity_state(state: dict[str, Any]) -> None`

Phase 2: Apply saved player position after sprite exists.

**Parameters:**

- `state` - Dictionary containing saved player state

**Example:**

```python
player_plugin.apply_entity_state(save_data["player"])
```

**Notes:**

- Restores player_x and player_y coordinates
- Must be called after `load_from_tiled()`
- Logs restored position for debugging

### State Serialization

#### to_dict

`to_dict() -> dict[str, float]`

Serialize player position to dictionary.

**Returns:**

- Dictionary with `player_x` and `player_y` keys

**Example:**

```python
position_data = player_plugin.to_dict()
print(f"Player at ({position_data['player_x']}, {position_data['player_y']})")
```

#### from_dict

`from_dict(data: dict[str, float]) -> None`

Restore player position from dictionary.

**Parameters:**

- `data` - Dictionary with `player_x` and `player_y` keys

**Example:**

```python
player_plugin.from_dict({"player_x": 320.0, "player_y": 240.0})
```

**Notes:**

- Only applies position if player sprite exists
- Requires both `player_x` and `player_y` keys

## Player Sprite and Content Registry

The player sprite is defined via the content registry rather than inline Tiled properties. During `load_from_tiled()` the plugin looks up the `sprite_id` property on the Tiled object (defaulting to `"player"`) in the `sprites` sub-registry and creates an `AnimatedSprite` from that definition.

### Tiled Map Integration

The player is placed in Tiled maps using the "Player" object layer:

1. Create a "Player" object layer
2. Add a point object where the player should spawn by default

**Optional Tiled Object Properties:**

- `sprite_id` (string) - Override which sprite definition to use from the `sprites` content registry (default: `"player"`)
- `spawn_at_portal` (bool) - Whether to use portal spawn waypoint (default: true)

All animation configuration (sprite sheet, frames, rows) comes from the sprite definition in the content registry.

**Example Tiled Object:**

```yaml
spawn_at_portal: true
```

**Example sprite content registry entry (`sprites.json`):**

```json
{
  "player": {
    "sprite_sheet": "characters/player.png",
    "frame_width": 32,
    "states": {
      "idle": {"row": 0, "frames": 4},
      "walk": {"row": 1, "frames": 6}
    }
  }
}
```

See the [Sprites Content Reference](../content/sprites.md) and [Players Content Reference](../content/players.md) for full details on defining sprite and player entries.

### Portal-Based Spawning

When loading a scene, the player can spawn at a waypoint instead of the default position:

**How It Works:**

1. ScenePlugin stores a `next_spawn_waypoint` when transitioning scenes
2. PlayerPlugin checks for this waypoint during `load_from_tiled()`
3. If `spawn_at_portal=true` and waypoint exists, player spawns at waypoint's pixel coordinates
4. If waypoint not found or `spawn_at_portal=false`, uses default position from Tiled

**Example:**

```python
# Request scene transition with spawn waypoint
context.scene_plugin.request_transition(
    map_file="castle.tmx",
    spawn_waypoint="entrance"
)

# PlayerPlugin will spawn player at "entrance" waypoint
# instead of default position from Tiled map
```

**Notes:**

- Waypoint must exist in target scene's waypoint plugin
- Spawn waypoint is cleared after use (one-time)
- Default position from Tiled is used as fallback

## Player State

The PlayerPlugin maintains the player sprite and its state throughout the game session.

### Player Sprite Lifecycle

1. **Creation** - Player sprite is created during `load_from_tiled()`
2. **Updates** - Position and animation updated every frame in `update()`
3. **Persistence** - Position saved/restored during save/load operations
4. **Reset** - Cleared when starting a new game

### State Tracking

The player state includes:

- **Position** - `center_x` and `center_y` coordinates in pixels
- **Direction** - Current facing direction (up, down, left, right)
- **Animation State** - Walking or idle
- **Velocity** - Movement vector from input plugin

## Movement Plugin

The PlayerPlugin handles movement processing each frame:

### Movement Processing Flow

1. **Input Check** - Get movement vector from InputPlugin
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
player_sprite = context.player_plugin.get_player_sprite()

if player_sprite:
    # Access position
    x = player_sprite.center_x
    y = player_sprite.center_y
    print(f"Player at ({x}, {y})")
```

### Checking Player Distance

```python
# Check distance to NPC
player_sprite = context.player_plugin.get_player_sprite()
npc_sprite = context.npc_plugin.get_npc_by_name("merchant").sprite

distance = arcade.get_distance_between_sprites(player_sprite, npc_sprite)
if distance < 50:
    print("Player near merchant")
```

### Following Player with Camera

```python
# Camera automatically follows player
context.camera_plugin.set_follow_player(smooth=True)

# Stop following
context.camera_plugin.stop_follow()
```

### Spawning at Specific Location

The player spawns at waypoints during scene transitions. This is typically handled by scripts:

```json
{
    "name": "change_scene",
    "target_map": "castle.tmx",
    "spawn_waypoint": "main_entrance"
}
```

## Integration with Other Plugins

### InputPlugin Integration

The InputPlugin provides movement vectors:

```python
# In update loop
dx, dy = context.input_plugin.get_movement_vector()

# PlayerPlugin processes this input
# Updates player sprite velocity and direction
```

**Notes:**

- Input is automatically processed during `update()`
- Movement is blocked when dialogs are showing
- Direction changes are based on movement vector

### CameraPlugin Integration

The CameraPlugin can follow the player:

```python
# Enable player following
context.camera_plugin.set_follow_player(smooth=True)

# Camera automatically tracks player position
```

**Notes:**

- Player sprite must exist before camera can follow
- Camera uses player position for centering
- Smooth following interpolates camera movement

### DialogPlugin Integration

Dialog blocks player movement:

```python
# During update
if context.dialog_plugin.is_showing():
    # Player movement is blocked
    return
```

**Notes:**

- Player cannot move while dialog is visible
- Input is still processed but not applied
- Movement resumes when dialog closes

### ScenePlugin Integration

Scene transitions handle player spawning:

```python
# ScenePlugin provides spawn waypoint
spawn_waypoint = context.scene_plugin.get_next_spawn_waypoint()

# PlayerPlugin spawns at waypoint location (pixel coordinates)
if spawn_waypoint:
    waypoint_pos = context.waypoint_plugin.get_waypoint(spawn_waypoint)
    if waypoint_pos:
        pixel_x, pixel_y = waypoint_pos
        player.center_x = pixel_x
        player.center_y = pixel_y
```

**Notes:**

- Waypoint-based spawning is optional (`spawn_at_portal` property)
- Falls back to Tiled map position if waypoint not found
- Spawn waypoint is cleared after use

### PhysicsPlugin Integration

Physics engine prevents wall collisions:

```python
# Physics engine uses player sprite
physics_engine = arcade.PhysicsEngineSimple(player_sprite, walls)

# Movement is constrained by physics
physics_engine.update()
```

**Notes:**

- Physics must be invalidated when player sprite changes
- Collision response is handled by physics plugin
- Player velocity is set by PlayerPlugin, constrained by PhysicsPlugin

## Troubleshooting

### Player Not Appearing

If the player doesn't appear on the map:

1. **Check Player layer** - Ensure Tiled map has "Player" object layer
2. **Verify content registry** - Ensure a `"player"` entry (or the value of `sprite_id`) exists in your `sprites` content registry
3. **Check spawn position** - Verify player object has valid x/y coordinates
4. **Review logs** - Look for errors during `load_from_tiled()`

### Player Not Moving

If the player sprite exists but doesn't move:

1. **Check InputPlugin** - Ensure input plugin is working (`get_movement_vector()`)
2. **Verify update loop** - Confirm `player_plugin.update(delta_time)` is called every frame
3. **Check dialog state** - Ensure dialog isn't blocking movement
4. **Test physics** - Verify physics engine allows movement (not stuck in walls)

### Animation Not Playing

If animations aren't working:

1. **Check sprite definition** - Ensure animation states are defined in the content registry sprite entry
2. **Verify sprite sheet** - Ensure the sprite sheet file exists at the configured path
3. **Test movement** - Animations require actual movement to trigger walk states
4. **Review AnimatedSprite** - Check base animation plugin is functioning

### Spawn Waypoint Issues

If portal-based spawning doesn't work:

1. **Check waypoint exists** - Verify target waypoint is in destination scene
2. **Verify spawn_at_portal** - Ensure property is set to `true`
3. **Check scene transition** - Confirm `spawn_waypoint` is passed to scene change
4. **Review logs** - Look for waypoint resolution warnings

## Custom Player Implementation

If you need to replace the player plugin with a custom implementation, you can extend the `PlayerBasePlugin` abstract base class.

### PlayerBasePlugin

**Location:** [src/pedre/plugins/player/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/player/base.py)

The `PlayerBasePlugin` class defines the minimum interface that any player plugin must implement.

#### Required Methods

Your custom player plugin must implement these abstract methods:

```python
from pedre.plugins.player.base import PlayerBasePlugin
from pedre.sprites import AnimatedSprite

class CustomPlayerPlugin(PlayerBasePlugin):
    """Custom player implementation."""

    name = "player"
    dependencies = ["input", "waypoint"]

    def get_player_sprite(self) -> AnimatedSprite | None:
        """Get the player sprite."""
        ...
```

#### Registration

Register your custom player plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.player.base import PlayerBasePlugin

@PluginRegistry.register
class CustomPlayerPlugin(PlayerBasePlugin):
    name = "player"
    dependencies = ["input", "waypoint"]

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom plugin inherits from `BasePlugin` (via `PlayerBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"player_plugin"` in the base class
- Your implementation can use any sprite type or movement system
- Register your custom player plugin in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.player"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_player.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.player.base import PlayerBasePlugin

@PluginRegistry.register
class PhysicsPlayerPlugin(PlayerBasePlugin):
    """Player plugin with physics-based movement."""

    name = "player"
    dependencies = ["input", "waypoint", "physics"]

    def __init__(self):
        self.player_sprite = None
        self.velocity = (0, 0)
        # ... rest of initialization ...

    def get_player_sprite(self) -> AnimatedSprite | None:
        return self.player_sprite

    def update(self, delta_time: float) -> None:
        # Custom physics-based movement
        # ... physics calculations ...
        pass

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_player",  # Load custom player first
    "pedre.plugins.camera",
    "pedre.plugins.audio",
    # ... rest of plugins (omit "pedre.plugins.player") ...
]
```

## See Also

- [InputPlugin](input.md) - Keyboard input handling
- [CameraPlugin](camera.md) - Camera following
- [ScenePlugin](scene.md) - Scene transitions and spawning
- [WaypointPlugin](waypoint.md) - Waypoint plugin
- [Configuration Guide](../guides/configuration.md)
- [AnimatedSprite](../api/sprites.md)
