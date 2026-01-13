"""Game constants and utility functions.

This module provides utility functions for working with game assets.
Settings are now accessed via window.settings instead of global constants.
"""

import arcade


def asset_path(relative_path: str, assets_handle: str = "game_assets") -> str:
    """Get the resolved absolute path for an asset file.

    This uses Arcade's resource handle system which works correctly in both
    development and PyInstaller bundled environments.

    Args:
        relative_path: Path relative to assets directory (e.g., "maps/Casa.tmx", "dialogs/config.json")
                       Must be a path to an actual file, not a directory.
        assets_handle: Name of the resource handle (default: "game_assets").

    Returns:
        Absolute file path as string.

    Example:
        >>> asset_path("maps/Casa.tmx")
        "/absolute/path/to/assets/maps/Casa.tmx"
    """
    # Remove leading slash if present
    relative_path = relative_path.lstrip("/")
    handle_path = f":{assets_handle}:/{relative_path}"
    return str(arcade.resources.resolve(handle_path))
