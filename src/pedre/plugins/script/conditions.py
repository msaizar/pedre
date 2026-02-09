"""Conditions module for script."""

import logging
from typing import TYPE_CHECKING, Any

from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


def _validate_script_completed(data: dict[str, Any]) -> list[str]:
    errors = []
    if not data.get("script"):
        errors.append("missing required 'script' field")
    return errors


@ConditionRegistry.register("script_completed", validator=_validate_script_completed)
def check_script_completed(condition: dict[str, Any], context: GameContext) -> bool:
    """Check if a specific script has fully completed all its actions.

    Condition format:
        {"check": "script_completed", "script": "script_name"}

    Args:
        condition: Condition data with "script" key.
        context: Game context for plugin access.

    Returns:
        True if the script has completed all actions, False otherwise.
    """
    script_plugin = context.script_plugin

    script_name = condition.get("script", "")
    if not script_name:
        logger.warning("script_completed condition missing 'script' field")
        return False

    script = script_plugin.get_scripts().get(script_name)
    if not script:
        logger.warning("script_completed condition script not found")
        return False

    return script.completed
