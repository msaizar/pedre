"""Type hints for settings object.

This stub file provides type information for IDE autocomplete and type checking
of the settings object.
"""

from typing import Any

# Window settings
SCREEN_WIDTH: int
SCREEN_HEIGHT: int
WINDOW_TITLE: str

# Menu settings
MENU_TITLE: str
MENU_TITLE_SIZE: int
MENU_OPTION_SIZE: int
MENU_SPACING: int
MENU_BACKGROUND_IMAGE: str
MENU_MUSIC_FILES: list[str]
MENU_TEXT_CONTINUE: str
MENU_TEXT_NEW_GAME: str
MENU_TEXT_SAVE_GAME: str
MENU_TEXT_LOAD_GAME: str
MENU_TEXT_EXIT: str

# Player settings
PLAYER_MOVEMENT_SPEED: int
TILE_SIZE: int
INTERACTION_MANAGER_DISTANCE: int
NPC_INTERACTION_DISTANCE: int
PORTAL_INTERACTION_DISTANCE: int
WAYPOINT_THRESHOLD: int

# NPC settings
NPC_SPEED: float

# Asset settings
ASSETS_HANDLE: str

# Game settings
INITIAL_MAP: str

# Inventory settings
INVENTORY_GRID_COLS: int
INVENTORY_GRID_ROWS: int
INVENTORY_BOX_SIZE: int
INVENTORY_BOX_SPACING: int
INVENTORY_BOX_BORDER_WIDTH: int
INVENTORY_BACKGROUND_IMAGE: str

# Dialog settings
DIALOG_AUTO_CLOSE_DEFAULT: bool
DIALOG_AUTO_CLOSE_DURATION: float

# Installed systems
INSTALLED_SYSTEMS: list[str]

# Methods
def configure(**options: Any) -> None:  # noqa: ANN401
    """Manually configure settings (useful for testing).

    Example:
        settings.configure(
            SCREEN_WIDTH=800,
            SCREEN_HEIGHT=600,
            TILE_SIZE=64
        )
    """

def is_configured() -> bool:
    """Check if settings have been loaded.

    Returns:
        True if settings have been initialized, False otherwise.
    """
