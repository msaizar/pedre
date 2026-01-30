"""Script actions for inventory system operations.

These actions allow scripts to manipulate inventory state,
such as acquiring items or waiting for inventory access.
"""

import logging
from typing import TYPE_CHECKING, Any

from pedre.actions import Action, WaitForConditionAction
from pedre.actions.registry import ActionRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@ActionRegistry.register("wait_inventory_access")
class WaitForInventoryAccessAction(WaitForConditionAction):
    """Wait for inventory to be accessed.

    This action pauses script execution until the player opens their inventory
    for the first time. It's useful for tutorial sequences or quests that require
    the player to check their items.

    The inventory manager tracks whether it has been accessed via the has_been_accessed
    flag, which this action monitors.

    Example usage in a tutorial sequence:
        [
            {"type": "dialog", "speaker": "martin", "text": ["Check your inventory!"]},
            {"type": "wait_for_dialog_close"},
            {"type": "wait_inventory_access"},
            {"type": "dialog", "speaker": "martin", "text": ["Great job!"]}
        ]
    """

    def __init__(self) -> None:
        """Initialize inventory access wait action."""
        super().__init__(lambda ctx: ctx.inventory_manager.has_been_accessed, "Inventory accessed")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WaitForInventoryAccessAction:  # noqa: ARG003
        """Create WaitForInventoryAccessAction from a dictionary."""
        return cls()


@ActionRegistry.register("acquire_item")
class AcquireItemAction(Action):
    """Give an item to the player's inventory.

    This action adds a specified item to the player's inventory by calling the
    inventory manager's acquire_item() method. The item must already be defined
    in the inventory manager - this action only marks it as acquired.

    When the item is successfully acquired, an ItemAcquiredEvent is published.
    If acquisition fails (inventory full, unknown item, or already owned), an
    ItemAcquisitionFailedEvent is published instead, and the action returns False,
    blocking script progression.

    Scripts can listen for ItemAcquisitionFailedEvent to show appropriate feedback
    to the player (e.g., "Your inventory is full!").

    Example usage:
        {
            "type": "acquire_item",
            "item_id": "rusty_key"
        }

        # In a script after finding a treasure chest
        {
            "actions": [
                {"type": "dialog", "speaker": "Narrator", "text": ["You found a key!"]},
                {"type": "acquire_item", "item_id": "tower_key"},
                {"type": "wait_for_dialog_close"}
            ]
        }

        # Script that listens for failure and shows message
        {
            "trigger": {
                "event": "item_acquisition_failed",
                "reason": "capacity"
            },
            "actions": [
                {"type": "dialog", "speaker": "Narrator", "text": ["Your inventory is full!"]}
            ]
        }
    """

    def __init__(self, item_id: str) -> None:
        """Initialize acquire item action.

        Args:
            item_id: Unique identifier of the item to acquire. Must match an item
                    ID in the inventory manager's registry.
        """
        self.item_id = item_id
        self.started = False
        self.success = False

    def execute(self, context: GameContext) -> bool:
        """Acquire the item if not already started.

        Returns:
            True if item was successfully acquired, False otherwise (blocks script progression).
        """
        if not self.started:
            inventory_manager = context.inventory_manager
            self.success = inventory_manager.acquire_item(self.item_id)
            self.started = True

            if self.success:
                logger.debug("AcquireItemAction: Successfully acquired item %s", self.item_id)
            else:
                logger.debug("AcquireItemAction: Failed to acquire item %s", self.item_id)

        return self.success

    def reset(self) -> None:
        """Reset the action."""
        self.started = False
        self.success = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AcquireItemAction:
        """Create AcquireItemAction from a dictionary."""
        return cls(item_id=data.get("item_id", ""))


@ActionRegistry.register("consume_item")
class ConsumeItemAction(Action):
    """Consume an item from the player's inventory.

    This action consumes a specified item by calling the inventory manager's consume_item()
    method. The item must already be acquired and not previously consumed. Once consumed,
    the item will no longer appear in the inventory display.

    Consuming an item is typically used for:
    - Consumable items (health potions, food, temporary buffs)
    - Quest items that are used once (key cards, tokens)
    - Resources that get depleted (ammunition, materials)

    The action completes immediately after attempting to consume the item. It returns True
    regardless of whether the item was successfully consumed, so it can be used safely in
    scripts without blocking progression.

    Example usage:
        {
            "type": "consume_item",
            "item_id": "health_potion"
        }

        # In a script for using a consumable
        {
            "actions": [
                {"type": "consume_item", "item_id": "ancient_key"},
                {"type": "dialog", "speaker": "Narrator", "text": ["The key dissolves into dust..."]},
                {"type": "wait_for_dialog_close"}
            ]
        }
    """

    def __init__(self, item_id: str) -> None:
        """Initialize consume item action.

        Args:
            item_id: Unique identifier of the item to consume. Must match an item
                    ID in the inventory manager's registry.
        """
        self.item_id = item_id
        self.started = False

    def execute(self, context: GameContext) -> bool:
        """Consume the item if not already started."""
        if not self.started:
            inventory_manager = context.inventory_manager
            inventory_manager.consume_item(self.item_id)
            self.started = True
            logger.debug("ConsumeItemAction: Consumed item %s", self.item_id)

        # Action completes immediately
        return True

    def reset(self) -> None:
        """Reset the action."""
        self.started = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConsumeItemAction:
        """Create ConsumeItemAction from a dictionary."""
        return cls(item_id=data.get("item_id", ""))
