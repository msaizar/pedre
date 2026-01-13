"""Input management system for handling player controls.

This module provides the InputManager class, which handles keyboard input for player
movement and actions. It maintains the state of currently pressed keys and calculates
movement vectors with proper normalization for smooth, consistent player control.

The InputManager uses a key state tracking approach where keys are added to a set when
pressed and removed when released. This allows for:
- Simultaneous multi-key input (e.g., holding W+D for diagonal movement)
- Smooth movement without key repeat delays
- Consistent diagonal speed through vector normalization
- Clean state management when focus is lost

Key features:
- Supports both arrow keys and WASD for movement
- Normalizes diagonal movement to prevent faster diagonal speed
- Configurable movement speed
- Simple key state queries for action keys (e.g., interaction, inventory)

The movement calculation uses vector normalization to ensure diagonal movement is the
same speed as cardinal movement. Without normalization, moving diagonally would be
√2 times faster (≈1.414x) than moving straight, which feels unnatural in gameplay.

Example usage:
    # Create input manager with movement speed
    input_mgr = InputManager(movement_speed=3.0)

    # Wire up to arcade window events
    def on_key_press(symbol, modifiers):
        input_mgr.on_key_press(symbol)

    def on_key_release(symbol, modifiers):
        input_mgr.on_key_release(symbol)

    # In update loop, get movement
    dx, dy = input_mgr.get_movement_vector()
    player.center_x += dx
    player.center_y += dy

    # Check for action keys
    if input_mgr.is_key_pressed(arcade.key.E):
        interact_with_npc()
"""

import arcade


class InputManager:
    """Manages player input state and movement calculation.

    The InputManager provides a clean interface for handling keyboard input in the game.
    It tracks which keys are currently pressed and provides methods to query input state
    and calculate movement vectors.

    This class uses a set-based approach to track key states, which has several advantages:
    - O(1) lookups for checking if a key is pressed
    - Automatically handles multiple simultaneous key presses
    - No need to track key repeat events (continuous input is implicit)
    - Easy to clear all keys when window loses focus

    The manager supports both arrow keys and WASD for movement, making the controls
    accessible to players with different preferences. The movement calculation normalizes
    diagonal movement so it has the same speed as cardinal movement, preventing the
    common game feel issue where diagonal movement is faster.

    Attributes:
        movement_speed: Base movement speed in pixels per frame (default 3.0).
        keys_pressed: Set of currently pressed key symbols (arcade.key constants).
    """

    def __init__(self, movement_speed: float = 3.0) -> None:
        """Initialize the input manager with configurable movement speed.

        Creates a new InputManager with an empty key state. The movement speed determines
        how many pixels the player moves per frame when a movement key is held. This speed
        is applied to the normalized movement vector returned by get_movement_vector().

        The default speed of 3.0 pixels per frame provides smooth movement at 60 FPS,
        resulting in 180 pixels per second. Adjust this value to make the player feel
        faster or slower.

        Args:
            movement_speed: Base movement speed in pixels per frame. Higher values make
                          movement faster. Typical values range from 2.0 (slow) to 5.0 (fast).
                          Default is 3.0 for moderate speed.
        """
        self.movement_speed = movement_speed
        self.keys_pressed: set[int] = set()

    def on_key_press(self, symbol: int) -> None:
        """Register a key press event.

        Called when the player presses a key. This should be wired up to the arcade window's
        on_key_press callback. The key symbol is added to the internal set of pressed keys,
        which will affect the movement vector returned by get_movement_vector() and the
        result of is_key_pressed() queries.

        Adding the same key multiple times (e.g., from key repeat events) has no effect
        since the storage is a set.

        Args:
            symbol: The arcade key constant for the pressed key (e.g., arcade.key.W,
                   arcade.key.SPACE). These are integer constants defined in arcade.key.
        """
        self.keys_pressed.add(symbol)

    def on_key_release(self, symbol: int) -> None:
        """Register a key release event.

        Called when the player releases a key. This should be wired up to the arcade window's
        on_key_release callback. The key symbol is removed from the internal set of pressed
        keys, which will immediately affect movement calculations and key state queries.

        Uses discard() instead of remove() so releasing an unpressed key has no effect
        (no exception is raised). This handles edge cases where a key might be released
        after the manager was cleared or if release events arrive out of order.

        Args:
            symbol: The arcade key constant for the released key (e.g., arcade.key.W,
                   arcade.key.SPACE). These are integer constants defined in arcade.key.
        """
        self.keys_pressed.discard(symbol)

    def get_movement_vector(self) -> tuple[float, float]:
        """Calculate normalized movement vector from currently pressed keys.

        This is the core method for player movement. It examines the current key state
        and returns a velocity vector (dx, dy) that should be applied to the player sprite.

        The method supports both arrow keys and WASD:
        - UP/W: positive Y (move up)
        - DOWN/S: negative Y (move down)
        - RIGHT/D: positive X (move right)
        - LEFT/A: negative X (move left)

        When diagonal movement is detected (e.g., UP+RIGHT pressed simultaneously), the
        vector is normalized by multiplying by 1/√2 (≈0.707). This ensures diagonal
        movement has the same speed as cardinal movement, which is important for fair
        gameplay and natural feel.

        Without normalization:
        - Cardinal movement: speed = movement_speed
        - Diagonal movement: speed = movement_speed * √2 ≈ 1.414x faster

        With normalization (applied here):
        - Cardinal movement: speed = movement_speed
        - Diagonal movement: speed = movement_speed (same speed)

        The final vector is scaled by movement_speed before being returned.

        Returns:
            Tuple of (dx, dy) representing the movement delta in pixels per frame.
            - (0, 0) if no movement keys are pressed
            - Values scaled by movement_speed and normalized for diagonal movement
            - Example: (3.0, 0) for rightward movement at speed 3.0
            - Example: (2.12, 2.12) for diagonal up-right at speed 3.0 (≈3.0 magnitude)
        """
        dx = 0.0
        dy = 0.0

        # Check vertical movement
        if arcade.key.UP in self.keys_pressed or arcade.key.W in self.keys_pressed:
            dy += 1
        if arcade.key.DOWN in self.keys_pressed or arcade.key.S in self.keys_pressed:
            dy -= 1

        # Check horizontal movement
        if arcade.key.RIGHT in self.keys_pressed or arcade.key.D in self.keys_pressed:
            dx += 1
        if arcade.key.LEFT in self.keys_pressed or arcade.key.A in self.keys_pressed:
            dx -= 1

        # Normalize diagonal movement to prevent faster diagonal speed
        if dx != 0 and dy != 0:
            # Divide by sqrt(2) to normalize diagonal movement
            # This ensures diagonal speed equals straight speed
            normalizer = 0.7071067811865476  # 1/sqrt(2)
            dx *= normalizer
            dy *= normalizer

        # Apply movement speed
        dx *= self.movement_speed
        dy *= self.movement_speed

        return dx, dy

    def is_key_pressed(self, symbol: int) -> bool:
        """Check if a specific key is currently pressed.

        This method provides a simple way to query whether a particular key is currently
        being held down. It's useful for checking action keys that aren't related to
        movement, such as interaction keys, inventory keys, or menu keys.

        The query is O(1) since keys_pressed is a set, making it efficient to call
        multiple times per frame.

        Common usage patterns:
        - Interaction: is_key_pressed(arcade.key.E) or is_key_pressed(arcade.key.SPACE)
        - Inventory: is_key_pressed(arcade.key.I) or is_key_pressed(arcade.key.TAB)
        - Menu: is_key_pressed(arcade.key.ESCAPE)

        Args:
            symbol: The arcade key constant to check (e.g., arcade.key.E, arcade.key.SPACE).

        Returns:
            True if the key is currently pressed (held down), False otherwise.
        """
        return symbol in self.keys_pressed

    def clear(self) -> None:
        """Clear all pressed keys from the input state.

        This method removes all keys from the pressed state, effectively resetting the
        input manager as if no keys are being held. This is essential for handling
        window focus changes and preventing stuck keys.

        When to use this method:
        - Window loses focus: When the game window loses focus, the OS may not send key
          release events for keys that are released while the window is unfocused. Clearing
          on focus loss prevents "stuck" keys when the player returns.
        - Dialog opens: When showing a modal dialog or menu, clear keys to prevent
          movement input from affecting the player while in the UI.
        - Scene transitions: When changing maps or game states, clear keys to prevent
          carried-over input from the previous state.

        After calling clear(), get_movement_vector() will return (0, 0) and is_key_pressed()
        will return False for all keys until the player presses keys again.

        Example usage:
            # In window focus handler
            def on_deactivate(self):
                self.input_manager.clear()

            # Before showing dialog
            self.input_manager.clear()
            self.dialog_manager.show_dialog("npc", ["Hello!"])
        """
        self.keys_pressed.clear()
