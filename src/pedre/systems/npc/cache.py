"""NPC cache provider for persisting NPC state across scene transitions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.caches.base import BaseCacheProvider
from pedre.caches.registry import CacheRegistry
from pedre.sprites.animated_npc import AnimatedNPC

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.systems.npc import NPCManager

logger = logging.getLogger(__name__)


@dataclass
class NPCSceneState:
    """State of a single NPC within a scene.

    Captures all the state needed to restore an NPC to its exact condition
    when the player left the scene.

    Attributes:
        x: X position in pixel coordinates.
        y: Y position in pixel coordinates.
        visible: Whether the sprite is visible.
        dialog_level: Current dialog progression level.
        appear_complete: Whether appear animation has completed (AnimatedNPC only).
        disappear_complete: Whether disappear animation has completed (AnimatedNPC only).
        interact_complete: Whether interact animation has completed (AnimatedNPC only).
    """

    x: float
    y: float
    visible: bool
    dialog_level: int = 0
    appear_complete: bool = False
    disappear_complete: bool = False
    interact_complete: bool = False

    def to_dict(self) -> dict[str, float | bool | int]:
        """Convert to dictionary for serialization."""
        return {
            "x": self.x,
            "y": self.y,
            "visible": self.visible,
            "dialog_level": self.dialog_level,
            "appear_complete": self.appear_complete,
            "disappear_complete": self.disappear_complete,
            "interact_complete": self.interact_complete,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float | bool | int]) -> NPCSceneState:
        """Create from dictionary loaded from save file."""
        return cls(
            x=float(data["x"]),
            y=float(data["y"]),
            visible=bool(data["visible"]),
            dialog_level=int(data.get("dialog_level", 0)),
            appear_complete=bool(data.get("appear_complete", False)),
            disappear_complete=bool(data.get("disappear_complete", False)),
            interact_complete=bool(data.get("interact_complete", False)),
        )


@CacheRegistry.register
class NPCCacheProvider(BaseCacheProvider):
    """Cache provider for NPC state persistence.

    Caches NPC position, visibility, dialog level, and animation flags
    per scene to preserve state across scene transitions.
    """

    name: ClassVar[str] = "npc"
    priority: ClassVar[int] = 100

    def __init__(self) -> None:
        """Initialize the NPC cache provider."""
        self._scene_states: dict[str, dict[str, NPCSceneState]] = {}

    def cache(self, scene_name: str, context: GameContext) -> None:
        """Cache NPC states for the scene."""
        npc_manager = cast("NPCManager | None", context.get_system("npc"))
        if not npc_manager:
            return

        scene_state: dict[str, NPCSceneState] = {}
        for npc_name, npc_state in npc_manager.npcs.items():
            appear_complete = False
            disappear_complete = False
            interact_complete = False
            if isinstance(npc_state.sprite, AnimatedNPC):
                appear_complete = npc_state.sprite.appear_complete
                disappear_complete = npc_state.sprite.disappear_complete
                interact_complete = npc_state.sprite.interact_complete

            scene_state[npc_name] = NPCSceneState(
                x=npc_state.sprite.center_x,
                y=npc_state.sprite.center_y,
                visible=npc_state.sprite.visible,
                dialog_level=npc_state.dialog_level,
                appear_complete=appear_complete,
                disappear_complete=disappear_complete,
                interact_complete=interact_complete,
            )

        self._scene_states[scene_name] = scene_state
        logger.debug("Cached state for %d NPCs in scene %s", len(scene_state), scene_name)

    def restore(self, scene_name: str, context: GameContext) -> bool:
        """Restore NPC states for the scene."""
        scene_state = self._scene_states.get(scene_name)
        if not scene_state:
            return False

        npc_manager = cast("NPCManager | None", context.get_system("npc"))
        if not npc_manager:
            return False

        restored_count = 0
        for npc_name, cached_state in scene_state.items():
            npc = npc_manager.npcs.get(npc_name)
            if npc:
                npc.sprite.center_x = cached_state.x
                npc.sprite.center_y = cached_state.y
                npc.sprite.visible = cached_state.visible
                npc.dialog_level = cached_state.dialog_level

                if isinstance(npc.sprite, AnimatedNPC):
                    npc.sprite.appear_complete = cached_state.appear_complete
                    npc.sprite.disappear_complete = cached_state.disappear_complete
                    npc.sprite.interact_complete = cached_state.interact_complete

                restored_count += 1

        logger.info(
            "Restored cached state for %d/%d NPCs in scene %s",
            restored_count,
            len(scene_state),
            scene_name,
        )
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize NPC cache state for save files."""
        result: dict[str, dict[str, dict[str, float | bool | int]]] = {}
        for scene_name, scene_state in self._scene_states.items():
            result[scene_name] = {npc_name: npc_state.to_dict() for npc_name, npc_state in scene_state.items()}
        return result

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore NPC cache state from save file data."""
        self._scene_states.clear()
        for scene_name, scene_data in data.items():
            self._scene_states[scene_name] = {
                npc_name: NPCSceneState.from_dict(npc_state) for npc_name, npc_state in scene_data.items()
            }

    def clear(self) -> None:
        """Clear all cached NPC states."""
        self._scene_states.clear()

    def has_cached_state(self, scene_name: str) -> bool:
        """Check if a scene has cached NPC state."""
        return scene_name in self._scene_states
