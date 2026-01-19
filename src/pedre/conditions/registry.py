"""Registry for pluggable script conditions.

This module provides the ConditionRegistry class which tracks all available
condition checkers for the scripting system. Systems register their own
condition logic, enabling the script system to remain decoupled.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


class ConditionRegistry:
    """Central registry for all available script conditions.

    The ConditionRegistry maintains a mapping of condition names (e.g., "npc_interacted")
    to checker functions. This allows any system to provide its own logic for
    evaluating script conditions.
    """

    _checkers: ClassVar[dict[str, Callable[[dict[str, Any], GameContext], bool]]] = {}

    @classmethod
    def register(
        cls, name: str
    ) -> Callable[
        [Callable[[dict[str, Any], GameContext], bool]],
        Callable[[dict[str, Any], GameContext], bool],
    ]:
        """Decorator to register a condition checker function.

        Args:
            name: The name used in JSON scripts to identify this condition
                 (e.g., "inventory_accessed").

        Returns:
            Decorator function that registers the checker.
        """

        def decorator(
            checker_func: Callable[[dict[str, Any], GameContext], bool],
        ) -> Callable[[dict[str, Any], GameContext], bool]:
            cls._checkers[name] = checker_func
            logger.debug("Registered condition checker: %s", name)
            return checker_func

        return decorator

    @classmethod
    def check(cls, name: str, condition_data: dict[str, Any], context: GameContext) -> bool:
        """Evaluate a condition by name using its registered checker.

        Args:
            name: Name of the condition to check.
            condition_data: Dictionary of parameters from the script.
            context: Game context for system access.

        Returns:
            True if the condition is met, False otherwise.
        """
        checker = cls._checkers.get(name)
        if not checker:
            logger.warning("ConditionRegistry: Unknown condition type: %s", name)
            return False

        try:
            return checker(condition_data, context)
        except Exception:
            logger.exception("ConditionRegistry: Error evaluating condition '%s'", name)
            return False

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (primarily for testing)."""
        cls._checkers.clear()
        logger.debug("Condition registry cleared")
