# WaypointManager

Manages named positions in the map used for NPC navigation, player spawning, and portal destinations.

## Location

- Implementation: [src/pedre/systems/waypoint/manager.py](../../src/pedre/systems/waypoint/manager.py)
- Base class: [src/pedre/systems/waypoint/base.py](../../src/pedre/systems/waypoint/base.py)

## Overview

The WaypointManager is a simple but essential system that stores named positions (waypoints) from Tiled maps. Waypoints are used throughout the framework for:

- **Player spawning** - Portal destinations when transitioning between maps
- **NPC movement** - Target positions for pathfinding-based movement
- **Scripting** - Named locations for positioning entities in cutscenes

Waypoints are defined as Point objects in Tiled's "Waypoints" object layer and automatically loaded when a map is loaded.

## Public API

### Waypoint Retrieval

#### `get_waypoint(name: str) -> tuple[float, float] | None`

Get waypoint position by name.

**Parameters:**

- `name` - Waypoint name as defined in Tiled

**Returns:**

- Tuple of `(tile_x, tile_y)` in tile coordinates, or `None` if not found

**Example:**

```python
# Get waypoint position
waypoint = waypoint_manager.get_waypoint("town_center")
if waypoint:
    tile_x, tile_y = waypoint
    print(f"Town center is at tile ({tile_x}, {tile_y})")
```

**Notes:**

- Returns tile coordinates, not pixel coordinates
- Waypoint names are case-sensitive
- Returns `None` for non-existent waypoints

#### `get_waypoints() -> dict[str, tuple[float, float]]`

Get all waypoints in the current map.

**Returns:**

- Dictionary mapping waypoint names to `(tile_x, tile_y)` tuples

**Example:**

```python
# List all waypoints
for name, (x, y) in waypoint_manager.get_waypoints().items():
    print(f"{name}: tile ({x}, {y})")
```

**Notes:**

- Returns all waypoints loaded from the current map
- Dictionary is empty if no waypoints are loaded
- Waypoints are cleared when transitioning to a new map

### Tiled Integration

#### `load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load waypoints from Tiled map object layer.

**Parameters:**

- `tile_map` - The loaded Tiled map
- `arcade_scene` - The arcade Scene (not used for waypoints)

**Notes:**

- Called automatically by SystemLoader during map loading
- Looks for "Waypoints" object layer in the Tiled map
- Converts pixel coordinates to tile coordinates using `settings.TILE_SIZE`
- Only processes Point objects with valid `name` and `shape` properties
- Logs waypoint loading for debugging

### System Lifecycle

#### `setup(context: GameContext) -> None`

Initialize the waypoint system with game context.

**Parameters:**

- `context` - Game context providing access to other systems

**Notes:**

- Called automatically by SystemLoader
- Stores reference to game context

#### `reset() -> None`

Reset waypoint manager for new game.

**Notes:**

- Clears all waypoints
- Called when starting a new game

## Usage Examples

### Basic Waypoint Lookup

```python
# Get a specific waypoint
spawn_point = waypoint_manager.get_waypoint("player_spawn")
if spawn_point:
    tile_x, tile_y = spawn_point
    # Convert to pixel coordinates if needed
    pixel_x = tile_x * settings.TILE_SIZE
    pixel_y = tile_y * settings.TILE_SIZE
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
if waypoint_manager.get_waypoint(waypoint_name):
    print(f"Waypoint '{waypoint_name}' exists")
    # Proceed with movement or spawning
else:
    logger.warning(f"Waypoint '{waypoint_name}' not found in current map")
```

### Listing All Waypoints

```python
# Debug: List all available waypoints
waypoints = waypoint_manager.get_waypoints()
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
- **Automatic Conversion:** Pixel coordinates are automatically converted to tile coordinates

## Technical Details

### Coordinate System

Waypoints are stored in tile coordinates internally:

```python
# Tiled stores waypoints in pixel coordinates (e.g., x=320, y=240)
# WaypointManager converts to tile coordinates during loading:
tile_x = int(pixel_x // settings.TILE_SIZE)  # e.g., 320 // 32 = 10
tile_y = int(pixel_y // settings.TILE_SIZE)  # e.g., 240 // 32 = 7
```

This makes waypoints independent of tile size and easier to use with grid-based pathfinding.

### Loading Process

When a map is loaded:

1. SystemLoader calls `waypoint_manager.load_from_tiled(tile_map, scene)`
2. WaypointManager looks for "Waypoints" object layer
3. For each Point object in the layer:
   - Validates it has a `name` and `shape` property
   - Extracts pixel coordinates from `shape[0]` and `shape[1]`
   - Converts to tile coordinates using `settings.TILE_SIZE`
   - Stores in `waypoints` dictionary: `{name: (tile_x, tile_y)}`
4. Logs the number of waypoints loaded

### Storage

Waypoints are stored in a simple dictionary:

```python
self.waypoints: dict[str, tuple[float, float]] = {
    "player_spawn": (10.0, 7.0),
    "merchant_home": (20.0, 15.0),
    "from_village": (3.0, 3.0),
}
```

### Reset Behavior

Waypoints are automatically cleared when:

- A new map is loaded (via `reset()`)
- A new game is started (via `reset()`)

This ensures waypoints from one map don't carry over to another.

## Custom Waypoint Implementation

If you need to replace the waypoint system with a custom implementation, you can extend the `WaypointBaseManager` abstract base class.

### WaypointBaseManager

**Location:** [src/pedre/systems/waypoint/base.py](../../src/pedre/systems/waypoint/base.py)

The `WaypointBaseManager` class defines the minimum interface that any waypoint manager must implement.

#### Required Methods

Your custom waypoint manager must implement this abstract method:

```python
from pedre.systems.waypoint.base import WaypointBaseManager

class CustomWaypointManager(WaypointBaseManager):
    """Custom waypoint implementation."""

    name = "waypoint"
    dependencies = []

    def get_waypoints(self) -> dict[str, tuple[float, float]]:
        """Get all waypoints."""
        ...
```

#### Registration

Register your custom waypoint manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.waypoint.base import WaypointBaseManager

@SystemRegistry.register
class CustomWaypointManager(WaypointBaseManager):
    name = "waypoint"
    dependencies = []

    def get_waypoints(self) -> dict[str, tuple[float, float]]:
        # Return waypoints from custom storage
        return self.custom_waypoint_storage
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `WaypointBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"waypoint_manager"` in the base class
- Your implementation can use any storage system (database, JSON, CSV, etc.)
- Register your custom waypoint manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.waypoint"` to replace it

**Example Custom Implementation:**

```python
# In myproject/systems/custom_waypoint.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.waypoint.base import WaypointBaseManager

@SystemRegistry.register
class DatabaseWaypointManager(WaypointBaseManager):
    """Waypoint manager that stores waypoints in a database."""

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
INSTALLED_SYSTEMS = [
    "myproject.systems.custom_waypoint",  # Load custom waypoint first
    "pedre.systems.camera",
    "pedre.systems.audio",
    # ... rest of systems (omit "pedre.systems.waypoint") ...
]
```

## See Also

- [NPCManager](npc.md) - Uses waypoints for NPC movement
- [PortalManager](portal.md) - Uses waypoints for player spawning
- [ScriptManager](script.md) - Uses waypoints in scripted actions
- [Tiled Integration](../tiled-integration.md) - How to create waypoints in Tiled
- [Configuration Guide](../configuration.md) - Waypoint system settings
