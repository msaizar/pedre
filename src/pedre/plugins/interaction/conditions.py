"""Conditions module for interaction."""

from typing import TYPE_CHECKING, Any

from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext


def _validate_object_interacted(data: dict[str, Any]) -> list[str]:
    errors = []
    if not data.get("object"):
        errors.append("missing required 'object' field")
    return errors


@ConditionRegistry.register("object_interacted", validator=_validate_object_interacted)
def check_object_interacted(condition_data: dict[str, Any], context: GameContext) -> bool:
    """Check if an object has been interacted with."""
    interaction = context.interaction_plugin
    object_name = condition_data.get("object")
    expected = condition_data.get("equals", True)
    if not object_name:
        return False
    return interaction.has_interacted_with(object_name) == expected
