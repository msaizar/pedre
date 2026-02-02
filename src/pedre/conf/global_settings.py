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


# Player settings
PLAYER_MOVEMENT_SPEED = 180.0
"""Player movement speed in pixels per second."""

TILE_SIZE = 32
"""Size of tiles in pixels (for grid-based movement and positioning)."""

INTERACTION_PLUGIN_DISTANCE = 50
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

INVENTORY_TITLE_FONT_SIZE = 20
"""Font size for inventory title text."""

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

# Save plugin settings
SAVE_FOLDER = "saves"
"""Directory where save files are stored."""

SAVE_QUICK_SAVE_KEY = "F5"
"""Keybind for quick save action."""

SAVE_QUICK_LOAD_KEY = "F9"
"""Keybind for quick load action."""

SAVE_SFX_FILE = "save.wav"
"""Sound effect played when saving/loading."""

# Pause Menu settings
PAUSE_MENU_OVERLAY_ALPHA = 180
"""Semi-transparent background overlay alpha value (0-255)."""

PAUSE_MENU_BOX_WIDTH = 500
"""Width of the pause menu box in pixels."""

PAUSE_MENU_BOX_HEIGHT = 400
"""Height of the pause menu box in pixels."""

PAUSE_MENU_TITLE = "PAUSED"
"""Title text displayed at the top of the pause menu."""

PAUSE_MENU_OPTION_FONT_SIZE = 20
"""Font size for menu options in pixels."""

PAUSE_MENU_TITLE_FONT_SIZE = 32
"""Font size for the menu title in pixels."""

PAUSE_MENU_SPACING = 40
"""Vertical spacing between menu options in pixels."""

PAUSE_MENU_SLOT_FONT_SIZE = 18
"""Font size for save/load slot text in pixels."""

PAUSE_MENU_TEXT_RESUME = "Resume"
"""Text for the Resume menu option."""

PAUSE_MENU_TEXT_NEW_GAME = "New Game"
"""Text for the New Game menu option."""

PAUSE_MENU_TEXT_LOAD_GAME = "Load Game"
"""Text for the Load Game menu option."""

PAUSE_MENU_TEXT_SAVE_GAME = "Save Game"
"""Text for the Save Game menu option."""

PAUSE_MENU_TEXT_EXIT = "Exit Game"
"""Text for the Exit menu option."""

PAUSE_MENU_TEXT_BACK = "Back"
"""Text for the Back option in submenus."""

PAUSE_MENU_TEXT_EMPTY_SLOT = "(Empty)"
"""Text displayed for empty save slots."""

PAUSE_MENU_CONFIRM_NEW_GAME = "Start a new game? Current progress will be lost. Press SPACE to confirm, ESC to cancel."
"""Confirmation message for starting a new game."""

# Installed plugins (like Django's INSTALLED_APPS)
INSTALLED_PLUGINS = [
    "pedre.plugins.audio",
    "pedre.plugins.cache",
    "pedre.plugins.camera",
    "pedre.plugins.debug",
    "pedre.plugins.dialog",
    "pedre.plugins.pause_menu",
    "pedre.plugins.input",
    "pedre.plugins.interaction",
    "pedre.plugins.inventory",
    "pedre.plugins.npc",
    "pedre.plugins.particle",
    "pedre.plugins.pathfinding",
    "pedre.plugins.portal",
    "pedre.plugins.save",
    "pedre.plugins.script",
    "pedre.plugins.waypoint",
    "pedre.plugins.player",
    "pedre.plugins.physics",
    "pedre.plugins.scene",
]
"""List of module paths to import for plugin registration.

Users can add custom plugins by extending this list in their settings.py:

Example:
    INSTALLED_PLUGINS = [
        *global_settings.INSTALLED_PLUGINS,
        "myproject.plugins.weather",
        "myproject.plugins.combat",
    ]
"""

# Installed actions (modules containing @ActionRegistry.register decorators)
INSTALLED_ACTIONS = [
    "pedre.plugins.audio.actions",
    "pedre.plugins.camera.actions",
    "pedre.plugins.dialog.actions",
    "pedre.plugins.inventory.actions",
    "pedre.plugins.particle.actions",
    "pedre.plugins.scene.actions",
    "pedre.plugins.npc.actions",
]
"""List of module paths to import for action registration.

Users can add custom actions by extending this list in their settings.py:

Example:
    INSTALLED_ACTIONS = [
        *global_settings.INSTALLED_ACTIONS,
        "myproject.custom_actions",
        "myproject.plugins.weather.actions",
    ]

Or replace plugin actions with custom implementations:
    INSTALLED_ACTIONS = [
        "pedre.plugins.audio.actions",
        "pedre.plugins.camera.actions",
        # Replace dialog actions with custom version
        "myproject.custom_dialog_actions",
        "pedre.plugins.inventory.actions",
        # ... rest of actions
    ]
"""

# Installed events (modules containing @EventRegistry.register decorators)
INSTALLED_EVENTS = [
    "pedre.plugins.interaction.events",
    "pedre.plugins.inventory.events",
    "pedre.plugins.npc.events",
    "pedre.plugins.portal.events",
    "pedre.plugins.scene.events",
    "pedre.plugins.script.events",
    "pedre.plugins.dialog.events",
]
"""List of module paths to import for event registration.

Users can add custom events by extending this list in their settings.py:

Example:
    INSTALLED_EVENTS = [
        *global_settings.INSTALLED_EVENTS,
        "myproject.custom_events",
        "myproject.plugins.weather.events",
    ]

Or replace plugin events with custom implementations:
    INSTALLED_EVENTS = [
        "pedre.plugins.interaction.events",
        "pedre.plugins.inventory.events",
        # Replace dialog events with custom version
        "myproject.custom_dialog_events",
        # ... rest of events
    ]
"""

# Installed conditions (modules containing @ConditionRegistry.register decorators)
INSTALLED_CONDITIONS = [
    "pedre.plugins.interaction.conditions",
    "pedre.plugins.inventory.conditions",
    "pedre.plugins.npc.conditions",
    "pedre.plugins.script.conditions",
]
"""List of module paths to import for condition registration.

Users can add custom conditions by extending this list in their settings.py:

Example:
    INSTALLED_CONDITIONS = [
        *global_settings.INSTALLED_CONDITIONS,
        "myproject.custom_conditions",
        "myproject.plugins.weather.conditions",
    ]

Or replace plugin conditions with custom implementations:
    INSTALLED_CONDITIONS = [
        "pedre.plugins.interaction.conditions",
        # Replace inventory conditions with custom version
        "myproject.custom_inventory_conditions",
        "pedre.plugins.npc.conditions",
        "pedre.plugins.script.conditions",
    ]
"""
