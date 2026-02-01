"""Camera plugin for smooth camera following and viewport control.

This package provides:
- CameraManager: Core camera management plugin with smooth following

Actions (registered via INSTALLED_ACTIONS):
- FollowNPCAction, FollowPlayerAction, StopCameraFollowAction

The camera plugin handles smooth camera following with lerp interpolation,
boundary constraints to prevent showing areas outside the map, and instant
teleportation for scene transitions.
"""

from pedre.plugins.camera.manager import CameraManager

__all__ = [
    "CameraManager",
]
