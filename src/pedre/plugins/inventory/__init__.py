"""Inventory plugin for managing player's collectible items.

This package provides:
- InventoryPlugin: Core inventory management plugin
- InventoryItem: Data class for inventory items

Actions (registered via INSTALLED_ACTIONS):
- AcquireItemAction, WaitForInventoryAccessAction

Events (registered via INSTALLED_EVENTS):
- InventoryClosedEvent, ItemAcquiredEvent

Conditions (registered via INSTALLED_CONDITIONS):
- check_inventory_accessed: Check if inventory has been accessed
- check_item_acquired: Check if a specific item has been acquired

The inventory plugin tracks which items player has collected,
provides methods for item acquisition and querying, and supports
save/load functionality for persistent state.
"""

from pedre.plugins.inventory.base import InventoryBasePlugin, InventoryItem
from pedre.plugins.inventory.plugin import InventoryPlugin

__all__ = ["InventoryBasePlugin", "InventoryItem", "InventoryPlugin"]
