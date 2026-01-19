"""Interaction cache provider for persisting interaction state across scene transitions."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.caches.base import BaseCacheProvider
from pedre.caches.registry import CacheRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.systems.interaction import InteractionManager

logger = logging.getLogger(__name__)


@dataclass
class InteractionSceneState:
    """State of interactions within a scene.

    Captures interaction state needed to restore interactions to their exact
    condition when the player left the scene.

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
    def from_dict(cls, data: dict[str, Any]) -> InteractionSceneState:
        """Create from dictionary loaded from save file."""
        return cls(
            interacted_objects=set(data.get("interacted_objects", [])),
            object_states=data.get("object_states", {}),
        )


@CacheRegistry.register
class InteractionCacheProvider(BaseCacheProvider):
    """Cache provider for interaction state persistence.

    Caches interacted objects and object states (like toggle on/off)
    per scene to preserve interaction state across scene transitions.
    """

    name: ClassVar[str] = "interaction"
    priority: ClassVar[int] = 120

    def __init__(self) -> None:
        """Initialize the interaction cache provider."""
        self._interaction_states: dict[str, InteractionSceneState] = {}

    def cache(self, scene_name: str, context: GameContext) -> None:
        """Cache interaction states for the scene."""
        interaction_manager = cast("InteractionManager | None", context.get_system("interaction"))
        if not interaction_manager:
            return

        # Capture object states (e.g., toggle states)
        object_states: dict[str, dict[str, Any]] = {}
        for obj_name, obj in interaction_manager.interactive_objects.items():
            if "state" in obj.properties:
                object_states[obj_name] = {"state": obj.properties["state"]}

        interaction_state = InteractionSceneState(
            interacted_objects=set(interaction_manager.interacted_objects),
            object_states=object_states,
        )
        self._interaction_states[scene_name] = interaction_state
        logger.debug(
            "Cached interaction state for scene %s: %d interacted objects, %d object states",
            scene_name,
            len(interaction_state.interacted_objects),
            len(interaction_state.object_states),
        )

    def restore(self, scene_name: str, context: GameContext) -> bool:
        """Restore interaction states for the scene."""
        interaction_state = self._interaction_states.get(scene_name)
        if not interaction_state:
            return False

        interaction_manager = cast("InteractionManager | None", context.get_system("interaction"))
        if not interaction_manager:
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
        """Serialize interaction cache state for save files."""
        result: dict[str, dict[str, Any]] = {}
        for scene_name, interaction_state in self._interaction_states.items():
            result[scene_name] = interaction_state.to_dict()
        return result

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore interaction cache state from save file data."""
        self._interaction_states.clear()
        for scene_name, scene_data in data.items():
            self._interaction_states[scene_name] = InteractionSceneState.from_dict(scene_data)

    def clear(self) -> None:
        """Clear all cached interaction states."""
        self._interaction_states.clear()

    def has_cached_state(self, scene_name: str) -> bool:
        """Check if a scene has cached interaction state."""
        return scene_name in self._interaction_states
