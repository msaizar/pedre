"""Events related to inventory plugin operations.

These events are published by the inventory plugin to notify other
plugins about inventory state changes, such as items being acquired
or the inventory view being closed.
"""

from dataclasses import dataclass
from typing import Any, ClassVar

from pedre.events import Event
from pedre.events.registry import EventRegistry


@EventRegistry.register
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

    name: ClassVar[str] = "inventory_closed"

    trigger_keys: ClassVar[frozenset[str]] = frozenset({"inventory_accessed"})
    has_been_accessed: bool

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"inventory_accessed": self.has_been_accessed}


@EventRegistry.register
@dataclass
class ItemAcquiredEvent(Event):
    """Fired when player acquires an inventory item.

    This event is published by the inventory plugin when an item is added to the
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

    name: ClassVar[str] = "item_acquired"

    trigger_keys: ClassVar[frozenset[str]] = frozenset({"item_id"})
    item_id: str
    item_name: str

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"item_id": self.item_id}


@EventRegistry.register
@dataclass
class ItemAcquisitionFailedEvent(Event):
    """Fired when an attempt to acquire an item fails.

    This event is published by the inventory plugin when an item cannot be acquired,
    which can happen for several reasons:
    - Inventory is at maximum capacity
    - Item doesn't exist in the registry
    - Item is already acquired

    This event allows scripts to provide feedback to the player about why the
    acquisition failed, such as showing a "Your inventory is full!" message.

    Script trigger example:
        {
            "trigger": {
                "event": "item_acquisition_failed",
                "reason": "capacity"
            }
        }

    Attributes:
        item_id: Unique identifier of the item that failed to be acquired.
        reason: Reason for failure ("capacity", "unknown_item", or "already_owned").
    """

    name: ClassVar[str] = "item_acquisition_failed"

    trigger_keys: ClassVar[frozenset[str]] = frozenset({"item_id", "reason"})
    item_id: str
    reason: str

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"item_id": self.item_id, "reason": self.reason}


@EventRegistry.register
@dataclass
class ItemConsumedEvent(Event):
    """Fired when player consumes an inventory item.

    This event is published by the inventory plugin when an item is consumed
    by the player, typically through the inventory overlay UI. This allows scripts
    to react to item consumption, such as restoring health for a potion or
    triggering special effects.

    The event includes both the item ID and category to allow scripts to filter
    based on item type (e.g., all consumable potions).

    Script trigger example:
        {
            "trigger": {
                "event": "item_consumed",
                "item_id": "health_potion_1"
            },
            "actions": [
                {"type": "dialog", "speaker": "Narrator", "text": ["You feel refreshed!"]}
            ]
        }

        # Or filter by category
        {
            "trigger": {
                "event": "item_consumed",
                "category": "consumable"
            },
            "actions": [
                {"type": "play_sound", "sound": "potion_drink.wav"}
            ]
        }

    Attributes:
        item_id: Unique identifier of the item that was consumed.
        item_name: Display name of the item (for logging/debugging).
        category: Category of the consumed item (e.g., "consumable").
    """

    name: ClassVar[str] = "item_consumed"

    trigger_keys: ClassVar[frozenset[str]] = frozenset({"item_id", "category"})
    item_id: str
    item_name: str
    category: str

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"item_id": self.item_id, "category": self.category}
