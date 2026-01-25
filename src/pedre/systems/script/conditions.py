"""Conditions module for script."""

import logging
from typing import TYPE_CHECKING, Any

from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@ConditionRegistry.register("script_completed")
def check_script_completed(condition: dict[str, Any], context: GameContext) -> bool:
    """Check if a specific script has fully completed all its actions.

    Condition format:
        {"check": "script_completed", "script": "script_name"}

    Args:
        condition: Condition data with "script" key.
        context: Game context for system access.

    Returns:
        True if the script has completed all actions, False otherwise.
    """
    script_manager = context.script_manager
    if not script_manager:
        return False

    script_name = condition.get("script", "")
    if not script_name:
        logger.warning("script_completed condition missing 'script' field")
        return False

    script = script_manager.get_scripts().get(script_name)
    if not script:
        return False

    return script.completed
