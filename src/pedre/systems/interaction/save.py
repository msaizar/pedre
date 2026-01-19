"""Interaction save provider for persisting interaction state to save files."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.saves.base import BaseSaveProvider
from pedre.saves.registry import SaveRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.systems.interaction import InteractionManager

logger = logging.getLogger(__name__)


@dataclass
class InteractionState:
    """State of interactions within a scene.

    Attributes:
        interacted_objects: Set of object names that have been interacted with.
        object_states: Dictionary of object states (e.g., toggle on/off).
    """

    interacted_objects: set[str] = field(default_factory=set)
    object_states: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "interacted_objects": list(self.interacted_objects),
            "object_states": self.object_states,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InteractionState:
        """Create from dictionary loaded from save file."""
        return cls(
            interacted_objects=set(data.get("interacted_objects", [])),
            object_states=data.get("object_states", {}),
        )


@SaveRegistry.register
class InteractionSaveProvider(BaseSaveProvider):
    """Save provider for interaction state persistence.

    Saves interacted objects and object states (like toggle on/off)
    per scene to preserve interaction state in save files.
    """

    name: ClassVar[str] = "interaction"
    priority: ClassVar[int] = 120

    def __init__(self) -> None:
        """Initialize the interaction save provider."""
        # scene_name -> InteractionState
        self._interaction_states: dict[str, InteractionState] = {}

    def gather(self, context: GameContext) -> None:
        """Gather interaction states from the interaction manager."""
        interaction_manager = cast("InteractionManager | None", context.get_system("interaction"))
        if not interaction_manager:
            return

        # Get current scene name from scene manager
        scene_manager = context.get_system("scene")
        scene_name = ""
        if scene_manager and hasattr(scene_manager, "current_map"):
            scene_name = scene_manager.current_map

        if not scene_name:
            return

        # Capture object states (e.g., toggle states)
        object_states: dict[str, dict[str, Any]] = {}
        for obj_name, obj in interaction_manager.interactive_objects.items():
            if "state" in obj.properties:
                object_states[obj_name] = {"state": obj.properties["state"]}

        interaction_state = InteractionState(
            interacted_objects=set(interaction_manager.interacted_objects),
            object_states=object_states,
        )
        self._interaction_states[scene_name] = interaction_state
        logger.debug(
            "Gathered interaction state for scene %s: %d interacted objects, %d object states",
            scene_name,
            len(interaction_state.interacted_objects),
            len(interaction_state.object_states),
        )

    def restore(self, context: GameContext) -> bool:
        """Restore interaction states to the interaction manager."""
        interaction_manager = cast("InteractionManager | None", context.get_system("interaction"))
        if not interaction_manager:
            return False

        # Get current scene name from scene manager
        scene_manager = context.get_system("scene")
        scene_name = ""
        if scene_manager and hasattr(scene_manager, "current_map"):
            scene_name = scene_manager.current_map

        if not scene_name:
            return False

        interaction_state = self._interaction_states.get(scene_name)
        if not interaction_state:
            return False

        # Restore interacted objects
        interaction_manager.interacted_objects.update(interaction_state.interacted_objects)

        # Restore object states
        for obj_name, obj_state in interaction_state.object_states.items():
            if obj_name in interaction_manager.interactive_objects:
                interaction_manager.interactive_objects[obj_name].properties.update(obj_state)

        logger.debug(
            "Restored interaction state for scene %s: %d interacted objects, %d object states",
            scene_name,
            len(interaction_state.interacted_objects),
            len(interaction_state.object_states),
        )
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize interaction state for save files."""
        result: dict[str, dict[str, Any]] = {}
        for scene_name, interaction_state in self._interaction_states.items():
            result[scene_name] = interaction_state.to_dict()
        return result

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore interaction state from save file data."""
        self._interaction_states.clear()
        for scene_name, scene_data in data.items():
            self._interaction_states[scene_name] = InteractionState.from_dict(scene_data)

    def clear(self) -> None:
        """Clear all saved interaction states."""
        self._interaction_states.clear()
