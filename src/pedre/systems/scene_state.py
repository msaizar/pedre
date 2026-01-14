"""Scene state cache for persisting NPC state across scene transitions.

This module provides a cache that stores NPC state (position, visibility, dialog level)
per-scene, allowing NPCs to maintain their state when the player leaves and returns
to a scene during a play session.

The cache works in two layers:
1. In-memory cache: Fast access during gameplay, cleared on game exit
2. Save file persistence: NPC states are included in save files for long-term storage

Key features:
- Per-scene NPC state storage (position, visibility, dialog level)
- Automatic caching during scene transitions
- Integration with save/load system
- Memory-efficient: only stores modified NPC states

Example usage:
    # Create cache (typically one per game session)
    scene_cache = SceneStateCache()

    # Before leaving a scene, cache NPC states
    scene_cache.cache_scene_state("village.tmx", npc_manager)

    # When returning to a scene, restore cached states
    scene_cache.restore_scene_state("village.tmx", npc_manager)

    # For save/load integration
    save_data = scene_cache.to_dict()  # Include in save file
    scene_cache.from_dict(loaded_data)  # Restore from save file
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
    """

    x: float
    y: float
    visible: bool
    dialog_level: int = 0

    def to_dict(self) -> dict[str, float | bool | int]:
        """Convert to dictionary for serialization."""
        return {
            "x": self.x,
            "y": self.y,
            "visible": self.visible,
            "dialog_level": self.dialog_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float | bool | int]) -> NPCSceneState:
        """Create from dictionary loaded from save file."""
        return cls(
            x=float(data["x"]),
            y=float(data["y"]),
            visible=bool(data["visible"]),
            dialog_level=int(data.get("dialog_level", 0)),
        )


@dataclass
class SceneStateCache:
    """Cache for storing NPC state per scene across transitions.

    Maintains a dictionary mapping scene names to NPC states, allowing
    NPCs to retain their position, visibility, and dialog state when
    the player leaves and later returns to a scene.

    The cache is designed to be:
    - Fast: In-memory storage for quick access during gameplay
    - Persistent: Can be serialized to save files
    - Memory-efficient: Only stores scenes that have been visited

    Attributes:
        _scene_states: Dictionary mapping scene names to NPC states.
            Each scene maps NPC names to their NPCSceneState.
    """

    _scene_states: dict[str, dict[str, NPCSceneState]] = field(default_factory=dict)

    def cache_scene_state(self, scene_name: str, npc_manager: NPCManager) -> None:
        """Cache the current NPC states for a scene.

        Should be called before transitioning away from a scene to preserve
        NPC positions and states.

        Args:
            scene_name: Name of the scene (e.g., "village.tmx").
            npc_manager: The NPC manager containing current NPC states.

        Side effects:
            - Updates _scene_states with current NPC data
            - Logs debug message with cached NPC count
        """
        scene_state: dict[str, NPCSceneState] = {}

        for npc_name, npc_state in npc_manager.npcs.items():
            scene_state[npc_name] = NPCSceneState(
                x=npc_state.sprite.center_x,
                y=npc_state.sprite.center_y,
                visible=npc_state.sprite.visible,
                dialog_level=npc_state.dialog_level,
            )

        self._scene_states[scene_name] = scene_state
        logger.debug(
            "Cached state for %d NPCs in scene %s",
            len(scene_state),
            scene_name,
        )

    def restore_scene_state(self, scene_name: str, npc_manager: NPCManager) -> bool:
        """Restore cached NPC states for a scene.

        Should be called after NPCs are created during scene setup to
        restore their previously cached positions and states.

        Args:
            scene_name: Name of the scene (e.g., "village.tmx").
            npc_manager: The NPC manager to restore states into.

        Returns:
            True if cached state was found and restored, False if no cache exists.

        Side effects:
            - Updates NPC sprite positions and visibility
            - Updates NPC dialog levels
            - Logs info message on restore, debug if no cache found
        """
        scene_state = self._scene_states.get(scene_name)
        if not scene_state:
            logger.debug("No cached state for scene %s", scene_name)
            return False

        restored_count = 0
        for npc_name, cached_state in scene_state.items():
            npc = npc_manager.npcs.get(npc_name)
            if npc:
                npc.sprite.center_x = cached_state.x
                npc.sprite.center_y = cached_state.y
                npc.sprite.visible = cached_state.visible
                npc.dialog_level = cached_state.dialog_level
                restored_count += 1
                logger.debug(
                    "Restored %s: pos=(%.1f, %.1f), visible=%s, dialog=%d",
                    npc_name,
                    cached_state.x,
                    cached_state.y,
                    cached_state.visible,
                    cached_state.dialog_level,
                )
            else:
                logger.warning("Cannot restore cached state for unknown NPC: %s", npc_name)

        logger.info(
            "Restored cached state for %d/%d NPCs in scene %s",
            restored_count,
            len(scene_state),
            scene_name,
        )
        return True

    def has_cached_state(self, scene_name: str) -> bool:
        """Check if a scene has cached state.

        Args:
            scene_name: Name of the scene to check.

        Returns:
            True if cached state exists for the scene, False otherwise.
        """
        return scene_name in self._scene_states

    def clear(self) -> None:
        """Clear all cached scene states.

        Typically called when starting a new game or loading a save file.
        """
        self._scene_states.clear()
        logger.debug("Cleared scene state cache")

    def to_dict(self) -> dict[str, dict[str, dict[str, float | bool | int]]]:
        """Convert cache to dictionary for save file serialization.

        Returns:
            Nested dictionary: scene_name -> npc_name -> state_dict
        """
        result: dict[str, dict[str, dict[str, float | bool | int]]] = {}
        for scene_name, scene_state in self._scene_states.items():
            result[scene_name] = {npc_name: npc_state.to_dict() for npc_name, npc_state in scene_state.items()}
        return result

    def from_dict(self, data: dict[str, dict[str, dict[str, float | bool | int]]]) -> None:
        """Restore cache from dictionary loaded from save file.

        Args:
            data: Nested dictionary from save file.

        Side effects:
            - Clears existing cache
            - Populates with loaded data
        """
        self._scene_states.clear()
        for scene_name, scene_data in data.items():
            self._scene_states[scene_name] = {
                npc_name: NPCSceneState.from_dict(npc_data) for npc_name, npc_data in scene_data.items()
            }
        logger.info("Loaded scene state cache with %d scenes", len(self._scene_states))
