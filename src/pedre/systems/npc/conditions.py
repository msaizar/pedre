"""Conditions module for npc."""

from typing import TYPE_CHECKING, Any

from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext


@ConditionRegistry.register("npc_interacted")
def check_npc_interacted(condition_data: dict[str, Any], context: GameContext) -> bool:
    """Check if an NPC has been interacted with in a specific scene.

    Args:
        condition_data: Dictionary containing:
            - npc: Name of the NPC to check
            - scene: Optional scene name (defaults to current scene)
            - equals: Expected value (default: True)
        context: Game context providing access to managers

    Returns:
        True if the interaction status matches the expected value.

    Example:
        # Check if NPC was interacted with in current scene
        {"check": "npc_interacted", "npc": "guard"}

        # Check if NPC was interacted with in specific scene
        {"check": "npc_interacted", "npc": "guard", "scene": "village"}

        # Check if NPC was NOT interacted with
        {"check": "npc_interacted", "npc": "guard", "equals": False}
    """
    npc_mgr = context.npc_manager
    npc_name = condition_data.get("npc")
    scene_name = condition_data.get("scene")
    expected = condition_data.get("equals", True)
    if not npc_name:
        return False
    return npc_mgr.has_npc_been_interacted_with(npc_name, scene_name) == expected


@ConditionRegistry.register("npc_dialog_level")
def check_npc_dialog_level(condition_data: dict[str, Any], context: GameContext) -> bool:
    """Check an NPC's dialog level."""
    npc_mgr = context.npc_manager
    npc_name = condition_data.get("npc")
    expected_level = condition_data.get("equals")
    if not npc_name or expected_level is None:
        return False
    npc_state = npc_mgr.get_npc_by_name(npc_name)
    return npc_state is not None and npc_state.dialog_level == expected_level
