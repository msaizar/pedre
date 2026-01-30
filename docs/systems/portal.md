# PortalManager

Handles map transitions through an event-driven system integrated with the script manager.

## Location

- Implementation: [src/pedre/systems/portal/manager.py](../../src/pedre/systems/portal/manager.py)
- Base class: [src/pedre/systems/portal/base.py](../../src/pedre/systems/portal/base.py)
- Events: [src/pedre/systems/portal/events.py](../../src/pedre/systems/portal/events.py)

## Configuration

The PortalManager uses the following settings from `pedre.conf.settings`:

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

The portal system uses an event-driven architecture where:

1. Portals are registered from Tiled map data during map loading
2. When the player enters a portal zone, `PortalEnteredEvent` is published
3. Scripts respond to the event and handle transitions via `change_scene` action

This approach allows full flexibility: conditional portals, cutscenes before transitions, failure messages, and complex multi-step sequences.

## Public API

### Portal Registration

#### `register_portal(sprite: arcade.Sprite, name: str) -> None`

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

#### `check_portals(player_sprite: arcade.Sprite | None) -> None`

Check if player is near any portal and publish events on entry.

**Parameters:**

- `player_sprite` - The player's arcade Sprite for position checking

**Example:**

```python
def on_update(self, delta_time):
    self.portal_manager.check_portals(self.player_sprite)
```

**Notes:**

- Called automatically by the system each frame via `update()`
- Events only fire when player enters a portal zone (transitions from outside to inside)
- Won't re-fire while player remains standing in the portal
- Uses `PORTAL_INTERACTION_DISTANCE` setting
- Distance calculation uses Euclidean distance (straight-line)
- Publishes `PortalEnteredEvent` when player enters

#### `clear() -> None`

Clear all registered portals.

**Notes:**

- Removes all portals from the manager's registry
- Called automatically when changing maps
- Also clears the internal tracking of which portals player is inside

### System Lifecycle

#### `setup(context: GameContext) -> None`

Initialize the portal system with game context.

**Parameters:**

- `context` - Game context providing access to other systems

**Notes:**

- Called automatically by SystemLoader
- Configures the manager with event bus and settings
- Stores reference to game context

#### `update(delta_time: float) -> None`

Update portal system, checking for player entry.

**Parameters:**

- `delta_time` - Time since last update in seconds

**Notes:**

- Called automatically by SystemLoader each frame
- Calls `check_portals()` with current player sprite
- Handles portal entry detection

#### `cleanup() -> None`

Clean up portal resources when the scene unloads.

**Notes:**

- Clears all registered portals
- Resets tracking state
- Called automatically by SystemLoader

#### `load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load portals from Tiled map object layer.

**Parameters:**

- `tile_map` - The loaded Tiled map
- `arcade_scene` - The arcade Scene to add portals to

**Notes:**

- Called automatically by SystemLoader
- Looks for "Portals" object layer
- Creates portal sprites from object shapes
- Clears old portals before loading new ones
- Portal objects need a `name` property

## Data Structures

### Portal

Runtime data for a single portal.

**Location:** [src/pedre/systems/portal/base.py](../../src/pedre/systems/portal/base.py)

**Attributes:**

- `sprite: arcade.Sprite` - The portal's sprite representing location and collision area
- `name: str` - Unique identifier for this portal (used in script triggers)

**Example:**

```python
from pedre.systems.portal.base import Portal

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

**Location:** [src/pedre/systems/portal/events.py](../../src/pedre/systems/portal/events.py)

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

## See Also

- [SceneManager](scene.md) - Map loading and transitions
- [ScriptManager](script.md) - Event-driven scripting
- [Configuration Guide](../configuration.md) - Portal system settings
- [Events Reference](../scripting/events.md) - `portal_entered` event
- [Actions Reference](../scripting/actions.md) - `change_scene` action
- [Conditions Reference](../scripting/conditions.md) - Conditional portal access
- [Tiled Integration](../tiled-integration.md) - Portal setup in Tiled
- [API Reference](../api-reference.md) - PortalManager API
