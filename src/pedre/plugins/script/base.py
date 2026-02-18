"""Base class for ScriptPlugin."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from pedre.events.registry import EventRegistry
from pedre.plugins.base import BasePlugin

if TYPE_CHECKING:
    from pedre.actions.base import Action
    from pedre.conditions.base import Condition
    from pedre.types import EntityReference


class ScriptValidationError(Exception):
    """Raised when script preflight validation fails.

    This exception is raised when one or more scripts fail validation during
    the preflight check. It contains a list of all validation errors found.

    Attributes:
        errors: List of error messages describing validation failures.
    """

    def __init__(self, errors: list[str]) -> None:
        """Initialize the exception with a list of errors.

        Args:
            errors: List of error message strings.
        """
        self.errors = errors
        summary = f"{len(errors)} script validation error(s):\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(summary)


class ScriptEvent(Protocol):
    """Protocol for events that support script data extraction."""

    def get_script_data(self) -> dict[str, Any]:
        """Get data formatted for script trigger evaluation."""
        ...


@dataclass(frozen=True)
class ScriptTrigger:
    """Data class for script trigger."""

    event_name: str
    filters: dict[str, Any]

    def get_references(self) -> set[EntityReference]:
        """Get references for the event."""
        event_cls = EventRegistry.get(self.event_name)
        if not event_cls:
            return set()

        return event_cls.get_references(self.filters)


@dataclass
class ScriptDefinition:
    """Represents a game script with triggers, conditions, and actions.

    A script encapsulates a sequence of actions that can be triggered by events
    or manual calls. Scripts support conditional execution, scene restrictions,
    and one-time execution for story progression control.

    Attributes:
        trigger: Event specification that triggers this script.
        conditions: List of condition dictionaries that must all be true.
        scene: Optional scene name where this script can run.
        run_once: If True, script only executes once per game session.
        actions: List of action dictionaries to execute in sequence.
        on_condition_fail: Optional actions to execute when conditions fail.
        has_run: Tracks if this script has started (for run_once prevention).
        completed: Tracks if this script has fully completed all actions.
    """

    trigger: ScriptTrigger | None = None
    conditions: list[dict[str, Any]] = field(default_factory=list)
    scene: str | None = None
    run_once: bool = False
    actions: list[dict[str, Any]] = field(default_factory=list)
    on_condition_fail: list[dict[str, Any]] = field(default_factory=list)
    has_run: bool = False
    completed: bool = False


@dataclass
class Script:
    """Data class for Script."""

    trigger: ScriptTrigger | None
    conditions: list[Condition]
    scene: str | None
    run_once: bool
    actions: list[Action]
    on_condition_fail: list[Action]
    has_run: bool = False
    completed: bool = False


class ScriptBasePlugin(BasePlugin, ABC):
    """Base class for ScriptPlugin."""

    role = "script_plugin"

    @abstractmethod
    def get_scripts(self) -> dict[str, Script]:
        """Get scripts."""
        ...
