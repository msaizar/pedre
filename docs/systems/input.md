# InputManager

Keyboard input handling and movement vector calculation.

## Location

`src/pedre/systems/input.py`

## Initialization

```python
from pedre.systems.input import InputManager

input_manager = InputManager()
```

## Key Methods

### `update_key_state(key: int, pressed: bool) -> None`

Update the state of a key.

**Parameters:**

- `key` - Arcade key constant (e.g., `arcade.key.UP`)
- `pressed` - `True` if pressed, `False` if released

**Example:**

```python
def on_key_press(self, key, modifiers):
    self.input_manager.update_key_state(key, True)

def on_key_release(self, key, modifiers):
    self.input_manager.update_key_state(key, False)
```

### `get_movement_vector() -> tuple[float, float]`

Get normalized movement vector based on pressed keys.

**Returns:**

- Tuple of `(dx, dy)` in range -1.0 to 1.0

**Example:**

```python
dx, dy = input_manager.get_movement_vector()
player.center_x += dx * speed * delta_time
player.center_y += dy * speed * delta_time
```

### `is_action_pressed(action: str) -> bool`

Check if an action key is pressed.

**Parameters:**

- `action` - Action name (e.g., "interact", "menu", "run")

**Returns:**

- `True` if action key is pressed

**Example:**

```python
if input_manager.is_action_pressed("interact"):
    # Player pressed interact button
    interact_with_npc()
```
