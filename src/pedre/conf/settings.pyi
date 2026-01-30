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

# Input settings
PLAYER_MOVEMENT_SPEED: float

# Player settings
TILE_SIZE: int
INTERACTION_MANAGER_DISTANCE: int
NPC_INTERACTION_DISTANCE: int
PORTAL_INTERACTION_DISTANCE: int
WAYPOINT_THRESHOLD: int

# NPC settings
NPC_SPEED: float
NPC_WAYPOINT_THRESHOLD: int
NPC_INTERACTION_KEY: str

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
INVENTORY_MAX_SPACE: int
INVENTORY_CAPACITY_FONT_SIZE: int
INVENTORY_ITEMS_FILE: str
INVENTORY_KEY_VIEW: str
INVENTORY_KEY_CONSUME: str
INVENTORY_HINT_VIEW: str
INVENTORY_HINT_CONSUME: str
INVENTORY_HINT_FONT_SIZE: int

# Dialog settings
DIALOG_AUTO_CLOSE_DEFAULT: bool
DIALOG_AUTO_CLOSE_DURATION: float
DIALOG_SHOW_HELP: bool
DIALOG_SHOW_PAGINATION: bool
DIALOG_TEXT_NEXT_PAGE: str
DIALOG_TEXT_CLOSE: str
DIALOG_TEXT_PAGE: str
DIALOG_CHAR_REVEAL_SPEED: int
DIALOG_INSTANT_TEXT_DEFAULT: bool
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

# Audio settings
AUDIO_MUSIC_VOLUME: float
AUDIO_MUSIC_ENABLED: bool
AUDIO_SFX_VOLUME: float
AUDIO_SFX_ENABLED: bool

# Camera settings
CAMERA_LERP_SPEED: float

# Installed systems
INSTALLED_SYSTEMS: list[str]

# Installed actions, events, and conditions
INSTALLED_ACTIONS: list[str]
INSTALLED_EVENTS: list[str]
INSTALLED_CONDITIONS: list[str]

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
