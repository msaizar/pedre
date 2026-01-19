"""Script save provider for persisting completed scripts to save files."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.saves.base import BaseSaveProvider
from pedre.saves.registry import SaveRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.systems.script import ScriptManager

logger = logging.getLogger(__name__)


@dataclass
class ScriptState:
    """State of scripts within a scene.

    Attributes:
        completed_scripts: Set of script names that have completed (run_once scripts).
    """

    completed_scripts: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, list[str]]:
        """Convert to dictionary for serialization."""
        return {
            "completed_scripts": list(self.completed_scripts),
        }

    @classmethod
    def from_dict(cls, data: dict[str, list[str]]) -> ScriptState:
        """Create from dictionary loaded from save file."""
        return cls(
            completed_scripts=set(data.get("completed_scripts", [])),
        )


@SaveRegistry.register
class ScriptSaveProvider(BaseSaveProvider):
    """Save provider for script state persistence.

    Saves completed run_once scripts per scene to prevent them from
    re-triggering when the game is loaded.
    """

    name: ClassVar[str] = "script"
    priority: ClassVar[int] = 110

    def __init__(self) -> None:
        """Initialize the script save provider."""
        # scene_name -> ScriptState
        self._script_states: dict[str, ScriptState] = {}

    def gather(self, context: GameContext) -> None:
        """Gather script states from the script manager."""
        script_manager = cast("ScriptManager | None", context.get_system("script"))
        if not script_manager:
            return

        # Get current scene name from scene manager
        scene_manager = context.get_system("scene")
        scene_name = ""
        if scene_manager and hasattr(scene_manager, "current_map"):
            scene_name = scene_manager.current_map

        if not scene_name:
            return

        script_state = ScriptState(
            completed_scripts=set(script_manager.get_completed_scripts()),
        )
        self._script_states[scene_name] = script_state
        logger.debug(
            "Gathered script state for scene %s: %d completed scripts",
            scene_name,
            len(script_state.completed_scripts),
        )

    def restore(self, context: GameContext) -> bool:
        """Restore script states to the script manager."""
        script_manager = cast("ScriptManager | None", context.get_system("script"))
        if not script_manager:
            return False

        # Get current scene name from scene manager
        scene_manager = context.get_system("scene")
        scene_name = ""
        if scene_manager and hasattr(scene_manager, "current_map"):
            scene_name = scene_manager.current_map

        if not scene_name:
            return False

        script_state = self._script_states.get(scene_name)
        if not script_state:
            return False

        script_manager.restore_completed_scripts(list(script_state.completed_scripts))
        logger.debug(
            "Restored script state for scene %s: %d completed scripts",
            scene_name,
            len(script_state.completed_scripts),
        )
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize script state for save files."""
        result: dict[str, dict[str, list[str]]] = {}
        for scene_name, script_state in self._script_states.items():
            result[scene_name] = script_state.to_dict()
        return result

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore script state from save file data."""
        self._script_states.clear()
        for scene_name, scene_data in data.items():
            self._script_states[scene_name] = ScriptState.from_dict(scene_data)

    def clear(self) -> None:
        """Clear all saved script states."""
        self._script_states.clear()
