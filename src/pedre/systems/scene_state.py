"""Scene state cache for persisting NPC and script state across scene transitions.

This module provides a cache that stores NPC state (position, visibility, dialog level)
and script state (has_run flags, interacted objects) per-scene, allowing NPCs and
scripts to maintain their state when the player leaves and returns to a scene during
a play session.

The cache works in two layers:
1. In-memory cache: Fast access during gameplay, cleared on game exit
2. Save file persistence: States are included in save files for long-term storage

Key features:
- Per-scene NPC state storage (position, visibility, dialog level)
- Per-scene script state storage (completed run_once scripts, interacted objects)
- Automatic caching during scene transitions
- Integration with save/load system
- Memory-efficient: only stores modified states

Example usage:
    # Create cache (typically one per game session)
    scene_cache = SceneStateCache()

    # Before leaving a scene, cache NPC and script states
    scene_cache.cache_scene_state("village.tmx", npc_manager, script_manager)

    # When returning to a scene, restore cached states
    scene_cache.restore_scene_state("village.tmx", npc_manager, script_manager)

    # For save/load integration
    save_data = scene_cache.to_dict()  # Include in save file
    scene_cache.from_dict(loaded_data)  # Restore from save file
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pedre.sprites.animated_npc import AnimatedNPC

if TYPE_CHECKING:
    from pedre.systems.interaction import InteractionManager
    from pedre.systems.npc import NPCManager
    from pedre.systems.script import ScriptManager
    from pedre.types import SceneStateCacheDict

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


@dataclass
class ScriptSceneState:
    """State of scripts within a scene.

    Captures script execution state needed to restore scripts to their exact
    condition when the player left the scene.

    Attributes:
        completed_scripts: Set of script names that have completed (run_once scripts).
        interacted_objects: Set of object names that have been interacted with.
    """

    completed_scripts: set[str] = field(default_factory=set)
    interacted_objects: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, list[str]]:
        """Convert to dictionary for serialization."""
        return {
            "completed_scripts": list(self.completed_scripts),
            "interacted_objects": list(self.interacted_objects),
        }

    @classmethod
    def from_dict(cls, data: dict[str, list[str]]) -> ScriptSceneState:
        """Create from dictionary loaded from save file."""
        return cls(
            completed_scripts=set(data.get("completed_scripts", [])),
            interacted_objects=set(data.get("interacted_objects", [])),
        )


@dataclass
class SceneStateCache:
    """Cache for storing NPC and script state per scene across transitions.

    Maintains dictionaries mapping scene names to NPC and script states, allowing
    NPCs and scripts to retain their state when the player leaves and later
    returns to a scene.

    The cache is designed to be:
    - Fast: In-memory storage for quick access during gameplay
    - Persistent: Can be serialized to save files
    - Memory-efficient: Only stores scenes that have been visited

    Attributes:
        _scene_states: Dictionary mapping scene names to NPC states.
            Each scene maps NPC names to their NPCSceneState.
        _script_states: Dictionary mapping scene names to script states.
            Each scene stores a ScriptSceneState with completed scripts and interacted objects.
    """

    _scene_states: dict[str, dict[str, NPCSceneState]] = field(default_factory=dict)
    _script_states: dict[str, ScriptSceneState] = field(default_factory=dict)

    def cache_scene_state(
        self,
        scene_name: str,
        npc_manager: NPCManager,
        script_manager: ScriptManager | None = None,
        interaction_manager: InteractionManager | None = None,
    ) -> None:
        """Cache the current NPC and script states for a scene.

        Should be called before transitioning away from a scene to preserve
        NPC positions, states, and script execution state.

        Args:
            scene_name: Name of the scene (e.g., "village.tmx").
            npc_manager: The NPC manager containing current NPC states.
            script_manager: Optional script manager containing current script states.
            interaction_manager: Optional interaction manager containing current interaction states.

        Side effects:
            - Updates _scene_states with current NPC data
            - Updates _script_states with current script data (if script_manager provided)
            - Logs debug message with cached NPC count
        """
        scene_state: dict[str, NPCSceneState] = {}

        for npc_name, npc_state in npc_manager.npcs.items():
            # Extract animation completion flags if this is an AnimatedNPC
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
        logger.debug(
            "Cached state for %d NPCs in scene %s",
            len(scene_state),
            scene_name,
        )

        # Cache script state if script manager provided
        if script_manager:
            script_state = ScriptSceneState(
                completed_scripts=set(script_manager.get_completed_scripts()),
                interacted_objects=set(interaction_manager.interacted_objects) if interaction_manager else set(),
            )
            self._script_states[scene_name] = script_state
            logger.debug(
                "Cached script state for scene %s: %d completed scripts, %d interacted objects",
                scene_name,
                len(script_state.completed_scripts),
                len(script_state.interacted_objects),
            )

    def restore_scene_state(
        self,
        scene_name: str,
        npc_manager: NPCManager,
        script_manager: ScriptManager | None = None,
        interaction_manager: InteractionManager | None = None,
    ) -> bool:
        """Restore cached NPC and script states for a scene.

        Should be called after NPCs and scripts are created during scene setup to
        restore their previously cached positions and states.

        Args:
            scene_name: Name of the scene (e.g., "village.tmx").
            npc_manager: The NPC manager to restore states into.
            script_manager: Optional script manager to restore script states into.
            interaction_manager: Optional interaction manager to restore interaction states into.

        Returns:
            True if cached state was found and restored, False if no cache exists.

        Side effects:
            - Updates NPC sprite positions and visibility
            - Updates NPC dialog levels
            - Updates AnimatedNPC animation completion flags
            - Restores completed script flags and interacted objects (if script_manager provided)
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

                # Restore animation completion flags for AnimatedNPC
                if isinstance(npc.sprite, AnimatedNPC):
                    npc.sprite.appear_complete = cached_state.appear_complete
                    npc.sprite.disappear_complete = cached_state.disappear_complete
                    npc.sprite.interact_complete = cached_state.interact_complete

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

        # Restore script state if script manager provided and cached state exists
        if script_manager:
            script_state = self._script_states.get(scene_name)
            if script_state:
                # Restore completed scripts (has_run flags)
                script_manager.restore_completed_scripts(list(script_state.completed_scripts))
                # Restore interacted objects
                if interaction_manager:
                    interaction_manager.interacted_objects.update(script_state.interacted_objects)
                logger.debug(
                    "Restored script state for scene %s: %d completed scripts, %d interacted objects",
                    scene_name,
                    len(script_state.completed_scripts),
                    len(script_state.interacted_objects),
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
        self._script_states.clear()
        logger.debug("Cleared scene state cache")

    def to_dict(self) -> SceneStateCacheDict:
        """Convert cache to dictionary for save file serialization.

        Returns:
            Nested dictionary with:
            - "npc_states": scene_name -> npc_name -> state_dict
            - "script_states": scene_name -> script_state_dict
        """
        npc_result: dict[str, dict[str, dict[str, float | bool | int]]] = {}
        for scene_name, scene_state in self._scene_states.items():
            npc_result[scene_name] = {npc_name: npc_state.to_dict() for npc_name, npc_state in scene_state.items()}

        script_result: dict[str, dict[str, list[str]]] = {}
        for scene_name, script_state in self._script_states.items():
            script_result[scene_name] = script_state.to_dict()

        return {
            "npc_states": npc_result,
            "script_states": script_result,
        }

    def from_dict(self, data: SceneStateCacheDict) -> None:
        """Restore cache from dictionary loaded from save file.

        Args:
            data: Nested dictionary from save file with "npc_states" and "script_states" keys.

        Side effects:
            - Clears existing cache
            - Populates with loaded data
        """
        self._scene_states.clear()
        self._script_states.clear()

        npc_data = data["npc_states"]
        for scene_name, scene_data in npc_data.items():
            self._scene_states[scene_name] = {
                npc_name: NPCSceneState.from_dict(npc_state) for npc_name, npc_state in scene_data.items()
            }

        script_data = data.get("script_states", {})
        for scene_name, scene_script_data in script_data.items():
            self._script_states[scene_name] = ScriptSceneState.from_dict(scene_script_data)

        logger.info(
            "Loaded scene state cache with %d NPC scenes, %d script scenes",
            len(self._scene_states),
            len(self._script_states),
        )
