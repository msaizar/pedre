"""Conditions module for script."""

import logging
from typing import TYPE_CHECKING, Any, Self

from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


@ConditionRegistry.register("script_completed")
class ScriptCompletedCondition(Condition):
    """Check if a specific script has fully completed all its actions."""

    def __init__(self, script_name: str) -> None:
        """Initialize condition with script name."""
        self.script_name = script_name

    def check(self, context: GameContext) -> bool:
        """Check if script is complete."""
        script_plugin = context.script_plugin
        if not self.script_name:
            logger.warning("script_completed condition missing 'script' field")
            return False

        script = script_plugin.get_scripts().get(self.script_name)
        if not script:
            # If the script doesn't exist, it can't be complete
            # (or maybe it should warn? Old logic warned and returned False)
            logger.warning("script_completed condition script not found: %s", self.script_name)
            return False

        return script.completed

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(script_name=data.get("script", ""))

    @staticmethod
    def validate_params(data: dict[str, Any]) -> list[str]:
        """Validate parameters."""
        errors = []
        script = data.get("script")
        if not script:
            errors.append("missing required 'script' field")
        elif not isinstance(script, str):
            errors.append("'script' must be a string")
        return errors
