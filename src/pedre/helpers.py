"""Helper functions for creating and running Pedre games.

This module provides high-level functions to simplify game creation and setup.
Users can choose between the simple run_game() function or create_game() for
more control over the game initialization.
"""

import logging
import sys
from pathlib import Path

import arcade
from platformdirs import user_data_dir
from rich.logging import RichHandler

from pedre.conf import settings
from pedre.game import Game


def setup_logging(log_level: str = "DEBUG") -> None:
    """Configure logging for the game.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Side effects:
        - Configures the root logger with RichHandler
        - Sets the specified log level
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )


def get_app_data_dir(subdir: str = "") -> Path:
    """Get application data directory for storing user data.

    When running from PyInstaller bundle, uses platform-specific user data directory.
    When running normally, uses current working directory.

    Args:
        subdir: Optional subdirectory within the app data directory.

    Returns:
        Path to the application data directory (or subdirectory if specified).

    Example:
        >>> # Normal execution
        >>> get_app_data_dir("saves")
        PosixPath('/path/to/project/saves')

        >>> # PyInstaller bundle on macOS
        >>> get_app_data_dir("saves")
        PosixPath('/Users/username/Library/Application Support/MyGame/saves')
    """
    if getattr(sys, "frozen", False):
        # Running from PyInstaller bundle - use platform-specific user data dir
        # Sanitize WINDOW_TITLE for use as directory name
        app_name = settings.WINDOW_TITLE.replace(" ", "").replace("/", "-")
        base = Path(user_data_dir(app_name, appauthor=False))
        return base / subdir if subdir else base
    # Running normally - use current working directory
    return Path.cwd() / subdir if subdir else Path.cwd()


def setup_resources(assets_handle: str) -> None:
    """Configure Arcade resource handles for game assets.

    Registers a resource handle pointing to the assets directory in the current
    working directory (user's game project).

    Args:
        assets_handle: Name of the resource handle to register.

    Side effects:
        - Adds resource handle to arcade.resources
        - Handle points to the directory specified by settings.ASSETS_DIRECTORY
        - When running from PyInstaller bundle, uses the bundle's assets directory
    """
    # Check if running from PyInstaller bundle
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running from PyInstaller bundle - assets are in the bundle directory
        assets_dir = Path(sys._MEIPASS) / settings.ASSETS_DIRECTORY  # noqa: SLF001
    else:
        # Running normally - assets are relative to current working directory
        assets_dir = Path.cwd() / settings.ASSETS_DIRECTORY

    arcade.resources.add_resource_handle(assets_handle, assets_dir.resolve())


def create_game() -> arcade.Window:
    """Create and configure a Pedre game window.

    Creates an arcade.Window using the settings from your project's settings.py
    (or the module specified by PEDRE_SETTINGS_MODULE), sets up logging
    and resource handles, and attaches a Game coordinator to the window.

    This is the recommended way to initialize a Pedre game when you need
    access to the window instance for customization.

    Returns:
        Configured arcade.Window with game attribute attached.

    Side effects:
        - Configures logging via setup_logging()
        - Registers resource handles via setup_resources()
        - Creates arcade.Window instance
        - Attaches Game coordinator to window

    Example:
        >>> # Create settings.py in your project with settings
        >>> # WINDOW_TITLE = "My RPG"
        >>> from pedre import create_game
        >>> window = create_game()
        >>> window.game.start_game_or_load()
        >>> arcade.run()
    """
    setup_logging()
    setup_resources(settings.ASSETS_HANDLE)

    window = arcade.Window(
        settings.SCREEN_WIDTH,
        settings.SCREEN_HEIGHT,
        settings.WINDOW_TITLE,
    )
    window.game = Game(window)
    return window


def matches_key(symbol: int, key_name: str) -> bool:
    """Check if a pressed key matches a key setting string.

    This helper function converts a key name from settings (like "V" or "C")
    to an arcade key constant and checks if it matches the pressed key symbol.

    Args:
        symbol: The arcade key symbol that was pressed.
        key_name: The key name from settings (e.g., "V", "C", "SPACE").

    Returns:
        True if the key matches, False otherwise.

    Example:
        >>> from arcade import key
        >>> matches_key(key.V, "V")
        True
        >>> matches_key(key.C, "V")
        False
        >>> matches_key(key.SPACE, "SPACE")
        True
    """
    if not key_name:
        return False

    # Convert settings key name to arcade key constant
    key_upper = key_name.upper()

    # Try to get the key from arcade.key module
    expected_symbol = getattr(arcade.key, key_upper, None)
    if expected_symbol is not None:
        return expected_symbol == symbol

    return False


def calculate_responsive_value(
    dimension: int,
    percent: float,
    min_val: int,
    max_val: int,
) -> int:
    """Calculate responsive UI value using min/max/percent pattern.

    This helper is used throughout Pedre's UI plugins to scale spacing,
    padding, borders, and font sizes proportionally to screen dimensions
    while respecting minimum and maximum bounds.

    Args:
        dimension: Base dimension to calculate from (typically window.height or box_width)
        percent: Percentage of dimension as decimal (0.0-1.0)
        min_val: Minimum allowed value in pixels
        max_val: Maximum allowed value in pixels

    Returns:
        Calculated responsive value clamped to min/max range

    Example:
        >>> # Calculate title font size: 2.2% of 720px height = 16px
        >>> calculate_responsive_value(720, 0.022, 12, 32)
        16
        >>> # At 4K (2160px), it hits the maximum
        >>> calculate_responsive_value(2160, 0.022, 12, 32)
        32
    """
    return min(max_val, max(min_val, int(dimension * percent)))


def compute_ui_scale(
    window_width: int,
    window_height: int,
    ref_width: int | None = None,
    ref_height: int | None = None,
    min_scale: float = 0.5,
    max_scale: float = 2.0,
) -> float:
    """Compute a uniform UI scale factor relative to a reference resolution.

    Uses the smaller of the width and height ratios to ensure the UI always
    fits on screen. All UI elements can multiply their design-unit values
    (pixel dimensions at reference resolution) by this factor.

    Args:
        window_width: Current window width in pixels.
        window_height: Current window height in pixels.
        ref_width: Reference design width. Defaults to settings.SCREEN_WIDTH.
        ref_height: Reference design height. Defaults to settings.SCREEN_HEIGHT.
        min_scale: Minimum scale factor (prevents UI from becoming too small).
        max_scale: Maximum scale factor (prevents UI from becoming too large).

    Returns:
        Scale factor clamped to [min_scale, max_scale].

    Example:
        >>> compute_ui_scale(1920, 1080, 1280, 720)
        1.5
        >>> compute_ui_scale(640, 360, 1280, 720)
        0.5
        >>> compute_ui_scale(1280, 720, 1280, 720)
        1.0
    """
    if ref_width is None:
        ref_width = settings.SCREEN_WIDTH
    if ref_height is None:
        ref_height = settings.SCREEN_HEIGHT
    raw_scale = min(window_width / ref_width, window_height / ref_height)
    return max(min_scale, min(max_scale, raw_scale))


def scale_font(
    font_tier: tuple[int, int, int],
    ui_scale: float,
    min_scale: float = 0.5,
    max_scale: float = 2.0,
) -> int:
    """Interpolate a font size from a (small, reference, large) tier based on ui_scale.

    Linearly interpolates between the three anchor values:
      - ui_scale <= min_scale: returns small
      - ui_scale == 1.0: returns reference
      - ui_scale >= max_scale: returns large
      - in between: linear interpolation

    Args:
        font_tier: Tuple of (small_screen, reference, large_screen) font sizes.
        ui_scale: Current UI scale factor from compute_ui_scale().
        min_scale: The ui_scale value that maps to the small_screen font size.
        max_scale: The ui_scale value that maps to the large_screen font size.

    Returns:
        Interpolated font size as an integer, at least 1.

    Example:
        >>> scale_font((8, 12, 16), 1.0)
        12
        >>> scale_font((8, 12, 16), 0.5)
        8
        >>> scale_font((8, 12, 16), 2.0)
        16
        >>> scale_font((8, 12, 16), 0.75)
        10
    """
    small, ref, large = font_tier
    if ui_scale <= min_scale:
        return max(1, small)
    if ui_scale >= max_scale:
        return max(1, large)
    if ui_scale <= 1.0:
        t = (ui_scale - min_scale) / (1.0 - min_scale)
        return max(1, int(small + (ref - small) * t))
    t = (ui_scale - 1.0) / (max_scale - 1.0)
    return max(1, int(ref + (large - ref) * t))


def run_game() -> None:
    """Create and run a Pedre game.

    This is the simplest way to start a Pedre game. It creates the window
    using settings from your project's settings.py (or the module specified
    by PEDRE_SETTINGS_MODULE), sets up all resources, starts the game,
    and starts the game loop.

    Side effects:
        - Configures logging via setup_logging()
        - Registers resource handles via setup_resources()
        - Creates arcade.Window and Game coordinator
        - Starts the game (new game or loads autosave)
        - Starts arcade.run() game loop (blocks until window closes)

    Example:
        >>> # Create settings.py in your project:
        >>> # WINDOW_TITLE = "My RPG"
        >>> # SCREEN_WIDTH = 1920
        >>> # SCREEN_HEIGHT = 1080
        >>> from pedre import run_game
        >>> if __name__ == "__main__":
        ...     run_game()
    """
    window = create_game()
    window.game.start_game_or_load()
    arcade.run()


def scale(value: int, scale: float, floor: int = 1) -> int:
    """Scale a design-unit value by ui_scale with a minimum floor.

    Args:
        value: Design-unit value (pixels at reference resolution).
        scale: UI scale factor from compute_ui_scale().
        floor: Minimum result value. Defaults to 1.

    Returns:
        Scaled integer value, at least floor.
    """
    return max(floor, int(value * scale))
