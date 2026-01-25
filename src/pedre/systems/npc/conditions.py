"""Conditions module for npc."""

from typing import TYPE_CHECKING, Any

from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext


@ConditionRegistry.register("npc_interacted")
def check_npc_interacted(condition_data: dict[str, Any], context: GameContext) -> bool:
    """Check if an NPC has been interacted with."""
    npc_mgr = context.npc_manager
    if not npc_mgr:
        return False
    npc_name = condition_data.get("npc")
    expected = condition_data.get("equals", True)
    if not npc_name:
        return False
    return npc_mgr.has_npc_been_interacted_with(npc_name) == expected


@ConditionRegistry.register("npc_dialog_level")
def check_npc_dialog_level(condition_data: dict[str, Any], context: GameContext) -> bool:
    """Check an NPC's dialog level."""
    npc_mgr = context.npc_manager
    if not npc_mgr:
        return False
    npc_name = condition_data.get("npc")
    expected_level = condition_data.get("equals")
    if not npc_name or expected_level is None:
        return False
    npc_state = npc_mgr.get_npc_by_name(npc_name)
    return npc_state is not None and npc_state.dialog_level == expected_level
