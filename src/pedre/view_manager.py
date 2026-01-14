"""View manager for coordinating view transitions and lifecycle.

This module provides the ViewManager class, which serves as the central controller
for all game views (screens). It handles view creation, caching, transitions, and
cleanup throughout the game's lifecycle.

Key features:
- Lazy view initialization (views created on first access)
- View caching for performance (reuse instances across transitions)
- Centralized view transition logic
- Cleanup coordination during transitions
- Save game loading and state restoration

View lifecycle management:
The ViewManager uses lazy loading to defer view creation until needed, reducing
startup time and memory usage. Views are cached after creation and reused when
the player navigates back to them.

View transition flow:
1. User triggers transition (e.g., selects "New Game" from menu)
2. ViewManager cleans up current view if needed (e.g., auto-save game state)
3. ViewManager gets or creates target view (cached or new instance)
4. ViewManager tells window to show the target view
5. Arcade calls target view's on_show_view() for initialization

Available views:
- MenuView: Main menu with asset preloading
- GameView: Primary gameplay view
- LoadGameView: Save slot selection menu for loading
- SaveGameView: Save slot selection menu for saving
- InventoryView: Inventory viewer

Example usage:
    # Create view manager with game window
    view_manager = ViewManager(window)

    # Start at main menu
    view_manager.show_menu()

    # User selects "New Game"
    view_manager.show_game()

    # User presses I for inventory
    view_manager.show_inventory()

    # User presses ESC to return
    view_manager.show_game()

    # User presses ESC to pause and selects "Save Game"
    view_manager.show_menu(from_game_pause=True)
    view_manager.show_save_game()
"""

import logging
from typing import TYPE_CHECKING

import arcade

from pedre.views.game_view import GameView
from pedre.views.inventory_view import InventoryView
from pedre.views.load_game_view import LoadGameView
from pedre.views.menu_view import MenuView
from pedre.views.save_game_view import SaveGameView

if TYPE_CHECKING:
    from pedre.systems import GameSaveData

logger = logging.getLogger(__name__)


class ViewManager:
    """Manages all game views and transitions between them.

    The ViewManager acts as the central coordinator for all game screens (views),
    handling their creation, caching, and transitions. It provides a clean API for
    switching between views and ensures proper cleanup during transitions.

    View caching strategy:
    Views are created lazily on first access and cached for reuse. This improves
    performance by avoiding redundant initialization and preserves view state
    across transitions (useful for game view state when showing inventory).

    The inventory view is special - it requires the game view's inventory_manager,
    so it's only created after the game view exists.

    Attributes:
        window: The arcade Window instance for displaying views.
        _menu_view: Cached MenuView instance, or None if not yet created.
        _game_view: Cached GameView instance, or None if not yet created.
        _load_game_view: Cached LoadGameView instance, or None if not yet created.
        _save_game_view: Cached SaveGameView instance, or None if not yet created.
        _inventory_view: Cached InventoryView instance, or None if not yet created.
    """

    def __init__(self, window: arcade.Window) -> None:
        """Initialize the view manager.

        Creates the view manager with a reference to the game window. All view
        instances start as None and are created lazily when first accessed.

        Args:
            window: Arcade Window instance for showing views.
        """
        self.window = window

        # Lazy-loaded views
        self._menu_view: MenuView | None = None
        self._game_view: GameView | None = None
        self._load_game_view: LoadGameView | None = None
        self._save_game_view: SaveGameView | None = None
        self._inventory_view: InventoryView | None = None

    @property
    def menu_view(self) -> MenuView:
        """Get or create the menu view (lazy initialization).

        Returns the cached MenuView instance, or creates a new one if this is the
        first access. The menu view handles main menu display, navigation, and
        background asset preloading.

        Returns:
            MenuView instance (cached or newly created).

        Side effects:
            - May create and cache MenuView instance on first access
        """
        if self._menu_view is None:
            self._menu_view = MenuView(self)
        return self._menu_view

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

        Used by the menu to determine if Continue should enable quick resume
        (game view exists) vs load from auto-save (no game view).

        Returns:
            True if game view has been created, False otherwise.
        """
        return self._game_view is not None

    @property
    def load_game_view(self) -> LoadGameView:
        """Get or create the load game view (lazy initialization).

        Returns the cached LoadGameView instance, or creates a new one if this is
        the first access. The load game view displays save slots and handles
        loading saved games.

        Returns:
            LoadGameView instance (cached or newly created).

        Side effects:
            - May create and cache LoadGameView instance on first access
        """
        if self._load_game_view is None:
            self._load_game_view = LoadGameView(self)
        return self._load_game_view

    @property
    def save_game_view(self) -> SaveGameView:
        """Get or create the save game view (lazy initialization).

        Returns the cached SaveGameView instance, or creates a new one if this is
        the first access. The save game view displays manual save slots and handles
        saving the current game state.

        Returns:
            SaveGameView instance (cached or newly created).

        Side effects:
            - May create and cache SaveGameView instance on first access
        """
        if self._save_game_view is None:
            self._save_game_view = SaveGameView(self)
        return self._save_game_view

    @property
    def inventory_view(self) -> InventoryView:
        """Get or create the inventory view (lazy initialization).

        Returns the cached InventoryView instance, or creates a new one if this is
        the first access. The inventory view requires the game view's inventory_manager,
        so it can only be created after the game view exists.

        Returns:
            InventoryView instance (cached or newly created), or None if game view
            doesn't exist yet.

        Side effects:
            - May create and cache InventoryView instance on first access
            - Returns None if game view hasn't been created yet
        """
        if self._inventory_view is None and self._game_view is not None:
            self._inventory_view = InventoryView(self, self._game_view.inventory_manager)
        return self._inventory_view  # type: ignore[return-value]

    def show_menu(self, *, from_game_pause: bool = False) -> None:
        """Switch to the menu view.

        Transitions to the main menu view. Optionally preserves the game view state
        when pausing from active gameplay (ESC key), allowing quick resume without
        reload. When not pausing, cleans up the game view and auto-saves.

        Args:
            from_game_pause: If True, preserve game view for quick resume (pause menu).
                           If False, cleanup game view and auto-save (quit to menu).

        Side effects:
            - Calls cleanup() on game view if not pausing
            - Shows menu view via window.show_view()
            - Triggers menu view's on_show_view() callback
        """
        # Only clean up game view if not pausing (e.g., from new game)
        if not from_game_pause and self._game_view is not None:
            self._game_view.cleanup()

        self.window.show_view(self.menu_view)

    def show_game(self, *, trigger_post_inventory_dialog: bool = False) -> None:
        """Switch to the game view.

        Transitions to the gameplay view, optionally triggering a post-inventory
        dialog event. The post-inventory dialog is used when returning from the
        inventory view to notify scripts that the player checked their inventory.

        Args:
            trigger_post_inventory_dialog: If True, calls trigger_post_inventory_dialog()
                on the game view after showing it. This publishes an InventoryClosedEvent
                for the script system.

        Side effects:
            - Shows game view via window.show_view()
            - Triggers game view's on_show_view() callback
            - May call game_view.trigger_post_inventory_dialog() to publish event
            - Logs transition details
        """
        logger.info("show_game called with trigger_post_inventory_dialog=%s", trigger_post_inventory_dialog)
        self.window.show_view(self.game_view)
        if trigger_post_inventory_dialog and hasattr(self.game_view, "trigger_post_inventory_dialog"):
            logger.info("Calling trigger_post_inventory_dialog on game_view")
            self.game_view.trigger_post_inventory_dialog()
        else:
            logger.info(
                "Not calling trigger (flag=%s, hasattr=%s)",
                trigger_post_inventory_dialog,
                hasattr(self.game_view, "trigger_post_inventory_dialog"),
            )

    def show_load_game(self) -> None:
        """Switch to the load game view.

        Transitions to the save slot selection menu where players can load
        previously saved games.

        Side effects:
            - Shows load game view via window.show_view()
            - Triggers load game view's on_show_view() callback
        """
        self.window.show_view(self.load_game_view)

    def show_save_game(self) -> None:
        """Switch to the save game view.

        Transitions to the save slot selection menu where players can save
        the current game to manual save slots (1-3).

        Side effects:
            - Shows save game view via window.show_view()
            - Triggers save game view's on_show_view() callback
        """
        self.window.show_view(self.save_game_view)

    def show_inventory(self) -> None:
        """Switch to the inventory view.

        Transitions to the inventory view for browsing collected photos. Only
        works if the game view exists (inventory requires inventory_manager).

        Side effects:
            - Shows inventory view via window.show_view() if it exists
            - Triggers inventory view's on_show_view() callback
            - Does nothing if inventory view doesn't exist yet
        """
        if self.inventory_view:
            self.window.show_view(self.inventory_view)

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
        save_data = self.game_view.save_manager.load_auto_save()

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
        5. Restore all manager states (NPCs, inventory, audio, interacted objects)

        Args:
            save_data: GameSaveData instance containing all saved game state.

        Side effects:
            - Calls cleanup() on old game view if it exists
            - Creates new game view with saved map
            - Shows game view via window.show_view()
            - Restores player sprite position
            - Restores all manager states via save_manager.restore_all_state()
        """
        # Clean up old game view if it exists
        if self._game_view is not None:
            self._game_view.cleanup()
            self._game_view = None

        # Create new game view with the saved map
        self._game_view = GameView(self, map_file=save_data.current_map)

        # Show the game view
        self.window.show_view(self.game_view)

        # Restore player position
        if self.game_view.player_sprite:
            self.game_view.player_sprite.center_x = save_data.player_x
            self.game_view.player_sprite.center_y = save_data.player_y

        # Restore all manager states using the centralized method
        restored_objects, scene_states = self.game_view.save_manager.restore_all_state(
            save_data,
            self.game_view.npc_manager,
            self.game_view.inventory_manager,
            self.game_view.audio_manager,
            self.game_view.script_manager,
        )

        # Update script manager's interacted_objects
        self.game_view.script_manager.interacted_objects = restored_objects

        # Restore scene state cache for NPC persistence across scene transitions
        if scene_states:
            GameView.restore_scene_state_cache(scene_states)

    def exit_game(self) -> None:
        """Close the game window and exit the application.

        Performs cleanup of all views (especially game view for auto-save) before
        closing the window. This ensures game state is saved before exit.

        Side effects:
            - Calls cleanup() on game view if it exists
            - Closes arcade window (exits application)
        """
        # Clean up all views before exiting
        if self._game_view is not None:
            self._game_view.cleanup()

        arcade.close_window()
