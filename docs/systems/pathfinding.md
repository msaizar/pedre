# PathfindingManager

A* pathfinding for NPC navigation.

## Location

`src/pedre/systems/pathfinding.py`

## Initialization

```python
from pedre.systems.pathfinding import PathfindingManager

pathfinding_manager = PathfindingManager(
    wall_list=self.wall_list,
    grid_size=32  # Should match tile size
)
```

## Key Methods

### `find_path(start: tuple[float, float], end: tuple[float, float]) -> list[tuple[float, float]]`

Find a path between two points.

**Parameters:**

- `start` - (x, y) starting position
- `end` - (x, y) destination position

**Returns:**

- List of (x, y) waypoints from start to end
- Empty list if no path found

**Example:**

```python
path = pathfinding_manager.find_path(
    start=(npc.center_x, npc.center_y),
    end=(target_x, target_y)
)
if path:
    # Move NPC along path
    for waypoint in path:
        move_to(waypoint)
```
