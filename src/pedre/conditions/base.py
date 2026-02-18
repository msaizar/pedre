"""Base class for all conditions."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Self

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext
    from pedre.types import EntityReference


class Condition(ABC):
    """Base class that all conditions must inherit from.

    A Condition represents a check that returns True or False based on the game state.
    Conditions are used in scripts to determine if actions should execute.

    Subclasses must implement:
    1. check(context) - The logic to evaluate the condition
    2. from_dict(data) - Factory method to create instance from JSON data
    """

    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs: dict[str, Any]) -> None:
        """Init for subclasses of Condition."""
        super().__init_subclass__(**kwargs)

        # Only enforce if class explicitly declares it wants registration
        if "name" not in cls.__dict__:
            return  # treat as non-registrable base class

        if not isinstance(cls.name, str):
            msg = f"{cls.__name__}.name must be a string"
            raise TypeError(msg)

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

    def get_references(self) -> set[EntityReference]:
        """Return entity references used by this condition."""
        return set()
