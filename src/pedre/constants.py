"""Game constants and utility functions.

This module provides utility functions for working with game assets.
Settings are now accessed via the global settings object.
"""

import arcade

from pedre.conf import settings

# Animation property names for Tiled integration
# These properties are extracted from Tiled objects when creating animated sprites

# Base animation properties (used by Player and NPC)
BASE_ANIMATION_PROPERTIES = [
    "idle_up_frames",
    "idle_up_row",
    "idle_down_frames",
    "idle_down_row",
    "idle_left_frames",
    "idle_left_row",
    "idle_right_frames",
    "idle_right_row",
    "walk_up_frames",
    "walk_up_row",
    "walk_down_frames",
    "walk_down_row",
    "walk_left_frames",
    "walk_left_row",
    "walk_right_frames",
    "walk_right_row",
]

# NPC-specific special animation properties
NPC_SPECIAL_ANIMATION_PROPERTIES = [
    "appear_frames",
    "appear_row",
    "disappear_frames",
    "disappear_row",
    "interact_up_frames",
    "interact_up_row",
    "interact_down_frames",
    "interact_down_row",
    "interact_left_frames",
    "interact_left_row",
    "interact_right_frames",
    "interact_right_row",
]

# All animation properties for NPCs (base + special)
ALL_ANIMATION_PROPERTIES = BASE_ANIMATION_PROPERTIES + NPC_SPECIAL_ANIMATION_PROPERTIES


def asset_path(relative_path: str, assets_handle: str | None = None) -> str:
    """Get the resolved absolute path for an asset file.

    This uses Arcade's resource handle system which works correctly in both
    development and PyInstaller bundled environments.

    Args:
        relative_path: Path relative to assets directory (e.g., "maps/Casa.tmx", "dialogs/config.json")
                       Must be a path to an actual file, not a directory.
        assets_handle: Name of the resource handle. If None, uses settings.ASSETS_HANDLE.

    Returns:
        Absolute file path as string.

    Example:
        >>> asset_path("maps/Casa.tmx")
        "/absolute/path/to/assets/maps/Casa.tmx"
    """
    if assets_handle is None:
        assets_handle = settings.ASSETS_HANDLE

    # Remove leading slash if present
    relative_path = relative_path.lstrip("/")
    handle_path = f":{assets_handle}:/{relative_path}"
    return str(arcade.resources.resolve(handle_path))
