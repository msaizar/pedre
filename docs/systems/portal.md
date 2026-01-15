# PortalManager

Handles map transitions through an event-driven system integrated with the script manager.

## Location

`src/pedre/systems/portal.py`

## Overview

The portal system uses an event-driven architecture where:

1. Portals are registered from Tiled map data during map loading
2. When the player enters a portal zone, `PortalEnteredEvent` is published
3. Scripts respond to the event and handle transitions via `change_scene` action

This approach allows full flexibility: conditional portals, cutscenes before transitions, failure messages, and complex multi-step sequences.

## Initialization

```python
from pedre.systems.portal import PortalManager
from pedre.systems.events import EventBus

event_bus = EventBus()
portal_manager = PortalManager(
    event_bus=event_bus,
    interaction_distance=64.0  # pixels
)
```

**Parameters:**

- `event_bus` - EventBus for publishing PortalEnteredEvent
- `interaction_distance` - Maximum distance for portal activation (default 64.0 pixels)

## Key Methods

### `register_portal(sprite: arcade.Sprite, name: str) -> None`

Register a portal from Tiled map data.

**Parameters:**

- `sprite` - The arcade Sprite representing the portal's location
- `name` - Unique portal identifier (used in script triggers)

**Example:**

```python
portal_manager.register_portal(
    sprite=portal_sprite,
    name="to_forest"
)
```

### `check_portals(player_sprite: arcade.Sprite) -> None`

Check if player is near any portal and publish events. Events only fire when the player enters a portal zone (transitions from outside to inside), not while standing on it.

**Parameters:**

- `player_sprite` - Player's arcade Sprite for position checking

**Example:**

```python
def on_update(self, delta_time):
    self.portal_manager.check_portals(self.player_sprite)
```

### `clear() -> None`

Clear all registered portals. Called when changing maps.

## Portal Dataclass

```python
from pedre.systems.portal import Portal

@dataclass
class Portal:
    sprite: arcade.Sprite  # Portal location and collision area
    name: str              # Unique identifier for script triggers
```

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

- [Events Reference](../scripting/events.md) - `portal_entered` event
- [Actions Reference](../scripting/actions.md) - `change_scene` action
- [Tiled Integration](../tiled-integration.md) - Portal setup in Tiled
