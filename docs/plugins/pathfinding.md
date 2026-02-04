# PathfindingPlugin

A* pathfinding for NPC navigation on tile-based grids.

## Location

- Implementation: [src/pedre/plugins/pathfinding/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/pathfinding/plugin.py)
- Base class: [src/pedre/plugins/pathfinding/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/pathfinding/base.py)

## Configuration

The PathfindingPlugin uses the following settings from `pedre.conf.settings`:

### Tile Settings

- `TILE_SIZE` - Size of each tile in pixels, used for coordinate conversion between pixel and tile space

These can be overridden in your project's `settings.py`:

```python
# Custom tile settings
TILE_SIZE = 32
```

## Public API

### Pathfinding

#### find_path

`find_path(start_x: float, start_y: float, end_x: float, end_y: float, exclude_sprite: arcade.Sprite | None = None, exclude_sprites: list[arcade.Sprite] | None = None) -> deque[tuple[float, float]]`

Find a path between two pixel positions using A* with automatic retry logic.

**Parameters:**

- `start_x` - Starting pixel x position (world coordinates)
- `start_y` - Starting pixel y position (world coordinates)
- `end_x` - Target pixel x position (world coordinates)
- `end_y` - Target pixel y position (world coordinates)
- `exclude_sprite` - Single sprite to exclude from collision checks (typically the moving entity itself)
- `exclude_sprites` - Additional sprites to exclude from collision detection

**Returns:**

- Deque of (x, y) pixel positions (waypoints) from start to destination
- Empty deque if no path found even with NPC passthrough

**Example:**

```python
path = pathfinding_plugin.find_path(
    start_x=npc.center_x,
    start_y=npc.center_y,
    end_x=320.0,
    end_y=480.0,
    exclude_sprite=npc_sprite
)
while path:
    next_point = path.popleft()
    # Move to next_point
```

**Notes:**

- Uses a two-phase approach:
  1. First attempt: Normal pathfinding with only specified exclusions
  2. Second attempt: If first fails, retries with all NPC sprites excluded (passthrough)
- The NPC passthrough prevents permanent deadlocks where NPCs block each other's paths
- The returned path excludes the starting tile but includes the destination
- Path is returned as a deque for efficient `popleft()` operations during movement
- Uses Manhattan distance heuristic and 4-directional movement (up, down, left, right)

#### is_tile_walkable

`is_tile_walkable(tile_x: int | float, tile_y: int | float, exclude_sprite: arcade.Sprite | None = None, exclude_sprites: list[arcade.Sprite] | None = None) -> bool`

Check if a tile position is walkable (free of obstacles).

**Parameters:**

- `tile_x` - Tile x coordinate in grid space
- `tile_y` - Tile y coordinate in grid space
- `exclude_sprite` - Single sprite to ignore during collision check
- `exclude_sprites` - List of sprites to ignore during collision check

**Returns:**

- `True` if the tile is walkable, `False` if blocked by any wall sprite

**Example:**

```python
if pathfinding_plugin.is_tile_walkable(10, 15):
    print("Tile is free")

# Check walkability ignoring a specific NPC
if pathfinding_plugin.is_tile_walkable(10, 15, exclude_sprite=npc_sprite):
    print("Tile is free (ignoring NPC)")
```

**Notes:**

- Converts tile coordinates to pixel center for collision detection
- Checks against the wall list from the scene plugin
- Returns `True` if the wall list is not set (fail-safe behavior)
- The exclusion system prevents entities from blocking their own paths

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the pathfinding plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context

#### cleanup

`cleanup() -> None`

Clean up pathfinding resources when the scene unloads.

**Notes:**

- Called automatically by PluginLoader

## How It Works

The pathfinding plugin operates on a tile-based grid and converts between two coordinate systems:

- **Pixel coordinates**: World positions used by sprites (e.g., 320.0, 240.0)
- **Tile coordinates**: Grid positions used for pathfinding (e.g., 10, 7)

### Pathfinding Workflow

1. Convert start and end positions (pixels) to tile coordinates
2. Use A* to find optimal tile path avoiding walls
3. Convert tile path back to pixel coordinates (tile centers)
4. Return path as deque for efficient pop operations during movement

### A* Algorithm

The implementation uses the A* search algorithm with:

- **Priority queue** (heap) to explore tiles in order of estimated total cost
- **f_score = g_score + heuristic**, where:
  - `g_score`: Actual cost from start to current tile
  - `heuristic`: Manhattan distance from current tile to goal
- **4-directional movement** (up, down, left, right)
- **came_from map** to reconstruct the path when the goal is reached

### NPC Passthrough

When normal pathfinding fails (typically because NPCs are blocking the path), the plugin automatically retries with all NPC sprites excluded from collision checks. This prevents permanent deadlocks where NPCs block each other's paths, with the expectation that NPCs will move out of the way before collision occurs.

### Integration with Other Plugins

- **NPCPlugin** calls `find_path` when moving NPCs to waypoints
- **MoveNPCAction** triggers pathfinding via NPC plugin
- The wall list is obtained from the **ScenePlugin** via `get_wall_list()`

## Custom Pathfinding Implementation

If you need to replace the pathfinding plugin with a custom implementation, you can extend the `PathfindingBasePlugin` abstract base class.

### PathfindingBasePlugin

**Location:** [src/pedre/plugins/pathfinding/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/pathfinding/base.py)

The `PathfindingBasePlugin` class defines the minimum interface that any pathfinding plugin must implement.

#### Required Methods

Your custom pathfinding plugin must implement these abstract methods:

```python
from pedre.plugins.pathfinding.base import PathfindingBasePlugin

class CustomPathfindingPlugin(PathfindingBasePlugin):
    """Custom pathfinding implementation."""

    name = "pathfinding"
    dependencies = []

    def find_path(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        exclude_sprite: arcade.Sprite | None = None,
        exclude_sprites: list[arcade.Sprite] | None = None,
    ) -> deque[tuple[float, float]]:
        """Find a path using pathfinding."""
        ...
```

#### Registration

Register your custom pathfinding plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.pathfinding.base import PathfindingBasePlugin

@PluginRegistry.register
class CustomPathfindingPlugin(PathfindingBasePlugin):
    name = "pathfinding"
    dependencies = []

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom plugin inherits from `BasePlugin` (via `PathfindingBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"pathfinding_plugin"` in the base class
- Your implementation can use any pathfinding algorithm (Dijkstra, JPS, navmesh, etc.)
- Register your custom pathfinding plugin in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.pathfinding"` to replace it

```python
# In myproject/settings.py
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_pathfinding",  # Load custom pathfinding first
    "pedre.plugins.camera",
    "pedre.plugins.audio",
    # ... rest of plugins (omit "pedre.plugins.pathfinding") ...
]
```

## See Also

- [NPCPlugin](npc.md) - NPC movement uses pathfinding
- [ScenePlugin](scene.md) - Provides wall list for collision
- [Configuration Guide](../guides/configuration.md)
