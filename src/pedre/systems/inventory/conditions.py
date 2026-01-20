"""Conditions module for inventory."""

from typing import TYPE_CHECKING, Any

from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext


@ConditionRegistry.register("inventory_accessed")
def check_inventory_accessed(_condition_data: dict[str, Any], context: GameContext) -> bool:
    """Check if inventory has been accessed."""
    inventory = context.get_system("inventory")
    if not inventory:
        return False
    return inventory.has_been_accessed
