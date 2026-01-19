"""Script cache provider for persisting completed scripts across scene transitions."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.caches.base import BaseCacheProvider
from pedre.caches.registry import CacheRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.systems.script import ScriptManager

logger = logging.getLogger(__name__)


@dataclass
class ScriptSceneState:
    """State of scripts within a scene.

    Captures script execution state needed to restore scripts to their exact
    condition when the player left the scene.

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
    def from_dict(cls, data: dict[str, list[str]]) -> ScriptSceneState:
        """Create from dictionary loaded from save file."""
        return cls(
            completed_scripts=set(data.get("completed_scripts", [])),
        )


@CacheRegistry.register
class ScriptCacheProvider(BaseCacheProvider):
    """Cache provider for script state persistence.

    Caches completed run_once scripts per scene to prevent them from
    re-triggering when the player returns to a scene.
    """

    name: ClassVar[str] = "script"
    priority: ClassVar[int] = 110

    def __init__(self) -> None:
        """Initialize the script cache provider."""
        self._script_states: dict[str, ScriptSceneState] = {}

    def cache(self, scene_name: str, context: GameContext) -> None:
        """Cache script states for the scene."""
        script_manager = cast("ScriptManager | None", context.get_system("script"))
        if not script_manager:
            return

        script_state = ScriptSceneState(
            completed_scripts=set(script_manager.get_completed_scripts()),
        )
        self._script_states[scene_name] = script_state
        logger.debug(
            "Cached script state for scene %s: %d completed scripts",
            scene_name,
            len(script_state.completed_scripts),
        )

    def restore(self, scene_name: str, context: GameContext) -> bool:
        """Restore script states for the scene."""
        script_state = self._script_states.get(scene_name)
        if not script_state:
            return False

        script_manager = cast("ScriptManager | None", context.get_system("script"))
        if not script_manager:
            return False

        script_manager.restore_completed_scripts(list(script_state.completed_scripts))
        logger.debug(
            "Restored script state for scene %s: %d completed scripts",
            scene_name,
            len(script_state.completed_scripts),
        )
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize script cache state for save files."""
        result: dict[str, dict[str, list[str]]] = {}
        for scene_name, script_state in self._script_states.items():
            result[scene_name] = script_state.to_dict()
        return result

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore script cache state from save file data."""
        self._script_states.clear()
        for scene_name, scene_data in data.items():
            self._script_states[scene_name] = ScriptSceneState.from_dict(scene_data)

    def clear(self) -> None:
        """Clear all cached script states."""
        self._script_states.clear()

    def has_cached_state(self, scene_name: str) -> bool:
        """Check if a scene has cached script state."""
        return scene_name in self._script_states
