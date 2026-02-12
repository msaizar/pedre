"""Base class for all conditions."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext


class Condition(ABC):
    """Base class that all conditions must inherit from.

    A Condition represents a check that returns True or False based on the game state.
    Conditions are used in scripts to determine if actions should execute.

    Subclasses must implement:
    1. check(context) - The logic to evaluate the condition
    2. from_dict(data) - Factory method to create instance from JSON data
    3. validate_params(data) - Static method to validate JSON parameters
    """

    @abstractmethod
    def check(self, context: GameContext) -> bool:
        """Evaluate the condition.

        Args:
            context: The game context providing access to plugins and state.

        Returns:
            True if the condition is met, False otherwise.
        """

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create a Condition instance from a dictionary.

        Args:
            data: Dictionary containing condition parameters.

        Returns:
            Review instance of the Condition subclass.
        """

    @staticmethod
    def validate_params(data: dict[str, Any]) -> list[str]:  # noqa: ARG004
        """Validate the parameters for this condition.

        Args:
            data: Dictionary containing condition parameters to validate.

        Returns:
            List of error messages. Empty list means validation passed.
        """
        return []
