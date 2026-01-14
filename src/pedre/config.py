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

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.menu_music_files is None:
            self.menu_music_files = []
