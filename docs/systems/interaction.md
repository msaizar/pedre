# InteractionManager

Manages interactive objects that players can activate in the game world.

## Location

- Implementation: `src/pedre/systems/interaction/manager.py`
- Base class: `src/pedre/systems/interaction/base.py`

## Configuration

The InteractionManager uses the following settings from `pedre.conf.settings`:

### Distance Settings

- `INTERACTION_MANAGER_DISTANCE` - Maximum distance in pixels for player to interact with objects (default: 50)

### Input Settings

- `INTERACTION_KEY` - Key for interacting with objects (default: `"SPACE"`)

These can be overridden in your project's `settings.py`:

```python
# Custom interaction settings
INTERACTION_MANAGER_DISTANCE = 64  # Increase interaction range
INTERACTION_KEY = "E"
```

## Public API

### Object Registration

#### `register_object(sprite: arcade.Sprite, name: str, properties: dict) -> None`

Register an interactive object in the manager.

**Parameters:**

- `sprite` - The arcade Sprite representing this object visually. The sprite's position (center_x, center_y) is used for distance calculations
- `name` - Unique identifier for this object. Used for lookups and tracking. Should match the object's name in Tiled for consistency
- `properties` - Dictionary of custom properties from Tiled. The entire dictionary is stored with the object for flexible configuration

**Example:**

```python
# From map loading code
for obj in tiled_map.object_lists["Interactive"]:
    interaction_mgr.register_object(
        sprite=obj.sprite,
        name=obj.name,
        properties=obj.properties
    )
```

**Notes:**

- Objects are stored by name, so each name must be unique within the manager
- Registering an object with an existing name will overwrite the previous object
- Typically called during map loading when processing Tiled object layers

### Object Queries

#### `get_nearby_object(player_sprite: arcade.Sprite) -> InteractiveObject | None`

Get the nearest interactive object within interaction distance.

**Parameters:**

- `player_sprite` - The player's arcade Sprite. The sprite's center_x and center_y are used as the player's position for distance calculations

**Returns:**

- The nearest `InteractiveObject` within `interaction_distance`, or `None` if no objects are in range
- When multiple objects are equidistant (rare), returns whichever was checked first

**Example:**

```python
# In game update loop
if input_mgr.is_key_pressed(arcade.key.E):
    nearby_obj = interaction_mgr.get_nearby_object(self.player_sprite)
    if nearby_obj:
        interaction_mgr.handle_interaction(nearby_obj)
    else:
        # Optional: Show "nothing to interact with" message
        pass
```

**Notes:**

- Uses Euclidean distance (straight-line distance) to determine proximity
- When multiple objects are within range, the nearest one is selected automatically
- Distance calculation uses center points of both the player sprite and object sprites
- Larger sprites may feel like they have a shorter interaction range since their edges are further from their centers

#### `get_interactive_objects() -> dict[str, InteractiveObject]`

Get all registered interactive objects.

**Returns:**

- Dictionary mapping object names to `InteractiveObject` instances

**Example:**

```python
# Get all interactive objects
objects = interaction_mgr.get_interactive_objects()
for name, obj in objects.items():
    print(f"Object: {name} at ({obj.sprite.center_x}, {obj.sprite.center_y})")
```

**Notes:**

- Returns the internal dictionary reference (not a copy)
- Useful for debugging or custom interaction logic

### Interaction Handling

#### `handle_interaction(obj: InteractiveObject) -> bool`

Handle interaction with an object by publishing an event.

**Parameters:**

- `obj` - The `InteractiveObject` to interact with

**Returns:**

- `True` when the interaction is handled

**Example:**

```python
obj = interaction_mgr.get_nearby_object(player_sprite)
if obj:
    success = interaction_mgr.handle_interaction(obj)
    if success:
        audio_mgr.play_sfx("interact.wav")
```

**Notes:**

- Publishes an `ObjectInteractedEvent` on the event bus
- Marks the object as interacted with using `mark_as_interacted()`
- Actual interaction behavior is typically handled by script system listening to the event

### Interaction State

#### `mark_as_interacted(object_name: str) -> None`

Mark an object as interacted with.

**Parameters:**

- `object_name` - Name of the object

**Example:**

```python
# Manually mark an object as interacted
interaction_mgr.mark_as_interacted("treasure_chest")
```

**Notes:**

- Automatically called by `handle_interaction()`
- Used for tracking interaction state (e.g., one-time interactions)

#### `has_interacted_with(object_name: str) -> bool`

Check if an object has been interacted with.

**Parameters:**

- `object_name` - Name of the object to check

**Returns:**

- `True` if the object has been interacted with, `False` otherwise

**Example:**

```python
# Check if player has already opened the chest
if not interaction_mgr.has_interacted_with("treasure_chest"):
    # First time opening
    show_treasure_animation()
else:
    # Already opened
    show_empty_chest()
```

**Notes:**

- Interaction state is persisted in save files
- Useful for one-time interactions or quest progression

### State Management

#### `clear() -> None`

Clear all registered interactive objects from the manager.

**Example:**

```python
# When loading a new map
interaction_mgr.clear()  # Remove old map's objects

# Load new map
new_map = load_tiled_map("new_level.tmx")

# Register new map's interactive objects
for obj in new_map.object_lists.get("Interactive", []):
    interaction_mgr.register_object(obj.sprite, obj.name, obj.properties)
```

**Notes:**

- Removes all interactive objects from the registry
- Typically called when transitioning between maps or scenes
- After calling `clear()`, `get_nearby_object()` will always return `None` until new objects are registered
- Important cleanup step to prevent memory leaks

#### `reset() -> None`

Reset both interactive objects and interaction state.

**Example:**

```python
# Complete reset (new game)
interaction_mgr.reset()
```

**Notes:**

- Clears both `interactive_objects` and `interacted_objects`
- More thorough than `clear()` which only removes object registrations
- Use when starting a new game or resetting all state

### Input Handling

#### `on_key_press(symbol: int, modifiers: int) -> bool`

Handle interaction input.

**Parameters:**

- `symbol` - Arcade key constant
- `modifiers` - Modifier key bitfield

**Returns:**

- `True` if interaction occurred, `False` otherwise

**Example:**

```python
# Automatically called by GameView
def on_key_press(self, symbol: int, modifiers: int):
    # InteractionManager.on_key_press() is called automatically
    pass
```

**Notes:**

- Automatically checks for nearby objects when the configured `INTERACTION_KEY` is pressed (default: SPACE)
- Calls `handle_interaction()` if an object is found
- Returns `True` if interaction occurred to prevent further processing

### Tiled Integration

#### `load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load interactive objects from a Tiled map's "Interactive" layer.

**Parameters:**

- `tile_map` - Loaded TileMap with object layers
- `arcade_scene` - Scene created from tile_map (unused)

**Notes:**

- Automatically called by the scene system when loading maps
- Looks for an object layer named "Interactive"
- Each object in the layer is automatically registered
- Objects without names are skipped

**Tiled Configuration:**

1. Create an Object Layer named "Interactive"
2. Add objects (rectangles, polygons, etc.) to represent interaction zones
3. Set object properties:
   - `name` (required): Unique identifier for the object

**Example Tiled Setup:**

```yaml
# Object Layer: Interactive
Objects:
  - name: "town_sign"
    type: "object"
    x: 320
    y: 240
    width: 32
    height: 32
```

## InteractiveObject

The `InteractiveObject` dataclass represents an interactive element in the game world.

**Location:** `src/pedre/systems/interaction/base.py`

**Attributes:**

- `sprite: arcade.Sprite` - The arcade Sprite representing this object in the game world
- `name: str` - Unique identifier for this object
- `properties: dict` - Dictionary of custom properties from Tiled or code

**Example:**

```python
from pedre.systems.interaction.base import InteractiveObject

# Create manually (usually created by register_object)
obj = InteractiveObject(
    sprite=my_sprite,
    name="mysterious_lever",
    properties={"message": "A rusty lever..."}
)
```

## Distance-Based Interaction

The InteractionManager uses Euclidean distance to determine if objects are within range.

### How It Works

1. When player presses the configured `INTERACTION_KEY` (default: SPACE), the manager:
   - Calculates distance from player to each registered object
   - Filters objects within `interaction_distance`
   - Selects the nearest object
   - Publishes `ObjectInteractedEvent` for that object

2. Distance calculation:

   ```python
   dx = player.center_x - object.sprite.center_x
   dy = player.center_y - object.sprite.center_y
   distance = (dx**2 + dy**2) ** 0.5
   ```

3. If `distance < interaction_distance`, the object is considered "nearby"

### Choosing Interaction Distance

Common values based on 32x32 tile size:

| Distance | Tiles | Use Case |
| -------- | ----- | ----------- |
| 32 | 1 tile | Very precise interaction (requires standing on/next to object) |
| 50 | ~1.5 tiles | Default - comfortable for most games |
| 64 | 2 tiles | More forgiving - good for larger sprites |
| 96 | 3 tiles | Very forgiving - good for open areas |

**Recommendation:** Start with the default (50) and adjust based on playtesting feedback.

## Event-Driven Interaction

The InteractionManager publishes events rather than handling interactions directly.

### ObjectInteractedEvent

When an object is interacted with, an `ObjectInteractedEvent` is published:

```python
from pedre.systems.interaction.events import ObjectInteractedEvent

# Published automatically by handle_interaction()
event = ObjectInteractedEvent(object_name="town_sign")
```

**Attributes:**

- `object_name: str` - Name of the interacted object

### Handling Interactions

Interactions are typically handled by the script system:

```json
{
  "event_type": "object_interacted",
  "conditions": [
    {
      "type": "object_name_equals",
      "object_name": "town_sign"
    }
  ],
  "actions": [
    {
      "type": "dialog",
      "npc_name": "Sign",
      "text": ["Welcome to Peaceful Village!"]
    }
  ]
}
```

This decoupled approach allows designers to configure interactions in data files without modifying code.

## Custom Interaction Implementation

If you need to replace the interaction system with a custom implementation (e.g., for different interaction mechanics, targeting systems, or UI), you can extend the `InteractionBaseManager` abstract base class.

### InteractionBaseManager

**Location:** `src/pedre/systems/interaction/base.py`

The `InteractionBaseManager` class defines the minimum interface that any interaction manager must implement.

#### Required Methods

Your custom interaction manager must implement these abstract methods:

```python
from pedre.systems.interaction.base import InteractionBaseManager, InteractiveObject

class CustomInteractionManager(InteractionBaseManager):
    """Custom interaction implementation."""

    name = "interaction"
    dependencies = []

    def get_interactive_objects(self) -> dict[str, InteractiveObject]:
        """Get interactive objects."""
        ...

    def has_interacted_with(self, object_name: str) -> bool:
        """Check if an object has been interacted with."""
        ...
```

#### Registration

Register your custom interaction manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.interaction.base import InteractionBaseManager, InteractiveObject

@SystemRegistry.register
class TargetedInteractionManager(InteractionBaseManager):
    """Custom interaction manager with cursor targeting."""

    name = "interaction"
    dependencies = []

    def __init__(self):
        self.interactive_objects = {}
        self.interacted_objects = set()
        self.targeted_object = None

    def get_interactive_objects(self) -> dict[str, InteractiveObject]:
        return self.interactive_objects

    def has_interacted_with(self, object_name: str) -> bool:
        return object_name in self.interacted_objects

    def on_mouse_motion(self, x: float, y: float):
        """Update targeted object based on cursor position."""
        # Custom targeting logic
        for name, obj in self.interactive_objects.items():
            if self.point_in_sprite(x, y, obj.sprite):
                self.targeted_object = obj
                return
        self.targeted_object = None

    def on_mouse_press(self, x: float, y: float, button: int):
        """Interact with targeted object on click."""
        if self.targeted_object and button == arcade.MOUSE_BUTTON_LEFT:
            self.handle_interaction(self.targeted_object)

    # ... implement other BaseSystem methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `InteractionBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `cleanup()`, `get_save_state()`, and `restore_save_state()`
- The `role` attribute is set to `"interaction_manager"` in the base class
- Your implementation can use any interaction method (distance-based, targeting, UI menus, etc.)
- The two abstract methods (`get_interactive_objects()` and `has_interacted_with()`) are the minimum required interface
- Register your custom interaction manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.interaction"` to replace it

**Example Custom Implementation:**

```python
# In myproject/systems/custom_interaction.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.interaction.base import InteractionBaseManager, InteractiveObject
from pedre.conf import settings
import arcade

@SystemRegistry.register
class MenuInteractionManager(InteractionBaseManager):
    """Interaction manager with radial menu selection."""

    name = "interaction"
    dependencies = []

    def __init__(self):
        self.interaction_distance = settings.INTERACTION_MANAGER_DISTANCE
        self.interactive_objects = {}
        self.interacted_objects = set()
        self.nearby_objects = []
        self.selected_index = 0

    def setup(self, context):
        self.context = context

    def cleanup(self):
        self.interactive_objects.clear()

    def get_save_state(self):
        return {"interacted_objects": list(self.interacted_objects)}

    def restore_save_state(self, state):
        self.interacted_objects = set(state.get("interacted_objects", []))

    def get_interactive_objects(self) -> dict[str, InteractiveObject]:
        return self.interactive_objects

    def has_interacted_with(self, object_name: str) -> bool:
        return object_name in self.interacted_objects

    def update_nearby_objects(self, player_sprite):
        """Update list of nearby objects."""
        self.nearby_objects = []
        for obj in self.interactive_objects.values():
            dx = player_sprite.center_x - obj.sprite.center_x
            dy = player_sprite.center_y - obj.sprite.center_y
            distance = (dx**2 + dy**2) ** 0.5
            if distance < self.interaction_distance:
                self.nearby_objects.append(obj)

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle menu navigation and selection."""
        if symbol == arcade.key.TAB:
            # Cycle through nearby objects
            if self.nearby_objects:
                self.selected_index = (self.selected_index + 1) % len(self.nearby_objects)
            return True
        elif symbol == arcade.key.E:
            # Interact with selected object
            if self.nearby_objects and self.selected_index < len(self.nearby_objects):
                obj = self.nearby_objects[self.selected_index]
                self.handle_interaction(obj)
            return True
        return False

    def handle_interaction(self, obj: InteractiveObject):
        """Handle interaction with object."""
        self.interacted_objects.add(obj.name)
        self.context.event_bus.publish(ObjectInteractedEvent(object_name=obj.name))
```

```python
# In myproject/settings.py
INSTALLED_SYSTEMS = [
    "myproject.systems.custom_interaction",  # Load custom interaction first
    "pedre.systems.camera",
    "pedre.systems.input",
    # ... rest of systems (omit "pedre.systems.interaction") ...
]
```

## Integration with Other Systems

The InteractionManager is designed to work seamlessly with other Pedre systems:

### Script System

The primary way to handle interactions is through the script system:

```json
{
  "event_type": "object_interacted",
  "conditions": [
    {
      "type": "object_name_equals",
      "object_name": "treasure_chest"
    },
    {
      "type": "not_interacted_with",
      "object_name": "treasure_chest"
    }
  ],
  "actions": [
    {
      "type": "dialog",
      "npc_name": "System",
      "text": ["You found a health potion!"]
    },
    {
      "type": "add_to_inventory",
      "item_name": "health_potion",
      "image_path": "items/potion.png"
    },
    {
      "type": "play_sfx",
      "sound": "item_get.wav"
    }
  ]
}
```

### Input System

The InteractionManager automatically handles the configured `INTERACTION_KEY` for interactions. To use a different key, override it in your `settings.py`:

```python
# In your project's settings.py
INTERACTION_KEY = "E"
```

### Scene System Integration

The InteractionManager automatically loads objects from Tiled maps when scenes are loaded:

```python
# Automatically handled by scene system
scene_manager.load_level("village.tmx")
# Interactive objects from "Interactive" layer are registered automatically
```

## Example Usage

### Basic Setup

```python
from pedre.systems.interaction import InteractionManager
from pedre.systems.game_context import GameContext

# Create interaction manager
interaction_manager = InteractionManager()

# Setup with game context
context = GameContext(view_manager=view_manager, event_bus=event_bus)
interaction_manager.setup(context)
```

### Manual Object Registration

```python
# Create an interactive object manually
sprite = arcade.Sprite("sign.png")
sprite.center_x = 320
sprite.center_y = 240

interaction_manager.register_object(
    sprite=sprite,
    name="town_sign",
    properties={"message": "Welcome to town!"}
)
```

### Handling Interactions

```python
def on_key_press(self, symbol: int, modifiers: int):
    if symbol == arcade.key.E:
        # Find nearby object
        obj = self.interaction_manager.get_nearby_object(self.player_sprite)

        if obj:
            # Interact with object
            self.interaction_manager.handle_interaction(obj)
            # Event is published automatically for script system to handle
        else:
            print("Nothing to interact with")
```

### Checking Interaction State

```python
# Check if player has already interacted with an object
if interaction_manager.has_interacted_with("treasure_chest"):
    print("Chest is empty")
else:
    print("Chest contains treasure!")
```

### Scene Transitions

```python
def load_new_map(self, map_name: str):
    # Clear old objects
    self.interaction_manager.clear()

    # Load new map (InteractionManager will auto-register objects from Tiled)
    self.scene_manager.load_level(map_name)
```
