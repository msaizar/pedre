"""Game coordinator for managing game lifecycle and plugin initialization.

This module provides the Game class, which serves as the central coordinator
for the game's lifecycle. It handles plugin initialization, game context management,
and core game operations like starting new games, loading saves, and managing the
GameView lifecycle.

Key responsibilities:
- Owns long-lived objects: EventBus, GameContext, PluginLoader
- Initializes plugins in correct order: Actions → Events → Conditions → Plugins
- Manages GameView lifecycle: new game, continue, load, exit
- Coordinates save/load operations

Architecture notes:
- Only ONE view exists: GameView (the "pause menu" is a plugin overlay, not a view)
- No view transitions - this coordinates game state, not multiple screens
- Plugins access via context.window.game (or preferably via context facade methods)

Example usage:
    # Create game coordinator with game window
    game = Game(window)

    # Start game directly (autoload or new game)
    game.start_game_or_load()

    # Or start a fresh new game
    game.start_new_game()
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import arcade

from pedre.actions.loader import ActionLoader
from pedre.conditions.loader import ConditionLoader
from pedre.conf import settings
from pedre.content.loader import ContentLoader
from pedre.content.registry import ContentRegistry
from pedre.events import EventBus
from pedre.events.loader import EventLoader
from pedre.helpers import asset_path
from pedre.plugins.game_context import GameContext
from pedre.plugins.loader import PluginLoader
from pedre.views.game_view import GameView

if TYPE_CHECKING:
    from pedre.plugins.save.base import GameSaveData

logger = logging.getLogger(__name__)


class Game:
    """Coordinates game lifecycle, plugin initialization, and game state management.

    The Game class acts as the central coordinator for the game, handling plugin
    initialization, the GameView lifecycle, and core game operations. It owns
    long-lived objects like EventBus, GameContext, and PluginLoader that persist
    throughout the game's lifetime.

    Responsibilities:
    - Initialize plugins in the correct order (Actions → Events → Conditions → Plugins)
    - Manage GameView lifecycle (creation, cleanup, recreation for new games)
    - Coordinate save/load operations
    - Provide access to game context and plugin loader

    Attributes:
        window: The arcade Window instance for displaying the game.
        event_bus: Central event bus for publish/subscribe communication.
        game_context: Game context providing access to all plugins.
        plugin_loader: Plugin loader for managing plugin lifecycle.
        _game_view: Cached GameView instance, or None if not yet created.
    """

    def __init__(self, window: arcade.Window) -> None:
        """Initialize the game coordinator.

        Creates the game coordinator with a reference to the game window, along with
        the centralized event bus and game context that outlive the GameView.
        Initializes all plugins in the correct order.

        Args:
            window: Arcade Window instance for showing the game.
        """
        self.window = window

        # Create event bus (outlives individual views)
        self.event_bus = EventBus()

        # Load content registry (sprite/NPC definitions from JSON)
        content_registry = self._load_content_registry()

        # Create game context (outlives individual views)
        self.game_context = GameContext(
            event_bus=self.event_bus,
            window=self.window,
            content_registry=content_registry,
        )

        # Load actions, events, and conditions BEFORE plugins (plugins may depend on them)
        action_loader = ActionLoader()
        action_loader.load_modules()
        logger.debug("Loaded action modules from settings.INSTALLED_ACTIONS")

        event_loader = EventLoader()
        event_loader.load_modules()
        logger.debug("Loaded event modules from settings.INSTALLED_EVENTS")

        condition_loader = ConditionLoader()
        condition_loader.load_modules()
        logger.debug("Loaded condition modules from settings.INSTALLED_CONDITIONS")

        # Load and instantiate plugins
        self.plugin_loader = PluginLoader()
        plugin_instances = self.plugin_loader.instantiate_all()

        # Register all plugins with the context
        for name, plugin in plugin_instances.items():
            self.game_context.register_plugin(name, plugin)

        # Setup all plugins
        self.plugin_loader.setup_all(self.game_context)

        # Lazy-loaded views
        self._game_view: GameView | None = None

    def _load_content_registry(self) -> ContentRegistry:
        """Load content registry from the configured content directory.

        Loads content type modules from settings.INSTALLED_CONTENT, then reads
        JSON files from CONTENT_DIRECTORY (relative to the assets directory) if
        they exist, and validates cross-references.

        Returns:
            Populated ContentRegistry (may be empty if directory/files are absent).
        """
        content_loader = ContentLoader()
        content_loader.load_modules()
        logger.debug("Loaded content modules from settings.INSTALLED_CONTENT")

        registry = ContentRegistry()
        try:
            content_dir = Path(asset_path(settings.CONTENT_DIRECTORY))
        except OSError, ValueError, TypeError:
            logger.debug("Content directory '%s' could not be resolved", settings.CONTENT_DIRECTORY)
            return registry

        if not content_dir.exists():
            logger.debug("Content directory not found: %s", content_dir)
            return registry

        registry.load_from_directory(content_dir)
        registry.validate_cross_references()
        logger.debug("Loaded content registry from %s", content_dir)
        return registry

    @property
    def game_view(self) -> GameView:
        """Get or create the game view (lazy initialization).

        Returns the cached GameView instance, or creates a new one if this is the
        first access. The game view is the primary gameplay screen with player
        control, NPCs, dialogs, and scripted events.

        Returns:
            GameView instance (cached or newly created).

        Side effects:
            - May create and cache GameView instance on first access
        """
        if self._game_view is None:
            self._game_view = GameView(self)
        return self._game_view

    def has_game_view(self) -> bool:
        """Check if a game view exists without creating one.

        Returns:
            True if game view has been created, False otherwise.
        """
        return self._game_view is not None

    def show_game(self) -> None:
        """Show the game view.

        Displays the gameplay view in the window.

        Side effects:
            - Shows game view via window.show_view()
            - Triggers game view's on_show_view() callback
        """
        self.window.show_view(self.game_view)

    def start_new_game(self) -> None:
        """Start a new game with fresh state.

        Cleans up and discards any existing game view to ensure a fresh start.
        This is different from show_game() which reuses the cached game view,
        preserving state when returning from inventory or resuming from pause.

        Side effects:
            - Calls cleanup() on existing game view if it exists
            - Sets _game_view to None to force recreation
            - Shows fresh game view via show_game()
        """
        # Clean up and discard old game view if it exists
        if self._game_view is not None:
            self._game_view.cleanup()
            self._game_view = None

        # Show fresh game view (will create new instance via property)
        self.show_game()

    def start_game_or_load(self) -> None:
        """Start game directly, loading autosave if exists, otherwise new game.

        This provides a streamlined startup experience that bypasses the main menu:
        - If autosave (slot 0) exists: Load it automatically
        - Otherwise: Start a fresh new game

        Side effects:
            - May load autosave via load_game()
            - Or start new game via start_new_game()
        """
        save_plugin = self.game_context.save_plugin

        # Check if autosave exists
        if save_plugin and save_plugin.save_exists(slot=0):
            save_data = save_plugin.load_auto_save()
            if save_data:
                logger.info("Autoloading game from autosave")
                self.load_game(save_data)
                return

        # No autosave, start new game
        logger.info("No autosave found, starting new game")
        self.start_new_game()

    def continue_game(self) -> None:
        """Continue/resume the game.

        If a game view already exists (player paused with ESC), simply resume it
        without any reload. Otherwise, load the auto-save file and restore state.

        This provides two behaviors:
        - Quick resume: If game view exists, just show it (pause/unpause)
        - Load auto-save: If no game view, load from auto-save file

        The menu should disable the Continue option if neither condition is met
        (no game view and no auto-save file).

        Side effects:
            - Shows existing game view if available (instant resume)
            - OR loads auto-save and creates new game view (full load)
            - Logs resume/load status
        """
        # Quick resume: if game view exists, just show it (no reload needed)
        if self._game_view is not None:
            logger.info("Resuming game from pause")
            self.window.show_view(self.game_view)
            return

        # Full load: no game view exists, load from auto-save
        save_plugin = self.game_context.save_plugin
        if not save_plugin:
            logger.error("Save plugin not available")
            return

        save_data = save_plugin.load_auto_save()

        if not save_data:
            logger.warning("Cannot continue: no game view or auto-save found")
            return

        # Use the unified load_game method
        self.load_game(save_data)
        logger.info("Loaded game from auto-save")

    def load_game(self, save_data: GameSaveData) -> None:
        """Load a game from save data.

        Creates a fresh game view with the saved map and restores the complete
        game state from the save data. This includes player position, NPC dialog
        levels, NPC positions, inventory contents, audio settings, and interacted
        objects.

        The old game view is cleaned up and discarded to ensure a clean state.
        A new game view is created with the saved map, then the game state is
        restored after the view is shown using the centralized restore_all_state()
        method.

        Load process:
        1. Clean up and discard old game view if it exists
        2. Create new game view with saved map file
        3. Show the new game view (triggers setup)
        4. Restore player position
        5. Restore all plugin states (NPCs, inventory, audio, interacted objects)

        Args:
            save_data: GameSaveData instance containing all saved game state.

        Side effects:
            - Calls cleanup() on old game view if it exists
            - Creates new game view with saved map
            - Shows game view via window.show_view()
            - Restores player sprite position
            - Restores all plugin states via save_plugin.restore_all_state()
        """
        # Clean up old game view if it exists
        if self._game_view is not None:
            self._game_view.cleanup()
            self._game_view = None

        # Restore all plugin states using the centralized method
        context = self.game_context
        if not context:
            logger.error("Game: No GameContext after showing GameView")
            return

        if not context.save_plugin:
            logger.error("Game: Save plugin not found in context")
            return

        # Restore all state from save data
        context.save_plugin.restore_game_data(save_data)

        self._game_view = GameView(self)

        # Show the game view
        self.window.show_view(self.game_view)

    def exit_game(self) -> None:
        """Close the game window and exit the application.

        Performs auto-save and cleanup of all views before closing the window.
        This ensures game state is saved before exit.

        Side effects:
            - Auto-saves game to slot 0 if game view exists
            - Calls cleanup() on game view if it exists
            - Closes arcade window (exits application)
        """
        # Auto-save before exiting if game is active
        if self._game_view is not None:
            save_plugin = self.game_context.save_plugin
            success = save_plugin.auto_save()
            if success:
                logger.info("Auto-saved game before exit")
            else:
                logger.warning("Auto-save failed before exit")

            # Clean up all views after saving
            self._game_view.cleanup()

        arcade.close_window()
