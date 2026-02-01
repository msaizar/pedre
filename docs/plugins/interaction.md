# InteractionPlugin

Manages interactive objects that players can activate in the game world.

## Location

- Implementation: [src/pedre/plugins/interaction/manager.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/interaction/manager.py)
- Base class: [src/pedre/plugins/interaction/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/interaction/base.py)
- Events: [src/pedre/plugins/interaction/events.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/interaction/events.py)
- Conditions: [src/pedre/plugins/interaction/conditions.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/interaction/conditions.py)

## Configuration

The InteractionPlugin uses the following settings from `pedre.conf.settings`:

### Distance and Input Settings

- `INTERACTION_PLUGIN_DISTANCE` - Maximum distance in pixels for player to interact with objects (default: 50)
- `INTERACTION_KEY` - Key for interacting with objects (default: `"SPACE"`)

These can be overridden in your project's `settings.py`:

```python
# Custom interaction settings
INTERACTION_PLUGIN_DISTANCE = 64  # Increase interaction range
INTERACTION_KEY = "E"
```

## Public API

### Object Registration

#### register_object

`register_object(sprite: arcade.Sprite, name: str, properties: dict) -> None`

Register an interactive object in the manager.

**Parameters:**

- `sprite` - The arcade Sprite representing this object visually. The sprite's position (center_x, center_y) is used for distance calculations
- `name` - Unique identifier for this object. Should match the object's name in Tiled for consistency
- `properties` - Dictionary of custom properties from Tiled

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
- Usually called automatically by `load_from_tiled()`

### Object Queries

#### get_nearby_object

`get_nearby_object(player_sprite: arcade.Sprite) -> InteractiveObject | None`

Get the nearest interactive object within interaction distance.

**Parameters:**

- `player_sprite` - The player's arcade Sprite

**Returns:**

- The nearest `InteractiveObject` within `interaction_distance`, or `None` if no objects are in range

**Example:**

```python
nearby_obj = interaction_mgr.get_nearby_object(self.player_sprite)
if nearby_obj:
    interaction_mgr.handle_interaction(nearby_obj)
```

**Notes:**

- Uses Euclidean distance to determine proximity
- When multiple objects are within range, the nearest one is selected automatically
- Distance calculation uses center points of both the player sprite and object sprites

#### get_interactive_objects

`get_interactive_objects() -> dict[str, InteractiveObject]`

Get all registered interactive objects.

**Returns:**

- Dictionary mapping object names to `InteractiveObject` instances

**Example:**

```python
objects = interaction_mgr.get_interactive_objects()
for name, obj in objects.items():
    print(f"Object: {name} at ({obj.sprite.center_x}, {obj.sprite.center_y})")
```

### Interaction Handling

#### handle_interaction

`handle_interaction(obj: InteractiveObject) -> bool`

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
- Actual interaction behavior is typically handled by the script plugin listening to the event

### Interaction State

#### mark_as_interacted

`mark_as_interacted(object_name: str) -> None`

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

#### has_interacted_with

`has_interacted_with(object_name: str) -> bool`

Check if an object has been interacted with.

**Parameters:**

- `object_name` - Name of the object to check

**Returns:**

- `True` if the object has been interacted with, `False` otherwise

**Example:**

```python
if not interaction_mgr.has_interacted_with("treasure_chest"):
    show_treasure_animation()
else:
    show_empty_chest()
```

**Notes:**

- Interaction state is persisted in save files
- Useful for one-time interactions or quest progression

### State Management

#### clear

`clear() -> None`

Clear all registered interactive objects from the manager.

**Example:**

```python
# When loading a new map
interaction_mgr.clear()
```

**Notes:**

- Removes all interactive objects from the registry
- Does not clear the `interacted_objects` set
- After calling `clear()`, `get_nearby_object()` will always return `None` until new objects are registered

### Save/Load Support

#### get_save_state

`get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing the set of interacted object names

**Example:**

```python
save_data = {
    "player_position": (x, y),
    "interaction": interaction_mgr.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Saves the `interacted_objects` set as a list
- Object registrations are not saved (recreated from Tiled maps on load)

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Restore interacted objects set from save data.

**Parameters:**

- `state` - Dictionary containing saved interaction state

**Example:**

```python
interaction_mgr.restore_save_state(save_data["interaction"])
```

**Notes:**

- Restores the `interacted_objects` set
- Does not need sprites to exist (phase 1 restore)

## InteractiveObject

The `InteractiveObject` dataclass represents an interactive element in the game world.

**Location:** [src/pedre/plugins/interaction/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/interaction/base.py)

**Attributes:**

- `sprite: arcade.Sprite` - The arcade Sprite representing this object in the game world
- `name: str` - Unique identifier for this object
- `properties: dict` - Dictionary of custom properties from Tiled or code

**Example:**

```python
from pedre.plugins.interaction.base import InteractiveObject

obj = InteractiveObject(
    sprite=my_sprite,
    name="mysterious_lever",
    properties={"message": "A rusty lever..."}
)
```

## Events

### ObjectInteractedEvent

Published when player interacts with an interactive object.

**Attributes:**

- `object_name: str` - Name of the interacted object

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "object_interacted",
        "object_name": "treasure_chest"
    },
    "actions": [
        {"type": "dialog", "speaker": "Plugin", "text": ["You found a health potion!"]}
    ]
}
```

**Notes:**

- Fires after the object is marked as interacted
- The `object_name` filter is optional (omit to trigger for any object)

## Conditions

### object_interacted

Check if an object has been interacted with.

**Parameters:**

- `check`: `"object_interacted"`
- `object`: Name of the object to check
- `equals`: Expected value (default: true)

**Example:**

```json
{
    "trigger": {
        "event": "portal_entered",
        "portal": "exit"
    },
    "conditions": [
        {
            "check": "object_interacted",
            "object": "treasure_chest"
        }
    ]
}
```

**Check if NOT interacted:**

```json
{
    "check": "object_interacted",
    "object": "treasure_chest",
    "equals": false
}
```

**Use Cases:**

- Gating progression behind object interactions
- Quest prerequisites
- One-time interactions (e.g., treasure chests)

## Tiled Map Integration

Interactive objects can be placed in Tiled maps using object layers:

1. Create an "Interactive" object layer
2. Add objects (rectangles, polygons, etc.) to represent interaction zones
3. Set custom properties on each object:

**Required Properties:**

- `name` (string) - Unique identifier for the object (e.g., "town_sign")

**Example Tiled Setup:**

```yaml
# Object Layer: Interactive
Objects:
  - name: "town_sign"
    x: 320
    y: 240
    width: 32
    height: 32
```

## Plugin Lifecycle

### setup

`setup(context: GameContext) -> None`

Initialize the interaction plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context

### cleanup

`cleanup() -> None`

Clean up interaction resources when the scene unloads.

**Notes:**

- Clears all registered interactive objects
- Called automatically by PluginLoader

### reset

`reset() -> None`

Reset interaction plugin for new game.

**Notes:**

- Clears interactive objects and interaction history
- Called when starting a new game

### on_key_press

`on_key_press(symbol: int, modifiers: int) -> bool`

Handle key presses for object interaction.

**Parameters:**

- `symbol` - Arcade key constant
- `modifiers` - Modifier key bitfield

**Returns:**

- `True` if interaction occurred

**Notes:**

- Called automatically by PluginLoader
- Checks for `INTERACTION_KEY` press (default: SPACE)
- Finds nearby object and triggers interaction

### load_from_tiled

`load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load interactive objects from Tiled map object layer.

**Parameters:**

- `tile_map` - The loaded Tiled map
- `arcade_scene` - The arcade Scene

**Notes:**

- Called automatically by PluginLoader
- Looks for "Interactive" object layer
- Creates sprites from object geometry
- Objects without names are skipped

## Custom Interaction Implementation

If you need to replace the interaction plugin with a custom implementation (e.g., for different interaction mechanics, targeting plugins, or UI), you can extend the `InteractionBasePlugin` abstract base class.

### InteractionBasePlugin

**Location:** [src/pedre/plugins/interaction/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/interaction/base.py)

The `InteractionBasePlugin` class defines the minimum interface that any interaction manager must implement.

#### Required Methods

Your custom interaction manager must implement these abstract methods:

```python
from pedre.plugins.interaction.base import InteractionBasePlugin, InteractiveObject

class CustomInteractionPlugin(InteractionBasePlugin):
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

Register your custom interaction manager using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.interaction.base import InteractionBasePlugin, InteractiveObject

@PluginRegistry.register
class TargetedInteractionPlugin(InteractionBasePlugin):
    """Custom interaction manager with cursor targeting."""

    name = "interaction"
    dependencies = []

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BasePlugin` (via `InteractionBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, `get_save_state()`, and `restore_save_state()`
- The `role` attribute is set to `"interaction_manager"` in the base class
- Your implementation can use any interaction method (distance-based, targeting, UI menus, etc.)
- The two abstract methods (`get_interactive_objects()` and `has_interacted_with()`) are the minimum required interface
- Register your custom interaction manager in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.interaction"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_interaction.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.interaction.base import InteractionBasePlugin, InteractiveObject
from pedre.plugins.interaction.events import ObjectInteractedEvent
from pedre.conf import settings
import arcade

@PluginRegistry.register
class MenuInteractionPlugin(InteractionBasePlugin):
    """Interaction manager with radial menu selection."""

    name = "interaction"
    dependencies = []

    def __init__(self):
        self.interaction_distance = settings.INTERACTION_PLUGIN_DISTANCE
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

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle menu navigation and selection."""
        if symbol == arcade.key.TAB:
            if self.nearby_objects:
                self.selected_index = (self.selected_index + 1) % len(self.nearby_objects)
            return True
        elif symbol == arcade.key.E:
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
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_interaction",  # Load custom interaction first
    "pedre.plugins.camera",
    "pedre.plugins.input",
    # ... rest of plugins (omit "pedre.plugins.interaction") ...
]
```

## See Also

- [ScriptPlugin](script.md) - Event-driven scripting for handling interactions
- [NPCPlugin](npc.md) - NPC interaction plugin
- [DialogPlugin](dialog.md) - Conversation plugin
- [Configuration Guide](../guides/configuration.md)
- [Scripting Conditions](../scripting/conditions.md)
- [Scripting Events](../scripting/events.md)
