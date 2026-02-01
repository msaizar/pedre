# GameContext

The `GameContext` serves as a central registry and state container for the game. It is passed to all systems and actions, providing access to shared resources and other systems.

## Location

[src/pedre/systems/game_context.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/game_context.py)

## Overview

Unlike a global singleton, `GameContext` is explicitly passed to methods that need it. This promotes testability and clear dependency management.

## Key Attributes

- **event_bus**: Central event system (`EventBus`)

## Key Methods

### get_system

`get_system(name: str) -> BaseSystem | None`

Retrieve a registered system by its name.

```python
dialog_manager = context.get_system("dialog")
if dialog_manager:
    dialog_manager.show_dialog("Hello!")
```

## Usage in Systems

```python
def update(self, delta_time):
    # Access other systems
    audio = self.context.get_system("audio")
```
