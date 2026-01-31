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
PLAYER_MOVEMENT_SPEED = 180.0
"""Player movement speed in pixels per second."""

TILE_SIZE = 32
"""Size of tiles in pixels (for grid-based movement and positioning)."""

INTERACTION_MANAGER_DISTANCE = 50
"""Maximum distance in pixels for general interactions."""

INTERACTION_KEY = "SPACE"
"""Key for interacting with objects."""

NPC_INTERACTION_DISTANCE = 50
"""Maximum distance in pixels for NPC interactions."""

PORTAL_INTERACTION_DISTANCE = 50
"""Maximum distance in pixels for portal interactions."""

WAYPOINT_THRESHOLD = 2
"""Distance threshold in pixels for reaching a waypoint."""

# NPC settings
NPC_MOVEMENT_SPEED = 80.0
"""Default NPC movement speed in pixels per second."""

NPC_WAYPOINT_THRESHOLD = 2
"""Distance threshold in pixels for NPCs to reach a waypoint during movement."""

NPC_INTERACTION_KEY = "SPACE"
"""Key for interacting with NPCs."""

# Asset settings
ASSETS_HANDLE = "game_assets"
"""Resource handle name for asset loading."""

# Game settings
INITIAL_MAP = "map.tmx"
"""Path to the initial map file to load."""

# Scene settings
SCENE_TRANSITION_ALPHA = 0.0
"""Initial transition alpha value (0.0 = transparent, 1.0 = opaque)."""

SCENE_TRANSITION_SPEED = 3.0
"""Alpha change per second during scene transitions."""

SCENE_MAPS_FOLDER = "maps"
"""Folder where map files are stored (relative to assets directory)."""

SCENE_TILEMAP_SCALING = 1.0
"""Scaling factor for tilemap rendering."""

SCENE_COLLISION_LAYER_NAMES = ["Walls", "Collision", "Objects", "Buildings"]
"""Names of tilemap layers that should be treated as collision layers."""

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

INVENTORY_MAX_SPACE = 12
"""Maximum number of items that can be held in inventory."""

INVENTORY_CAPACITY_FONT_SIZE = 14
"""Font size for the inventory capacity counter display."""

INVENTORY_ITEMS_FILE = "data/inventory_items.json"
"""Path to the inventory items JSON data file."""

INVENTORY_KEY_TOGGLE = "I"
"""Key to open/close the inventory overlay."""

INVENTORY_KEY_VIEW = "V"
"""Key to view the selected item in detail (full-screen mode)."""

INVENTORY_KEY_CONSUME = "C"
"""Key to consume the selected item (if it's consumable)."""

INVENTORY_HINT_VIEW = "[V] View"
"""Help text shown for viewing an item."""

INVENTORY_HINT_CONSUME = "[C] Consume"
"""Help text shown for consuming an item."""

INVENTORY_HINT_FONT_SIZE = 12
"""Font size for inventory hint text."""

# Dialog settings
DIALOG_AUTO_CLOSE_DEFAULT = False
"""Default auto-close behavior for dialogs."""

DIALOG_AUTO_CLOSE_DURATION = 0.5
"""Seconds to wait after text is fully revealed before auto-closing dialog."""

DIALOG_SHOW_HELP = True
"""Whether to show help instructions in the dialog box."""

DIALOG_SHOW_PAGINATION = True
"""Whether to show page numbers in multi-page dialogs."""

DIALOG_TEXT_NEXT_PAGE = "Press SPACE for next page"
"""Help instruction text shown when there are more pages."""

DIALOG_TEXT_CLOSE = "Press SPACE to close"
"""Help instruction text shown on the last page."""

DIALOG_TEXT_PAGE = "Page"
"""Text label for page indicator (e.g., 'Page 1/3')."""

DIALOG_CHAR_REVEAL_SPEED = 20
"""Characters revealed per second during text animation."""

DIALOG_INSTANT_TEXT_DEFAULT = False
"""Default instant text behavior for dialogs. If True, text appears immediately without reveal animation."""

DIALOG_KEY_ADVANCE = "SPACE"
"""Key for advancing dialog pages and closing dialogs."""

# Dialog UI Layout Settings
DIALOG_BOX_WIDTH_PERCENT = 0.75
"""Dialog box width as fraction of window width (0.0-1.0). Default: 75% of window width."""

DIALOG_BOX_MAX_WIDTH = 800
"""Maximum dialog box width in pixels."""

DIALOG_BOX_MIN_WIDTH = 400
"""Minimum dialog box width in pixels."""

DIALOG_BOX_HEIGHT_PERCENT = 0.25
"""Dialog box height as fraction of window height (0.0-1.0). Default: 25% of window height."""

DIALOG_BOX_MIN_HEIGHT = 150
"""Minimum dialog box height in pixels."""

DIALOG_VERTICAL_POSITION = 0.25
"""Dialog box vertical position from bottom as fraction of window height (0.0-1.0).
Maintains current behavior at 25% from bottom.
"""

DIALOG_OVERLAY_ALPHA = 128
"""Transparency of the dialog overlay background (0-255)."""

DIALOG_BORDER_WIDTH = 3
"""Width of dialog box border in pixels."""

DIALOG_PADDING_HORIZONTAL = 20
"""Horizontal padding inside dialog box in pixels."""

DIALOG_PADDING_VERTICAL = 20
"""Vertical padding inside dialog box in pixels."""

DIALOG_NPC_NAME_OFFSET = 30
"""Vertical offset of NPC name from top of dialog box in pixels."""

DIALOG_FOOTER_OFFSET = 20
"""Vertical offset of footer elements from bottom of dialog box in pixels."""

# Dialog Font Sizes
DIALOG_NPC_NAME_FONT_SIZE = 20
"""Font size for NPC name text."""

DIALOG_TEXT_FONT_SIZE = 16
"""Font size for dialog message text."""

DIALOG_INSTRUCTION_FONT_SIZE = 12
"""Font size for instruction text."""

DIALOG_PAGE_INDICATOR_FONT_SIZE = 10
"""Font size for page indicator text."""

# Audio settings
AUDIO_MUSIC_VOLUME = 0.5
"""Default music volume (0.0 to 1.0)."""

AUDIO_MUSIC_ENABLED = True
"""Whether music is enabled by default."""

AUDIO_SFX_VOLUME = 0.7
"""Default sound effects volume (0.0 to 1.0)."""

AUDIO_SFX_ENABLED = True
"""Whether sound effects are enabled by default."""

# Camera settings
CAMERA_LERP_SPEED = 0.1
"""Camera interpolation speed for smooth following (0.0 to 1.0).
Higher values make the camera catch up faster to the target.
- 0.05: Very slow, dramatic following
- 0.1: Default smooth following (recommended)
- 0.2: Responsive following
- 1.0: Instant following (no smoothing)
"""

# Particle settings
PARTICLE_ENABLED = True
"""Whether particle effects are enabled by default."""

PARTICLE_COLOR_HEARTS = (255, 105, 180)
"""Default color for heart particles (hot pink)."""

PARTICLE_COLOR_SPARKLES = (255, 255, 100)
"""Default color for sparkle particles (yellow)."""

PARTICLE_COLOR_TRAIL = (200, 200, 255)
"""Default color for trail particles (light blue)."""

PARTICLE_COLOR_BURST = (255, 200, 0)
"""Default color for burst particles (orange)."""

# Save system settings
SAVE_FOLDER = "saves"
"""Directory where save files are stored."""

SAVE_QUICK_SAVE_KEY = "F5"
"""Keybind for quick save action."""

SAVE_QUICK_LOAD_KEY = "F9"
"""Keybind for quick load action."""

SAVE_SFX_FILE = "save.wav"
"""Sound effect played when saving/loading."""

# Installed systems (like Django's INSTALLED_APPS)
INSTALLED_SYSTEMS = [
    "pedre.systems.audio",
    "pedre.systems.cache",
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

# Installed actions (modules containing @ActionRegistry.register decorators)
INSTALLED_ACTIONS = [
    "pedre.systems.audio.actions",
    "pedre.systems.camera.actions",
    "pedre.systems.dialog.actions",
    "pedre.systems.inventory.actions",
    "pedre.systems.particle.actions",
    "pedre.systems.scene.actions",
    "pedre.systems.npc.actions",
]
"""List of module paths to import for action registration.

Users can add custom actions by extending this list in their settings.py:

Example:
    INSTALLED_ACTIONS = [
        *global_settings.INSTALLED_ACTIONS,
        "myproject.custom_actions",
        "myproject.systems.weather.actions",
    ]

Or replace system actions with custom implementations:
    INSTALLED_ACTIONS = [
        "pedre.systems.audio.actions",
        "pedre.systems.camera.actions",
        # Replace dialog actions with custom version
        "myproject.custom_dialog_actions",
        "pedre.systems.inventory.actions",
        # ... rest of actions
    ]
"""

# Installed events (modules containing @EventRegistry.register decorators)
INSTALLED_EVENTS = [
    "pedre.systems.interaction.events",
    "pedre.systems.inventory.events",
    "pedre.systems.npc.events",
    "pedre.systems.portal.events",
    "pedre.systems.scene.events",
    "pedre.systems.script.events",
    "pedre.systems.dialog.events",
]
"""List of module paths to import for event registration.

Users can add custom events by extending this list in their settings.py:

Example:
    INSTALLED_EVENTS = [
        *global_settings.INSTALLED_EVENTS,
        "myproject.custom_events",
        "myproject.systems.weather.events",
    ]

Or replace system events with custom implementations:
    INSTALLED_EVENTS = [
        "pedre.systems.interaction.events",
        "pedre.systems.inventory.events",
        # Replace dialog events with custom version
        "myproject.custom_dialog_events",
        # ... rest of events
    ]
"""

# Installed conditions (modules containing @ConditionRegistry.register decorators)
INSTALLED_CONDITIONS = [
    "pedre.systems.interaction.conditions",
    "pedre.systems.inventory.conditions",
    "pedre.systems.npc.conditions",
    "pedre.systems.script.conditions",
]
"""List of module paths to import for condition registration.

Users can add custom conditions by extending this list in their settings.py:

Example:
    INSTALLED_CONDITIONS = [
        *global_settings.INSTALLED_CONDITIONS,
        "myproject.custom_conditions",
        "myproject.systems.weather.conditions",
    ]

Or replace system conditions with custom implementations:
    INSTALLED_CONDITIONS = [
        "pedre.systems.interaction.conditions",
        # Replace inventory conditions with custom version
        "myproject.custom_inventory_conditions",
        "pedre.systems.npc.conditions",
        "pedre.systems.script.conditions",
    ]
"""
