# ViewManager

Central controller for all game views and screen transitions.

## Location

[src/pedre/view_manager.py](../../src/pedre/view_manager.py)

## Overview

The ViewManager orchestrates transitions between different game screens (menu, gameplay, save/load) and manages the game loop lifecycle. It serves as the entry point for scene changes and game state management.

## Constructor

```python
from pedre import ViewManager

view_manager = ViewManager(window)
```

**Parameters:**

- `window: arcade.Window` - The Arcade window instance

## Methods

### View Transitions

#### show_menu

`show_menu(*, from_game_pause: bool = False) -> None`

Switch to menu view.

**Parameters:**

- `from_game_pause` (bool, optional) - Whether transitioning from paused game (default: False)

**Example:**

```python
view_manager.show_menu()
```

#### show_game

`show_game(*, trigger_post_inventory_dialog: bool = False) -> None`

Switch to game view.

**Parameters:**

- `trigger_post_inventory_dialog` (bool, optional) - Whether to trigger post-inventory dialog event (default: False)

**Example:**

```python
view_manager.show_game()
```

#### show_load_game

`show_load_game() -> None`

Switch to load game view.

**Example:**

```python
view_manager.show_load_game()
```

#### show_save_game

`show_save_game() -> None`

Switch to save game view.

**Example:**

```python
view_manager.show_save_game()
```

### Game State Management

#### continue_game

`continue_game() -> None`

Resume or load auto-save.

**Example:**

```python
view_manager.continue_game()
```

#### load_game

`load_game(save_data: GameSaveData) -> None`

Load game from save data.

**Parameters:**

- `save_data: GameSaveData` - Save data to restore

**Example:**

```python
from pedre.systems.save.base import GameSaveData

save_data = save_manager.load_game(slot=1)
if save_data:
    view_manager.load_game(save_data)
```

#### exit_game

`exit_game() -> None`

Close window and exit.

**Example:**

```python
view_manager.exit_game()
```

### Map Loading

#### load_map

`load_map(map_name: str, spawn_waypoint: str | None = None) -> None`

Request map load via SceneManager.

**Parameters:**

- `map_name` (str) - Name of the map file (e.g., "forest.tmx")
- `spawn_waypoint` (str | None) - Optional waypoint name for player spawn position

**Example:**

```python
view_manager.load_map("village.tmx", spawn_waypoint="from_forest")
```

## Properties

### menu_view

`menu_view: MenuView`

Get or create menu view (lazy-loaded).

**Example:**

```python
menu = view_manager.menu_view
```

### game_view

`game_view: GameView`

Get or create game view (lazy-loaded).

**Example:**

```python
game = view_manager.game_view
```

### load_game_view

`load_game_view: LoadGameView`

Get or create load game view (lazy-loaded).

**Example:**

```python
load_view = view_manager.load_game_view
```

### save_game_view

`save_game_view: SaveGameView`

Get or create save game view (lazy-loaded).

**Example:**

```python
save_view = view_manager.save_game_view
```

## See Also

- [Views](views.md) - GameView, MenuView, LoadGameView, SaveGameView documentation
- [GameContext](game-context.md) - Shared state container
- [Getting Started Guide](../getting-started.md) - Build your first RPG
