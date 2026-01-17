"""Camera system for smooth camera following and viewport control.

This package provides:
- CameraManager: Core camera management system with smooth following

The camera system handles smooth camera following with lerp interpolation,
boundary constraints to prevent showing areas outside the map, and instant
teleportation for scene transitions.
"""

from pedre.systems.camera.manager import CameraManager

__all__ = [
    "CameraManager",
]
