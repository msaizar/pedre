"""Action plugin for reusable, chainable game actions."""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Self

if TYPE_CHECKING:
    from collections.abc import Callable

    from pedre.plugins.game_context import GameContext
    from pedre.types import EntityReference

logger = logging.getLogger(__name__)


class Action(ABC):
    """Base class for all actions."""

    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs: dict[str, Any]) -> None:
        """Init for subclasses of Action."""
        super().__init_subclass__(**kwargs)

        # Only enforce if class explicitly declares it wants registration
        if "name" not in cls.__dict__:
            return  # treat as non-registrable base class

        if not isinstance(cls.name, str):
            msg = f"{cls.__name__}.name must be a string"
            raise TypeError(msg)

    @abstractmethod
    def execute(self, context: GameContext) -> bool:
        """Execute the action.

        Args:
            context: Game context containing all plugins and state.

        Returns:
            True if action is complete, False if still executing.
        """

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create Action from a dictionary."""

    def get_references(self) -> set[EntityReference]:
        """Return entity references used by this action.

        Default: no references.
        """
        return set()

    @abstractmethod
    def reset(self) -> None:
        """Reset action state for reuse."""


class WaitForConditionAction(Action):
    """Wait until a condition is met.

    This is a base class for creating actions that pause execution until a specific
    condition becomes true. Unlike actions that complete immediately, this action
    will continue to return False from execute() until the condition function returns True.

    This enables complex sequencing where later actions wait for asynchronous events
    like NPC movements, animations, or player interactions to complete.

    The condition function receives the GameContext and should return True when the
    wait is over. The description is used for debug logging to help track what the
    plugin is waiting for.

    This class is typically subclassed for specific wait conditions rather than used
    directly. See WaitForDialogCloseAction, WaitForNPCMovementAction, etc.

    Example subclass:
        class WaitForCustomAction(WaitForConditionAction):
            def __init__(self):
                super().__init__(
                    lambda ctx: ctx.custom_plugin.is_ready,
                    "Custom event ready"
                )
    """

    def __init__(self, condition: Callable[[GameContext], bool], description: str = "") -> None:
        """Initialize wait action.

        Args:
            condition: Function that returns True when condition is met.
            description: Description of what we're waiting for (for debugging).
        """
        self.condition = condition
        self.description = description

    def execute(self, context: GameContext) -> bool:
        """Check if condition is met."""
        result = self.condition(context)
        if result:
            logger.debug("WaitForConditionAction: Condition met - %s", self.description)
        return result

    def reset(self) -> None:
        """Reset does nothing for wait actions."""


class ActionSequence(Action):
    """Execute multiple actions in sequence.

    This action container executes a list of actions one after another, waiting
    for each action to complete before proceeding to the next. This enables
    complex scripted sequences where actions must happen in a specific order.

    The sequence tracks which action is currently executing via current_index.
    Each frame, it executes the current action and advances to the next when
    that action returns True (indicating completion).

    Actions within the sequence can be immediate (complete in one frame) or
    waiting actions (complete when a condition is met), allowing for flexible
    timing and synchronization.

    Example usage:
        ActionSequence([
            DialogAction("martin", ["Hello!"]),
            WaitForDialogCloseAction(),
            MoveNPCAction("martin", "waypoint_1"),
            WaitForNPCMovementAction("martin"),
            DialogAction("martin", ["I'm here!"])
        ])

    This is typically constructed programmatically rather than from JSON,
    though scripts can define action sequences in data files.
    """

    def __init__(self, actions: list[Action]) -> None:
        """Initialize action sequence.

        Args:
            actions: List of actions to execute in order.
        """
        self.actions = actions
        self.current_index = 0

    def execute(self, context: GameContext) -> bool:
        """Execute current action and advance if complete."""
        if self.current_index >= len(self.actions):
            return True

        current_action = self.actions[self.current_index]
        if current_action.execute(context):
            self.current_index += 1

        return self.current_index >= len(self.actions)

    def reset(self) -> None:
        """Reset the sequence and all actions."""
        self.current_index = 0
        for action in self.actions:
            action.reset()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create ActionSequence from a dictionary."""
        return cls(**data)
