"""Default settings for Pedre framework.

Users can override these in their project's settings.py file.

Example:
    # In your project's settings.py:

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
ASSETS_HANDLE = "assets"
"""Resource handle name for asset loading."""

ASSETS_DIRECTORY = "assets"
"""Directory name where game assets are stored."""

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

INVENTORY_DESIGN = {
    # Grid item dimensions
    "box_size": 30,
    "box_spacing": 15,
    "box_border_width": 3,
    # Overlay dimensions
    "overlay_height_fraction": 0.3,  # Overlay covers bottom half of screen
    # Text positioning
    "item_name_y_offset": 30,
    "hint_y_offset": 10,
    "capacity_x_offset": 10,
    "capacity_y_offset": 10,
    "grid_y_offset": 20,  # Slight upward offset for grid centering
    # Photo view text positioning
    "photo_title_y_offset": 90,
    "photo_description_y_offset": 60,
    # Photo view sizing
    "photo_max_width_fraction": 0.7,
    "photo_max_height_fraction": 0.7,
    "photo_text_area_height": 120,
    # Icon padding
    "icon_padding": 4,
}
"""Design-unit values for the inventory UI layout.

All values except fractions are in pixels at the reference resolution (SCREEN_WIDTH x SCREEN_HEIGHT).
They are scaled proportionally to the actual window size at runtime.
Override individual values by merging with the default dictionary.
"""

INVENTORY_UI_SCALE_MIN = 0.5
"""Minimum UI scale factor for the inventory. Prevents the inventory from shrinking too small."""

INVENTORY_UI_SCALE_MAX = 2.0
"""Maximum UI scale factor for the inventory. Prevents the inventory from growing too large."""

INVENTORY_BACKGROUND_IMAGE = ""
"""Path to background image for inventory screen (empty string for no image)."""

INVENTORY_MAX_SPACE = 12
"""Maximum number of items that can be held in inventory."""

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
DIALOG_DESIGN = {
    # Box dimensions (design units at reference resolution)
    "box_width": 800,
    "box_height": 200,
    # Border
    "border_width": 3,
    # Padding
    "horizontal_padding": 20,
    "vertical_padding": 20,
    # NPC name positioning
    "npc_name_offset": 30,
    # Footer positioning (page indicator and instructions)
    "footer_offset": 20,
    # Vertical position of dialog box from bottom (as fraction of window height)
    "vertical_position": 0.25,
}
"""Design-unit values for the dialog UI layout.

All values except 'vertical_position' are in pixels at the reference resolution (SCREEN_WIDTH x SCREEN_HEIGHT).
They are scaled proportionally to the actual window size at runtime.
The 'vertical_position' value is a fraction (0.0-1.0) and is not scaled.
Override individual values by merging with the default dictionary.
"""

DIALOG_UI_SCALE_MIN = 0.5
"""Minimum UI scale factor for the dialog. Prevents the dialog from shrinking too small."""

DIALOG_UI_SCALE_MAX = 2.0
"""Maximum UI scale factor for the dialog. Prevents the dialog from growing too large."""

DIALOG_OVERLAY_ALPHA = 128
"""Transparency of the dialog overlay background (0-255)."""

DIALOG_COLOR_BOX_BACKGROUND = (45, 52, 54)
"""RGB color for the dialog box background (dark blue-gray)."""

DIALOG_COLOR_BOX_BORDER = (255, 255, 255)
"""RGB color for the dialog box border."""

DIALOG_COLOR_NPC_NAME = (255, 255, 0)
"""RGB color for the NPC name text (yellow)."""

DIALOG_COLOR_TEXT = (255, 255, 255)
"""RGB color for the dialog text (white)."""

DIALOG_COLOR_INSTRUCTION = (211, 211, 211)
"""RGB color for instruction text (light gray)."""

DIALOG_COLOR_PAGE_INDICATOR = (211, 211, 211)
"""RGB color for page indicator text (light gray)."""

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

# UI Font Scale
# Framework-wide font tiers as (small_screen, reference, large_screen) tuples.
# The actual font size is interpolated based on ui_scale:
#   - At ui_scale <= min_scale (e.g. 0.5): uses the small_screen value
#   - At ui_scale == 1.0: uses the reference value
#   - At ui_scale >= max_scale (e.g. 2.0): uses the large_screen value
#   - In between: linear interpolation
UI_FONT_SMALL = (8, 12, 16)
"""Small font tier (small_screen, reference, large_screen). Used for slot text, fine print."""

UI_FONT_NORMAL = (12, 16, 22)
"""Normal font tier (small_screen, reference, large_screen). Used for menu options, body text."""

UI_FONT_LARGE = (16, 22, 30)
"""Large font tier (small_screen, reference, large_screen). Used for titles, headings."""

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

PAUSE_MENU_TITLE = "Pedre Game"
"""Title text displayed at the top of the pause menu."""

# Pause Menu Design Units
# All spatial values are in "design units" -- pixels at the reference resolution
# (SCREEN_WIDTH x SCREEN_HEIGHT, default 1280x720). At runtime, they are multiplied
# by a ui_scale factor derived from the actual window size.
# Font sizes come from UI_FONT_SMALL/NORMAL/LARGE, not from this dictionary.

PAUSE_MENU_DESIGN = {
    # Box dimensions
    "box_width": 512,
    "box_height": 396,
    # Title area
    "title_padding": 20,
    "title_area_height": 59,
    # Content layout
    "spacing": 28,
    "horizontal_padding": 25,
    "content_bottom_padding": 40,
    # Feedback
    "feedback_offset": 40,
    # Confirmation
    "confirmation_message_offset": 40,
    "confirmation_options_offset": 20,
    # Border
    "border_width": 2,
}
"""Design-unit values for the pause menu UI layout.

All values are in pixels at the reference resolution (SCREEN_WIDTH x SCREEN_HEIGHT).
They are scaled proportionally to the actual window size at runtime.
Override individual values by merging with the default dictionary.
"""

PAUSE_MENU_UI_SCALE_MIN = 0.5
"""Minimum UI scale factor for the pause menu. Prevents the menu from shrinking too small."""

PAUSE_MENU_UI_SCALE_MAX = 2.0
"""Maximum UI scale factor for the pause menu. Prevents the menu from growing too large."""

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

PAUSE_MENU_CONFIRM_NEW_GAME = "Start a new game? Current progress will be lost."
"""Confirmation message for starting a new game."""

PAUSE_MENU_COLOR_OVERLAY = (0, 0, 0)
"""RGB color for the full-screen overlay background behind the menu."""

PAUSE_MENU_COLOR_BOX_BACKGROUND = (102, 102, 153)
"""RGB color for the menu box background (dark blue-gray)."""

PAUSE_MENU_COLOR_BOX_BORDER = (255, 255, 255)
"""RGB color for the menu box border."""

PAUSE_MENU_COLOR_TITLE = (255, 255, 255)
"""RGB color for the menu title text."""

PAUSE_MENU_COLOR_OPTION = (255, 255, 255)
"""RGB color for unselected menu options and text."""

PAUSE_MENU_COLOR_SELECTED = (255, 255, 0)
"""RGB color for the currently selected menu option."""

PAUSE_MENU_COLOR_DISABLED = (128, 128, 128)
"""RGB color for disabled/empty slot text."""

PAUSE_MENU_COLOR_FEEDBACK = (0, 255, 0)
"""RGB color for feedback messages (e.g. 'Game Saved!')."""

PAUSE_MENU_OVERLAY_ALPHA = 128
"""Transparency of the pause menu overlay background (0-255)."""

# Inventory colors
INVENTORY_COLOR_OVERLAY = (45, 52, 54)
"""RGB color for the full-screen overlay background behind the inventory."""

INVENTORY_OVERLAY_ALPHA = 255
"""Transparency of the inventory overlay background (0-255)."""

INVENTORY_COLOR_BOX_FILLED = (47, 79, 79)
"""RGB color for filled inventory slot background (dark slate gray)."""

INVENTORY_COLOR_BOX_EMPTY = (30, 30, 35)
"""RGBA color for empty inventory slot background."""

INVENTORY_COLOR_BOX_BORDER = (255, 255, 255)
"""RGB color for inventory box border (white)."""

INVENTORY_COLOR_BOX_BORDER_SELECTED = (255, 255, 0)
"""RGB color for selected inventory box border (yellow)."""

INVENTORY_COLOR_BOX_BORDER_EMPTY = (105, 105, 105)
"""RGB color for empty inventory box border (dim gray)."""

INVENTORY_COLOR_TEXT_ITEM_NAME = (255, 255, 255)
"""RGB color for selected item name text (white)."""

INVENTORY_COLOR_TEXT_HINT = (211, 211, 211)
"""RGB color for hint text (light gray)."""

INVENTORY_COLOR_TEXT_CAPACITY = (255, 255, 255)
"""RGB color for capacity counter text (white)."""

INVENTORY_COLOR_TEXT_PHOTO_TITLE = (255, 255, 255)
"""RGB color for photo title text (white)."""

INVENTORY_COLOR_TEXT_PHOTO_DESCRIPTION = (211, 211, 211)
"""RGB color for photo description text (light gray)."""

INVENTORY_COLOR_PHOTO_BACKGROUND = (0, 0, 0)
"""RGB color for photo view background (black)."""

INVENTORY_EMPTY_BOX_ALPHA = 180
"""Transparency of empty inventory slot backgrounds (0-255)."""

# Script settings
SCRIPTS_DIRECTORY = "data/scripts"
"""Directory where script files are stored (relative to assets directory)."""

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
