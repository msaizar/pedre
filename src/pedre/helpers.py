"""Helper functions for creating and running Pedre games.

This module provides high-level functions to simplify game creation and setup.
Users can choose between the simple run_game() function or create_game() for
more control over the game initialization.
"""

import logging
from pathlib import Path

import arcade
from rich.logging import RichHandler

from pedre.config import GameSettings
from pedre.view_manager import ViewManager


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


def setup_resources(assets_handle: str) -> None:
    """Configure Arcade resource handles for game assets.

    Registers a resource handle pointing to the assets directory in the current
    working directory (user's game project).

    Args:
        assets_handle: Name of the resource handle to register.

    Side effects:
        - Adds resource handle to arcade.resources
        - Handle points to the assets/ directory in the current working directory
    """
    assets_dir = Path.cwd() / "assets"
    arcade.resources.add_resource_handle(assets_handle, assets_dir.resolve())


def create_game(settings: GameSettings) -> arcade.Window:
    """Create and configure a Pedre game window.

    Creates an arcade.Window with the provided settings, sets up logging
    and resource handles, and attaches a ViewManager to the window.

    This is the recommended way to initialize a Pedre game when you need
    access to the window instance for customization.

    Args:
        settings: Game configuration settings.

    Returns:
        Configured arcade.Window with view_manager and settings attributes attached.

    Side effects:
        - Configures logging via setup_logging()
        - Registers resource handles via setup_resources()
        - Creates arcade.Window instance
        - Attaches ViewManager and settings to window

    Example:
        >>> settings = GameSettings(window_title="My RPG")
        >>> window = create_game(settings)
        >>> window.view_manager.show_menu()
        >>> arcade.run()
    """
    setup_logging()
    setup_resources(settings.assets_handle)

    window = arcade.Window(
        settings.screen_width,
        settings.screen_height,
        settings.window_title,
    )
    window.settings = settings
    window.view_manager = ViewManager(window)
    return window


def run_game(settings: GameSettings | None = None) -> None:
    """Create and run a Pedre game.

    This is the simplest way to start a Pedre game. It creates the window,
    sets up all resources, shows the main menu, and starts the game loop.

    Args:
        settings: Game configuration settings. If None, uses default GameSettings.

    Side effects:
        - Configures logging via setup_logging()
        - Registers resource handles via setup_resources()
        - Creates arcade.Window and ViewManager
        - Shows the menu view
        - Starts arcade.run() game loop (blocks until window closes)

    Example:
        >>> from pedre import GameSettings, run_game
        >>> settings = GameSettings(
        ...     window_title="My RPG",
        ...     screen_width=1920,
        ...     screen_height=1080,
        ... )
        >>> if __name__ == "__main__":
        ...     run_game(settings)
    """
    if settings is None:
        settings = GameSettings()
    window = create_game(settings)
    window.view_manager.show_menu()
    arcade.run()
