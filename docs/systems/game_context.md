# GameContext

The `GameContext` serves as a central registry and state container for the game. It is passed to all systems and actions, providing access to shared resources and other systems.

## Location

`src/pedre/systems/game_context.py`

## Overview

Unlike a global singleton, `GameContext` is explicitly passed to methods that need it. This promotes testability and clear dependency management.

## Key Attributes

- **event_bus**: Central event system (`EventBus`)
- **player_sprite**: Reference to the player's sprite
- **current_scene**: Name of the active map/scene
- **wall_list**: Collision sprites for the current map
- **waypoints**: Named locations on the map
- **interacted_objects**: Set of object IDs the player has interacted with

## Key Methods

### `get_system(name: str) -> BaseSystem | None`

Retrieve a registered system by its name.

```python
dialog_manager = context.get_system("dialog")
if dialog_manager:
    dialog_manager.show_dialog("Hello!")
```

### `update_player(player_sprite)`

Update the reference to the player sprite (e.g., after spawning).

### `update_scene(scene_name)`

Update the current scene identifier.

## Usage in Systems

```python
def update(self, delta_time, context: GameContext):
    # Access other systems
    audio = context.get_system("audio")

    # Access game state
    player = context.player_sprite
```
