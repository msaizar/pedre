# API Reference

Complete reference for the Pedre framework's Python API.

## Overview

The Pedre framework is built on several core architectural components that work together to provide a flexible, event-driven RPG engine. This reference covers the framework's public API for Python developers.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     ViewManager                         │
│  (Orchestrates view transitions & game lifecycle)       │
└─────────────────┬───────────────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
      ▼           ▼           ▼
 ┌─────────┐ ┌─────────┐ ┌──────────┐
 │MenuView │ │GameView │ │SaveViews │
 └─────────┘ └────┬────┘ └──────────┘
                   │
                   ▼
           ┌───────────────┐
           │ GameContext   │
           │  ┌─────────┐  │
           │  │EventBus │  │
           │  └─────────┘  │
           └───────┬───────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
      ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Systems  │ │ Actions  │ │  Events  │
│(Managers)│ │(Scripts) │ │(EventBus)│
└──────────┘ └──────────┘ └──────────┘
```

## Core Components

### [ViewManager](view-manager.md)

Central controller for view transitions and game lifecycle.

**Responsibilities:**
- Switch between menu, gameplay, and save/load views
- Manage game state (new game, continue, load, exit)
- Trigger map transitions

**Key Methods:**
- `show_menu()`, `show_game()`, `show_load_game()`, `show_save_game()`
- `continue_game()`, `load_game()`, `exit_game()`
- `load_map()`

### [Views](views.md)

Different game screens and states.

**Available Views:**
- `GameView` - Main gameplay with all systems active
- `MenuView` - Main menu with asset preloading
- `LoadGameView` - Load game screen
- `SaveGameView` - Save game screen

### [GameContext](game-context.md)

Central registry providing systems with access to the event bus and other systems.

**Responsibilities:**
- System registration and retrieval
- Event bus access
- Dependency injection

**Key Methods:**
- `get_system(name: str) -> BaseSystem | None`

### [EventBus](event-bus.md)

Publish-subscribe event system for decoupled communication.

**Responsibilities:**
- Event subscription and publishing
- System-to-system communication
- Script trigger handling

**Key Methods:**
- `subscribe(event_type, callback)`
- `publish(event)`
- `unsubscribe(event_type, callback)`

### [Sprites](sprites.md)

Animated character sprites for player and NPCs.

**Available Sprites:**
- `AnimatedPlayer` - Player character with 4-directional animation
- `AnimatedNPC` - NPC characters with special animations

## Game Systems

Pedre uses a manager-based architecture where each system handles specific functionality. All systems are documented in the [Systems Reference](../systems/index.md).

**Core Systems:**
- [DialogManager](../systems/dialog.md) - Conversations and text display
- [NPCManager](../systems/npc.md) - NPC behavior and interactions
- [PlayerManager](../systems/player.md) - Player character management
- [ScriptManager](../systems/script.md) - Event-driven scripting
- [InventoryManager](../systems/inventory.md) - Item management
- [AudioManager](../systems/audio.md) - Music and sound effects
- [CameraManager](../systems/camera.md) - Camera control
- [SceneManager](../systems/scene.md) - Map loading and transitions
- [SaveManager](../systems/save.md) - Game persistence

[See all systems →](../systems/index.md)

## Extension System

Pedre supports adding custom functionality without modifying framework code. See [Extending Pedre](../extending/index.md) for details.

**Extension Points:**
- Custom Actions - Script commands
- Custom Events - Trigger types
- Custom Conditions - Conditional logic
- Custom Systems - Complete game features

## Usage Patterns

### Accessing Systems

Systems are accessed through the GameContext:

```python
# In a system or action
dialog_manager = context.get_system("dialog")
npc_manager = context.get_system("npc")
audio_manager = context.get_system("audio")
```

### Publishing Events

Events enable decoupled communication:

```python
from pedre.events import DialogClosedEvent

# Publish an event
context.event_bus.publish(DialogClosedEvent(
    npc_name="merchant",
    dialog_level=1
))
```

### Subscribing to Events

Systems can react to events:

```python
def on_dialog_closed(event: DialogClosedEvent):
    print(f"Dialog closed: {event.npc_name}")

context.event_bus.subscribe(DialogClosedEvent, on_dialog_closed)
```

### View Transitions

Control game flow through the ViewManager:

```python
# Show menu
view_manager.show_menu()

# Start game
view_manager.show_game()

# Load a different map
view_manager.load_map("forest.tmx", spawn_waypoint="entrance")
```

## Configuration

Game behavior is configured through `settings.py`. See [Configuration Guide](../guides/configuration.md) for all available settings.

**Common Settings:**
- Window size and title
- Player movement speed
- System-specific configuration
- Asset paths

## Type System

Pedre uses Python type hints throughout. Key types:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.events.base import EventBus
    from pedre.systems.base import BaseSystem
```

## Initialization Flow

### 1. Game Startup

```python
from pedre import run_game

if __name__ == "__main__":
    run_game()
```

### 2. System Loading

The framework automatically:
1. Loads configuration from `settings.py`
2. Creates ViewManager and window
3. Initializes GameContext and EventBus
4. Loads all systems via SystemLoader
5. Sets up event subscriptions
6. Shows initial view (menu or game)

### 3. Game Loop

Each frame:
1. Process input
2. Update systems (`update(delta_time)`)
3. Render views (`on_draw()`)
4. Handle events

## Best Practices

### Event-Driven Design

Prefer events over direct system calls:

```python
# Good: Event-driven
context.event_bus.publish(NPCInteractedEvent(npc_name="merchant"))

# Avoid: Direct coupling
npc_manager.interact("merchant")
dialog_manager.show_dialog("merchant", ["Hello!"])
```

### System Dependencies

Access systems through GameContext, not global imports:

```python
# Good: Via context
def execute(self, context):
    audio = context.get_system("audio")
    if audio:
        audio.play_sfx("sound.wav")

# Avoid: Direct import
from pedre.systems.audio import AudioManager
audio = AudioManager()  # Creates duplicate instance
```

### Error Handling

Check for system availability:

```python
weather = context.get_system("weather")
if weather:
    weather.set_weather("rain")
else:
    # Weather system not installed
    pass
```

## Next Steps

- [Getting Started](../getting-started.md) - Build your first game
- [Systems Reference](../systems/index.md) - Individual system documentation
- [Scripting Guide](../scripting/index.md) - Event-driven scripting
- [Extending Pedre](../extending/index.md) - Add custom functionality
- [Tiled Integration](../guides/tiled-integration.md) - Level design workflow
