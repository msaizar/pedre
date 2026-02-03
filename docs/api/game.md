# Game

Central coordinator for game lifecycle and plugin initialization.

## Location

[src/pedre/game.py](https://github.com/msaizar/pedre/blob/main/src/pedre/game.py)

## Overview

The Game class coordinates the game's lifecycle, handling plugin initialization, GameView management, and core game operations. It owns long-lived objects like EventBus, GameContext, and PluginLoader that persist throughout the game's lifetime.

## Constructor

```python
from pedre.game import Game

game = Game(window)
```

**Parameters:**

- `window: arcade.Window` - The Arcade window instance

## Methods

### Game Lifecycle

#### start_new_game

`start_new_game() -> None`

Start a new game with fresh state.

Cleans up and discards any existing game view to ensure a fresh start. This is different from `show_game()` which reuses the cached game view.

**Example:**

```python
game.start_new_game()
```

#### start_game_or_load

`start_game_or_load() -> None`

Start game directly, loading autosave if exists, otherwise new game.

Provides a streamlined startup experience that bypasses the main menu:

- If autosave (slot 0) exists: Load it automatically
- Otherwise: Start a fresh new game

**Example:**

```python
game.start_game_or_load()
```

#### continue_game

`continue_game() -> None`

Continue/resume the game.

If a game view already exists (player paused with ESC), simply resume it without any reload. Otherwise, load the auto-save file and restore state.

**Example:**

```python
game.continue_game()
```

#### show_game

`show_game() -> None`

Show the game view.

Displays the gameplay view in the window. Creates the GameView lazily if it doesn't exist yet.

**Example:**

```python
game.show_game()
```

#### load_game

`load_game(save_data: GameSaveData) -> None`

Load a game from save data.

Creates a fresh game view and restores the complete game state from the save data, including player position, NPC dialog levels, inventory contents, and more.

**Parameters:**

- `save_data: GameSaveData` - Save data to restore

**Example:**

```python
from pedre.plugins.save.base import GameSaveData

save_data = save_plugin.load_game(slot=1)
if save_data:
    game.load_game(save_data)
```

#### exit_game

`exit_game() -> None`

Close window and exit.

Performs auto-save and cleanup of the game view before closing the window.

**Example:**

```python
game.exit_game()
```

## Properties

### game_view

`game_view: GameView`

Get or create the game view (lazy initialization).

Returns the cached GameView instance, or creates a new one if this is the first access.

**Example:**

```python
view = game.game_view
```

### game_context

`game_context: GameContext`

The game context providing access to all plugins.

**Example:**

```python
context = game.game_context
dialog_plugin = context.get_plugin("dialog")
```

### event_bus

`event_bus: EventBus`

The central event bus for publish/subscribe communication.

**Example:**

```python
bus = game.event_bus
bus.publish(CustomEvent())
```

### plugin_loader

`plugin_loader: PluginLoader`

The plugin loader for managing plugin lifecycle.

**Example:**

```python
loader = game.plugin_loader
```

## Methods (Checking State)

### has_game_view

`has_game_view() -> bool`

Check if a game view exists without creating one.

**Returns:**

- `bool` - True if game view has been created, False otherwise

**Example:**

```python
if game.has_game_view():
    print("Game view exists")
```

## Architecture Notes

- **Only ONE view exists**: GameView (the "pause menu" is a plugin overlay, not a view)
- **No view transitions**: This coordinates game state, not multiple screens
- **Long-lived objects**: EventBus, GameContext, and PluginLoader outlive individual GameView instances
- **Plugin initialization order**: Actions → Events → Conditions → Plugins
- **GameView lifecycle**: Can be recreated for new games or loaded games

## See Also

- [Views](views.md) - GameView documentation
- [GameContext](game-context.md) - Shared state container
- [EventBus](event-bus.md) - Event system
- [Getting Started Guide](../getting-started.md) - Build your first RPG
