"""Actions for camera system."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self, cast

from pedre.actions import Action
from pedre.actions.registry import ActionRegistry

if TYPE_CHECKING:
    from pedre.systems.camera import CameraManager
    from pedre.systems.game_context import GameContext
    from pedre.systems.npc import NPCManager

logger = logging.getLogger(__name__)


@ActionRegistry.register("follow_player")
class FollowPlayerAction(Action):
    """Set camera to follow the player.

    This action configures the camera to continuously follow the player sprite.
    The camera will keep tracking the player's position across all frames until
    another camera action changes the follow behavior or the scene changes.

    The action completes immediately after setting the follow mode. The actual
    camera movement happens in CameraManager.update() which is called every frame.

    By default, the camera smoothly interpolates to the player's position using
    lerp (creates a slight lag effect). Set smooth=false for instant tracking.

    Example usage:
        # Smooth following (default)
        {
            "type": "follow_player"
        }

        # Instant following (no smoothing)
        {
            "type": "follow_player",
            "smooth": false
        }
    """

    def __init__(self, *, smooth: bool = True) -> None:
        """Initialize follow player action.

        Args:
            smooth: If True, use smooth interpolation. If False, instant follow.
        """
        self.smooth = smooth
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Set camera to follow player."""
        if not self.executed:
            camera_manager = cast("CameraManager", context.get_system("camera"))
            if camera_manager:
                camera_manager.set_follow_player(smooth=self.smooth)
                logger.debug(
                    "FollowPlayerAction: Camera now following player (smooth=%s)",
                    self.smooth,
                )
            else:
                logger.warning("FollowPlayerAction: No camera manager available")
            self.executed = True

        return True  # Complete immediately

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create FollowPlayerAction from a dictionary."""
        return cls(smooth=data.get("smooth", True))


@ActionRegistry.register("follow_npc")
class FollowNPCAction(Action):
    """Set camera to follow a specific NPC.

    This action configures the camera to continuously follow a named NPC sprite.
    The camera will keep tracking the NPC's position across all frames until
    another camera action changes the follow behavior or the scene changes.

    This is useful for cutscenes or scripted sequences where you want to focus
    the camera on an NPC rather than the player.

    The action completes immediately after setting the follow mode. The actual
    camera movement happens in CameraManager.update() which is called every frame.

    By default, the camera smoothly interpolates to the NPC's position using
    lerp. Set smooth=false for instant tracking.

    If the specified NPC doesn't exist, a warning is logged but the action
    still completes. The camera will not move until a valid target is set.

    Example usage:
        # Smooth following (default)
        {
            "type": "follow_npc",
            "npc": "martin"
        }

        # Instant following (no smoothing)
        {
            "type": "follow_npc",
            "npc": "boss_enemy",
            "smooth": false
        }

    Common pattern - cutscene focusing on NPC:
        [
            {"type": "follow_npc", "npc": "martin"},
            {"type": "dialog", "speaker": "martin", "text": ["Watch this!"]},
            {"type": "wait_for_dialog_close"},
            {"type": "move_npc", "npcs": ["martin"], "waypoint": "destination"},
            {"type": "wait_for_movement", "npc": "martin"},
            {"type": "follow_player"}
        ]
    """

    def __init__(self, npc_name: str, *, smooth: bool = True) -> None:
        """Initialize follow NPC action.

        Args:
            npc_name: Name of the NPC to follow.
            smooth: If True, use smooth interpolation. If False, instant follow.
        """
        self.npc_name = npc_name
        self.smooth = smooth
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Set camera to follow NPC."""
        if not self.executed:
            camera_manager = cast("CameraManager", context.get_system("camera"))
            if camera_manager:
                # Validate NPC exists
                npc_manager = cast("NPCManager", context.get_system("npc"))
                if npc_manager:
                    npc_state = npc_manager.get_npc_by_name(self.npc_name)
                    if not npc_state:
                        logger.warning("FollowNPCAction: NPC '%s' not found", self.npc_name)

                camera_manager.set_follow_npc(self.npc_name, smooth=self.smooth)
                logger.debug(
                    "FollowNPCAction: Camera now following '%s' (smooth=%s)",
                    self.npc_name,
                    self.smooth,
                )
            else:
                logger.warning("FollowNPCAction: No camera manager available")
            self.executed = True

        return True  # Complete immediately

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create FollowNPCAction from a dictionary."""
        return cls(npc_name=data.get("npc", ""), smooth=data.get("smooth", True))


@ActionRegistry.register("stop_camera_follow")
class StopCameraFollowAction(Action):
    """Stop camera following, keeping it at current position.

    This action disables camera following behavior set by follow_player or
    follow_npc actions. The camera will remain at its current position and
    stop tracking any targets.

    This is useful for:
    - Freezing camera during dialog or cutscenes
    - Manual camera control via other means
    - Creating static camera shots

    The action completes immediately.

    Example usage:
        {
            "type": "stop_camera_follow"
        }

    Example - freeze camera during dialog:
        [
            {"type": "stop_camera_follow"},
            {"type": "dialog", "speaker": "narrator", "text": ["Time stands still..."]},
            {"type": "wait_for_dialog_close"},
            {"type": "follow_player"}
        ]
    """

    def __init__(self) -> None:
        """Initialize stop camera follow action."""
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Stop camera following."""
        if not self.executed:
            camera_manager = cast("CameraManager", context.get_system("camera"))
            if camera_manager:
                camera_manager.stop_follow()
                logger.debug("StopCameraFollowAction: Camera following stopped")
            else:
                logger.warning("StopCameraFollowAction: No camera manager available")
            self.executed = True

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:  # noqa: ARG003
        """Create StopCameraFollowAction from a dictionary."""
        return cls()
