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
DIALOG_BOX_WIDTH_PERCEN: float
DIALOG_BOX_MAX_WIDTH: int
DIALOG_BOX_MIN_WIDTH: int
DIALOG_BOX_HEIGHT_PERCENT: float
DIALOG_BOX_MIN_HEIGHT: int
DIALOG_VERTICAL_POSITION: float
DIALOG_OVERLAY_ALPHA: int
DIALOG_BORDER_WIDTH: int
DIALOG_PADDING_HORIZONTAL: int
DIALOG_PADDING_VERTICAL: int
DIALOG_NPC_NAME_OFFSET: int
DIALOG_FOOTER_OFFSET: int
DIALOG_NPC_NAME_FONT_SIZE: int
DIALOG_TEXT_FONT_SIZE: int
DIALOG_INSTRUCTION_FONT_SIZE: int
DIALOG_PAGE_INDICATOR_FONT_SIZE: int

# Installed systems
INSTALLED_SYSTEMS: list[str]

# Methods
def configure(**options: Any) -> None:  # noqa: ANN401
    """Manually configure settings (useful for testing).

    Example:
        settings.configure(
            SCREEN_WIDTH=800,
            SCREEN_HEIGHT=600
        )
    """

def is_configured() -> bool:
    """Check if settings have been loaded.

    Returns:
        True if settings have been initialized, False otherwise.
    """
