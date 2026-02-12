"""Registry for pluggable script conditions.

This module provides the ConditionRegistry class which tracks all available
condition classes for the scripting plugin.
"""

import logging
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from pedre.conditions.base import Condition

if TYPE_CHECKING:
    from collections.abc import Callable

    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=type[Condition])


class ConditionRegistry:
    """Central registry for all available script condition classes."""

    _conditions: ClassVar[dict[str, type[Condition]]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[T], T]:
        """Decorator to register a condition class.

        Args:
            name: The name used to identify this condition (e.g., "npc_interacted").

        Returns:
            Decorator function that registers the class.
        """

        def decorator(condition_cls: T) -> T:
            cls._conditions[name] = condition_cls
            logger.debug("Registered condition class: %s", name)
            return condition_cls

        return decorator

    @classmethod
    def create(cls, name: str, data: dict[str, Any]) -> Condition | None:
        """Create a condition instance from a dictionary.

        Args:
            name: Name of the condition type.
            data: Dictionary of parameters.

        Returns:
            Instance of the condition class, or None if unknown.
        """
        condition_cls = cls._conditions.get(name)
        if not condition_cls:
            logger.warning("ConditionRegistry: Unknown condition type: %s", name)
            return None

        try:
            return condition_cls.from_dict(data)
        except Exception:
            logger.exception("ConditionRegistry: Error creating condition '%s'", name)
            return None

    @classmethod
    def check(cls, name: str, condition_data: dict[str, Any], context: GameContext) -> bool:
        """Evaluate a condition by name.

        Convenience method that instantiates and checks the condition in one step.

        Args:
            name: Name of the condition to check.
            condition_data: Dictionary of parameters from the script.
            context: Game context for plugin access.

        Returns:
            True if the condition is met, False otherwise.
        """
        condition = cls.create(name, condition_data)
        if not condition:
            return False

        try:
            return condition.check(context)
        except Exception:
            logger.exception("ConditionRegistry: Error evaluating condition '%s'", name)
            return False

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a condition type is registered."""
        return name in cls._conditions

    @classmethod
    def get_all_types(cls) -> list[str]:
        """Get all registered condition type names."""
        return list(cls._conditions.keys())

    @classmethod
    def validate(cls, name: str, condition_data: dict[str, Any]) -> list[str]:
        """Validate condition parameters using the registered class.

        Args:
            name: The condition type name.
            condition_data: Dictionary of condition parameters.

        Returns:
            List of error message strings.
        """
        condition_cls = cls._conditions.get(name)
        if condition_cls:
            return condition_cls.validate_params(condition_data)
        return []

    @classmethod
    def clear(cls) -> None:
        """Clear the registry."""
        cls._conditions.clear()
        logger.debug("Condition registry cleared")
