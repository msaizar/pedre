# InteractionManager

Manages interactive objects that players can interact with.

## Location

`src/pedre/systems/interaction.py`

## Initialization

```python
from pedre.systems.interaction import InteractionManager

interaction_manager = InteractionManager()
```

## Key Methods

### `register_object(obj: InteractiveObject) -> None`

Register an interactive object.

**Parameters:**

- `obj` - InteractiveObject instance

**Example:**

```python
from pedre.systems.interaction import InteractiveObject

chest = InteractiveObject(
    name="treasure_chest",
    position=(400, 300),
    interaction_type="item",
    properties={"item_name": "golden_key", "message": "You found a key!"}
)
interaction_manager.register_object(chest)
```

### `get_nearby_object(position: tuple[float, float], distance: float = 50) -> InteractiveObject | None`

Find an interactive object near a position.

**Parameters:**

- `position` - (x, y) coordinates to check
- `distance` - Maximum distance to check (default: 50 pixels)

**Returns:**

- `InteractiveObject` if one is found nearby
- `None` if no object within distance

**Example:**

```python
nearby = interaction_manager.get_nearby_object(player.position)
if nearby:
    print(f"Found {nearby.name}: {nearby.properties.get('message')}")
```

### `remove_object(name: str) -> None`

Remove an interactive object (e.g., after it's been used).

**Parameters:**

- `name` - Object identifier

**Example:**

```python
# After collecting an item
interaction_manager.remove_object("treasure_chest")
```

## Interactive Object Types

| Type | Description | Required Properties |
| ---- | ----------- | ------------------- |
| `"item"` | Gives player an item | `item_name`, `item_category` |
| `"message"` | Shows a message | `message` |
| `"toggle"` | Toggles layer visibility | `toggle_layer` |
