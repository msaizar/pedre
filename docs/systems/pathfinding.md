# PathfindingManager

A* pathfinding for NPC navigation.

## Location

`src/pedre/systems/pathfinding/manager.py`

## Initialization

```python
from pedre.systems.pathfinding import PathfindingManager

pathfinding_manager = PathfindingManager(
    wall_list=self.wall_list,
    grid_size=32  # Should match tile size
)
```

## Key Methods

### `find_path(start_x: float, start_y: float, end_tile_x: int, end_tile_y: int) -> deque[tuple[float, float]]`

Find a path between a pixel position and a target tile.

**Parameters:**

- `start_x`, `start_y` - Starting pixel position
- `end_tile_x`, `end_tile_y` - Target tile coordinates

**Returns:**

- Deque of (x, y) pixel positions (waypoints)
- Empty deque if no path found

**Example:**

```python
path = pathfinding_manager.find_path(
    start_x=npc.center_x,
    start_y=npc.center_y,
    end_tile_x=10,
    end_tile_y=15
)
while path:
    next_point = path.popleft()
    # Move to next_point
```
