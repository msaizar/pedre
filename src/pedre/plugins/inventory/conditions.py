"""Conditions module for inventory."""

from typing import TYPE_CHECKING, Any, Self

from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionParseError, ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext


@ConditionRegistry.register
class InventoryAccessedCondition(Condition):
    """Check if inventory has been accessed."""

    name = "inventory_accessed"

    def check(self, context: GameContext) -> bool:
        """Check if inventory accessed."""
        inventory = context.inventory_plugin
        return inventory.has_been_accessed()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:  # noqa: ARG003
        """Create from dictionary."""
        return cls()


@ConditionRegistry.register
class ItemAcquiredCondition(Condition):
    """Check if an item has been acquired."""

    name = "item_acquired"

    def __init__(self, item_id: str) -> None:
        """Initialize condition with item ID."""
        self.item_id = item_id

    def check(self, context: GameContext) -> bool:
        """Check if item is in inventory."""
        inventory = context.inventory_plugin
        if not self.item_id:
            return False
        return inventory.has_item(self.item_id)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        item_id = data.get("item_id")
        if not item_id:
            msg = "missing required 'item_id' field"
            raise ConditionParseError(msg)
        if not isinstance(item_id, str):
            msg = "'item_id' must be a string"
            raise ConditionParseError(msg)

        return cls(item_id=item_id)
