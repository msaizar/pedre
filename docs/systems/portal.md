# PortalManager

Handles map transitions and portal collision detection.

## Location

`src/pedre/systems/portal.py`

## Initialization

```python
from pedre.systems.portal import PortalManager

portal_manager = PortalManager()
```

## Key Methods

### `register_portal(name: str, bounds: tuple, target_map: str, target_portal: str, condition: dict | None = None) -> None`

Register a portal for map transitions.

**Parameters:**

- `name` - Unique portal identifier
- `bounds` - (x, y, width, height) rectangle
- `target_map` - Destination map filename
- `target_portal` - Waypoint name in destination map
- `condition` - Optional activation conditions

**Example:**

```python
portal_manager.register_portal(
    name="to_forest",
    bounds=(0, 300, 32, 128),
    target_map="forest.tmx",
    target_portal="from_village"
)
```

### `check_portal_collision(player: arcade.Sprite) -> tuple[str, str] | None`

Check if player is in a portal zone.

**Parameters:**

- `player` - Player sprite

**Returns:**

- Tuple of `(target_map, target_portal)` if in active portal
- `None` if not in any portal

**Example:**

```python
def on_update(self, delta_time):
    portal = self.portal_manager.check_portal_collision(self.player)
    if portal:
        target_map, target_portal = portal
        self.transition_to_map(target_map, target_portal)
```

### `set_condition_checker(checker: Callable) -> None`

Set a function to check portal activation conditions.

**Example:**

```python
def check_conditions(condition: dict) -> bool:
    if "require_item" in condition:
        return inventory_manager.has_item(condition["require_item"])
    return True

portal_manager.set_condition_checker(check_conditions)
```
