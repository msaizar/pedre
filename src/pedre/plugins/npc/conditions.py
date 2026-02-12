"""Conditions module for npc."""

from typing import TYPE_CHECKING, Any, Self

from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext


@ConditionRegistry.register("npc_interacted")
class NPCInteractedCondition(Condition):
    """Check if an NPC has been interacted with in a specific scene."""

    def __init__(self, npc_name: str, scene_name: str | None = None, *, expected: bool = True) -> None:
        """Initialize condition with NPC name, scene, and expected state."""
        self.npc_name = npc_name
        self.scene_name = scene_name
        self.expected = expected

    def check(self, context: GameContext) -> bool:
        """Check if interaction status matches expectation."""
        npc_mgr = context.npc_plugin
        if not self.npc_name:
            return False
        return npc_mgr.has_npc_been_interacted_with(self.npc_name, self.scene_name) == self.expected

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            npc_name=data.get("npc", ""),
            scene_name=data.get("scene"),
            expected=data.get("equals", True),
        )

    @staticmethod
    def validate_params(data: dict[str, Any]) -> list[str]:
        """Validate parameters."""
        errors = []
        npc = data.get("npc")
        if not npc:
            errors.append("missing required 'npc' field")
        elif not isinstance(npc, str):
            errors.append("'npc' must be a string")

        if "scene" in data and not isinstance(data["scene"], str):
            errors.append("'scene' must be a string")

        if "equals" in data and not isinstance(data["equals"], bool):
            errors.append("'equals' must be a bool")

        return errors


@ConditionRegistry.register("npc_dialog_level")
class NPCDialogLevelCondition(Condition):
    """Check an NPC's dialog level."""

    def __init__(self, npc_name: str, expected_level: int) -> None:
        """Initialize condition with NPC name and expected dialog level."""
        self.npc_name = npc_name
        self.expected_level = expected_level

    def check(self, context: GameContext) -> bool:
        """Check if dialog level matches."""
        npc_mgr = context.npc_plugin
        if not self.npc_name:
            return False
        npc_state = npc_mgr.get_npc_by_name(self.npc_name)
        return npc_state is not None and npc_state.dialog_level == self.expected_level

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            npc_name=data.get("npc", ""),
            expected_level=data.get("equals", 0),
        )

    @staticmethod
    def validate_params(data: dict[str, Any]) -> list[str]:
        """Validate parameters."""
        errors = []
        npc = data.get("npc")
        if not npc:
            errors.append("missing required 'npc' field")
        elif not isinstance(npc, str):
            errors.append("'npc' must be a string")

        if "equals" not in data:
            errors.append("missing required 'equals' field")
        elif not isinstance(data["equals"], int) or isinstance(data["equals"], bool):
            errors.append("'equals' must be an int")

        return errors
