"""Conditions module for interaction."""

from typing import TYPE_CHECKING, Any, Self

from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext


@ConditionRegistry.register("object_interacted")
class ObjectInteractedCondition(Condition):
    """Check if an object has been interacted with."""

    def __init__(self, object_name: str, *, expected: bool = True) -> None:
        """Initialize condition with object name and expected state."""
        self.object_name = object_name
        self.expected = expected

    def check(self, context: GameContext) -> bool:
        """Check if object interaction matches expected state."""
        interaction = context.interaction_plugin
        if not self.object_name:
            return False
        return interaction.has_interacted_with(self.object_name) == self.expected

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            object_name=data.get("object", ""),
            expected=data.get("equals", True),
        )

    @staticmethod
    def validate_params(data: dict[str, Any]) -> list[str]:
        """Validate parameters."""
        errors = []
        obj = data.get("object")
        if not obj:
            errors.append("missing required 'object' field")
        elif not isinstance(obj, str):
            errors.append("'object' must be a string")

        if "equals" in data and not isinstance(data["equals"], bool):
            errors.append("'equals' must be a bool")

        return errors
