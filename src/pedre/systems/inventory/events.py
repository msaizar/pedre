"""Events related to inventory system operations.

These events are published by the inventory system to notify other
systems about inventory state changes, such as items being acquired
or the inventory view being closed.
"""

from dataclasses import dataclass

from pedre.systems.event_registry import EventRegistry
from pedre.systems.events import Event


@EventRegistry.register("inventory_closed")
@dataclass
class InventoryClosedEvent(Event):
    """Fired when the inventory view is closed by the player.

    This event is published when the player closes the inventory screen,
    which can be used to trigger tutorial progression or other
    inventory-related logic.

    Script trigger example:
        {
            "trigger": {
                "event": "inventory_closed"
            }
        }

    Attributes:
        has_been_accessed: Whether inventory has been accessed before.
    """

    has_been_accessed: bool


@EventRegistry.register("item_acquired")
@dataclass
class ItemAcquiredEvent(Event):
    """Fired when player acquires an inventory item.

    This event is published by the inventory manager when an item is added to the
    player's inventory for the first time. It can be used to trigger congratulatory
    messages, unlock new areas, or advance quest chains.

    The event is only published when an item transitions from unacquired to acquired.
    Attempting to acquire an already-owned item will not fire this event.

    Script trigger example:
        {
            "trigger": {
                "event": "item_acquired",
                "item_id": "rusty_key"
            }
        }

    The item_id filter is optional:
    - item_id: Only trigger for specific item (omit to trigger for any item)

    Attributes:
        item_id: Unique identifier of the item that was acquired.
        item_name: Display name of the item (for logging/debugging).
    """

    item_id: str
    item_name: str
