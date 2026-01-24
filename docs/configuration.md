# Configuration Guide

Pedre uses the `settings.py` file for configuration.

## Configuration Overview

Configure your game by creating a `settings.py` file in your project root:

```python

SCREEN_WIDTH=1280
SCREEN_HEIGHT=720
WINDOW_TITLE="My RPG Game"
PLAYER_MOVEMENT_SPEED=3
TILE_SIZE=32
INTERACTION_MANAGER_DISTANCE=50
NPC_INTERACTION_DISTANCE=50
PORTAL_INTERACTION_DISTANCE=50
WAYPOINT_THRESHOLD=2
NPC_SPEED=80.0
MENU_TITLE="My RPG Game"
MENU_TITLE_SIZE=48
MENU_OPTION_SIZE=24
MENU_SPACING=50
MENU_BACKGROUND_IMAGE="images/backgrounds/menu.png"
MENU_MUSIC_FILES=["menu_music.ogg"]
INVENTORY_GRID_COLS=10
INVENTORY_GRID_ROWS=4
INVENTORY_BOX_SIZE=30
INVENTORY_BOX_SPACING=5
INVENTORY_BOX_BORDER_WIDTH=1
INVENTORY_BACKGROUND_IMAGE=""
DIALOG_AUTO_CLOSE_DEFAULT=False
DIALOG_AUTO_CLOSE_DURATION=0.5
ASSETS_HANDLE="game_assets"
INITIAL_MAP="start.tmx"
```

## Configuration Settings

### Window Settings

Control window and display properties.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `SCREEN_WIDTH` | int | 1280 | Window width in pixels |
| `SCREEN_HEIGHT` | int | 720 | Window height in pixels |
| `WINDOW_TITLE` | string | "Pedre Game" | Window title text |

### Player Settings

Player character movement and interaction settings.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `PLAYER_MOVEMENT_SPEED` | int | 3 | Player movement speed in pixels per frame |
| `TILE_SIZE` | int | 32 | Base tile size for grid-based movement |
| `INTERACTION_MANAGER_DISTANCE` | int | 50 | Maximum distance for player to interact with objects |
| `NPC_INTERACTION_DISTANCE` | int | 50 | Maximum distance for player to interact with NPCs |
| `PORTAL_INTERACTION_DISTANCE` | int | 50 | Maximum distance for player to activate portals |
| `WAYPOINT_THRESHOLD` | int | 2 | Distance threshold to consider waypoint reached |

**Notes:**

- `PLAYER_MOVEMENT_SPEED` affects how fast the player moves when clicking to move
- `INTERACTION_MANAGER_DISTANCE` determines how close the player must be to interact with objects
- `NPC_INTERACTION_DISTANCE` determines how close the player must be to interact with NPCs
- `PORTAL_INTERACTION_DISTANCE` determines how close the player must be to activate portals
- `WAYPOINT_THRESHOLD` controls pathfinding precision (lower = more precise)

### NPC Settings

NPC behavior settings.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `NPC_SPEED` | float | 80.0 | NPC movement speed in pixels per second |

**Notes:**

- This is the default speed for all NPCs
- Individual NPCs can override this in their sprite initialization

### Menu Settings

Main menu appearance and behavior.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `MENU_TITLE` | string | "Pedre Game" | Menu title text |
| `MENU_TITLE_SIZE` | int | 48 | Font size for the title |
| `MENU_OPTION_SIZE` | int | 24 | Font size for menu options |
| `MENU_SPACING` | int | 50 | Vertical spacing between menu options |
| `MENU_BACKGROUND_IMAGE` | string | "" | Path to background image (relative to assets handle) |
| `MENU_MUSIC_FILES` | list[string] | [] | Music files to preload before game start |
| `MENU_TEXT_CONTINUE` | string | "Continue" | Text for Continue option |
| `MENU_TEXT_NEW_GAME` | string | "New Game" | Text for New Game option |
| `MENU_TEXT_SAVE_GAME` | string | "Save Game" | Text for Save Game option |
| `MENU_TEXT_LOAD_GAME` | string | "Load Game" | Text for Load Game option |
| `MENU_TEXT_EXIT` | string | "Exit" | Text for Exit option |

**Notes:**

- `menu_background_image` is optional; leave empty for solid color background
- All paths are relative to the assets resource handle

### Inventory Settings

Inventory grid layout and appearance.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `INVENTORY_GRID_COLS` | int | 4 | Number of columns in inventory grid |
| `INVENTORY_GRID_ROWS` | int | 3 | Number of rows in inventory grid |
| `INVENTORY_BOX_SIZE` | int | 100 | Size of each inventory slot in pixels |
| `INVENTORY_BOX_SPACING` | int | 15 | Spacing between inventory slots |
| `INVENTORY_BOX_BORDER_WIDTH` | int | 3 | Border width for inventory slots |
| `INVENTORY_BACKGROUND_IMAGE` | string | "" | Path to background image (optional) |

**Notes:**

- Total inventory capacity = `inventory_grid_cols` × `inventory_grid_rows`
- `inventory_background_image` is optional; leave empty for default background

### Dialog Settings

Dialog system behavior and timing.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `DIALOG_AUTO_CLOSE_DEFAULT` | bool | False | Default auto-close behavior for dialogs when not explicitly specified |
| `DIALOG_AUTO_CLOSE_DURATION` | float | 0.5 | Seconds to wait after text is fully revealed before auto-closing |

**Notes:**

- `DIALOG_AUTO_CLOSE_DEFAULT` controls whether dialogs auto-close by default (when `auto_close` parameter is not specified)
- `DIALOG_AUTO_CLOSE_DURATION` only applies when auto-close is enabled for a dialog
- The timer starts after the text reveal animation completes
- Useful for cutscenes where you want dialogs to automatically advance

### Asset Settings

Asset management configuration.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `ASSETS_HANDLE` | string | "game_assets" | Arcade resource handle name for assets directory |

**Notes:**

- This handle is registered with Arcade's resource system
- Used to load assets with `arcade.resources.resolve()`
- Should match the handle used when registering your assets directory

### Game Settings

Core game settings.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `INITIAL_MAP` | string | "map.tmx" | Initial Tiled map file to load |
| `INSTALLED_SYSTEMS` | list[string] | None | List of system modules to load (defaults to all core systems) |

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

# Player settings
PLAYER_MOVEMENT_SPEED=4
TILE_SIZE=32
INTERACTION_MANAGER_DISTANCE=60
NPC_INTERACTION_DISTANCE=60
PORTAL_INTERACTION_DISTANCE=60
WAYPOINT_THRESHOLD=2

# NPC settings
NPC_SPEED=90.0

# Menu settings
MENU_TITLE="Mystic Quest"
MENU_TITLE_SIZE=56
MENU_OPTION_SIZE=28
MENU_SPACING=55
MENU_BACKGROUND_IMAGE="images/backgrounds/mystic.png"
MENU_MUSIC_FILES=["music/menu1.ogg", "music/menu2.ogg"]

# Inventory settings
INVENTORY_GRID_COLS=12
INVENTORY_GRID_ROWS=5
INVENTORY_BOX_SIZE=35
INVENTORY_BOX_SPACING=6
INVENTORY_BOX_BORDER_WIDTH=2
INVENTORY_BACKGROUND_IMAGE="images/ui/inventory.png"

# Dialog settings
DIALOG_AUTO_CLOSE_DEFAULT=False
DIALOG_AUTO_CLOSE_DURATION=0.5

# Asset settings
ASSETS_HANDLE="mystic_quest_assets"

# Game settings
INITIAL_MAP="starting_village.tmx"
```

## Default Values

If you don't specify a setting, `pedre.conf.settings` uses these defaults:

```python
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
WINDOW_TITLE: str = "Pedre Game"
MENU_TITLE: str = "Pedre Game"
MENU_TITLE_SIZE: int = 48
MENU_OPTION_SIZE: int = 24
MENU_SPACING: int = 50
MENU_BACKGROUND_IMAGE: str = ""
MENU_MUSIC_FILES: list[str] = []
PLAYER_MOVEMENT_SPEED: int = 3
TILE_SIZE: int = 32
INTERACTION_MANAGER_DISTANCE: int = 50
NPC_INTERACTION_DISTANCE: int = 50
PORTAL_INTERACTION_DISTANCE: int = 50
WAYPOINT_THRESHOLD: int = 2
NPC_SPEED: float = 80.0
ASSETS_HANDLE: str = "game_assets"
INITIAL_MAP: str = "map.tmx"
INVENTORY_GRID_COLS: int = 4
INVENTORY_GRID_ROWS: int = 3
INVENTORY_BOX_SIZE: int = 100
INVENTORY_BOX_SPACING: int = 15
INVENTORY_BOX_BORDER_WIDTH: int = 3
INVENTORY_BACKGROUND_IMAGE: str = ""
DIALOG_AUTO_CLOSE_DEFAULT: bool = False
DIALOG_AUTO_CLOSE_DURATION: float = 0.5
```

## See Also

- [Getting Started Guide](getting-started.md) - Build your first RPG
- [API Reference](api-reference.md) - Core classes and methods
