# GameContext

The `GameContext` serves as a central registry and state container for the game. It is passed to all plugins and actions, providing access to shared resources and other plugins.

## Location

[src/pedre/plugins/game_context.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/game_context.py)

## Overview

Unlike a global singleton, `GameContext` is explicitly passed to methods that need it. This promotes testability and clear dependency management.

## Key Attributes

- **event_bus**: Central event system (`EventBus`)

## Key Methods

### get_plugin

`get_plugin(name: str) -> BasePlugin | None`

Retrieve a registered plugin by its name.

```python
dialog_manager = context.get_plugin("dialog")
if dialog_manager:
    dialog_manager.show_dialog("Hello!")
```

## Usage in Plugins

```python
def update(self, delta_time):
    # Access other plugins
    audio = self.context.get_plugin("audio")
```
