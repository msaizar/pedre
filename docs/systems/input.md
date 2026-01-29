# InputManager

Manages keyboard input state and movement calculation for player control.

## Location

- Implementation: `src/pedre/systems/input/manager.py`
- Base class: `src/pedre/systems/input/base.py`

## Configuration

The InputManager uses the following settings from `pedre.conf.settings`:

- `PLAYER_MOVEMENT_SPEED` - Base movement speed in pixels per frame (default: 3.0)

This can be overridden in your project's `settings.py`:

```python
# Custom input settings
PLAYER_MOVEMENT_SPEED = 5.0  # Faster player movement
```

## Public API

### Key Event Handling

#### `on_key_press(symbol: int, modifiers: int) -> bool`

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
    handled = input_manager.on_key_press(symbol, modifiers)
    if not handled:
        # Handle other keys
        pass
```

**Notes:**

- Keys are added to the internal `keys_pressed` set for tracking
- Handles special keys like `arcade.key.ESCAPE` to trigger the pause menu
- Returns `True` when handling ESCAPE to prevent further processing

#### `on_key_release(symbol: int, modifiers: int) -> bool`

Register a key release event.

**Parameters:**

- `symbol` - The arcade key constant for the released key
- `modifiers` - Bitfield of modifier keys held

**Returns:**

- `False` (allows other systems to process if needed)

**Example:**

```python
# Wire up to arcade window events
def on_key_release(symbol, modifiers):
    input_manager.on_key_release(symbol, modifiers)
```

**Notes:**

- Keys are removed from the internal `keys_pressed` set
- Uses `discard()` instead of `remove()` to avoid errors if key wasn't pressed

### Movement Calculation

#### `get_movement_vector() -> tuple[float, float]`

Calculate normalized movement vector from currently pressed keys.

**Returns:**

- Tuple of `(dx, dy)` representing the movement delta in pixels per frame
  - `(0, 0)` if no movement keys are pressed
  - Values scaled by `movement_speed` and normalized for diagonal movement
  - Example: `(3.0, 0)` for rightward movement at speed 3.0
  - Example: `(2.12, 2.12)` for diagonal up-right at speed 3.0 (≈3.0 magnitude)

**Example:**

```python
# In update loop, get movement
dx, dy = input_manager.get_movement_vector()
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
  - Without normalization: diagonal speed = movement_speed × √2 ≈ 1.414x faster
  - With normalization: diagonal speed = movement_speed (same as cardinal)
- The normalization multiplier is 1/√2 ≈ 0.707
- Final vector is scaled by `movement_speed` before being returned

### Key State Queries

#### `is_key_pressed(symbol: int) -> bool`

Check if a specific key is currently pressed.

**Parameters:**

- `symbol` - The arcade key constant to check (e.g., `arcade.key.E`, `arcade.key.SPACE`)

**Returns:**

- `True` if the key is currently pressed (held down), `False` otherwise

**Example:**

```python
# Check for action keys
if input_manager.is_key_pressed(arcade.key.E):
    interact_with_npc()

if input_manager.is_key_pressed(arcade.key.SPACE):
    player_jump()

if input_manager.is_key_pressed(arcade.key.I):
    toggle_inventory()
```

**Notes:**

- Query is O(1) since `keys_pressed` is a set
- Efficient to call multiple times per frame
- Common usage patterns:
  - Interaction: `arcade.key.E` or `arcade.key.SPACE`
  - Inventory: `arcade.key.I` or `arcade.key.TAB`
  - Menu: `arcade.key.ESCAPE`

### State Management

#### `clear() -> None`

Clear all pressed keys from the input state.

**Example:**

```python
# In window focus handler
def on_deactivate(self):
    input_manager.clear()

# Before showing dialog
input_manager.clear()
dialog_manager.show_dialog("npc", ["Hello!"])
```

**Notes:**

- Removes all keys from the pressed state
- Essential for handling window focus changes to prevent "stuck" keys
- After calling `clear()`:
  - `get_movement_vector()` will return `(0, 0)`
  - `is_key_pressed()` will return `False` for all keys

**When to use:**

- **Window loses focus**: When the game window loses focus, the OS may not send key release events for keys that are released while unfocused. Clear on focus loss to prevent stuck keys.
- **Dialog opens**: When showing a modal dialog or menu, clear keys to prevent movement input from affecting the player while in the UI.
- **Scene transitions**: When changing maps or game states, clear keys to prevent carried-over input from the previous state.

## Supported Input

### Movement Keys

The InputManager supports two control schemes simultaneously:

| Arrow Keys | WASD | Direction |
| ---------- | ---- | ----------- |
| UP | W | Move up (positive Y) |
| DOWN | S | Move down (negative Y) |
| RIGHT | D | Move right (positive X) |
| LEFT | A | Move left (negative X) |

### Special Keys

- **ESCAPE**: Opens pause menu (handled automatically by InputManager)

## Movement Speed Normalization

The InputManager ensures consistent movement speed in all directions through vector normalization.

### The Problem

Without normalization, diagonal movement is faster than cardinal movement:

- Cardinal movement (e.g., pressing UP): speed = `movement_speed`
- Diagonal movement (e.g., pressing UP+RIGHT): speed = `movement_speed × √2 ≈ 1.414×` faster

This is because when moving diagonally, both dx and dy are non-zero, creating a longer vector.

### The Solution

The InputManager detects diagonal movement and multiplies both components by `1/√2 ≈ 0.707`:

```python
if dx != 0 and dy != 0:
    normalizer = 0.7071067811865476  # 1/sqrt(2)
    dx *= normalizer
    dy *= normalizer
```

This ensures that the magnitude of the movement vector is the same for both cardinal and diagonal movement, resulting in consistent player speed regardless of direction.

## Key State Tracking

The InputManager uses a set-based approach to track key states:

```python
self.keys_pressed: set[int] = set()
```

### Advantages

- **O(1) lookups**: Checking if a key is pressed is constant time
- **Automatic deduplication**: Key repeat events don't cause issues
- **Multiple simultaneous inputs**: Supports holding multiple keys at once (e.g., W+D for diagonal movement)
- **Easy to clear**: Simple `clear()` operation removes all keys

### Implementation Details

- Keys are added to the set on `on_key_press()`
- Keys are removed from the set on `on_key_release()`
- `get_movement_vector()` checks the set to determine which movement keys are pressed
- `is_key_pressed()` queries the set directly

## Custom Input Implementation

If you need to replace the input system with a custom implementation (e.g., for gamepad support, touch controls, or a different input handling approach), you can extend the `InputBaseManager` abstract base class.

### InputBaseManager

**Location:** `src/pedre/systems/input/base.py`

The `InputBaseManager` class defines the minimum interface that any input manager must implement. All methods are abstract and must be implemented by your custom class.

#### Required Methods

Your custom input manager must implement this abstract method:

```python
from pedre.systems.input.base import InputBaseManager

class CustomInputManager(InputBaseManager):
    """Custom input implementation."""

    name = "input"
    dependencies = []

    def get_movement_vector(self) -> tuple[float, float]:
        """Calculate normalized movement vector."""
        # Your custom implementation
        ...
```

#### Registration

Register your custom input manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.input.base import InputBaseManager

@SystemRegistry.register
class GamepadInputManager(InputBaseManager):
    name = "input"
    dependencies = []

    def __init__(self):
        self.gamepad = initialize_gamepad()
        # ... rest of initialization ...

    def get_movement_vector(self) -> tuple[float, float]:
        # Read gamepad analog stick
        stick_x, stick_y = self.gamepad.get_left_stick()

        # Apply deadzone
        if abs(stick_x) < 0.15:
            stick_x = 0
        if abs(stick_y) < 0.15:
            stick_y = 0

        # Scale by movement speed
        dx = stick_x * self.movement_speed
        dy = stick_y * self.movement_speed

        return dx, dy

    # ... implement other BaseSystem methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `InputBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `cleanup()`, `get_save_state()`, and `restore_save_state()`
- The `role` attribute is set to `"input_manager"` in the base class
- Your implementation can use any input method, not just keyboard
- The `get_movement_vector()` method is the minimum required interface
- You can add additional methods for action keys, button presses, etc.
- Register your custom input manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.input"` to replace it

**Example Custom Implementation:**

```python
# In myproject/systems/custom_input.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.input.base import InputBaseManager
from pedre.conf import settings
import arcade

@SystemRegistry.register
class GamepadInputManager(InputBaseManager):
    """Custom gamepad-based input manager."""

    name = "input"
    dependencies = []

    def __init__(self):
        self.movement_speed = settings.PLAYER_MOVEMENT_SPEED
        self.gamepad = None
        self.action_buttons = {}

    def setup(self, context):
        self.context = context
        # Initialize gamepad
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

    def get_movement_vector(self) -> tuple[float, float]:
        if not self.gamepad:
            return 0.0, 0.0

        # Read analog stick with deadzone
        stick_x = self.gamepad.x
        stick_y = self.gamepad.y

        if abs(stick_x) < 0.15:
            stick_x = 0
        if abs(stick_y) < 0.15:
            stick_y = 0

        # Scale by movement speed
        dx = stick_x * self.movement_speed
        dy = stick_y * self.movement_speed

        return dx, dy

    def is_button_pressed(self, button_index: int) -> bool:
        """Check if a gamepad button is pressed."""
        if not self.gamepad:
            return False
        return self.gamepad.buttons[button_index]
```

```python
# In myproject/settings.py
INSTALLED_SYSTEMS = [
    "myproject.systems.custom_input",  # Load custom input first
    "pedre.systems.camera",
    "pedre.systems.debug",
    # ... rest of systems (omit "pedre.systems.input") ...
]
```

## Integration with Other Systems

The InputManager is designed to work seamlessly with other Pedre systems:

### GameView Integration

The InputManager is automatically registered with the GameView's input handlers:

```python
# GameView automatically wires up InputManager
def on_key_press(self, symbol: int, modifiers: int):
    # InputManager.on_key_press() is called automatically
    pass

def on_key_release(self, symbol: int, modifiers: int):
    # InputManager.on_key_release() is called automatically
    pass
```

### Player Movement

In your update loop, use the InputManager to move the player:

```python
def on_update(self, delta_time: float):
    # Get movement from input manager
    dx, dy = self.input_manager.get_movement_vector()

    # Apply to player position
    self.player.center_x += dx
    self.player.center_y += dy

    # Update player animation based on movement
    if dx != 0 or dy != 0:
        self.player.update_animation(delta_time)
```

### Dialog System

The InputManager should be cleared when dialogs are shown to prevent player movement during conversations:

```python
# Before showing dialog
self.input_manager.clear()
self.dialog_manager.show_dialog("npc", ["Hello, traveler!"])
```

### Escape Key Handling

The InputManager automatically publishes a `ShowMenuEvent` when ESCAPE is pressed, which the ViewManager subscribes to:

```python
# In InputManager.on_key_press()
if symbol == arcade.key.ESCAPE:
    self.context.event_bus.publish(ShowMenuEvent(from_game_pause=True))
    return True
```

## Example Usage

### Basic Setup

```python
from pedre.systems.input import InputManager
from pedre.systems.game_context import GameContext

# Create input manager
input_manager = InputManager()

# Setup with game context
context = GameContext(view_manager=view_manager, event_bus=event_bus)
input_manager.setup(context)
```

### Movement Loop

```python
def on_update(self, delta_time: float):
    # Get movement vector
    dx, dy = self.input_manager.get_movement_vector()

    # Apply to player
    self.player.center_x += dx
    self.player.center_y += dy

    # Check for action keys
    if self.input_manager.is_key_pressed(arcade.key.E):
        self.check_npc_interaction()

    if self.input_manager.is_key_pressed(arcade.key.I):
        self.toggle_inventory()
```

### Window Focus Handling

```python
def on_deactivate(self):
    """Called when window loses focus."""
    # Clear all keys to prevent stuck inputs
    self.input_manager.clear()

def on_activate(self):
    """Called when window gains focus."""
    # No need to do anything - keys will be tracked normally
    pass
```

### Dialog Integration

```python
def show_conversation(self, npc_name: str, text: list[str]):
    # Clear input state before dialog
    self.input_manager.clear()

    # Show dialog
    self.dialog_manager.show_dialog(npc_name, text)

    # Input will be blocked while dialog is showing
```
