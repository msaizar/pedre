"""Conditions module for inventory."""

from typing import TYPE_CHECKING, Any

from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext


@ConditionRegistry.register("inventory_accessed")
def check_inventory_accessed(_condition_data: dict[str, Any], context: GameContext) -> bool:
    """Check if inventory has been accessed."""
    inventory = context.inventory_plugin
    return inventory.has_been_accessed()


def _validate_item_acquired(data: dict[str, Any]) -> list[str]:
    errors = []
    item_id = data.get("item_id")
    if not item_id:
        errors.append("missing required 'item_id' field")
    elif not isinstance(item_id, str):
        errors.append("'item_id' must be a string")
    return errors


@ConditionRegistry.register("item_acquired", validator=_validate_item_acquired)
def check_item_acquired(condition_data: dict[str, Any], context: GameContext) -> bool:
    """Check if we've acquired an item."""
    inventory = context.inventory_plugin
    item_id = condition_data.get("item_id")
    if not item_id:
        return False
    return inventory.has_item(item_id)
