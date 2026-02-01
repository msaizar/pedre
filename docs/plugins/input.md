# InputPlugin

Manages keyboard input state and movement calculation for player control.

## Location

- Implementation: [src/pedre/plugins/input/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/input/plugin.py)
- Base class: [src/pedre/plugins/input/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/input/base.py)

## Configuration

The InputPlugin uses the following settings from `pedre.conf.settings`:

### Movement Settings

- `PLAYER_MOVEMENT_SPEED` - Base movement speed in pixels per second (default: 180.0)

These can be overridden in your project's `settings.py`:

```python
# Custom input settings
PLAYER_MOVEMENT_SPEED = 250.0  # Faster player movement
```

## Public API

### Key Event Handling

#### on_key_press

`on_key_press(symbol: int, modifiers: int) -> bool`

Register a key press event.

**Parameters:**

- `symbol` - The arcade key constant for the pressed key (e.g., `arcade.key.UP`, `arcade.key.W`)
- `modifiers` - Bitfield of modifier keys held (e.g., `arcade.key.MOD_SHIFT`)

**Returns:**

- `True` if the event was handled and should not propagate further, `False` otherwise

**Example:**

```python
# Wire up to arcade window events
def on_key_press(symbol, modifiers):
    handled = input_plugin.on_key_press(symbol, modifiers)
    if not handled:
        # Handle other keys
        pass
```

**Notes:**

- Keys are added to the internal `keys_pressed` set for tracking
- Handles `arcade.key.ESCAPE` to publish `ShowMenuEvent` for the pause menu
- Returns `True` when handling ESCAPE to prevent further processing

#### on_key_release

`on_key_release(symbol: int, modifiers: int) -> bool`

Register a key release event.

**Parameters:**

- `symbol` - The arcade key constant for the released key
- `modifiers` - Bitfield of modifier keys held

**Returns:**

- `False` (allows other plugins to process if needed)

**Example:**

```python
# Wire up to arcade window events
def on_key_release(symbol, modifiers):
    input_plugin.on_key_release(symbol, modifiers)
```

**Notes:**

- Keys are removed from the internal `keys_pressed` set
- Uses `discard()` instead of `remove()` to avoid errors if key wasn't pressed

### Movement Calculation

#### get_movement_vector

`get_movement_vector(delta_time: float) -> tuple[float, float]`

Calculate normalized movement vector from currently pressed keys.

**Parameters:**

- `delta_time` - Time elapsed since last frame in seconds

**Returns:**

- Tuple of `(dx, dy)` representing the movement delta in pixels
  - `(0, 0)` if no movement keys are pressed
  - Values scaled by `movement_speed`, `delta_time`, and normalized for diagonal movement

**Example:**

```python
# In update loop, get movement
dx, dy = input_plugin.get_movement_vector(delta_time)
player.center_x += dx
player.center_y += dy
```

**Supported Keys:**

- **UP/W**: Positive Y (move up)
- **DOWN/S**: Negative Y (move down)
- **RIGHT/D**: Positive X (move right)
- **LEFT/A**: Negative X (move left)

**Notes:**

- Supports both arrow keys and WASD for movement
- Diagonal movement is automatically normalized to prevent faster diagonal speed
  - Without normalization: diagonal speed = `movement_speed × √2 ≈ 1.414x` faster
  - With normalization: diagonal speed = `movement_speed` (same as cardinal)
- The normalization multiplier is `1/√2 ≈ 0.707`
- Final vector is scaled by `movement_speed` and `delta_time` for frame-rate independent movement

### Key State Queries

#### is_key_pressed

`is_key_pressed(symbol: int) -> bool`

Check if a specific key is currently pressed.

**Parameters:**

- `symbol` - The arcade key constant to check (e.g., `arcade.key.E`, `arcade.key.SPACE`)

**Returns:**

- `True` if the key is currently pressed (held down), `False` otherwise

**Example:**

```python
# Check for action keys
if input_plugin.is_key_pressed(arcade.key.E):
    interact_with_npc()

if input_plugin.is_key_pressed(arcade.key.SPACE):
    player_jump()

if input_plugin.is_key_pressed(arcade.key.I):
    toggle_inventory()
```

**Notes:**

- Query is O(1) since `keys_pressed` is a set
- Efficient to call multiple times per frame

### State Management

#### clear

`clear() -> None`

Clear all pressed keys from the input state.

**Example:**

```python
# In window focus handler
def on_deactivate(self):
    input_plugin.clear()

# Before showing dialog
input_plugin.clear()
dialog_plugin.show_dialog("npc", ["Hello!"])
```

**Notes:**

- Removes all keys from the pressed state
- Essential for handling window focus changes to prevent "stuck" keys
- After calling `clear()`:
  - `get_movement_vector()` will return `(0, 0)`
  - `is_key_pressed()` will return `False` for all keys

**When to use:**

- **Window loses focus**: The OS may not send key release events for keys released while unfocused
- **Dialog opens**: Prevent movement input from affecting the player while in the UI
- **Scene transitions**: Prevent carried-over input from the previous state

### Save/Load Support

#### get_save_state

`get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing movement speed

**Example:**

```python
save_data = {
    "player_position": (x, y),
    "input": input_plugin.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Saves `movement_speed` in case it was modified at runtime
- Key press state is transient and not saved

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Restore state from save data.

**Parameters:**

- `state` - Dictionary containing saved input state

**Example:**

```python
input_plugin.restore_save_state(save_data["input"])
```

**Notes:**

- Restores `movement_speed` from saved state
- Falls back to `PLAYER_MOVEMENT_SPEED` setting if not present

## Supported Input

### Movement Keys

The InputPlugin supports two control schemes simultaneously:

| Arrow Keys | WASD | Direction               |
| ---------- | ---- | ----------------------- |
| UP         | W    | Move up (positive Y)    |
| DOWN       | S    | Move down (negative Y)  |
| RIGHT      | D    | Move right (positive X) |
| LEFT       | A    | Move left (negative X)  |

### Special Keys

- **ESCAPE**: Publishes `ShowMenuEvent` to open the pause menu

## Plugin Lifecycle

### setup

`setup(context: GameContext) -> None`

Initialize the input plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context

### cleanup

`cleanup() -> None`

Clean up input resources when the scene unloads.

**Notes:**

- Clears all pressed keys
- Called automatically by PluginLoader

## Custom Input Implementation

If you need to replace the input plugin with a custom implementation (e.g., for gamepad support, touch controls, or a different input handling approach), you can extend the `InputBasePlugin` abstract base class.

### InputBasePlugin

**Location:** [src/pedre/plugins/input/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/input/base.py)

The `InputBasePlugin` class defines the minimum interface that any input plugin must implement.

#### Required Methods

Your custom input plugin must implement this abstract method:

```python
from pedre.plugins.input.base import InputBasePlugin

class CustomInputPlugin(InputBasePlugin):
    """Custom input implementation."""

    name = "input"
    dependencies = []

    def get_movement_vector(self, delta_time: float) -> tuple[float, float]:
        """Calculate normalized movement vector.

        Args:
            delta_time: Time elapsed since last frame in seconds.
        """
        # Your custom implementation
        ...
```

#### Registration

Register your custom input plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.input.base import InputBasePlugin

@PluginRegistry.register
class GamepadInputPlugin(InputBasePlugin):
    name = "input"
    dependencies = []

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom plugin inherits from `BasePlugin` (via `InputBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, `get_save_state()`, and `restore_save_state()`
- The `role` attribute is set to `"input_plugin"` in the base class
- Your implementation can use any input method, not just keyboard
- The `get_movement_vector()` method is the minimum required interface
- You can add additional methods for action keys, button presses, etc.
- Register your custom input plugin in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.input"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_input.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.input.base import InputBasePlugin
from pedre.conf import settings
import arcade

@PluginRegistry.register
class GamepadInputPlugin(InputBasePlugin):
    """Custom gamepad-based input plugin."""

    name = "input"
    dependencies = []

    def __init__(self):
        self.movement_speed = settings.PLAYER_MOVEMENT_SPEED
        self.gamepad = None

    def setup(self, context):
        self.context = context
        joysticks = arcade.joysticks.get_joysticks()
        if joysticks:
            self.gamepad = joysticks[0]
            self.gamepad.open()

    def cleanup(self):
        if self.gamepad:
            self.gamepad.close()

    def get_save_state(self):
        return {"movement_speed": self.movement_speed}

    def restore_save_state(self, state):
        self.movement_speed = state.get("movement_speed", settings.PLAYER_MOVEMENT_SPEED)

    def get_movement_vector(self, delta_time: float) -> tuple[float, float]:
        if not self.gamepad:
            return 0.0, 0.0

        # Read analog stick with deadzone
        stick_x = self.gamepad.x
        stick_y = self.gamepad.y

        if abs(stick_x) < 0.15:
            stick_x = 0
        if abs(stick_y) < 0.15:
            stick_y = 0

        # Scale by movement speed and delta_time
        dx = stick_x * self.movement_speed * delta_time
        dy = stick_y * self.movement_speed * delta_time

        return dx, dy
```

```python
# In myproject/settings.py
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_input",  # Load custom input first
    "pedre.plugins.camera",
    "pedre.plugins.debug",
    # ... rest of plugins (omit "pedre.plugins.input") ...
]
```

## See Also

- [PlayerPlugin](player.md) - Player sprite and movement
- [DialogPlugin](dialog.md) - Conversation plugin
- [Configuration Guide](../guides/configuration.md)
