# EventBus

Publish-subscribe event system for loose coupling.

## Location

`src/pedre/systems/events.py`

## Initialization

```python
from pedre.systems.events import EventBus

event_bus = EventBus()
```

## Key Methods

### `subscribe(event_type: type[Event], callback: Callable) -> None`

Subscribe to an event type.

**Parameters:**

- `event_type` - Event class to listen for
- `callback` - Function to call when event is published

**Example:**

```python
def on_dialog_closed(event: DialogClosedEvent):
    print(f"Dialog with {event.npc_name} closed")

event_bus.subscribe(DialogClosedEvent, on_dialog_closed)
```

### `publish(event: Event) -> None`

Publish an event to all subscribers.

**Parameters:**

- `event` - Event instance to publish

**Example:**

```python
from pedre.systems.events import DialogClosedEvent

event_bus.publish(DialogClosedEvent(
    npc_name="merchant",
    dialog_level=1
))
```

### `unsubscribe(event_type: type[Event], callback: Callable) -> None`

Unsubscribe from an event type.

**Example:**

```python
event_bus.unsubscribe(DialogClosedEvent, on_dialog_closed)
```

## Available Events

| Event | Fields | Description |
| ----- | ------ | ----------- |
| `DialogClosedEvent` | `npc_name`, `dialog_level` | Dialog window closed |
| `NPCInteractedEvent` | `npc_name`, `position` | Player interacted with NPC |
| `NPCMovementCompleteEvent` | `npc_name`, `waypoint` | NPC reached destination |
| `NPCDisappearCompleteEvent` | `npc_name` | NPC disappear animation finished |
| `InventoryClosedEvent` | - | Inventory screen closed |
| `ObjectInteractedEvent` | `object_name`, `position` | Player interacted with object |
| `ScriptCompleteEvent` | `script_name` | Script finished executing |

## Creating Custom Events

```python
from dataclasses import dataclass
from pedre.systems.events import Event

@dataclass
class ItemCollectedEvent(Event):
    """Published when player collects an item."""
    item_name: str
    category: str
    position: tuple[float, float]

# Publish
event_bus.publish(ItemCollectedEvent(
    item_name="golden_key",
    category="keys",
    position=(320, 240)
))

# Subscribe
def on_item_collected(event: ItemCollectedEvent):
    print(f"Collected: {event.item_name}")

event_bus.subscribe(ItemCollectedEvent, on_item_collected)
```
