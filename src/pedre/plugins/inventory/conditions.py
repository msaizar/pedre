"""Conditions module for inventory."""

from typing import TYPE_CHECKING, Any, Self

from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext


@ConditionRegistry.register("inventory_accessed")
class InventoryAccessedCondition(Condition):
    """Check if inventory has been accessed."""

    def check(self, context: GameContext) -> bool:
        """Check if inventory accessed."""
        inventory = context.inventory_plugin
        return inventory.has_been_accessed()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:  # noqa: ARG003
        """Create from dictionary."""
        return cls()

    @staticmethod
    def validate_params(data: dict[str, Any]) -> list[str]:  # noqa: ARG004
        """Validate parameters (none required)."""
        return []


@ConditionRegistry.register("item_acquired")
class ItemAcquiredCondition(Condition):
    """Check if an item has been acquired."""

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
        return cls(item_id=data.get("item_id", ""))

    @staticmethod
    def validate_params(data: dict[str, Any]) -> list[str]:
        """Validate parameters."""
        errors = []
        item_id = data.get("item_id")
        if not item_id:
            errors.append("missing required 'item_id' field")
        elif not isinstance(item_id, str):
            errors.append("'item_id' must be a string")
        return errors
