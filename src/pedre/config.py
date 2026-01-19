"""Game settings and configuration for Pedre framework."""

from dataclasses import dataclass


@dataclass
class GameSettings:
    """Game configuration settings with sensible defaults.

    This is the core configuration object for Pedre games. Users can create
    instances directly with custom values.

    Example:
        >>> # Create settings directly
        >>> settings = GameSettings(
        ...     window_title="My RPG",
        ...     screen_width=1920,
        ...     screen_height=1080
        ... )
    """

    # Window settings
    screen_width: int = 1280
    screen_height: int = 720
    window_title: str = "Pedre Game"

    # Menu settings
    menu_title: str = "Pedre Game"
    menu_title_size: int = 48
    menu_option_size: int = 24
    menu_spacing: int = 50
    menu_background_image: str = ""
    menu_music_files: list[str] | None = None
    menu_text_continue: str = "Continue"
    menu_text_new_game: str = "New Game"
    menu_text_save_game: str = "Save Game"
    menu_text_load_game: str = "Load Game"
    menu_text_exit: str = "Exit"

    # Player settings
    player_movement_speed: int = 3
    tile_size: int = 32
    interaction_manager_distance: int = 50
    npc_interaction_distance: int = 50
    portal_interaction_distance: int = 50
    waypoint_threshold: int = 2

    # NPC settings
    npc_speed: float = 80.0

    # Asset settings
    assets_handle: str = "game_assets"

    # Game settings
    initial_map: str = "map.tmx"

    # Inventory settings
    inventory_grid_cols: int = 4
    inventory_grid_rows: int = 3
    inventory_box_size: int = 100
    inventory_box_spacing: int = 15
    inventory_box_border_width: int = 3
    inventory_background_image: str = ""

    # Pluggable systems configuration (like Django's INSTALLED_APPS)
    # List of module paths to import, which will register their systems
    # Users can add custom systems by appending to this list
    installed_systems: list[str] | None = None

    # Pluggable cache providers configuration
    # List of module paths to import, which will register their cache providers
    # Users can add custom caches by appending to this list
    installed_caches: list[str] | None = None

    # Pluggable save providers configuration
    # Uses same interface as cache providers but for save file persistence
    # Users can add custom save providers by appending to this list
    installed_saves: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.menu_music_files is None:
            self.menu_music_files = []

        if self.installed_systems is None:
            # Default installed systems - includes all built-in systems
            self.installed_systems = [
                "pedre.systems.audio",
                "pedre.systems.camera",
                "pedre.systems.debug",
                "pedre.systems.dialog",
                "pedre.systems.input",
                "pedre.systems.interaction",
                "pedre.systems.inventory",
                "pedre.systems.npc",
                "pedre.systems.particle",
                "pedre.systems.pathfinding",
                "pedre.systems.portal",
                "pedre.systems.save",
                "pedre.systems.script",
                "pedre.systems.player",
                "pedre.systems.physics",
                "pedre.systems.map",
                "pedre.systems.scene",
            ]

        if self.installed_caches is None:
            # Default installed caches - includes all built-in cache providers
            self.installed_caches = [
                "pedre.systems.npc.cache",
                "pedre.systems.script.cache",
                "pedre.systems.interaction.cache",
            ]

        if self.installed_saves is None:
            # Default installed saves - includes all built-in save providers
            self.installed_saves = [
                "pedre.systems.npc.save",
                "pedre.systems.script.save",
                "pedre.systems.interaction.save",
                "pedre.systems.audio.save",
                "pedre.systems.inventory.save",
            ]
