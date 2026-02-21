# PluginLoader

The `PluginLoader` is responsible for dynamically loading, initializing, and managing the lifecycle of game plugins.

## Location

[src/pedre/plugins/loader.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/loader.py)

## Overview

The loader implements a dependency injection pattern where plugins declare their dependencies and the loader ensures they are initialized in the correct order.

## Key Methods

### instantiate_all

`instantiate_all() -> dict[str, BasePlugin]`

Creates instances of all registered plugins.

- Resolves dependencies using topological sort
- Detects circular dependencies
- Returns dictionary of instantiated plugins

### setup_all

`setup_all(context: GameContext) -> None`

Calls `setup()` on all plugins in dependency order. This is where plugins should initialize their state and subscribe to events.

### reset_all

`reset_all() -> None`

Resets all plugins to their initial state for a new game session.

- Clears transient state (items, flags, etc.)
- Preserves persistent wiring (event bus connections)
- Called when starting a new game

### cleanup_all

`cleanup_all() -> None`

Calls `cleanup()` on all plugins in reverse dependency order.

## Usage

```python
from pedre.plugins.loader import PluginLoader

# Initialize loader
loader = PluginLoader(settings)

# Instantiate plugins
plugins = loader.instantiate_all()

# Setup with context
loader.setup_all(game_context)

# In game loop
loader.update_all(delta_time)

# Start new game
loader.reset_all()
```
