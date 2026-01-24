"""Helper functions for creating and running Pedre games.

This module provides high-level functions to simplify game creation and setup.
Users can choose between the simple run_game() function or create_game() for
more control over the game initialization.
"""

import logging
from pathlib import Path

import arcade
from rich.logging import RichHandler

from pedre.conf import settings
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


def create_game() -> arcade.Window:
    """Create and configure a Pedre game window.

    Creates an arcade.Window using the settings from your project's settings.py
    (or the module specified by PEDRE_SETTINGS_MODULE), sets up logging
    and resource handles, and attaches a ViewManager to the window.

    This is the recommended way to initialize a Pedre game when you need
    access to the window instance for customization.

    Returns:
        Configured arcade.Window with view_manager attribute attached.

    Side effects:
        - Configures logging via setup_logging()
        - Registers resource handles via setup_resources()
        - Creates arcade.Window instance
        - Attaches ViewManager to window

    Example:
        >>> # Create settings.py in your project with settings
        >>> # WINDOW_TITLE = "My RPG"
        >>> from pedre import create_game
        >>> window = create_game()
        >>> window.view_manager.show_menu()
        >>> arcade.run()
    """
    setup_logging()
    setup_resources(settings.ASSETS_HANDLE)

    window = arcade.Window(
        settings.SCREEN_WIDTH,
        settings.SCREEN_HEIGHT,
        settings.WINDOW_TITLE,
    )
    window.view_manager = ViewManager(window)
    return window


def run_game() -> None:
    """Create and run a Pedre game.

    This is the simplest way to start a Pedre game. It creates the window
    using settings from your project's settings.py (or the module specified
    by PEDRE_SETTINGS_MODULE), sets up all resources, shows the main menu,
    and starts the game loop.

    Side effects:
        - Configures logging via setup_logging()
        - Registers resource handles via setup_resources()
        - Creates arcade.Window and ViewManager
        - Shows the menu view
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
    window.view_manager.show_menu()
    arcade.run()
