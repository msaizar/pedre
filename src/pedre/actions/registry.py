"""Registry for pluggable script actions.

The ActionRegistry maps JSON "type" strings to Action classes.

It acts purely as a factory:
    JSON dict → Action.from_dict(...) → Action instance

All validation and parsing logic lives inside the Action classes.
"""

import logging
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pedre.actions import Action

logger = logging.getLogger(__name__)


class ActionParseError(Exception):
    """Raised when an action cannot be parsed."""


class ActionRegistry:
    """Central registry for all available script actions.

    Responsibilities:
        - Map string type → Action subclass
        - Instantiate Action objects from dicts

    """

    _actions: ClassVar[dict[str, type[Action]]] = {}

    @classmethod
    def register(cls, action_class: type[Action]) -> type[Action]:
        """Decorator to register an Action class."""
        action_name = action_class.name

        if action_name in cls._actions:
            msg = f"Action '{action_name}' already registered"
            raise ValueError(msg)

        cls._actions[action_name] = action_class
        logger.debug("Registered action: %s", action_name)
        return action_class

    @classmethod
    def create(cls, data: dict[str, Any]) -> Action:
        """Create an Action instance from a dictionary."""
        action_name = data.get("name")
        if not action_name:
            msg = "Action missing 'name' field"
            raise ActionParseError(msg)

        action_cls = cls._actions.get(action_name)
        if not action_cls:
            msg = f"Unknown action '{action_name}'"
            raise ActionParseError(msg)

        try:
            return action_cls.from_dict(data)
        except Exception as exc:
            msg = f"Failed to parse action '{action_name}': {exc}"
            raise ActionParseError(msg) from exc

    @classmethod
    def get(cls, name: str) -> type[Action] | None:
        """Get the action class for an action name.

        Args: name: The "action" value used in JSON scripts.

        Returns: The Action class if registered, None otherwise.
        """
        return cls._actions.get(name)

    @classmethod
    def get_all_names(cls) -> list[str]:
        """Get all registered action names.

        Returns:
            List of action names strings that areregistered.
        """
        return list(cls._actions.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if an action is registered.

        Args:
            name: The action name to check.

        Returns:
            True if the action name has an action registered, False otherwise.
        """
        return name in cls._actions

    @classmethod
    def clear(cls) -> None:
        """Clear the registry.

        Removes all registered actions. This is primarily useful
        for testing to ensure a clean state between tests.

        Removes all registered actions. This is primarily useful
        for testing to ensure a clean state between tests.
        """
        cls._actions.clear()
        logger.debug("Action registry cleared")
