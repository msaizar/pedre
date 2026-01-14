# Configuration Guide

Pedre uses the `GameSettings` dataclass for configuration.

## Configuration Overview

Configure your game by creating a `GameSettings` object and passing it to `run_game()`:

```python
from pedre import run_game, GameSettings

settings = GameSettings(
    screen_width=1280,
    screen_height=720,
    window_title="My RPG Game",
    player_movement_speed=3,
    tile_size=32,
    interaction_manager_distance=50,
    npc_interaction_distance=50,
    portal_interaction_distance=50,
    waypoint_threshold=2,
    npc_speed=80.0,
    menu_title="My RPG Game",
    menu_title_size=48,
    menu_option_size=24,
    menu_spacing=50,
    menu_background_image="images/backgrounds/menu.png",
    menu_music_files=["menu_music.ogg"],
    inventory_grid_cols=10,
    inventory_grid_rows=4,
    inventory_box_size=30,
    inventory_box_spacing=5,
    inventory_box_border_width=1,
    inventory_background_image="",
    assets_handle="game_assets",
    initial_map="start.tmx"
)

if __name__ == "__main__":
    run_game(settings)
```

## Configuration Settings

### Window Settings

Control window and display properties.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `screen_width` | int | 1280 | Window width in pixels |
| `screen_height` | int | 720 | Window height in pixels |
| `window_title` | string | "Pedre Game" | Window title text |

**Example:**

```python
settings = GameSettings(
    screen_width=1920,
    screen_height=1080,
    window_title="My Epic Adventure"
)
```

### Player Settings

Player character movement and interaction settings.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `player_movement_speed` | int | 3 | Player movement speed in pixels per frame |
| `tile_size` | int | 32 | Base tile size for grid-based movement |
| `interaction_manager_distance` | int | 50 | Maximum distance for player to interact with objects |
| `npc_interaction_distance` | int | 50 | Maximum distance for player to interact with NPCs |
| `portal_interaction_distance` | int | 50 | Maximum distance for player to activate portals |
| `waypoint_threshold` | int | 2 | Distance threshold to consider waypoint reached |

**Example:**

```python
settings = GameSettings(
    player_movement_speed=5,
    tile_size=16,
    interaction_manager_distance=64,
    npc_interaction_distance=64,
    portal_interaction_distance=64,
    waypoint_threshold=1
)
```

**Notes:**

- `player_movement_speed` affects how fast the player moves when clicking to move
- `interaction_manager_distance` determines how close the player must be to interact with objects
- `npc_interaction_distance` determines how close the player must be to interact with NPCs
- `portal_interaction_distance` determines how close the player must be to activate portals
- `waypoint_threshold` controls pathfinding precision (lower = more precise)

### NPC Settings

NPC behavior settings.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `npc_speed` | float | 80.0 | NPC movement speed in pixels per second |

**Example:**

```python
settings = GameSettings(
    npc_speed=100.0
)
```

**Notes:**

- This is the default speed for all NPCs
- Individual NPCs can override this in their sprite initialization

### Menu Settings

Main menu appearance and behavior.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `menu_title` | string | "Pedre Game" | Menu title text |
| `menu_title_size` | int | 48 | Font size for the title |
| `menu_option_size` | int | 24 | Font size for menu options |
| `menu_spacing` | int | 50 | Vertical spacing between menu options |
| `menu_background_image` | string | "" | Path to background image (relative to assets handle) |
| `menu_music_files` | list[string] | [] | List of music files to play randomly in menu |

**Example:**

```python
settings = GameSettings(
    menu_title="Dragon Quest",
    menu_title_size=64,
    menu_option_size=32,
    menu_spacing=60,
    menu_background_image="images/backgrounds/castle.png",
    menu_music_files=["menu_theme.ogg", "ambient.ogg"]
)
```

**Notes:**

- `menu_background_image` is optional; leave empty for solid color background
- `menu_music_files` will be shuffled and played randomly
- All paths are relative to the assets resource handle

### Inventory Settings

Inventory grid layout and appearance.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `inventory_grid_cols` | int | 4 | Number of columns in inventory grid |
| `inventory_grid_rows` | int | 3 | Number of rows in inventory grid |
| `inventory_box_size` | int | 100 | Size of each inventory slot in pixels |
| `inventory_box_spacing` | int | 15 | Spacing between inventory slots |
| `inventory_box_border_width` | int | 3 | Border width for inventory slots |
| `inventory_background_image` | string | "" | Path to background image (optional) |

**Example:**

```python
settings = GameSettings(
    inventory_grid_cols=8,
    inventory_grid_rows=5,
    inventory_box_size=40,
    inventory_box_spacing=8,
    inventory_box_border_width=2,
    inventory_background_image="images/ui/inventory_bg.png"
)
```

**Notes:**

- Total inventory capacity = `inventory_grid_cols` × `inventory_grid_rows`
- `inventory_background_image` is optional; leave empty for default background

### Asset Settings

Asset management configuration.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `assets_handle` | string | "game_assets" | Arcade resource handle name for assets directory |

**Example:**

```python
settings = GameSettings(
    assets_handle="my_game_assets"
)
```

**Notes:**

- This handle is registered with Arcade's resource system
- Used to load assets with `arcade.resources.resolve()`
- Should match the handle used when registering your assets directory

### Game Settings

Core game settings.

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `initial_map` | string | "map.tmx" | Initial Tiled map file to load |

**Example:**

```python
settings = GameSettings(
    initial_map="village.tmx"
)
```

**Notes:**

- Path is relative to your assets directory
- Must be a valid Tiled `.tmx` file

## Accessing Configuration in Code

Configuration is accessed through the `GameSettings` object you create:

```python
from pedre import run_game, GameSettings

settings = GameSettings(
    screen_width=1280,
    screen_height=720,
    player_movement_speed=3,
    interaction_manager_distance=50,
    npc_interaction_distance=50,
    portal_interaction_distance=50
)

# Access settings directly
print(f"Window size: {settings.screen_width}x{settings.screen_height}")
print(f"Player speed: {settings.player_movement_speed}")

if __name__ == "__main__":
    run_game(settings)
```

## Example: Complete Configuration

Here's a complete example configuration for a game:

```python
from pedre import run_game, GameSettings

settings = GameSettings(
    # Window settings
    screen_width=1600,
    screen_height=900,
    window_title="Mystic Quest",

    # Player settings
    player_movement_speed=4,
    tile_size=32,
    interaction_manager_distance=60,
    npc_interaction_distance=60,
    portal_interaction_distance=60,
    waypoint_threshold=2,

    # NPC settings
    npc_speed=90.0,

    # Menu settings
    menu_title="Mystic Quest",
    menu_title_size=56,
    menu_option_size=28,
    menu_spacing=55,
    menu_background_image="images/backgrounds/mystic.png",
    menu_music_files=["music/menu1.ogg", "music/menu2.ogg"],

    # Inventory settings
    inventory_grid_cols=12,
    inventory_grid_rows=5,
    inventory_box_size=35,
    inventory_box_spacing=6,
    inventory_box_border_width=2,
    inventory_background_image="images/ui/inventory.png",

    # Asset settings
    assets_handle="mystic_quest_assets",

    # Game settings
    initial_map="starting_village.tmx"
)

if __name__ == "__main__":
    run_game(settings)
```

## Default Values

If you don't specify a setting, `GameSettings` uses these defaults:

```python
screen_width: int = 1280
screen_height: int = 720
window_title: str = "Pedre Game"
menu_title: str = "Pedre Game"
menu_title_size: int = 48
menu_option_size: int = 24
menu_spacing: int = 50
menu_background_image: str = ""
menu_music_files: list[str] = []
player_movement_speed: int = 3
tile_size: int = 32
interaction_manager_distance: int = 50
npc_interaction_distance: int = 50
portal_interaction_distance: int = 50
waypoint_threshold: int = 2
npc_speed: float = 80.0
assets_handle: str = "game_assets"
initial_map: str = "map.tmx"
inventory_grid_cols: int = 4
inventory_grid_rows: int = 3
inventory_box_size: int = 100
inventory_box_spacing: int = 15
inventory_box_border_width: int = 3
inventory_background_image: str = ""
```

## See Also

- [Getting Started Guide](getting-started.md) - Build your first RPG
- [API Reference](api-reference.md) - Core classes and methods
