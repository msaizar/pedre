"""Conditions module for npc."""

from typing import TYPE_CHECKING, Any, Self

from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionParseError, ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext


@ConditionRegistry.register
class NPCInteractedCondition(Condition):
    """Check if an NPC has been interacted with in a specific scene."""

    name = "npc_interacted"

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
        npc = data.get("npc")
        if not npc:
            msg = "missing required 'npc' field"
            raise ConditionParseError(msg)
        if not isinstance(npc, str):
            msg = "'npc' must be a string"
            raise ConditionParseError(msg)
        scene = data.get("scene")
        if scene and not isinstance(scene, str):
            msg = "'scene' must be a string"
            raise ConditionParseError(msg)
        equals = data.get("equals", True)
        if equals and not isinstance(equals, bool):
            msg = "'equals' must be a bool"
            raise ConditionParseError(msg)
        return cls(
            npc_name=npc,
            scene_name=scene,
            expected=equals,
        )


@ConditionRegistry.register
class NPCDialogLevelCondition(Condition):
    """Check an NPC's dialog level."""

    name = "npc_dialog_level"

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
        npc = data.get("npc")
        if not npc:
            msg = "missing required 'npc' field"
            raise ConditionParseError(msg)
        if not isinstance(npc, str):
            msg = "'npc' must be a string"
            raise ConditionParseError(msg)

        equals = data.get("equals")
        if equals is None:
            msg = "missing required 'equals' field"
            raise ConditionParseError(msg)

        if not isinstance(equals, int) or isinstance(equals, bool):
            msg = "'equals' must be an int"
            raise ConditionParseError(msg)
        return cls(
            npc_name=npc,
            expected_level=equals,
        )
