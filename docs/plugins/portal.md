# PortalPlugin

Handles map transitions through an event-driven system integrated with the script manager.

## Location

- Implementation: [src/pedre/plugins/portal/manager.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/portal/manager.py)
- Base class: [src/pedre/plugins/portal/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/portal/base.py)
- Events: [src/pedre/plugins/portal/events.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/portal/events.py)

## Configuration

The PortalPlugin uses the following settings from `pedre.conf.settings`:

### Portal Settings

- `PORTAL_INTERACTION_DISTANCE` - Maximum distance in pixels for player to activate portals (default: 50)

This can be overridden in your project's `settings.py`:

```python
# Custom portal settings
PORTAL_INTERACTION_DISTANCE = 64
```

**Notes:**

- `PORTAL_INTERACTION_DISTANCE` determines how close the player must be to trigger a portal
  - Common values: 32 (1 tile), 50 (default, ~1.5 tiles), 64 (2 tiles), 96 (3 tiles)
  - Uses Euclidean distance from player center to portal center
  - Creates a circular activation zone around each portal
  - Only fires when player enters the zone (transitions from outside to inside)
  - Won't re-fire while player remains standing in the zone

## Overview

The portal plugin uses an event-driven architecture where:

1. Portals are registered from Tiled map data during map loading
2. When the player enters a portal zone, `PortalEnteredEvent` is published
3. Scripts respond to the event and handle transitions via `change_scene` action

This approach allows full flexibility: conditional portals, cutscenes before transitions, failure messages, and complex multi-step sequences.

## Public API

### Portal Registration

#### register_portal

`register_portal(sprite: arcade.Sprite, name: str) -> None`

Register a portal from Tiled map data.

**Parameters:**

- `sprite` - The arcade Sprite representing the portal's location and collision area
- `name` - Unique portal identifier (used in script triggers)

**Example:**

```python
portal_manager.register_portal(
    sprite=portal_sprite,
    name="to_forest"
)
```

**Notes:**

- Portals must be registered before they can be activated
- Portal name should be unique within the map
- Usually called automatically by `load_from_tiled()`
- The sprite defines the physical location and activation area

### Portal Checking

#### check_portals

`check_portals(player_sprite: arcade.Sprite | None) -> None`

Check if player is near any portal and publish events on entry.

**Parameters:**

- `player_sprite` - The player's arcade Sprite for position checking

**Example:**

```python
def on_update(self, delta_time):
    self.portal_manager.check_portals(self.player_sprite)
```

**Notes:**

- Called automatically by the plugin each frame via `update()`
- Events only fire when player enters a portal zone (transitions from outside to inside)
- Won't re-fire while player remains standing in the portal
- Uses `PORTAL_INTERACTION_DISTANCE` setting
- Distance calculation uses Euclidean distance (straight-line)
- Publishes `PortalEnteredEvent` when player enters

#### clear

`clear() -> None`

Clear all registered portals.

**Notes:**

- Removes all portals from the manager's registry
- Called automatically when changing maps
- Also clears the internal tracking of which portals player is inside

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the portal plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Configures the manager with event bus and settings
- Stores reference to game context

#### update

`update(delta_time: float) -> None`

Update portal plugin, checking for player entry.

**Parameters:**

- `delta_time` - Time since last update in seconds

**Notes:**

- Called automatically by PluginLoader each frame
- Calls `check_portals()` with current player sprite
- Handles portal entry detection

#### cleanup

`cleanup() -> None`

Clean up portal resources when the scene unloads.

**Notes:**

- Clears all registered portals
- Resets tracking state
- Called automatically by PluginLoader

#### load_from_tiled

`load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load portals from Tiled map object layer.

**Parameters:**

- `tile_map` - The loaded Tiled map
- `arcade_scene` - The arcade Scene to add portals to

**Notes:**

- Called automatically by PluginLoader
- Looks for "Portals" object layer
- Creates portal sprites from object shapes
- Clears old portals before loading new ones
- Portal objects need a `name` property

## Data Structures

### Portal

Runtime data for a single portal.

**Location:** [src/pedre/plugins/portal/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/portal/base.py)

**Attributes:**

- `sprite: arcade.Sprite` - The portal's sprite representing location and collision area
- `name: str` - Unique identifier for this portal (used in script triggers)

**Example:**

```python
from pedre.plugins.portal.base import Portal

portal = Portal(
    sprite=portal_sprite,
    name="forest_entrance"
)
```

**Notes:**

- Portals are typically created automatically from Tiled map data
- The sprite defines the physical location and activation zone
- Portal name is used in script triggers to match specific portals

## Events

### PortalEnteredEvent

Published when player enters a portal zone.

**Location:** [src/pedre/plugins/portal/events.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/portal/events.py)

**Attributes:**

- `portal_name: str` - Name of the portal that was entered

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "portal_entered",
        "portal": "forest_gate"
    },
    "actions": [
        {"type": "change_scene", "target_map": "Forest.tmx", "spawn_waypoint": "entrance"}
    ]
}
```

**Notes:**

- Fires when player enters the portal zone (not while standing in it)
- The `portal` filter is optional (omit to trigger for any portal)
- Only triggers on entry (transitions from outside to inside)
- Won't re-fire until player leaves and re-enters the zone
- Uses Euclidean distance calculation with `PORTAL_INTERACTION_DISTANCE`

**Use Cases:**

- Map transitions
- Conditional portal access (with conditions)
- Cutscenes before transitions
- Locked doors with failure messages
- Multi-step portal sequences

## Script Integration

Portals are handled through scripts using the `portal_entered` event trigger and `change_scene` action.

### Simple Portal

Tiled properties:

```text
name: "forest_entrance"
```

Script JSON:

```json
{
  "forest_entrance_portal": {
    "trigger": {"event": "portal_entered", "portal": "forest_entrance"},
    "actions": [
      {"type": "change_scene", "target_map": "Forest.tmx", "spawn_waypoint": "forest_start"}
    ]
  }
}
```

### Conditional Portal

Portal that requires a condition to be met:

```json
{
  "tower_gate_open": {
    "trigger": {"event": "portal_entered", "portal": "tower_gate"},
    "conditions": [{"check": "npc_dialog_level", "npc": "guard", "gte": 2}],
    "actions": [
      {"type": "change_scene", "target_map": "Tower.tmx", "spawn_waypoint": "tower_entrance"}
    ]
  },
  "tower_gate_locked": {
    "trigger": {"event": "portal_entered", "portal": "tower_gate"},
    "conditions": [{"check": "npc_dialog_level", "npc": "guard", "lt": 2}],
    "actions": [
      {"type": "dialog", "speaker": "Narrator", "text": ["The gate is sealed. Perhaps the guard knows something..."]}
    ]
  }
}
```

### Portal with Cutscene

Portal that plays a cutscene on first entry:

```json
{
  "dungeon_cutscene": {
    "trigger": {"event": "portal_entered", "portal": "dungeon_portal"},
    "run_once": true,
    "actions": [
      {"type": "dialog", "speaker": "Narrator", "text": ["A cold wind blows from the depths..."]},
      {"type": "wait_for_dialog_close"},
      {"type": "play_sfx", "file": "wind.wav"},
      {"type": "change_scene", "target_map": "Dungeon.tmx", "spawn_waypoint": "dungeon_entrance"}
    ]
  },
  "dungeon_return": {
    "trigger": {"event": "portal_entered", "portal": "dungeon_portal"},
    "conditions": [{"check": "script_completed", "script": "dungeon_cutscene"}],
    "actions": [
      {"type": "change_scene", "target_map": "Dungeon.tmx", "spawn_waypoint": "dungeon_entrance"}
    ]
  }
}
```

## Tiled Setup

1. Create a "Portals" object layer in your Tiled map
2. Add rectangle objects where you want portals
3. Set the `name` property on each portal object

The portal name is used in script triggers to match specific portals:

```json
{"trigger": {"event": "portal_entered", "portal": "forest_gate"}}
```

## Portal Behavior

### Entry Detection

The portal plugin uses zone-based detection:

1. **Distance Check** - Calculates Euclidean distance from player center to portal center
2. **Zone Entry** - Player enters when distance < `PORTAL_INTERACTION_DISTANCE`
3. **Event Publishing** - `PortalEnteredEvent` published on zone entry
4. **Entry Tracking** - Tracks which portals player is currently inside
5. **Exit Detection** - Player exits when distance >= `PORTAL_INTERACTION_DISTANCE`
6. **Re-entry** - Can re-fire if player leaves and returns

### Distance Calculation

```python
distance = arcade.get_distance_between_sprites(player_sprite, portal_sprite)
if distance < PORTAL_INTERACTION_DISTANCE:
    # Player is in portal zone
```

**Notes:**

- Uses center points of both sprites
- Creates circular activation zone
- Works with portals of any size
- Distance is in pixels

### Portal Lifecycle

1. **Registration** - Portals loaded from Tiled during scene setup
2. **Checking** - Distance checked every frame in `update()`
3. **Event Publishing** - Events published on zone entry
4. **Script Execution** - Scripts respond to events
5. **Cleanup** - Portals cleared when scene unloads

## Implementation Details

### Portal Tracking

The manager tracks portal entry state to prevent duplicate events:

```python
# Internal tracking set
self._player_in_portals = set()

# Check if player just entered
if portal.name not in self._player_in_portals:
    self._player_in_portals.add(portal.name)
    # Publish event only on entry
```

**Benefits:**

- Events fire once per entry
- No spam while standing in portal
- Clean re-entry detection
- Minimal state tracking

### Portal Loading from Tiled

Portals are registered during map loading:

```python
for portal_object in portal_layer:
    portal_sprite = arcade.Sprite()
    portal_sprite.center_x = portal_object.shape.x
    portal_sprite.center_y = portal_object.shape.y

    self.register_portal(
        sprite=portal_sprite,
        name=portal_object.properties.get("name")
    )
```

**Requirements:**

- Portal object must have `name` property
- Portal sprite defines activation zone
- Usually rectangular objects in Tiled

## Usage Examples

### Basic Portal Transition

```json
{
  "go_to_forest": {
    "trigger": {
      "event": "portal_entered",
      "portal": "forest_entrance"
    },
    "actions": [
      {"type": "change_scene", "target_map": "forest.tmx", "spawn_waypoint": "entrance"}
    ]
  }
}
```

### Two-Way Portal

Create matching portals in both maps:

**village.tmx:**

```json
{
  "to_forest": {
    "trigger": {"event": "portal_entered", "portal": "forest_gate"},
    "actions": [
      {"type": "change_scene", "target_map": "forest.tmx", "spawn_waypoint": "from_village"}
    ]
  }
}
```

**forest.tmx:**

```json
{
  "to_village": {
    "trigger": {"event": "portal_entered", "portal": "village_gate"},
    "actions": [
      {"type": "change_scene", "target_map": "village.tmx", "spawn_waypoint": "from_forest"}
    ]
  }
}
```

### Quest-Locked Portal

```json
{
  "castle_open": {
    "trigger": {"event": "portal_entered", "portal": "castle_gate"},
    "conditions": [
      {"check": "npc_interacted", "npc": "king", "scene": "throne_room"}
    ],
    "actions": [
      {"type": "change_scene", "target_map": "castle_interior.tmx", "spawn_waypoint": "entrance"}
    ]
  },
  "castle_locked": {
    "trigger": {"event": "portal_entered", "portal": "castle_gate"},
    "conditions": [
      {"check": "npc_interacted", "npc": "king", "scene": "throne_room", "equals": false}
    ],
    "actions": [
      {"type": "dialog", "speaker": "Guard", "text": ["The castle is closed to visitors."]}
    ]
  }
}
```

### Portal with Sound Effect

```json
{
  "enter_cave": {
    "trigger": {"event": "portal_entered", "portal": "cave_entrance"},
    "actions": [
      {"type": "play_sfx", "file": "cave_echo.wav"},
      {"type": "wait", "duration": 0.5},
      {"type": "change_scene", "target_map": "cave.tmx", "spawn_waypoint": "entrance"}
    ]
  }
}
```

## Integration with Other Plugins

### ScenePlugin Integration

The ScenePlugin handles map transitions:

```python
# Portal triggers scene change via script action
context.scene_manager.request_transition(
    map_file="forest.tmx",
    spawn_waypoint="entrance"
)
```

**Notes:**

- Portal event triggers script
- Script executes `change_scene` action
- ScenePlugin handles the actual transition
- Player spawns at specified waypoint

### PlayerPlugin Integration

The PlayerPlugin provides player position:

```python
# Portal plugin checks player position
player_sprite = context.player_manager.get_player_sprite()
if player_sprite:
    portal_manager.check_portals(player_sprite)
```

**Notes:**

- Player must exist for portal checking
- Uses player sprite center position
- Checked every frame in update loop

### ScriptPlugin Integration

Scripts handle portal responses:

```python
# PortalEnteredEvent published
event = PortalEnteredEvent(portal_name="forest_gate")
context.event_bus.publish(event)

# Scripts listen and respond
# Execute actions (change_scene, dialog, etc.)
```

**Notes:**

- Portal plugin only publishes events
- Scripts define what happens
- Full flexibility for conditional behavior
- Can chain multiple actions

### WaypointPlugin Integration

Waypoints define spawn positions:

```python
# Scene transition with waypoint
{"type": "change_scene", "target_map": "castle.tmx", "spawn_waypoint": "main_gate"}

# Player spawns at waypoint location
waypoint = context.waypoint_manager.get_waypoint("main_gate")
player.center_x = waypoint.x
player.center_y = waypoint.y
```

**Notes:**

- Waypoints must exist in target scene
- Falls back to default position if waypoint missing
- Enables precise spawn positioning

## Troubleshooting

### Portal Not Triggering

If portals don't activate when player walks over them:

1. **Check portal layer** - Ensure Tiled map has "Portals" object layer
2. **Verify name property** - Each portal object must have unique `name` property
3. **Check distance setting** - Increase `PORTAL_INTERACTION_DISTANCE` if needed
4. **Review scripts** - Ensure script exists with matching portal name
5. **Test player position** - Verify player sprite exists and has valid position

### Portal Triggers Multiple Times

If portal events fire repeatedly:

1. **Check script conditions** - Ensure conditions prevent re-triggering
2. **Use run_once** - Add `"run_once": true` to script if it should only run once
3. **Review exit detection** - Player must fully exit zone before re-entry triggers

### Portal Activates from Too Far

If portals trigger from unexpected distance:

1. **Reduce distance** - Lower `PORTAL_INTERACTION_DISTANCE` value
2. **Check portal size** - Portal sprite size affects center point
3. **Verify collision** - Ensure portal sprite position is correct in Tiled

### Scene Transition Not Working

If portal event fires but scene doesn't change:

1. **Check action** - Verify script has `change_scene` action
2. **Verify map file** - Ensure `target_map` path is correct
3. **Check waypoint** - Verify `spawn_waypoint` exists in target scene
4. **Review logs** - Look for scene loading errors

## Custom Portal Implementation

If you need to replace the portal plugin with a custom implementation, you can extend the `PortalBasePlugin` abstract base class.

### PortalBasePlugin

**Location:** [src/pedre/plugins/portal/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/portal/base.py)

The `PortalBasePlugin` class defines the minimum interface that any portal manager must implement.

#### Required Methods

Your custom portal manager must implement these abstract methods:

```python
from pedre.plugins.portal.base import PortalBasePlugin

class CustomPortalPlugin(PortalBasePlugin):
    """Custom portal implementation."""

    name = "portal"

    def register_portal(self, sprite: arcade.Sprite, name: str) -> None:
        """Register a portal."""
        ...

    def check_portals(self, player_sprite: arcade.Sprite | None) -> None:
        """Check for portal activation."""
        ...

    def clear(self) -> None:
        """Clear all portals."""
        ...
```

#### Registration

Register your custom portal manager using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.portal.base import PortalBasePlugin

@PluginRegistry.register
class TriggerPortalPlugin(PortalBasePlugin):
    """Portal manager with touch triggers instead of zones."""

    name = "portal"

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BasePlugin` (via `PortalBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"portal_manager"` in the base class
- Your implementation can use any detection system (zones, triggers, collisions)
- Register your custom portal manager in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.portal"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_portal.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.portal.base import PortalBasePlugin

@PluginRegistry.register
class CollisionPortalPlugin(PortalBasePlugin):
    """Portal manager using collision detection instead of distance."""

    name = "portal"

    def __init__(self):
        self.portals = []
        # ... rest of initialization ...

    def check_portals(self, player_sprite: arcade.Sprite | None) -> None:
        if not player_sprite:
            return

        # Use collision detection instead of distance
        for portal in self.portals:
            if arcade.check_for_collision(player_sprite, portal.sprite):
                # Publish event
                event = PortalEnteredEvent(portal_name=portal.name)
                self.context.event_bus.publish(event)

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_portal",  # Load custom portal first
    "pedre.plugins.camera",
    "pedre.plugins.audio",
    # ... rest of plugins (omit "pedre.plugins.portal") ...
]
```

## See Also

- [ScenePlugin](scene.md) - Map loading and transitions
- [ScriptPlugin](script.md) - Event-driven scripting
- [Configuration Guide](../guides/configuration.md)
- [Events Reference](../scripting/events.md)
- [Actions Reference](../scripting/actions.md)
- [Conditions Reference](../scripting/conditions.md)
- [Tiled Integration](../guides/tiled-integration.md)
