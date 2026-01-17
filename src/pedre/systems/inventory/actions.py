"""Script actions for inventory system operations.

These actions allow scripts to manipulate inventory state,
such as acquiring items or waiting for inventory access.
"""

import logging
from typing import TYPE_CHECKING, Any

from pedre.systems.action_registry import ActionRegistry
from pedre.systems.actions import Action, WaitForConditionAction
from pedre.systems.inventory.manager import InventoryManager

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
            {"type": "wait_dialog_close"},
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

    When the item is successfully acquired, an ItemAcquiredEvent is published
    (if the inventory manager has an event bus), which can trigger follow-up
    scripts or reactions.

    The action completes immediately after attempting to acquire the item. It
    returns True regardless of whether the item was newly acquired or already
    owned, so it can be used safely in scripts without worrying about double
    acquisition.

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
    """

    def __init__(self, item_id: str) -> None:
        """Initialize acquire item action.

        Args:
            item_id: Unique identifier of the item to acquire. Must match an item
                    ID in the inventory manager's registry.
        """
        self.item_id = item_id
        self.started = False

    def execute(self, context: GameContext) -> bool:
        """Acquire the item if not already started."""
        if not self.started:
            inventory_manager = context.get_system("inventory")
            if inventory_manager and isinstance(inventory_manager, InventoryManager):
                # Use acquire_item method directly since inventory manager is BaseSystem
                inventory_manager.acquire_item(self.item_id)  # type: ignore[attr-defined]
            self.started = True
            logger.debug("AcquireItemAction: Acquired item %s", self.item_id)

        # Action completes immediately
        return True

    def reset(self) -> None:
        """Reset the action."""
        self.started = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AcquireItemAction:
        """Create AcquireItemAction from a dictionary."""
        return cls(item_id=data.get("item_id", ""))
