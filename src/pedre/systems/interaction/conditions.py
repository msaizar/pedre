"""Conditions module for interaction."""

from typing import TYPE_CHECKING, Any

from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext


@ConditionRegistry.register("object_interacted")
def check_object_interacted(condition_data: dict[str, Any], context: GameContext) -> bool:
    """Check if an object has been interacted with."""
    interaction = context.get_system("interaction")
    if not interaction:
        return False
    object_name = condition_data.get("object")
    expected = condition_data.get("equals", True)
    if not object_name:
        return False
    return interaction.has_interacted_with(object_name) == expected
