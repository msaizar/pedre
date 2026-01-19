"""NPC save provider for persisting NPC state to save files."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.saves.base import BaseSaveProvider
from pedre.saves.registry import SaveRegistry
from pedre.sprites.animated_npc import AnimatedNPC

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.systems.npc import NPCManager

logger = logging.getLogger(__name__)


@dataclass
class NPCState:
    """State of a single NPC.

    Attributes:
        x: X position in pixel coordinates.
        y: Y position in pixel coordinates.
        visible: Whether the sprite is visible.
        dialog_level: Current dialog progression level.
        appear_complete: Whether appear animation has completed.
        disappear_complete: Whether disappear animation has completed.
        interact_complete: Whether interact animation has completed.
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
    def from_dict(cls, data: dict[str, float | bool | int]) -> NPCState:
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


@SaveRegistry.register
class NPCSaveProvider(BaseSaveProvider):
    """Save provider for NPC state persistence.

    Saves NPC position, visibility, dialog level, and animation flags
    per scene to preserve state in save files.
    """

    name: ClassVar[str] = "npc"
    priority: ClassVar[int] = 100

    def __init__(self) -> None:
        """Initialize the NPC save provider."""
        # scene_name -> npc_name -> NPCState
        self._scene_states: dict[str, dict[str, NPCState]] = {}

    def gather(self, context: GameContext) -> None:
        """Gather NPC states from the NPC manager."""
        npc_manager = cast("NPCManager | None", context.get_system("npc"))
        if not npc_manager:
            return

        # Get current scene name from map manager
        map_manager = context.get_system("map")
        scene_name = ""
        if map_manager and hasattr(map_manager, "current_map"):
            scene_name = map_manager.current_map

        if not scene_name:
            return

        scene_state: dict[str, NPCState] = {}
        for npc_name, npc_state in npc_manager.npcs.items():
            appear_complete = False
            disappear_complete = False
            interact_complete = False
            if isinstance(npc_state.sprite, AnimatedNPC):
                appear_complete = npc_state.sprite.appear_complete
                disappear_complete = npc_state.sprite.disappear_complete
                interact_complete = npc_state.sprite.interact_complete

            scene_state[npc_name] = NPCState(
                x=npc_state.sprite.center_x,
                y=npc_state.sprite.center_y,
                visible=npc_state.sprite.visible,
                dialog_level=npc_state.dialog_level,
                appear_complete=appear_complete,
                disappear_complete=disappear_complete,
                interact_complete=interact_complete,
            )

        self._scene_states[scene_name] = scene_state
        logger.debug("Gathered state for %d NPCs in scene %s", len(scene_state), scene_name)

    def restore(self, context: GameContext) -> bool:
        """Restore NPC states to the NPC manager."""
        npc_manager = cast("NPCManager | None", context.get_system("npc"))
        if not npc_manager:
            return False

        # Get current scene name from map manager
        map_manager = context.get_system("map")
        scene_name = ""
        if map_manager and hasattr(map_manager, "current_map"):
            scene_name = map_manager.current_map

        if not scene_name:
            return False

        scene_state = self._scene_states.get(scene_name)
        if not scene_state:
            return False

        restored_count = 0
        for npc_name, saved_state in scene_state.items():
            npc = npc_manager.npcs.get(npc_name)
            if npc:
                npc.sprite.center_x = saved_state.x
                npc.sprite.center_y = saved_state.y
                npc.sprite.visible = saved_state.visible
                npc.dialog_level = saved_state.dialog_level

                if isinstance(npc.sprite, AnimatedNPC):
                    npc.sprite.appear_complete = saved_state.appear_complete
                    npc.sprite.disappear_complete = saved_state.disappear_complete
                    npc.sprite.interact_complete = saved_state.interact_complete

                restored_count += 1

        logger.info(
            "Restored state for %d/%d NPCs in scene %s",
            restored_count,
            len(scene_state),
            scene_name,
        )
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize NPC state for save files."""
        result: dict[str, dict[str, dict[str, float | bool | int]]] = {}
        for scene_name, scene_state in self._scene_states.items():
            result[scene_name] = {npc_name: npc_state.to_dict() for npc_name, npc_state in scene_state.items()}
        return result

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore NPC state from save file data."""
        self._scene_states.clear()
        for scene_name, scene_data in data.items():
            self._scene_states[scene_name] = {
                npc_name: NPCState.from_dict(npc_state) for npc_name, npc_state in scene_data.items()
            }

    def clear(self) -> None:
        """Clear all saved NPC states."""
        self._scene_states.clear()
