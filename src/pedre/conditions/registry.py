"""Registry for pluggable script conditions.

This module provides the ConditionRegistry class which tracks all available
condition checkers for the scripting plugin. Plugins register their own
condition logic, enabling the script plugin to remain decoupled.
"""

import logging
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


class ConditionRegistry:
    """Central registry for all available script conditions.

    The ConditionRegistry maintains a mapping of condition names (e.g., "npc_interacted")
    to checker functions. This allows any plugin to provide its own logic for
    evaluating script conditions.
    """

    _checkers: ClassVar[dict[str, Callable[[dict[str, Any], GameContext], bool]]] = {}
    _validators: ClassVar[dict[str, Callable[[dict[str, Any]], list[str]]]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        *,
        validator: Callable[[dict[str, Any]], list[str]] | None = None,
    ) -> Callable[
        [Callable[[dict[str, Any], GameContext], bool]],
        Callable[[dict[str, Any], GameContext], bool],
    ]:
        """Decorator to register a condition checker function.

        Args:
            name: The name used in JSON scripts to identify this condition
                 (e.g., "inventory_accessed").
            validator: Optional parameter validation function that takes condition
                 data and returns a list of error strings.

        Returns:
            Decorator function that registers the checker.

        Example:
            Registering a condition with validator::

                def _validate_npc_interacted(data: dict[str, Any]) -> list[str]:
                    errors = []
                    if not data.get("npc"):
                        errors.append("npc_interacted: missing required 'npc' field")
                    return errors

                @ConditionRegistry.register("npc_interacted", validator=_validate_npc_interacted)
                def check_npc_interacted(condition_data: dict[str, Any], context: GameContext) -> bool:
                    ...
        """

        def decorator(
            checker_func: Callable[[dict[str, Any], GameContext], bool],
        ) -> Callable[[dict[str, Any], GameContext], bool]:
            cls._checkers[name] = checker_func
            logger.debug("Registered condition checker: %s", name)

            if validator is not None:
                cls._validators[name] = validator
                logger.debug("Registered condition validator: %s", name)

            return checker_func

        return decorator

    @classmethod
    def check(cls, name: str, condition_data: dict[str, Any], context: GameContext) -> bool:
        """Evaluate a condition by name using its registered checker.

        Args:
            name: Name of the condition to check.
            condition_data: Dictionary of parameters from the script.
            context: Game context for plugin access.

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
    def is_registered(cls, name: str) -> bool:
        """Check if a condition type is registered.

        Args:
            name: The condition type name to check.

        Returns:
            True if the condition type has a checker registered, False otherwise.
        """
        return name in cls._checkers

    @classmethod
    def get_all_types(cls) -> list[str]:
        """Get all registered condition type names.

        Returns:
            List of condition type strings that have checkers registered.
        """
        return list(cls._checkers.keys())

    @classmethod
    def validate(cls, name: str, condition_data: dict[str, Any]) -> list[str]:
        """Validate condition parameters.

        Args:
            name: The condition type name.
            condition_data: Dictionary of condition parameters from the script.

        Returns:
            List of error message strings. Empty list means validation passed.

        Example:
            Validating a condition::

                errors = ConditionRegistry.validate("npc_interacted", {
                    "check": "npc_interacted",
                    "scene": "village"
                    # Missing required "npc" field
                })
                # Returns: ["npc_interacted: missing required 'npc' field"]
        """
        validator = cls._validators.get(name)
        if validator:
            return validator(condition_data)
        return []

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (primarily for testing)."""
        cls._checkers.clear()
        cls._validators.clear()
        logger.debug("Condition registry cleared")
