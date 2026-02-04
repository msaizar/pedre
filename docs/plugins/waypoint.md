# WaypointPlugin

Manages named positions in the map used for NPC navigation, player spawning, and portal destinations.

## Location

- Implementation: [src/pedre/plugins/waypoint/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/waypoint/plugin.py)
- Base class: [src/pedre/plugins/waypoint/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/waypoint/base.py)

## Overview

The WaypointPlugin is a simple but essential plugin that stores named positions (waypoints) from Tiled maps. Waypoints are used throughout the framework for:

- **Player spawning** - Portal destinations when transitioning between maps
- **NPC movement** - Target positions for pathfinding-based movement
- **Scripting** - Named locations for positioning entities in cutscenes

Waypoints are defined as Point objects in Tiled's "Waypoints" object layer and automatically loaded when a map is loaded.

## Configuration

The WaypointPlugin does not require any configuration settings. Waypoints are stored as pixel coordinates directly from the Tiled map.

## Public API

### Waypoint Retrieval

#### get_waypoint

`get_waypoint(name: str) -> tuple[float, float] | None`

Get waypoint position by name.

**Parameters:**

- `name` - Waypoint name as defined in Tiled

**Returns:**

- Tuple of `(pixel_x, pixel_y)` in pixel coordinates, or `None` if not found

**Example:**

```python
# Get waypoint position
waypoint = waypoint_plugin.get_waypoint("town_center")
if waypoint:
    pixel_x, pixel_y = waypoint
    print(f"Town center is at ({pixel_x}, {pixel_y})")
```

**Notes:**

- Returns pixel coordinates from Tiled map
- Waypoint names are case-sensitive
- Returns `None` for non-existent waypoints

#### get_waypoints

`get_waypoints() -> dict[str, tuple[float, float]]`

Get all waypoints in the current map.

**Returns:**

- Dictionary mapping waypoint names to `(pixel_x, pixel_y)` tuples

**Example:**

```python
# List all waypoints
for name, (x, y) in waypoint_plugin.get_waypoints().items():
    print(f"{name}: ({x}, {y})")
```

**Notes:**

- Returns all waypoints loaded from the current map
- Dictionary is empty if no waypoints are loaded
- Waypoints are cleared when transitioning to a new map

### Tiled Integration

#### load_from_tiled

`load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load waypoints from Tiled map object layer.

**Parameters:**

- `tile_map` - The loaded Tiled map
- `arcade_scene` - The arcade Scene (not used for waypoints)

**Notes:**

- Called automatically by PluginLoader during map loading
- Looks for "Waypoints" object layer in the Tiled map
- Stores pixel coordinates directly from Tiled map
- Only processes Point objects with valid `name` and `shape` properties
- Logs waypoint loading for debugging

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the waypoint plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context

#### reset

`reset() -> None`

Reset waypoint plugin for new game.

**Notes:**

- Clears all waypoints
- Called when starting a new game

## Usage Examples

### Basic Waypoint Lookup

```python
# Get a specific waypoint (returns pixel coordinates)
spawn_point = waypoint_plugin.get_waypoint("player_spawn")
if spawn_point:
    pixel_x, pixel_y = spawn_point
    print(f"Spawn point at ({pixel_x}, {pixel_y})")
```

### Using Waypoints in Scripts

Waypoints are commonly used in scripts for NPC movement:

```json
{
    "merchant_goes_home": {
        "scene": "village",
        "trigger": {
            "event": "time_of_day",
            "hour": 18
        },
        "actions": [
            {"type": "move_npc", "npcs": ["merchant"], "waypoint": "merchant_home"},
            {"type": "wait_for_movement", "npc": "merchant"}
        ]
    }
}
```

### Portal Destinations

Waypoints define where the player spawns after portal transitions:

**In Tiled (forest.tmx):**

```text
Waypoints Layer:
  - Point named "from_village" at (100, 200)
  - Point named "from_cave" at (500, 300)
```

**In Script:**

```json
{
    "village_to_forest": {
        "trigger": {"event": "portal_entered", "portal": "forest_entrance"},
        "actions": [
            {"type": "change_scene", "target_map": "forest.tmx", "spawn_waypoint": "from_village"}
        ]
    }
}
```

### Checking Waypoint Existence

```python
# Verify waypoint exists before using it
waypoint_name = "secret_cave"
if waypoint_plugin.get_waypoint(waypoint_name):
    print(f"Waypoint '{waypoint_name}' exists")
    # Proceed with movement or spawning
else:
    logger.warning(f"Waypoint '{waypoint_name}' not found in current map")
```

### Listing All Waypoints

```python
# Debug: List all available waypoints
waypoints = waypoint_plugin.get_waypoints()
if waypoints:
    print(f"Found {len(waypoints)} waypoints:")
    for name, (x, y) in waypoints.items():
        print(f"  {name}: ({x}, {y})")
else:
    print("No waypoints in this map")
```

## Tiled Map Setup

### Creating Waypoints in Tiled

1. **Create Waypoints Layer:**
   - Add an Object Layer named "Waypoints"
   - This layer should be at the top of the layer stack

2. **Add Point Objects:**
   - Select the Waypoints layer
   - Click "Insert Point" tool (or press I)
   - Click on the map where you want the waypoint
   - Set the `name` property for the point

3. **Naming Convention:**
   - Use descriptive names (e.g., "player_spawn", "merchant_home", "from_village")
   - Names should be lowercase with underscores
   - Names must be unique within the map

**Example Waypoint Setup:**

```text
Layer: Waypoints (Object Layer)

Points:
  - name: "player_spawn" at (320, 240)
  - name: "merchant_home" at (640, 480)
  - name: "from_village" at (100, 100)
  - name: "from_forest" at (750, 50)
  - name: "town_square" at (400, 300)
  - name: "inn_entrance" at (200, 450)
```

### Important Notes

- **Point Objects Only:** Waypoints must be Point objects, not rectangles or polygons
- **Name Required:** Each waypoint must have a `name` property set
- **No Duplicates:** Waypoint names must be unique within a map
- **Case Sensitive:** Waypoint names are case-sensitive in lookups
- **Pixel Coordinates:** Waypoints are stored as pixel coordinates directly from Tiled

## Technical Details

### Coordinate System

Waypoints are stored in pixel coordinates as they appear in Tiled:

```python
# Tiled stores waypoints in pixel coordinates (e.g., x=320.0, y=240.0)
# WaypointPlugin stores them directly as pixel coordinates:
self.waypoints["player_spawn"] = (320.0, 240.0)
```

This makes waypoints directly usable with sprite positions and pathfinding without manual conversion.

### Loading Process

When a map is loaded:

1. PluginLoader calls `waypoint_plugin.load_from_tiled(tile_map, scene)`
2. WaypointPlugin looks for "Waypoints" object layer
3. For each Point object in the layer:
   - Validates it has a `name` and `shape` property
   - Extracts pixel coordinates from `shape[0]` and `shape[1]`
   - Stores in `waypoints` dictionary: `{name: (pixel_x, pixel_y)}`
4. Logs the number of waypoints loaded

### Storage

Waypoints are stored in a simple dictionary:

```python
self.waypoints: dict[str, tuple[float, float]] = {
    "player_spawn": (320.0, 224.0),
    "merchant_home": (640.0, 480.0),
    "from_village": (96.0, 96.0),
}
```

### Reset Behavior

Waypoints are automatically cleared when:

- A new map is loaded (via `reset()`)
- A new game is started (via `reset()`)

This ensures waypoints from one map don't carry over to another.

## Custom Waypoint Implementation

If you need to replace the waypoint plugin with a custom implementation, you can extend the `WaypointBasePlugin` abstract base class.

### WaypointBasePlugin

**Location:** [src/pedre/plugins/waypoint/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/waypoint/base.py)

The `WaypointBasePlugin` class defines the minimum interface that any waypoint plugin must implement.

#### Required Methods

Your custom waypoint plugin must implement this abstract method:

```python
from pedre.plugins.waypoint.base import WaypointBasePlugin

class CustomWaypointPlugin(WaypointBasePlugin):
    """Custom waypoint implementation."""

    name = "waypoint"
    dependencies = []

    def get_waypoints(self) -> dict[str, tuple[float, float]]:
        """Get all waypoints."""
        ...
```

#### Registration

Register your custom waypoint plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.waypoint.base import WaypointBasePlugin

@PluginRegistry.register
class CustomWaypointPlugin(WaypointBasePlugin):
    name = "waypoint"
    dependencies = []

    def get_waypoints(self) -> dict[str, tuple[float, float]]:
        # Return waypoints from custom storage
        return self.custom_waypoint_storage
```

#### Notes on Custom Implementation

- Your custom plugin inherits from `BasePlugin` (via `WaypointBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"waypoint_plugin"` in the base class
- Your implementation can use any storage system (database, JSON, CSV, etc.)
- Register your custom waypoint plugin in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.waypoint"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_waypoint.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.waypoint.base import WaypointBasePlugin

@PluginRegistry.register
class DatabaseWaypointPlugin(WaypointBasePlugin):
    """Waypoint plugin that stores waypoints in a database."""

    name = "waypoint"
    dependencies = []

    def __init__(self):
        self.db = Database()
        # ... rest of initialization ...

    def get_waypoints(self) -> dict[str, tuple[float, float]]:
        # Query database for waypoints
        return self.db.query("SELECT name, x, y FROM waypoints")

    # ... implement other methods ...
```

```python
# In myproject/settings.py
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_waypoint",  # Load custom waypoint first
    "pedre.plugins.camera",
    "pedre.plugins.audio",
    # ... rest of plugins (omit "pedre.plugins.waypoint") ...
]
```

## See Also

- [NPCPlugin](npc.md) - Uses waypoints for NPC movement
- [PortalPlugin](portal.md) - Uses waypoints for player spawning
- [ScriptPlugin](script.md) - Uses waypoints in scripted actions
- [Configuration Guide](../guides/configuration.md)
- [Tiled Integration](../guides/tiled-integration.md)
