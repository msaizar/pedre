"""Default settings for Pedre framework.

Users can override these in their project's settings.py file.

Example:
    # In your project's settings.py:
    from pedre.conf import global_settings

    # Override framework defaults
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080
    WINDOW_TITLE = "My RPG"

    # Add custom settings
    WEATHER_UPDATE_INTERVAL = 5.0
    ENEMY_SPAWN_RATE = 0.5
"""

# Window settings
SCREEN_WIDTH = 1280
"""Width of the game window in pixels."""

SCREEN_HEIGHT = 720
"""Height of the game window in pixels."""

WINDOW_TITLE = "Pedre Game"
"""Title displayed in the window title bar."""

# Menu settings
MENU_TITLE = "Pedre Game"
"""Title displayed on the main menu screen."""

MENU_TITLE_SIZE = 48
"""Font size for the menu title."""

MENU_OPTION_SIZE = 24
"""Font size for menu options."""

MENU_SPACING = 50
"""Vertical spacing between menu items in pixels."""

MENU_BACKGROUND_IMAGE = ""
"""Path to background image for menu screen (empty string for no image)."""

MENU_MUSIC_FILES = []
"""List of music file paths to play in the menu."""

MENU_TEXT_CONTINUE = "Continue"
"""Text for the Continue menu option."""

MENU_TEXT_NEW_GAME = "New Game"
"""Text for the New Game menu option."""

MENU_TEXT_SAVE_GAME = "Save Game"
"""Text for the Save Game menu option."""

MENU_TEXT_LOAD_GAME = "Load Game"
"""Text for the Load Game menu option."""

MENU_TEXT_EXIT = "Exit"
"""Text for the Exit menu option."""

# Player settings
PLAYER_MOVEMENT_SPEED = 3
"""Player movement speed in pixels per frame."""

TILE_SIZE = 32
"""Size of tiles in pixels (for grid-based movement and positioning)."""

INTERACTION_MANAGER_DISTANCE = 50
"""Maximum distance in pixels for general interactions."""

NPC_INTERACTION_DISTANCE = 50
"""Maximum distance in pixels for NPC interactions."""

PORTAL_INTERACTION_DISTANCE = 50
"""Maximum distance in pixels for portal interactions."""

WAYPOINT_THRESHOLD = 2
"""Distance threshold in pixels for reaching a waypoint."""

# NPC settings
NPC_SPEED = 80.0
"""Default NPC movement speed in pixels per second."""

# Asset settings
ASSETS_HANDLE = "game_assets"
"""Resource handle name for asset loading."""

# Game settings
INITIAL_MAP = "map.tmx"
"""Path to the initial map file to load."""

# Inventory settings
INVENTORY_GRID_COLS = 4
"""Number of columns in the inventory grid."""

INVENTORY_GRID_ROWS = 3
"""Number of rows in the inventory grid."""

INVENTORY_BOX_SIZE = 100
"""Size of each inventory box in pixels."""

INVENTORY_BOX_SPACING = 15
"""Spacing between inventory boxes in pixels."""

INVENTORY_BOX_BORDER_WIDTH = 3
"""Border width for inventory boxes in pixels."""

INVENTORY_BACKGROUND_IMAGE = ""
"""Path to background image for inventory screen (empty string for no image)."""

# Dialog settings
DIALOG_AUTO_CLOSE_DEFAULT = False
"""Default auto-close behavior for dialogs."""

DIALOG_AUTO_CLOSE_DURATION = 0.5
"""Seconds to wait after text is fully revealed before auto-closing dialog."""

# Installed systems (like Django's INSTALLED_APPS)
INSTALLED_SYSTEMS = [
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
    "pedre.systems.waypoint",
    "pedre.systems.player",
    "pedre.systems.physics",
    "pedre.systems.scene",
]
"""List of module paths to import for system registration.

Users can add custom systems by extending this list in their settings.py:

Example:
    INSTALLED_SYSTEMS = [
        *global_settings.INSTALLED_SYSTEMS,
        "myproject.systems.weather",
        "myproject.systems.combat",
    ]
"""
