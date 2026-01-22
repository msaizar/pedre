# SystemLoader

The `SystemLoader` is responsible for dynamically loading, initializing, and managing the lifecycle of game systems.

## Location

`src/pedre/systems/loader.py`

## Overview

The loader implements a dependency injection pattern where systems declare their dependencies and the loader ensures they are initialized in the correct order.

## Key Methods

### `instantiate_all() -> dict[str, BaseSystem]`

Creates instances of all registered systems.

- Resolves dependencies using topological sort
- Detects circular dependencies
- Returns dictionary of instantiated systems

### `setup_all(context: GameContext)`

Calls `setup()` on all systems in dependency order. This is where systems should initialize their state and subscribe to events.

### `reset_all(context: GameContext)`

Resets all systems to their initial state for a new game session.

- Clears transient state (items, flags, etc.)
- Preserves persistent wiring (event bus connections)
- Called when starting a new game

### `cleanup_all()`

Calls `cleanup()` on all systems in reverse dependency order.

## Usage

```python
from pedre.systems.loader import SystemLoader

# Initialize loader
loader = SystemLoader(settings)

# Instantiate systems
systems = loader.instantiate_all()

# Setup with context
loader.setup_all(game_context)

# In game loop
loader.update_all(delta_time, game_context)

# Start new game
loader.reset_all(game_context)
```
