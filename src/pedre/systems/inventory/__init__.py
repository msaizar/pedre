"""Inventory system for managing player's collectible items.

This package provides:
- InventoryManager: Core inventory management system
- Actions: Script actions for inventory operations
- Events: Events related to inventory state changes

The inventory system tracks which items player has collected,
provides methods for item acquisition and querying, and supports
save/load functionality for persistent state.
"""

from pedre.systems.inventory.actions import AcquireItemAction, WaitForInventoryAccessAction
from pedre.systems.inventory.events import InventoryClosedEvent, ItemAcquiredEvent
from pedre.systems.inventory.manager import InventoryItem, InventoryManager

__all__ = [
    "AcquireItemAction",
    "InventoryClosedEvent",
    "InventoryItem",
    "InventoryManager",
    "ItemAcquiredEvent",
    "WaitForInventoryAccessAction",
]
