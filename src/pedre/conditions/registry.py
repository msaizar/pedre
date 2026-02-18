"""Registry for pluggable script conditions.

This module provides the ConditionRegistry class which tracks all available
condition classes for the scripting plugin.
"""

import logging
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pedre.conditions.base import Condition

logger = logging.getLogger(__name__)


class ConditionParseError(Exception):
    """Raised when a condition cannot be parsed."""


class ConditionRegistry:
    """Central registry for all available script condition classes."""

    _conditions: ClassVar[dict[str, type[Condition]]] = {}

    @classmethod
    def register(cls, condition_class: type[Condition]) -> type[Condition]:
        """Decorator to register a Condition class."""
        condition_name = condition_class.name

        if condition_name in cls._conditions:
            msg = f"Condition '{condition_name}' already registered"
            raise ValueError(msg)

        cls._conditions[condition_name] = condition_class
        logger.debug("Registered condition: %s", condition_name)
        return condition_class

    @classmethod
    def create(cls, data: dict[str, Any]) -> Condition:
        """Create a condition instance from a dictionary."""
        name = data.get("name")
        if not name:
            msg = "Condition missing 'name' field"
            raise ConditionParseError(msg)

        condition_cls = cls._conditions.get(name)
        if not condition_cls:
            msg = f"Unknown condition '{name}'"
            raise ConditionParseError(msg)

        params = {k: v for k, v in data.items() if k != "name"}
        return condition_cls.from_dict(params)

    @classmethod
    def get(cls, name: str) -> type[Condition] | None:
        """Get a condition from a name."""
        return cls._conditions.get(name)

    @classmethod
    def get_all_names(cls) -> list[str]:
        """Get all registered condition names."""
        return list(cls._conditions.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a condition is registered.

        Args:
            name: The condition name to check.

        Returns:
            True if the condition name has a condition registered, False otherwise.
        """
        return name in cls._conditions

    @classmethod
    def clear(cls) -> None:
        """Clear the registry.

        Removes all registered actions. This is primarily useful
        for testing to ensure a clean state between tests.
        """
        cls._conditions.clear()
        logger.debug("Condition registry cleared")
