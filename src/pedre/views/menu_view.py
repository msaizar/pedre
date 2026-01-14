"""Main menu view for game navigation and asset preloading.

This module provides the MenuView class, which serves as the initial screen when
the game launches and when returning from gameplay. It displays navigation options
and handles background preloading of game assets for improved performance.

Key features:
- Main menu navigation (Continue, New Game, Save Game, Load Game, Exit)
- Background image display
- Parallel asset preloading using thread pool
- Disabled option state management (Continue and Save Game disabled based on game state)
- Keyboard navigation with arrow keys

Background asset preloading:
The menu intelligently preloads game assets (music and sound effects) in parallel
using a thread pool while the menu is displayed. This reduces loading times when
starting the game and improves the first-play experience.

Preloading strategy:
- Looping music files loaded in parallel (background.ogg, beach.ogg)
- Common sound effects loaded in parallel (avi.mp3, martin.mp3, etc.)
- Uses ThreadPoolExecutor with 4 workers for concurrent loading
- Runs in background daemon thread, won't block menu interaction
- Audio manager tracks loading state to prevent duplicate loads

User interface flow:
1. Game launches and shows menu with background image
2. Background thread starts preloading assets
3. Player navigates options with arrow keys
4. Player selects option with ENTER to start game, load game, or exit
5. Assets are ready when transitioning to game

Example usage:
    # Create menu view
    menu_view = MenuView(view_manager)

    # Show the view (typically called at game startup)
    view_manager.show_menu()
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import arcade

from pedre.constants import asset_path
from pedre.types import MenuOption

if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.view_manager import ViewManager

logger = logging.getLogger(__name__)


class MenuView(arcade.View):
    """Main menu view with navigation and background asset preloading.

    The MenuView serves as the game's main entry point and hub for navigation.
    It displays menu options with a background image and handles user selection
    for starting new games, loading saved games, or exiting.

    A key feature is background asset preloading - when the menu is shown, it
    spawns a background thread that preloads music and sound effects in parallel,
    ensuring assets are ready when the game starts.

    Menu options state:
    Each menu option has an enabled/disabled state. Disabled options are shown
    in gray and cannot be selected. Navigation automatically skips disabled options.

    Attributes:
        view_manager: ViewManager instance for handling view transitions.
        selected_option: Currently selected menu option (MenuOption enum).
        menu_text: Dictionary mapping MenuOption to display text (Spanish).
        menu_enabled: Dictionary mapping MenuOption to enabled state (bool).
        background_texture: Loaded background image texture, or None if not loaded.
    """

    def __init__(self, view_manager: ViewManager) -> None:
        """Initialize the menu view.

        Creates the view with menu options configuration and prepares for
        background image and asset loading.

        Args:
            view_manager: ViewManager for handling transitions to game or load view.
        """
        super().__init__()
        self.view_manager = view_manager
        self.selected_option = MenuOption.CONTINUE

        # Menu option enabled state (Continue and Save Game will be updated based on game view existence)
        self.menu_enabled = {
            MenuOption.CONTINUE: False,  # Updated in on_show_view
            MenuOption.NEW_GAME: True,
            MenuOption.SAVE_GAME: False,  # Updated in on_show_view
            MenuOption.LOAD_GAME: True,
            MenuOption.EXIT: True,
        }

        # Load background image
        self.background_texture = None

        # Text objects (created on first draw)
        self.title_text: arcade.Text | None = None
        self.menu_text_objects: dict[MenuOption, arcade.Text] = {}

    def on_show_view(self) -> None:
        """Called when this view becomes active (arcade lifecycle callback).

        Initializes the menu view by loading the background image (if not already
        loaded), checking if auto-save exists to enable/disable Continue option,
        and starting background asset preloading in a daemon thread.

        Background image loading:
        - Only loads once (cached for subsequent shows)
        - Logs warning if image file not found
        - Menu still functions without background

        Auto-save check:
        - Checks if auto-save file exists via save_manager
        - Enables Continue option if auto-save found
        - Disables Continue and selects New Game if no auto-save

        Background preloading:
        - Spawns daemon thread for asset loading
        - Thread uses ThreadPoolExecutor for parallel loading
        - Won't block menu interaction or game startup
        - Logs progress and errors during loading

        Side effects:
            - Sets background color to black
            - Loads background texture if not cached
            - Updates Continue option enabled state
            - Updates selected_option if Continue disabled
            - Starts background preloading thread (daemon)
            - Logs background image loading status
        """
        arcade.set_background_color(arcade.color.BLACK)

        # Load background image if not already loaded
        settings = self.window.settings
        if self.background_texture is None and settings.menu_background_image:
            background_path = asset_path(settings.menu_background_image, settings.assets_handle)
            try:
                self.background_texture = arcade.load_texture(background_path)
                logger.info("Loaded menu background: %s", background_path)
            except FileNotFoundError:
                logger.warning("Background image not found: %s", background_path)

        # Check if auto-save exists to enable/disable Continue and Save Game options
        self._update_menu_options()

        # Start preloading game assets in background
        self._start_background_preloading()

    def on_draw(self) -> None:
        """Render the menu (arcade lifecycle callback).

        Draws the main menu interface showing:
        - Background image (if loaded)
        - Game title in red at top
        - Menu options with state-based colors
        - Selection indicator (">" prefix)

        Menu option colors:
        - Selected: Purple with ">" prefix
        - Disabled: Gray
        - Enabled (not selected): Pink

        Side effects:
            - Clears the screen
            - Draws background texture if available
            - Draws text to window
        """
        self.clear()

        # Draw background image if loaded
        if self.background_texture:
            arcade.draw_texture_rect(
                self.background_texture,
                arcade.LBWH(0, 0, self.window.width, self.window.height),
            )

        # Create or update title text
        settings = self.window.settings
        if self.title_text is None:
            self.title_text = arcade.Text(
                settings.menu_title,
                self.window.width / 2,
                self.window.height * 0.75,
                arcade.color.RED,
                font_size=settings.menu_title_size,
                anchor_x="center",
            )
        else:
            self.title_text.x = self.window.width / 2
            self.title_text.y = self.window.height * 0.75

        # Draw title
        self.title_text.draw()

        # Draw menu options
        settings = self.window.settings
        menu_options = list(MenuOption)
        start_y = self.window.height * 0.5

        for i, option in enumerate(menu_options):
            y_position = start_y - (i * settings.menu_spacing)

            # Determine color based on state
            if option == self.selected_option:
                color = arcade.color.PURPLE
            elif not self.menu_enabled[option]:
                color = arcade.color.GRAY
            else:
                color = arcade.color.PINK

            # Add selection indicator
            prefix = "> " if option == self.selected_option else "  "
            text = prefix + self._get_menu_text(option, settings)

            # Create or update text object for this option
            if option not in self.menu_text_objects:
                text_obj = arcade.Text(
                    text,
                    self.window.width / 2,
                    y_position,
                    color,
                    font_size=settings.menu_option_size,
                    anchor_x="center",
                )
                self.menu_text_objects[option] = text_obj
            else:
                text_obj = self.menu_text_objects[option]
                text_obj.text = text
                text_obj.x = self.window.width / 2
                text_obj.y = y_position
                text_obj.color = color

            # Draw menu option text
            text_obj.draw()

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        """Handle keyboard input (arcade lifecycle callback).

        Processes keyboard input for menu navigation and selection:
        - UP: Move selection up (skips disabled options, wraps to bottom)
        - DOWN: Move selection down (skips disabled options, wraps to top)
        - ENTER: Execute selected option (if enabled)

        Args:
            symbol: Arcade key constant (e.g., arcade.key.ENTER).
            modifiers: Bitfield of modifier keys held (unused).

        Returns:
            None to allow other handlers to process the key.

        Side effects:
            - May change selected_option
            - May trigger view transitions (game, load game view)
            - May exit the game
        """
        if symbol == arcade.key.UP:
            self._move_selection(-1)
        elif symbol == arcade.key.DOWN:
            self._move_selection(1)
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._execute_selection()
        return None

    def _move_selection(self, direction: int) -> None:
        """Move selection up or down, skipping disabled options (internal implementation).

        Updates the selected option by cycling through available MenuOption values,
        automatically skipping any disabled options. Wraps around when reaching the
        end of the list.

        The method will try up to len(options) times to find an enabled option. If
        all options are disabled (edge case), the selection won't change.

        Args:
            direction: Direction to move selection. -1 for up, 1 for down.

        Side effects:
            - Updates self.selected_option to next enabled option
        """
        options = list(MenuOption)
        current_index = options.index(self.selected_option)

        # Find next enabled option
        attempts = 0
        while attempts < len(options):
            current_index = (current_index + direction) % len(options)
            next_option = options[current_index]
            if self.menu_enabled[next_option]:
                self.selected_option = next_option
                break
            attempts += 1

    def _execute_selection(self) -> None:
        """Execute the action for the currently selected menu option (internal implementation).

        Handles the ENTER key action based on selected option:
        - CONTINUE: Load auto-save and resume game
        - NEW_GAME: Start new game (transitions to game view)
        - SAVE_GAME: Show save game menu (transitions to save game view)
        - LOAD_GAME: Show load game menu (transitions to load game view)
        - EXIT: Exit the game application

        Does nothing if the selected option is disabled.

        Side effects:
            - May call view_manager.continue_game() to load auto-save
            - May call view_manager.show_game() for new game
            - May call view_manager.show_save_game() for save game
            - May call view_manager.show_load_game() for load game
            - May call view_manager.exit_game() to quit application
        """
        if not self.menu_enabled[self.selected_option]:
            return

        if self.selected_option == MenuOption.CONTINUE:
            self.view_manager.continue_game()
        elif self.selected_option == MenuOption.NEW_GAME:
            self.view_manager.show_game()
        elif self.selected_option == MenuOption.SAVE_GAME:
            self.view_manager.show_save_game()
        elif self.selected_option == MenuOption.LOAD_GAME:
            self.view_manager.show_load_game()
        elif self.selected_option == MenuOption.EXIT:
            self.view_manager.exit_game()

    def _update_menu_options(self) -> None:
        """Update Continue and Save Game options based on game view or auto-save existence (internal implementation).

        Enables menu options based on game state:
        - Continue: Enabled if game view exists (paused) OR auto-save exists (fresh launch)
        - Save Game: Enabled only if game view exists (can only save when paused from game)

        If a currently selected option becomes disabled, automatically selects the
        next enabled option (typically New Game) to prevent confusion.

        Side effects:
            - Updates self.menu_enabled[MenuOption.CONTINUE]
            - Updates self.menu_enabled[MenuOption.SAVE_GAME]
            - May update self.selected_option if currently selected option disabled
            - Logs menu option detection status
        """
        # Check if game view exists (paused game - quick resume)
        has_game_view = self.view_manager.has_game_view()

        # Check if auto-save exists (fresh launch - load from save)
        has_autosave = False
        if has_game_view:
            # If game view exists, check for auto-save through it
            game_view = self.view_manager.game_view
            if hasattr(game_view, "save_manager"):
                has_autosave = game_view.save_manager.save_exists(slot=0)

        # Enable Continue if either condition is met
        can_continue = has_game_view or has_autosave
        self.menu_enabled[MenuOption.CONTINUE] = can_continue

        # Enable Save Game only if game view exists (can only save when paused)
        can_save = has_game_view
        self.menu_enabled[MenuOption.SAVE_GAME] = can_save

        if can_continue:
            if has_game_view:
                logger.debug("Game view exists, Continue option enabled (quick resume)")
            else:
                logger.debug("Auto-save found, Continue option enabled (load from save)")
        else:
            logger.debug("No game view or auto-save found, Continue option disabled")

        if can_save:
            logger.debug("Game view exists, Save Game option enabled")
        else:
            logger.debug("No game view, Save Game option disabled")

        # If currently selected option is now disabled, move to next enabled option
        if not self.menu_enabled.get(self.selected_option, False):
            self.selected_option = MenuOption.NEW_GAME

    def _get_menu_text(self, option: MenuOption, settings: GameSettings) -> str:
        """Get the display text for a menu option from settings."""
        menu_text_map: dict[MenuOption, str] = {
            MenuOption.CONTINUE: settings.menu_text_continue,
            MenuOption.NEW_GAME: settings.menu_text_new_game,
            MenuOption.SAVE_GAME: settings.menu_text_save_game,
            MenuOption.LOAD_GAME: settings.menu_text_load_game,
            MenuOption.EXIT: settings.menu_text_exit,
        }
        return menu_text_map.get(option, option.name)

    def _start_background_preloading(self) -> None:
        """Start preloading game assets in parallel using thread pool (internal implementation).

        Spawns a background daemon thread that coordinates parallel loading of music
        and sound effect files using a ThreadPoolExecutor. The preloading runs
        concurrently with menu display and won't block user interaction.

        The worker thread submits individual load tasks to a thread pool with 4 workers,
        allowing multiple audio files to be loaded simultaneously for faster startup.

        Side effects:
            - Spawns daemon thread for background loading
            - Thread will terminate when main program exits
            - Logs preloading start, progress, and completion
        """

        def preload_worker() -> None:
            """Background worker to coordinate parallel asset loading (internal function).

            Coordinates the loading of music and sound effect files by submitting
            load tasks to a thread pool executor. Handles errors gracefully and
            logs all operations.

            The worker accesses the game view's audio manager to cache loaded sounds.
            Files are only loaded if not already in cache, preventing duplicate loads.

            Side effects:
                - Loads audio files into audio_manager.music_cache
                - Loads audio files into audio_manager.sfx_cache
                - Marks files as loading during load operation
                - Logs loading progress and errors
            """
            try:
                # Get game view's audio manager
                game_view = self.view_manager.game_view
                if not game_view or not hasattr(game_view, "audio_manager"):
                    return

                audio_manager = game_view.audio_manager

                def load_music_file(music_file: str) -> None:
                    """Load a single music file (internal worker function).

                    Loads a music file if not already cached, using arcade.load_sound
                    with streaming=False for better performance with looping music.

                    The loading state is tracked to prevent concurrent loads of the
                    same file.

                    Args:
                        music_file: Filename of music file (e.g., "background.ogg").

                    Side effects:
                        - Marks file as loading in audio_manager
                        - Loads sound from disk using arcade.load_sound
                        - Caches loaded sound in audio_manager.music_cache
                        - Removes loading marker when complete
                        - Logs loading status
                    """
                    if music_file not in audio_manager.music_cache:
                        logger.debug("Starting to load music: %s", music_file)
                        # Mark as loading
                        audio_manager.mark_music_loading(music_file)
                        try:
                            # Load music file using asset_path
                            settings = self.window.settings
                            music_path = asset_path(f"audio/music/{music_file}", settings.assets_handle)
                            sound = arcade.load_sound(music_path, streaming=False)
                            audio_manager.music_cache[music_file] = sound
                            logger.info("Preloaded music in background: %s", music_file)
                        finally:
                            # Remove from loading set
                            audio_manager.unmark_music_loading(music_file)

                # Load all music files in parallel using thread pool
                # Only preload looping music (streaming music like turntable.mp3 loads instantly)
                settings = self.window.settings
                music_files = settings.menu_music_files

                with ThreadPoolExecutor(max_workers=4) as executor:
                    # Submit all music files for parallel loading
                    music_futures = [executor.submit(load_music_file, f) for f in music_files]
                    # Submit all SFX files for parallel loading

                    # Wait for all to complete
                    for future in music_futures:
                        future.result()  # Will raise exception if any occurred

                logger.info("Background asset preloading complete")

            except Exception:
                logger.exception("Error during background preloading")

        # Start background coordinator thread
        preload_thread = threading.Thread(target=preload_worker, daemon=True)
        preload_thread.start()
        logger.debug("Started background asset preloading")
