# PathfindingManager

A* pathfinding for NPC navigation.

## Location

`src/pedre/systems/pathfinding/manager.py`

## Key Methods

### `find_path(start_x: float, start_y: float, end_x: int, end_y: int) -> deque[tuple[float, float]]`

Find a path between a pixel position and a target pixel position.

**Parameters:**

- `start_x`, `start_y` - Starting pixel position
- `end_x`, `end_y` - Target pixel coordinates

**Returns:**

- Deque of (x, y) pixel positions (waypoints)
- Empty deque if no path found

**Example:**

```python
path = pathfinding_manager.find_path(
    start_x=npc.center_x,
    start_y=npc.center_y,
    end_x=10,
    end_y=15
)
while path:
    next_point = path.popleft()
    # Move to next_point
```
