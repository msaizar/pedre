# Configuration Guide

Pedre uses the `settings.py` file for configuration.

## Configuration Overview

Configure your game by creating a `settings.py` file in your project root:

```python

SCREEN_WIDTH=1280
SCREEN_HEIGHT=720
WINDOW_TITLE="My RPG Game"
PLAYER_MOVEMENT_SPEED=180.0
TILE_SIZE=32
INTERACTION_PLUGIN_DISTANCE=50
NPC_INTERACTION_DISTANCE=50
PORTAL_INTERACTION_DISTANCE=50
WAYPOINT_THRESHOLD=2
NPC_SPEED=80.0
INVENTORY_GRID_COLS=4
INVENTORY_GRID_ROWS=3
INVENTORY_MAX_SPACE=12
INVENTORY_DESIGN={
    **INVENTORY_DESIGN,
    "box_size": 80,
}
DIALOG_AUTO_CLOSE_DEFAULT=False
DIALOG_AUTO_CLOSE_DURATION=0.5
AUDIO_MUSIC_VOLUME=0.5
AUDIO_MUSIC_ENABLED=True
AUDIO_SFX_VOLUME=0.7
AUDIO_SFX_ENABLED=True
CAMERA_LERP_SPEED=0.1
ASSETS_HANDLE="assets"
INITIAL_MAP="start.tmx"
```

## Configuration Settings

### Window Settings

Control window and display properties.

| Setting         | Type   | Default      | Description             |
| --------------- | ------ | ------------ | ----------------------- |
| `SCREEN_WIDTH`  | int    | 1280         | Window width in pixels  |
| `SCREEN_HEIGHT` | int    | 720          | Window height in pixels |
| `WINDOW_TITLE`  | string | "Pedre Game" | Window title text       |

### Input Settings

Input handling and player movement configuration.

| Setting                 | Type  | Default | Description                              |
| ----------------------- | ----- | ------- | ---------------------------------------- |
| `PLAYER_MOVEMENT_SPEED` | float | 180.0   | Base movement speed in pixels per second |

**Notes:**

- `PLAYER_MOVEMENT_SPEED` controls how fast the player moves per second when movement keys are pressed
- Applied to the normalized movement vector returned by `InputPlugin.get_movement_vector(delta_time)`
- Movement is frame-rate independent, ensuring consistent speed across different devices
- Typical values range from 100.0 (slow) to 300.0 (fast)
- For more details, see the [InputPlugin documentation](plugins/input.md)

### Player Settings

Player character interaction settings.

| Setting                        | Type   | Default | Description                                                 |
| ------------------------------ | ------ | ------- | ----------------------------------------------------------- |
| `TILE_SIZE`                    | int    | 32      | Base tile size for grid-based movement                      |
| `INTERACTION_PLUGIN_DISTANCE`  | int    | 50      | Maximum distance for player to interact with objects        |
| `INTERACTION_KEY`              | string | "SPACE" | Key for interacting with objects (use arcade.key constants) |
| `NPC_INTERACTION_DISTANCE`     | int    | 50      | Maximum distance for player to interact with NPCs           |
| `PORTAL_INTERACTION_DISTANCE`  | int    | 50      | Maximum distance for player to activate portals             |
| `WAYPOINT_THRESHOLD`           | int    | 2       | Distance threshold to consider waypoint reached             |

**Notes:**

- `INTERACTION_PLUGIN_DISTANCE` determines how close the player must be to interact with objects
  - Common values: 32 (1 tile), 50 (default, ~1.5 tiles), 64 (2 tiles), 96 (3 tiles)
  - Uses Euclidean distance from player center to object center
  - For more details, see the [InteractionPlugin documentation](plugins/interaction.md)
- `INTERACTION_KEY` can be set to any arcade key constant (e.g., "E", "SPACE", "RETURN"). Keys are matched using the `matches_key()` helper function
- `NPC_INTERACTION_DISTANCE` determines how close the player must be to interact with NPCs
- `PORTAL_INTERACTION_DISTANCE` determines how close the player must be to activate portals
  - Common values: 32 (1 tile), 50 (default, ~1.5 tiles), 64 (2 tiles), 96 (3 tiles)
  - Uses Euclidean distance from player center to portal center
  - Creates a circular activation zone around each portal
  - Events only fire when player enters the zone (not while standing in it)
  - For more details, see the [PortalPlugin documentation](plugins/portal.md)
- `WAYPOINT_THRESHOLD` controls pathfinding precision (lower = more precise)

### NPC Settings

NPC behavior and interaction settings.

| Setting                    | Type  | Default | Description                                                  |
| -------------------------- | ----- | ------- | ------------------------------------------------------------ |
| `NPC_INTERACTION_DISTANCE` | int   | 50      | Maximum distance in pixels for player to interact with NPCs  |
| `NPC_MOVEMENT_SPEED`       | float | 80.0    | NPC movement speed in pixels per second                      |
| `NPC_WAYPOINT_THRESHOLD`   | int   | 2       | Distance in pixels to consider an NPC has reached a waypoint |
| `NPC_INTERACTION_KEY`      | str   | "SPACE" | Key to interact with NPCs (use arcade.key constants)         |

**Notes:**

- `NPC_INTERACTION_DISTANCE` determines how close the player must be to interact with NPCs
- `NPC_MOVEMENT_SPEED` is the default speed for all NPCs using pathfinding
- `NPC_WAYPOINT_THRESHOLD` controls pathfinding precision (lower = more precise turns)
- `NPC_INTERACTION_KEY` can be set to any arcade key constant (e.g., "E", "F", "RETURN")

### Pause Menu Settings

In-game pause menu overlay appearance and behavior.

#### Visual Settings

| Setting                           | Type                 | Default         | Description                                           |
| --------------------------------- | -------------------- | --------------- | ----------------------------------------------------- |
| `PAUSE_MENU_OVERLAY_ALPHA`        | int                  | 180             | Opacity of the semi-transparent overlay (0-255)       |
| `PAUSE_MENU_COLOR_OVERLAY`        | tuple[int, int, int] | (0, 0, 0)       | RGB color of the overlay                              |
| `PAUSE_MENU_COLOR_BOX_BACKGROUND` | tuple[int, int, int] | (102, 102, 153) | RGB color of the menu box background                  |
| `PAUSE_MENU_COLOR_BOX_BORDER`     | tuple[int, int, int] | (255, 255, 255) | RGB color of the menu box border                      |
| `PAUSE_MENU_COLOR_TITLE`          | tuple[int, int, int] | (255, 255, 255) | RGB color of the title text                           |
| `PAUSE_MENU_COLOR_OPTION`         | tuple[int, int, int] | (255, 255, 255) | RGB color of unselected options                       |
| `PAUSE_MENU_COLOR_SELECTED`       | tuple[int, int, int] | (255, 255, 0)   | RGB color of the selected option                      |
| `PAUSE_MENU_COLOR_DISABLED`       | tuple[int, int, int] | (128, 128, 128) | RGB color of disabled options                         |
| `PAUSE_MENU_COLOR_FEEDBACK`       | tuple[int, int, int] | (0, 255, 0)     | RGB color of feedback messages (e.g., "Game Saved!")  |

#### Text Settings

| Setting                       | Type   | Default                                            | Description                        |
| ----------------------------- | ------ | -------------------------------------------------- | ---------------------------------- |
| `PAUSE_MENU_TITLE`            | string | "Pedre Game"                                       | Title shown at the top of the menu |
| `PAUSE_MENU_TEXT_RESUME`      | string | "Resume"                                           | Text for Resume option             |
| `PAUSE_MENU_TEXT_NEW_GAME`    | string | "New Game"                                         | Text for New Game option           |
| `PAUSE_MENU_TEXT_LOAD_GAME`   | string | "Load Game"                                        | Text for Load Game option          |
| `PAUSE_MENU_TEXT_SAVE_GAME`   | string | "Save Game"                                        | Text for Save Game option          |
| `PAUSE_MENU_TEXT_EXIT`        | string | "Exit Game"                                        | Text for Exit option               |
| `PAUSE_MENU_TEXT_BACK`        | string | "Back"                                             | Text for Back option               |
| `PAUSE_MENU_TEXT_EMPTY_SLOT`  | string | "(Empty)"                                          | Text shown for empty save slots    |
| `PAUSE_MENU_CONFIRM_NEW_GAME` | string | "Start a new game? Current progress will be lost." | Confirmation message for New Game  |

#### Layout Settings

| Setting                | Type | Default     | Description                                                 |
| ---------------------- | ---- | ----------- | ----------------------------------------------------------- |
| `PAUSE_MENU_DESIGN`    | dict | (see below) | Dictionary containing all design specifications (see below) |

**PAUSE_MENU_DESIGN dictionary:**

```python
PAUSE_MENU_DESIGN = {
    "box_width": 500,                    # Width of the menu box in design units
    "box_height": 400,                   # Height of the menu box in design units
    "border_width": 4,                   # Width of the menu box border
    "title_padding": 20,                 # Padding above the title
    "title_area_height": 80,             # Height reserved for the title area
    "horizontal_padding": 40,            # Left/right padding inside the box
    "spacing": 50,                       # Vertical spacing between options
    "content_bottom_padding": 20,        # Bottom padding for slot lists
    "confirmation_message_offset": 50,   # Vertical offset for confirmation message
    "confirmation_options_offset": 30,   # Vertical offset for confirmation options
    "feedback_offset": 50,               # Offset for feedback messages
}
```

#### Scaling Settings

| Setting                   | Type  | Default | Description                 |
| ------------------------- | ----- | ------- | --------------------------- |
| `PAUSE_MENU_UI_SCALE_MIN` | float | 0.5     | Minimum UI scale factor     |
| `PAUSE_MENU_UI_SCALE_MAX` | float | 2.0     | Maximum UI scale factor     |

**Notes:**

- **Responsive scaling**: The pause menu uses responsive UI scaling that adapts to different window sizes
  - Design units are scaled based on window dimensions using `compute_ui_scale()`
  - Scale factor is clamped between `PAUSE_MENU_UI_SCALE_MIN` and `PAUSE_MENU_UI_SCALE_MAX`
  - Fonts are scaled using `scale_font()` for optimal readability
- **Colors**: All color settings use RGB tuples (0-255 for each component)
- **Overlay alpha**: Value of 180 (default) = ~70% opacity for the background overlay
- **Menu states**: The pause menu has four states: MAIN_MENU, LOAD_SLOTS, SAVE_SLOTS, and CONFIRMATION
- **Save slots**:
  - Load slots: 0-3 (slot 0 is autosave)
  - Save slots: 1-3 (manual saves only)
- **Auto-save on exit**: When Exit is selected, the game automatically saves to slot 0 before closing
- For more details, see the [PauseMenuPlugin documentation](../plugins/pause-menu.md)

### Inventory Settings

Inventory grid layout, capacity, and appearance. The inventory uses responsive design that scales proportionally to screen size.

#### Grid Layout Settings

| Setting               | Type | Default | Description                         |
| --------------------- | ---- | ------- | ----------------------------------- |
| `INVENTORY_GRID_COLS` | int  | 4       | Number of columns in inventory grid |
| `INVENTORY_GRID_ROWS` | int  | 3       | Number of rows in inventory grid    |
| `INVENTORY_MAX_SPACE` | int  | 12      | Maximum number of items to hold     |

#### Responsive Design Settings

The `INVENTORY_DESIGN` dictionary contains design-unit values (pixels at reference resolution) that scale automatically:

| Key                         | Type  | Default | Description                            |
| --------------------------- | ----- | ------- | -------------------------------------- |
| `box_size`                  | int   | 100     | Size of each inventory slot            |
| `box_spacing`               | int   | 15      | Spacing between slots                  |
| `box_border_width`          | int   | 3       | Border width for slots                 |
| `overlay_height_fraction`   | float | 0.5     | Fraction of screen for overlay         |
| `item_name_y_offset`        | int   | 30      | Y position for item name               |
| `hint_y_offset`             | int   | 10      | Y position for hints                   |
| `capacity_x_offset`         | int   | 10      | X offset for capacity counter          |
| `capacity_y_offset`         | int   | 10      | Y offset for capacity counter          |
| `grid_y_offset`             | int   | 20      | Vertical centering offset              |
| `photo_title_y_offset`      | int   | 90      | Y position for photo title             |
| `photo_description_y_offset`| int   | 60      | Y position for photo description       |
| `photo_max_width_fraction`  | float | 0.7     | Max photo width fraction               |
| `photo_max_height_fraction` | float | 0.7     | Max photo height fraction              |
| `photo_text_area_height`    | int   | 120     | Reserved height for photo text         |
| `icon_padding`              | int   | 4       | Padding inside icon boxes              |

UI scaling bounds:

| Setting                   | Type  | Default | Description           |
| ------------------------- | ----- | ------- | --------------------- |
| `INVENTORY_UI_SCALE_MIN`  | float | 0.5     | Minimum UI scale      |
| `INVENTORY_UI_SCALE_MAX`  | float | 2.0     | Maximum UI scale      |

#### Color Settings

| Setting                                  | Type  | Default         | Description                  |
| ---------------------------------------- | ----- | --------------- | ---------------------------- |
| `INVENTORY_COLOR_OVERLAY`                | tuple | (0, 0, 0)       | Overlay background RGB       |
| `INVENTORY_OVERLAY_ALPHA`                | int   | 200             | Overlay transparency (0-255) |
| `INVENTORY_COLOR_BOX_FILLED`             | tuple | (47, 79, 79)    | Filled slot background       |
| `INVENTORY_COLOR_BOX_EMPTY`              | tuple | (30, 30, 35)    | Empty slot background        |
| `INVENTORY_EMPTY_BOX_ALPHA`              | int   | 180             | Empty slot transparency      |
| `INVENTORY_COLOR_BOX_BORDER`             | tuple | (255, 255, 255) | Slot border RGB              |
| `INVENTORY_COLOR_BOX_BORDER_SELECTED`    | tuple | (255, 255, 0)   | Selected border RGB          |
| `INVENTORY_COLOR_BOX_BORDER_EMPTY`       | tuple | (105, 105, 105) | Empty slot border RGB        |
| `INVENTORY_COLOR_TEXT_ITEM_NAME`         | tuple | (255, 255, 255) | Item name text RGB           |
| `INVENTORY_COLOR_TEXT_HINT`              | tuple | (211, 211, 211) | Hint text RGB                |
| `INVENTORY_COLOR_TEXT_CAPACITY`          | tuple | (255, 255, 255) | Capacity counter RGB         |
| `INVENTORY_COLOR_TEXT_PHOTO_TITLE`       | tuple | (255, 255, 255) | Photo title RGB              |
| `INVENTORY_COLOR_TEXT_PHOTO_DESCRIPTION` | tuple | (211, 211, 211) | Photo description RGB        |
| `INVENTORY_COLOR_PHOTO_BACKGROUND`       | tuple | (0, 0, 0)       | Photo view background        |

#### Data and Input Settings

| Setting                      | Type   | Default                     | Description                         |
| ---------------------------- | ------ | --------------------------- | ----------------------------------- |
| `INVENTORY_BACKGROUND_IMAGE` | string | ""                          | Optional background image path      |
| `INVENTORY_KEY_TOGGLE`       | string | "I"                         | Key to open/close overlay           |
| `INVENTORY_KEY_VIEW`         | string | "V"                         | Key to view item in detail          |
| `INVENTORY_KEY_CONSUME`      | string | "C"                         | Key to consume item                 |

#### Hint Text Settings

| Setting                 | Type   | Default       | Description                   |
| ----------------------- | ------ | ------------- | ----------------------------- |
| `INVENTORY_HINT_VIEW`   | string | "[V] View"    | Hint text for viewing items   |
| `INVENTORY_HINT_CONSUME`| string | "[C] Consume" | Hint text for consuming items |

**Notes:**

- Inventory uses responsive scaling - all UI elements scale proportionally to screen size
- Design values are in pixels at reference resolution (`SCREEN_WIDTH` × `SCREEN_HEIGHT`)
- Actual rendered sizes are scaled by `compute_ui_scale()` within min/max bounds
- Font sizes use the global `UI_FONT_SMALL`, `UI_FONT_NORMAL`, and `UI_FONT_LARGE` tiers
- Total capacity is controlled by `INVENTORY_MAX_SPACE`, independent of grid size
- `INVENTORY_BACKGROUND_IMAGE` is optional; solid color overlay is used by default
- Override specific design values by merging with the default `INVENTORY_DESIGN` dict
- For more details, see the [InventoryPlugin documentation](plugins/inventory.md)

### Dialog Settings

Dialog plugin behavior, timing, and appearance.

#### Behavior Settings

| Setting                       | Type   | Default | Description                                                           |
| ----------------------------- | ------ | ------- | --------------------------------------------------------------------- |
| `DIALOG_AUTO_CLOSE_DEFAULT`   | bool   | False   | Default auto-close behavior for dialogs when not explicitly specified |
| `DIALOG_AUTO_CLOSE_DURATION`  | float  | 0.5     | Seconds to wait after text is fully revealed before auto-closing      |
| `DIALOG_CHAR_REVEAL_SPEED`    | int    | 20      | Characters per second for text reveal animation                       |
| `DIALOG_INSTANT_TEXT_DEFAULT` | bool   | False   | Whether text appears instantly by default (skips reveal animation)    |
| `DIALOG_SHOW_HELP`            | bool   | True    | Whether to show instruction text at the bottom of the dialog          |
| `DIALOG_SHOW_PAGINATION`      | bool   | True    | Whether to show page indicators (e.g., "Page 1/3")                    |
| `DIALOG_KEY_ADVANCE`          | string | "SPACE" | Key for advancing dialog pages and closing dialogs                    |

#### Layout Settings

| Setting                | Type | Default     | Description                                                                          |
| ---------------------- | ---- | ----------- | ------------------------------------------------------------------------------------ |
| `DIALOG_DESIGN`        | dict | (see below) | Dictionary containing all design specifications (see below)                          |
| `DIALOG_OVERLAY_ALPHA` | int  | 128         | Transparency of background overlay (0-255, where 0 is transparent and 255 is opaque) |

**DIALOG_DESIGN dictionary:**

```python
DIALOG_DESIGN = {
    "box_width": 800,           # Width of the dialog box in design units
    "box_height": 200,          # Height of the dialog box in design units
    "border_width": 3,          # Width of the dialog box border
    "horizontal_padding": 20,   # Left/right padding inside the box
    "vertical_padding": 20,     # Top/bottom padding inside the box
    "npc_name_offset": 30,      # Vertical offset of NPC name from top
    "footer_offset": 20,        # Vertical offset of footer elements from bottom
    "vertical_position": 0.25,  # Dialog box vertical position from bottom (fraction 0.0-1.0)
}
```

#### Dialog Scaling Settings

| Setting               | Type  | Default | Description             |
| --------------------- | ----- | ------- | ----------------------- |
| `DIALOG_UI_SCALE_MIN` | float | 0.5     | Minimum UI scale factor |
| `DIALOG_UI_SCALE_MAX` | float | 2.0     | Maximum UI scale factor |

#### Dialog Visual Settings

| Setting                       | Type                 | Default         | Description                                 |
| ----------------------------- | -------------------- | --------------- | ------------------------------------------- |
| `DIALOG_COLOR_BOX_BACKGROUND` | tuple[int, int, int] | (45, 52, 54)    | RGB color of the dialog box background      |
| `DIALOG_COLOR_BOX_BORDER`     | tuple[int, int, int] | (255, 255, 255) | RGB color of the dialog box border          |
| `DIALOG_COLOR_NPC_NAME`       | tuple[int, int, int] | (255, 255, 0)   | RGB color of the NPC name text              |
| `DIALOG_COLOR_TEXT`           | tuple[int, int, int] | (255, 255, 255) | RGB color of the dialog text                |
| `DIALOG_COLOR_INSTRUCTION`    | tuple[int, int, int] | (211, 211, 211) | RGB color of instruction text               |
| `DIALOG_COLOR_PAGE_INDICATOR` | tuple[int, int, int] | (211, 211, 211) | RGB color of page indicator text            |

#### Text Labels

| Setting                 | Type   | Default                     | Description                                      |
| ----------------------- | ------ | --------------------------- | ------------------------------------------------ |
| `DIALOG_TEXT_NEXT_PAGE` | string | "Press SPACE for next page" | Instruction text shown when there are more pages |
| `DIALOG_TEXT_CLOSE`     | string | "Press SPACE to close"      | Instruction text shown on the last page          |
| `DIALOG_TEXT_PAGE`      | string | "Page"                      | Label for page indicator (e.g., "Page 1/3")      |

**Notes:**

- **Auto-close behavior**: `DIALOG_AUTO_CLOSE_DEFAULT` controls whether dialogs auto-close by default. The timer starts after the text reveal animation completes. Useful for cutscenes where you want dialogs to automatically advance.
- **Text reveal animation**: `DIALOG_CHAR_REVEAL_SPEED` controls how fast text appears (characters per second). Set `DIALOG_INSTANT_TEXT_DEFAULT=True` to disable the reveal animation globally, or use the `instant` parameter in `show_dialog()` for specific dialogs.
- **UI toggles**: Use `DIALOG_SHOW_HELP` and `DIALOG_SHOW_PAGINATION` to control which UI elements are displayed. Hiding these can create a cleaner look for cutscenes.
- **Responsive scaling**: The dialog uses responsive UI scaling that adapts to different window sizes
  - Design units are scaled based on window dimensions using `compute_ui_scale()`
  - Scale factor is clamped between `DIALOG_UI_SCALE_MIN` and `DIALOG_UI_SCALE_MAX`
  - Fonts are scaled using `scale_font()` with `UI_FONT_*` tiers for optimal readability
  - All layout dimensions from `DIALOG_DESIGN` are scaled proportionally
- **Font tiers**: The dialog uses the following font tiers:
  - `UI_FONT_LARGE` for NPC name (default: `(16, 22, 30)`)
  - `UI_FONT_NORMAL` for dialog text (default: `(12, 16, 22)`)
  - `UI_FONT_SMALL` for instructions and page indicator (default: `(8, 12, 16)`)
- **Colors**: All color settings use RGB tuples (0-255 for each component)
- **Overlay**: Semi-transparent overlay covers the entire screen behind the dialog. Alpha value of 128 = 50% transparency
- **Input**: `DIALOG_KEY_ADVANCE` can be set to any arcade key constant (e.g., "RETURN", "E", "SPACE"). Keys are matched using the `matches_key()` helper function
- **Localization**: The `DIALOG_TEXT_*` settings allow you to customize instruction text for different languages or game styles
- For more details, see the [DialogPlugin documentation](../plugins/dialog.md)

### Audio Settings

Audio plugin default values for music and sound effects.

| Setting               | Type  | Default | Description                                                    |
| --------------------- | ----- | ------- | -------------------------------------------------------------- |
| `AUDIO_MUSIC_VOLUME`  | float | 0.5     | Default music volume (0.0 = silent, 1.0 = full volume)         |
| `AUDIO_MUSIC_ENABLED` | bool  | True    | Whether music is enabled by default                            |
| `AUDIO_SFX_VOLUME`    | float | 0.7     | Default sound effects volume (0.0 = silent, 1.0 = full volume) |
| `AUDIO_SFX_ENABLED`   | bool  | True    | Whether sound effects are enabled by default                   |

**Notes:**

- These settings control the initial state of the AudioPlugin when it's initialized
- Volume values are clamped to the range 0.0 to 1.0
- Players can change these values at runtime using the AudioPlugin methods
- Changes made at runtime are not persisted unless explicitly saved
- For more details, see the [AudioPlugin documentation](plugins/audio.md)

### Camera Settings

Camera plugin behavior and movement configuration.

| Setting             | Type  | Default | Description                                                  |
| ------------------- | ----- | ------- | ------------------------------------------------------------ |
| `CAMERA_LERP_SPEED` | float | 0.1     | Camera interpolation speed for smooth following (0.0 to 1.0) |

**Notes:**

- `CAMERA_LERP_SPEED` controls how quickly the camera catches up to its target
  - Lower values (e.g., 0.05): Slower, more dramatic camera movement
  - Default (0.1): Smooth, balanced camera following
  - Higher values (e.g., 0.2): More responsive, tighter camera
  - 1.0: Instant following with no smoothing
- The lerp speed determines what fraction of the remaining distance the camera moves each frame
- For more details, see the [CameraPlugin documentation](plugins/camera.md)

### Particle Settings

Particle plugin configuration for visual effects.

| Setting                   | Type                 | Default         | Description                                        |
| ------------------------- | -------------------- | --------------- | -------------------------------------------------- |
| `PARTICLE_ENABLED`        | bool                 | True            | Whether particle effects are enabled by default    |
| `PARTICLE_COLOR_HEARTS`   | tuple[int, int, int] | (255, 105, 180) | Default RGB color for heart particles (hot pink)   |
| `PARTICLE_COLOR_SPARKLES` | tuple[int, int, int] | (255, 255, 100) | Default RGB color for sparkle particles (yellow)   |
| `PARTICLE_COLOR_TRAIL`    | tuple[int, int, int] | (200, 200, 255) | Default RGB color for trail particles (light blue) |
| `PARTICLE_COLOR_BURST`    | tuple[int, int, int] | (255, 200, 0)   | Default RGB color for burst particles (orange)     |

**Notes:**

- `PARTICLE_ENABLED` controls whether particles are active on game start
  - Can be toggled at runtime using `particle_plugin.toggle()`
  - Useful for performance optimization on low-end devices
- Color settings define default colors for each particle type
  - Colors can be overridden per-action using the `color` parameter in scripts
  - RGB values range from 0 to 255
  - Example custom colors:
    - Deep pink hearts: `PARTICLE_COLOR_HEARTS = (255, 20, 147)`
    - Gold sparkles: `PARTICLE_COLOR_SPARKLES = (255, 215, 0)`
    - Green trail: `PARTICLE_COLOR_TRAIL = (0, 255, 100)`
    - Red burst: `PARTICLE_COLOR_BURST = (255, 0, 0)`
- For more details, see the [ParticlePlugin documentation](plugins/particle.md)

### Scene Settings

Scene transition and map loading configuration.

| Setting                       | Type         | Default                                        | Description                                                                  |
| ----------------------------- | ------------ | ---------------------------------------------- | ---------------------------------------------------------------------------- |
| `SCENE_TRANSITION_ALPHA`      | float        | 0.0                                            | Starting alpha value for scene transitions (0.0 = transparent, 1.0 = opaque) |
| `SCENE_TRANSITION_SPEED`      | float        | 3.0                                            | Speed of fade in/out transitions (higher = faster)                           |
| `SCENE_MAPS_FOLDER`           | string       | "maps"                                         | Folder containing Tiled .tmx map files (relative to assets)                  |
| `SCENE_TILEMAP_SCALING`       | float        | 1.0                                            | Scaling factor applied to loaded tile maps                                   |
| `SCENE_COLLISION_LAYER_NAMES` | list[string] | ["Walls", "Collision", "Objects", "Buildings"] | Names of Tiled layers used for collision detection                           |

**Notes:**

- **Transition timing**: The total transition duration is `2.0 / SCENE_TRANSITION_SPEED` seconds
  - Default (3.0): ~0.67 seconds total (~0.33s fade out + ~0.33s fade in)
  - Faster (5.0): ~0.4 seconds total
  - Slower (2.0): ~1.0 second total
  - Very fast (10.0): ~0.2 seconds total
- **Transition alpha**: `SCENE_TRANSITION_ALPHA` controls the starting transparency for transitions
  - 0.0 (default): Starts fully transparent, fades to black
  - Higher values create different effects (not recommended to change)
- **Map folder**: `SCENE_MAPS_FOLDER` is where the ScenePlugin looks for .tmx files
  - Path is relative to the assets directory
  - Example: If `ASSETS_HANDLE` points to "assets/", then "maps" resolves to "assets/maps/"
- **Tilemap scaling**: `SCENE_TILEMAP_SCALING` scales the entire loaded map
  - 1.0 (default): No scaling
  - 2.0: Double size (useful for pixel art)
  - 0.5: Half size
- **Collision layers**: `SCENE_COLLISION_LAYER_NAMES` defines which Tiled layers become collision walls
  - All layers in this list are combined into a single collision wall list
  - Layer names are case-sensitive and must match exactly
  - Order doesn't matter (all layers are combined)
  - Can customize to use fewer or different layer names:

    ```python
    SCENE_COLLISION_LAYER_NAMES = ["Walls"]  # Only use Walls layer
    ```

- For more details, see the [ScenePlugin documentation](plugins/scene.md)

### Debug Settings

Debug plugin configuration for development overlays.

| Setting     | Type | Default | Description                                                    |
| ----------- | ---- | ------- | -------------------------------------------------------------- |
| `TILE_SIZE` | int  | 32      | Size of tiles in pixels (used for tile coordinate calculation) |

**Notes:**

- `TILE_SIZE` is used by the debug plugin to convert pixel coordinates to tile coordinates
  - Debug overlay displays both pixel coordinates and tile coordinates
  - Tile coordinates are calculated as: `tile_x = int(pixel_x / TILE_SIZE)`
- Debug mode is toggled with Shift+D keyboard shortcut
  - Shows player position in tile and pixel coordinates
  - Shows visible NPC positions in tile and pixel coordinates
  - Shows NPC dialog levels
- For more details, see the [DebugPlugin documentation](plugins/debug.md)

### Asset Settings

Asset management configuration.

| Setting             | Type   | Default  | Description                                           |
| ------------------- | ------ | -------- | ----------------------------------------------------- |
| `ASSETS_HANDLE`     | string | "assets" | Arcade resource handle name for referencing assets    |
| `ASSETS_DIRECTORY`  | string | "assets" | Directory name where game assets are stored on disk   |

**Notes:**

- `ASSETS_HANDLE` is the name used to reference assets in code (e.g., `:assets:/maps/file.tmx`)
  - This handle is registered with Arcade's resource system
  - Used with `arcade.resources.resolve()` for asset path resolution
- `ASSETS_DIRECTORY` is the actual folder name on the filesystem
  - Can be different from the handle name if desired
  - Path is relative to the project root directory
  - In PyInstaller bundles, uses the bundled assets directory
- Typically both settings use the same value ("assets"), but can differ for flexibility

### Content Registry Settings

Content registry configuration for loading JSON-defined game data.

| Setting              | Type         | Default          | Description                                                        |
| -------------------- | ------------ | ---------------- | ------------------------------------------------------------------ |
| `CONTENT_DIRECTORY`  | string       | `"data/content"` | Directory where content JSON files are stored (relative to assets) |
| `INSTALLED_CONTENT`  | list[string] | Built-in types   | Modules containing `@ContentTypeRegistry.register` decorators      |

**Notes:**

- `CONTENT_DIRECTORY` is relative to the assets directory
  - Example: If `ASSETS_HANDLE` points to "assets/", then "data/content" resolves to "assets/data/content/"
  - Each registered content type looks for its own JSON file in this directory (e.g., `sprites.json`, `npcs.json`)
- `INSTALLED_CONTENT` controls which content type modules are imported at startup
  - Each module must contain at least one `@ContentTypeRegistry.register`-decorated class
  - To add custom content types, extend the default list:

```python
from pedre.conf import global_settings

INSTALLED_CONTENT = [
    *global_settings.INSTALLED_CONTENT,  # Include built-in types
    "myproject.content.enemies",          # Your custom content types
]
```

- For more details, see the [Custom Content Types guide](../extending/custom-content.md)

### Dialog Plugin Settings

Dialog plugin configuration for NPC dialogs.

| Setting             | Type   | Default         | Description                                                          |
| ------------------- | ------ | --------------- | -------------------------------------------------------------------- |
| `DIALOGS_DIRECTORY` | string | "data/dialogs"  | Directory where NPC dialog files are stored (relative to assets)     |

**Notes:**

- `DIALOGS_DIRECTORY` specifies where the NPCPlugin looks for `*_dialogs.json` files
  - Path is relative to the assets directory
  - Example: If `ASSETS_HANDLE` points to "assets/", then "data/dialogs" resolves to "assets/data/dialogs/"
  - Dialog files are named `{scene}_dialogs.json` (e.g., `village_dialogs.json`)
  - Dialogs are loaded automatically when a scene starts
- For more details, see the [NPCPlugin documentation](../plugins/npc.md)

### Script Plugin Settings

Script plugin configuration for event-driven scripting.

| Setting             | Type   | Default         | Description                                                       |
| ------------------- | ------ | --------------- | ----------------------------------------------------------------- |
| `SCRIPTS_DIRECTORY` | string | "data/scripts"  | Directory where script files are stored (relative to assets)      |

**Notes:**

- `SCRIPTS_DIRECTORY` specifies where the ScriptPlugin looks for `*_scripts.json` files
  - Path is relative to the assets directory
  - Example: If `ASSETS_HANDLE` points to "assets/", then "data/scripts" resolves to "assets/data/scripts/"
  - All script files matching the pattern `*_scripts.json` in this directory are loaded automatically
- Scripts are loaded globally during plugin initialization and made available across all scenes
- The `scene` field in each script definition controls when it can execute
- For more details, see the [ScriptPlugin documentation](../plugins/script.md)

### Save Plugin Settings

Save plugin configuration for game persistence.

| Setting               | Type   | Default    | Description                             |
| --------------------- | ------ | ---------- | --------------------------------------- |
| `SAVE_FOLDER`         | string | "saves"    | Directory where save files are stored   |
| `SAVE_QUICK_SAVE_KEY` | string | "F5"       | Keybind for quick save action           |
| `SAVE_QUICK_LOAD_KEY` | string | "F9"       | Keybind for quick load action           |
| `SAVE_SFX_FILE`       | string | "save.wav" | Sound effect played when saving/loading |

**Notes:**

- `SAVE_FOLDER` specifies the directory path (relative to project root) where save files are stored
  - Directory is created automatically if it doesn't exist
  - Save files are JSON format: `autosave.json`, `save_slot_1.json`, etc.
- `SAVE_QUICK_SAVE_KEY` and `SAVE_QUICK_LOAD_KEY` can be any arcade key constant
  - Common values: "F5", "F6", "F7", "F8", "F9"
  - Keys are matched using the `matches_key()` helper function
  - Quick save uses the auto-save slot (slot 0)
  - Quick load loads from the auto-save slot
- `SAVE_SFX_FILE` is played on successful save/load operations
  - Path is relative to the assets directory
  - Only plays if AudioPlugin is enabled
- For more details, see the [SavePlugin documentation](plugins/save.md)

### Game Settings

Core game settings.

| Setting             | Type         | Default   | Description                                                   |
| ------------------- | ------------ | --------- | ------------------------------------------------------------- |
| `INITIAL_MAP`       | string       | "map.tmx" | Initial Tiled map file to load                                |
| `INSTALLED_PLUGINS` | list[string] | None      | List of plugin modules to load (defaults to all core plugins) |

## Accessing Configuration in Code

Configuration is accessed through `pedre.conf.settings`:

```python
from pedre.conf import settings

# Access settings directly
print(f"Window size: {settings.SCREEN_WIDTH}x{settings.SCREEN_HEIGHT}")
print(f"Player speed: {settings.PLAYER_MOVEMENT_SPEED}")


```

## Example: Complete Configuration

Here's a complete example configuration for a game:

```python
# Window settings
SCREEN_WIDTH=1600
SCREEN_HEIGHT=900
WINDOW_TITLE="Mystic Quest"

# Input settings
PLAYER_MOVEMENT_SPEED=200.0

# Player settings
TILE_SIZE=32
INTERACTION_PLUGIN_DISTANCE=60
INTERACTION_KEY="E"
NPC_INTERACTION_DISTANCE=60
PORTAL_INTERACTION_DISTANCE=60
WAYPOINT_THRESHOLD=2

# NPC settings
NPC_MOVEMENT_SPEED=90.0
NPC_WAYPOINT_THRESHOLD=2
NPC_INTERACTION_KEY="E"

# Inventory settings
INVENTORY_GRID_COLS=12
INVENTORY_GRID_ROWS=5
INVENTORY_MAX_SPACE=60
INVENTORY_DESIGN={
    **INVENTORY_DESIGN,  # Keep defaults
    "box_size": 80,
    "box_spacing": 12,
}
INVENTORY_COLOR_BOX_FILLED=(60, 80, 100)
INVENTORY_COLOR_BOX_BORDER_SELECTED=(100, 200, 255)
INVENTORY_BACKGROUND_IMAGE="images/ui/inventory.png"

# Dialog settings
DIALOG_AUTO_CLOSE_DEFAULT=False
DIALOG_AUTO_CLOSE_DURATION=0.5
DIALOG_KEY_ADVANCE="SPACE"
DIALOG_COLOR_BOX_BACKGROUND=(30, 35, 40)
DIALOG_COLOR_NPC_NAME=(255, 200, 0)
DIALOG_DESIGN={
    "box_width": 900,
    "box_height": 250,
    "npc_name_offset": 40,
}

# Audio settings
AUDIO_MUSIC_VOLUME=0.3
AUDIO_SFX_VOLUME=0.9

# Camera settings
CAMERA_LERP_SPEED=0.15

# Asset settings
ASSETS_HANDLE="mystic_quest_assets"
ASSETS_DIRECTORY="assets"

# Game settings
INITIAL_MAP="starting_village.tmx"
```

## Default Values

If you don't specify a setting, `pedre.conf.settings` uses these defaults:

```python
# Window settings
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
WINDOW_TITLE: str = "Pedre Game"

# Player settings
PLAYER_MOVEMENT_SPEED: float = 180.0
TILE_SIZE: int = 32
INTERACTION_PLUGIN_DISTANCE: int = 50
INTERACTION_KEY: str = "SPACE"
NPC_INTERACTION_DISTANCE: int = 50
PORTAL_INTERACTION_DISTANCE: int = 50
WAYPOINT_THRESHOLD: int = 2

# NPC settings
NPC_MOVEMENT_SPEED: float = 80.0
NPC_WAYPOINT_THRESHOLD: int = 2
NPC_INTERACTION_KEY: str = "SPACE"

# Asset settings
ASSETS_HANDLE: str = "assets"
ASSETS_DIRECTORY: str = "assets"

# Game settings
INITIAL_MAP: str = "map.tmx"

# Scene settings
SCENE_TRANSITION_ALPHA: float = 0.0
SCENE_TRANSITION_SPEED: float = 3.0
SCENE_MAPS_FOLDER: str = "maps"
SCENE_TILEMAP_SCALING: float = 1.0
SCENE_COLLISION_LAYER_NAMES: list[str] = ["Walls", "Collision", "Objects", "Buildings"]

# Inventory settings
INVENTORY_GRID_COLS: int = 4
INVENTORY_GRID_ROWS: int = 3
INVENTORY_MAX_SPACE: int = 12
INVENTORY_DESIGN: dict[str, int | float] = {
    "box_size": 100,
    "box_spacing": 15,
    "box_border_width": 3,
    "overlay_height_fraction": 0.5,
    "item_name_y_offset": 30,
    "hint_y_offset": 10,
    "capacity_x_offset": 10,
    "capacity_y_offset": 10,
    "grid_y_offset": 20,
    "photo_title_y_offset": 90,
    "photo_description_y_offset": 60,
    "photo_max_width_fraction": 0.7,
    "photo_max_height_fraction": 0.7,
    "photo_text_area_height": 120,
    "icon_padding": 4,
}
INVENTORY_UI_SCALE_MIN: float = 0.5
INVENTORY_UI_SCALE_MAX: float = 2.0
INVENTORY_BACKGROUND_IMAGE: str = ""
INVENTORY_ITEMS_FILE: str = "data/inventory_items.json"
INVENTORY_KEY_TOGGLE: str = "I"
INVENTORY_KEY_VIEW: str = "V"
INVENTORY_KEY_CONSUME: str = "C"
INVENTORY_HINT_VIEW: str = "[V] View"
INVENTORY_HINT_CONSUME: str = "[C] Consume"
INVENTORY_COLOR_OVERLAY: tuple[int, int, int] = (0, 0, 0)
INVENTORY_OVERLAY_ALPHA: int = 200
INVENTORY_COLOR_BOX_FILLED: tuple[int, int, int] = (47, 79, 79)
INVENTORY_COLOR_BOX_EMPTY: tuple[int, int, int] = (30, 30, 35)
INVENTORY_EMPTY_BOX_ALPHA: int = 180
INVENTORY_COLOR_BOX_BORDER: tuple[int, int, int] = (255, 255, 255)
INVENTORY_COLOR_BOX_BORDER_SELECTED: tuple[int, int, int] = (255, 255, 0)
INVENTORY_COLOR_BOX_BORDER_EMPTY: tuple[int, int, int] = (105, 105, 105)
INVENTORY_COLOR_TEXT_ITEM_NAME: tuple[int, int, int] = (255, 255, 255)
INVENTORY_COLOR_TEXT_HINT: tuple[int, int, int] = (211, 211, 211)
INVENTORY_COLOR_TEXT_CAPACITY: tuple[int, int, int] = (255, 255, 255)
INVENTORY_COLOR_TEXT_PHOTO_TITLE: tuple[int, int, int] = (255, 255, 255)
INVENTORY_COLOR_TEXT_PHOTO_DESCRIPTION: tuple[int, int, int] = (211, 211, 211)
INVENTORY_COLOR_PHOTO_BACKGROUND: tuple[int, int, int] = (0, 0, 0)

# Dialog settings
DIALOG_AUTO_CLOSE_DEFAULT: bool = False
DIALOG_AUTO_CLOSE_DURATION: float = 0.5
DIALOG_CHAR_REVEAL_SPEED: int = 20
DIALOG_INSTANT_TEXT_DEFAULT: bool = False
DIALOG_KEY_ADVANCE: str = "SPACE"
DIALOG_SHOW_HELP: bool = True
DIALOG_SHOW_PAGINATION: bool = True
DIALOG_TEXT_NEXT_PAGE: str = "Press SPACE for next page"
DIALOG_TEXT_CLOSE: str = "Press SPACE to close"
DIALOG_TEXT_PAGE: str = "Page"
DIALOG_DESIGN: dict = {
    "box_width": 800,
    "box_height": 200,
    "border_width": 3,
    "horizontal_padding": 20,
    "vertical_padding": 20,
    "npc_name_offset": 30,
    "footer_offset": 20,
    "vertical_position": 0.25,
}
DIALOG_UI_SCALE_MIN: float = 0.5
DIALOG_UI_SCALE_MAX: float = 2.0
DIALOG_OVERLAY_ALPHA: int = 128
DIALOG_COLOR_BOX_BACKGROUND: tuple[int, int, int] = (45, 52, 54)
DIALOG_COLOR_BOX_BORDER: tuple[int, int, int] = (255, 255, 255)
DIALOG_COLOR_NPC_NAME: tuple[int, int, int] = (255, 255, 0)
DIALOG_COLOR_TEXT: tuple[int, int, int] = (255, 255, 255)
DIALOG_COLOR_INSTRUCTION: tuple[int, int, int] = (211, 211, 211)
DIALOG_COLOR_PAGE_INDICATOR: tuple[int, int, int] = (211, 211, 211)

# Audio settings
AUDIO_MUSIC_VOLUME: float = 0.5
AUDIO_MUSIC_ENABLED: bool = True
AUDIO_SFX_VOLUME: float = 0.7
AUDIO_SFX_ENABLED: bool = True

# Camera settings
CAMERA_LERP_SPEED: float = 0.1

# Particle settings
PARTICLE_ENABLED: bool = True
PARTICLE_COLOR_HEARTS: tuple[int, int, int] = (255, 105, 180)
PARTICLE_COLOR_SPARKLES: tuple[int, int, int] = (255, 255, 100)
PARTICLE_COLOR_TRAIL: tuple[int, int, int] = (200, 200, 255)
PARTICLE_COLOR_BURST: tuple[int, int, int] = (255, 200, 0)

# Dialog plugin settings
DIALOGS_DIRECTORY: str = "data/dialogs"

# Script plugin settings
SCRIPTS_DIRECTORY: str = "data/scripts"

# Save plugin settings
SAVE_FOLDER: str = "saves"
SAVE_QUICK_SAVE_KEY: str = "F5"
SAVE_QUICK_LOAD_KEY: str = "F9"
SAVE_SFX_FILE: str = "save.wav"

# Pause menu settings
PAUSE_MENU_OVERLAY_ALPHA: int = 180
PAUSE_MENU_TITLE: str = "Pedre Game"
PAUSE_MENU_DESIGN: dict = {
    "box_width": 500,
    "box_height": 400,
    "border_width": 4,
    "title_padding": 20,
    "title_area_height": 80,
    "horizontal_padding": 40,
    "spacing": 50,
    "content_bottom_padding": 20,
    "confirmation_message_offset": 50,
    "confirmation_options_offset": 30,
    "feedback_offset": 50,
}
PAUSE_MENU_UI_SCALE_MIN: float = 0.5
PAUSE_MENU_UI_SCALE_MAX: float = 2.0
PAUSE_MENU_TEXT_RESUME: str = "Resume"
PAUSE_MENU_TEXT_NEW_GAME: str = "New Game"
PAUSE_MENU_TEXT_LOAD_GAME: str = "Load Game"
PAUSE_MENU_TEXT_SAVE_GAME: str = "Save Game"
PAUSE_MENU_TEXT_EXIT: str = "Exit Game"
PAUSE_MENU_TEXT_BACK: str = "Back"
PAUSE_MENU_TEXT_EMPTY_SLOT: str = "(Empty)"
PAUSE_MENU_CONFIRM_NEW_GAME: str = "Start a new game? Current progress will be lost."
PAUSE_MENU_COLOR_OVERLAY: tuple[int, int, int] = (0, 0, 0)
PAUSE_MENU_COLOR_BOX_BACKGROUND: tuple[int, int, int] = (102, 102, 153)
PAUSE_MENU_COLOR_BOX_BORDER: tuple[int, int, int] = (255, 255, 255)
PAUSE_MENU_COLOR_TITLE: tuple[int, int, int] = (255, 255, 255)
PAUSE_MENU_COLOR_OPTION: tuple[int, int, int] = (255, 255, 255)
PAUSE_MENU_COLOR_SELECTED: tuple[int, int, int] = (255, 255, 0)
PAUSE_MENU_COLOR_DISABLED: tuple[int, int, int] = (128, 128, 128)
PAUSE_MENU_COLOR_FEEDBACK: tuple[int, int, int] = (0, 255, 0)
```

## See Also

- [Getting Started Guide](../getting-started.md) - Build your first RPG
- [API Reference](../api/index.md) - API Reference
