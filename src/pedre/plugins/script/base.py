"""Base class for ScriptPlugin."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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
