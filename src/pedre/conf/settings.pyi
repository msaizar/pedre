"""Type hints for settings object.

This stub file provides type information for IDE autocomplete and type checking
of the settings object.
"""

from typing import Any

# Window settings
SCREEN_WIDTH: int
SCREEN_HEIGHT: int
WINDOW_TITLE: str

# Pause Menu settings
PAUSE_MENU_OVERLAY_ALPHA: int
PAUSE_MENU_TITLE: str
PAUSE_MENU_DESIGN: dict[str, int]
PAUSE_MENU_UI_SCALE_MIN: float
PAUSE_MENU_UI_SCALE_MAX: float
PAUSE_MENU_TEXT_RESUME: str
PAUSE_MENU_TEXT_NEW_GAME: str
PAUSE_MENU_TEXT_LOAD_GAME: str
PAUSE_MENU_TEXT_SAVE_GAME: str
PAUSE_MENU_TEXT_EXIT: str
PAUSE_MENU_TEXT_BACK: str
PAUSE_MENU_TEXT_EMPTY_SLOT: str
PAUSE_MENU_CONFIRM_NEW_GAME: str
PAUSE_MENU_COLOR_OVERLAY: tuple[int, int, int]
PAUSE_MENU_COLOR_BOX_BACKGROUND: tuple[int, int, int]
PAUSE_MENU_COLOR_BOX_BORDER: tuple[int, int, int]
PAUSE_MENU_COLOR_TITLE: tuple[int, int, int]
PAUSE_MENU_COLOR_OPTION: tuple[int, int, int]
PAUSE_MENU_COLOR_SELECTED: tuple[int, int, int]
PAUSE_MENU_COLOR_DISABLED: tuple[int, int, int]
PAUSE_MENU_COLOR_FEEDBACK: tuple[int, int, int]
PAUSE_MENU_OVERLAY_ALPHA: int

PLAYER_MOVEMENT_SPEED: float

# Player settings
TILE_SIZE: int
INTERACTION_PLUGIN_DISTANCE: int
INTERACTION_KEY: str
NPC_INTERACTION_DISTANCE: int
PORTAL_INTERACTION_DISTANCE: int
WAYPOINT_THRESHOLD: int

# NPC settings
NPC_MOVEMENT_SPEED: float
NPC_WAYPOINT_THRESHOLD: int
NPC_INTERACTION_KEY: str

# Asset settings
ASSETS_HANDLE: str
ASSETS_DIRECTORY: str

# Game settings
INITIAL_MAP: str

# Scene settings
SCENE_TRANSITION_ALPHA: float
SCENE_TRANSITION_SPEED: float
SCENE_MAPS_FOLDER: str
SCENE_TILEMAP_SCALING: float
SCENE_COLLISION_LAYER_NAMES: list[str]

# Inventory settings
INVENTORY_GRID_COLS: int
INVENTORY_GRID_ROWS: int
INVENTORY_DESIGN: dict[str, int | float]
INVENTORY_UI_SCALE_MIN: float
INVENTORY_UI_SCALE_MAX: float
INVENTORY_BACKGROUND_IMAGE: str
INVENTORY_MAX_SPACE: int
INVENTORY_ITEMS_FILE: str
INVENTORY_KEY_TOGGLE: str
INVENTORY_KEY_VIEW: str
INVENTORY_KEY_CONSUME: str
INVENTORY_HINT_VIEW: str
INVENTORY_HINT_CONSUME: str
INVENTORY_COLOR_OVERLAY: tuple[int, int, int]
INVENTORY_OVERLAY_ALPHA: int
INVENTORY_COLOR_BOX_FILLED: tuple[int, int, int]
INVENTORY_COLOR_BOX_EMPTY: tuple[int, int, int]
INVENTORY_COLOR_BOX_BORDER: tuple[int, int, int]
INVENTORY_COLOR_BOX_BORDER_SELECTED: tuple[int, int, int]
INVENTORY_COLOR_BOX_BORDER_EMPTY: tuple[int, int, int]
INVENTORY_COLOR_TEXT_ITEM_NAME: tuple[int, int, int]
INVENTORY_COLOR_TEXT_HINT: tuple[int, int, int]
INVENTORY_COLOR_TEXT_CAPACITY: tuple[int, int, int]
INVENTORY_COLOR_TEXT_PHOTO_TITLE: tuple[int, int, int]
INVENTORY_COLOR_TEXT_PHOTO_DESCRIPTION: tuple[int, int, int]
INVENTORY_COLOR_PHOTO_BACKGROUND: tuple[int, int, int]
INVENTORY_EMPTY_BOX_ALPHA: int

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
DIALOG_KEY_ADVANCE: str
DIALOG_DESIGN: dict[str, int | float]
DIALOG_UI_SCALE_MIN: float
DIALOG_UI_SCALE_MAX: float
DIALOG_OVERLAY_ALPHA: int
DIALOG_COLOR_BOX_BACKGROUND: tuple[int, int, int]
DIALOG_COLOR_BOX_BORDER: tuple[int, int, int]
DIALOG_COLOR_NPC_NAME: tuple[int, int, int]
DIALOG_COLOR_TEXT: tuple[int, int, int]
DIALOG_COLOR_INSTRUCTION: tuple[int, int, int]
DIALOG_COLOR_PAGE_INDICATOR: tuple[int, int, int]

# Audio settings
AUDIO_MUSIC_VOLUME: float
AUDIO_MUSIC_ENABLED: bool
AUDIO_SFX_VOLUME: float
AUDIO_SFX_ENABLED: bool

# UI Font Scale
UI_FONT_SMALL: tuple[int, int, int]
UI_FONT_NORMAL: tuple[int, int, int]
UI_FONT_LARGE: tuple[int, int, int]

# Camera settings
CAMERA_LERP_SPEED: float

# Particle settings
PARTICLE_ENABLED: bool
PARTICLE_COLOR_HEARTS: tuple[int, int, int]
PARTICLE_COLOR_SPARKLES: tuple[int, int, int]
PARTICLE_COLOR_TRAIL: tuple[int, int, int]
PARTICLE_COLOR_BURST: tuple[int, int, int]

# Save system settings
SAVE_FOLDER: str
SAVE_QUICK_SAVE_KEY: str
SAVE_QUICK_LOAD_KEY: str
SAVE_SFX_FILE: str

# Content registry settings
CONTENT_DIRECTORY: str

# Dialog settings
DIALOGS_DIRECTORY: str

# Script settings
SCRIPTS_DIRECTORY: str

# Installed systems
INSTALLED_PLUGINS: list[str]

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
