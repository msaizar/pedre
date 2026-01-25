"""Base class for ScriptManager."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol

from pedre.systems.base import BaseSystem


class ScriptEvent(Protocol):
    """Protocol for events that support script data extraction."""

    def get_script_data(self) -> dict[str, Any]:
        """Get data formatted for script trigger evaluation."""
        ...


@dataclass
class Script:
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

    trigger: dict[str, Any] | None = None
    conditions: list[dict[str, Any]] = field(default_factory=list)
    scene: str | None = None
    run_once: bool = False
    actions: list[dict[str, Any]] = field(default_factory=list)
    on_condition_fail: list[dict[str, Any]] = field(default_factory=list)
    has_run: bool = False
    completed: bool = False


class ScriptBaseManager(BaseSystem, ABC):
    """Base class for ScriptManager."""

    role = "script_manager"

    @abstractmethod
    def load_scene_scripts(self, scene_name: str, npc_dialogs_data: dict[str, Any]) -> dict[str, Any]:
        """Load and cache scripts for a specific scene."""
        ...

    @abstractmethod
    def get_scripts(self) -> dict[str, Script]:
        """Get scripts."""
        ...
