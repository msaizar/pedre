# Custom Systems

Create complete game systems that integrate with the Pedre framework lifecycle.

## Overview

A system (manager) is a self-contained module that handles a specific aspect of game functionality. Systems can:

- Subscribe to events
- Publish events
- Access other systems via GameContext
- Maintain state that persists across scenes
- Participate in save/load operations

## System Lifecycle

Systems follow a standard lifecycle managed by the SystemLoader:

1. **Instantiation** - Constructor called, dependencies injected
2. **Setup** - `setup(context)` called to initialize and subscribe to events
3. **Update** - `update(delta_time)` called each frame (optional)
4. **Reset** - `reset()` called when starting a new game
5. **Cleanup** - `cleanup()` called when system is destroyed

## Creating a Custom System

### 1. Define the System Class

```python
# myproject/systems/weather.py
from pedre.systems.base import BaseSystem
from pedre.systems.game_context import GameContext

class WeatherManager(BaseSystem):
    """Manages weather effects and time of day."""

    # Declare system dependencies
    DEPENDENCIES = ["audio", "particle"]

    def __init__(self):
        """Initialize the system."""
        self.current_weather = "clear"
        self.intensity = 0.0
        self.context: GameContext | None = None

    def setup(self, context: GameContext) -> None:
        """Initialize the system with game context.

        Subscribe to events and set up initial state.
        """
        self.context = context

        # Subscribe to events
        from myproject.events import TimeChangedEvent
        context.event_bus.subscribe(TimeChangedEvent, self._on_time_changed)

    def update(self, delta_time: float) -> None:
        """Update weather effects each frame."""
        if self.current_weather == "rain":
            # Emit rain particles
            particle_manager = self.context.get_system("particle")
            if particle_manager:
                particle_manager.emit_rain()

    def reset(self) -> None:
        """Reset to initial state for new game."""
        self.current_weather = "clear"
        self.intensity = 0.0

    def cleanup(self) -> None:
        """Clean up resources when system is destroyed."""
        if self.context:
            from myproject.events import TimeChangedEvent
            self.context.event_bus.unsubscribe(TimeChangedEvent, self._on_time_changed)

    # Public API
    def set_weather(self, weather: str, intensity: float = 1.0) -> None:
        """Change the current weather.

        Args:
            weather: Weather type (e.g., "rain", "snow", "clear")
            intensity: Weather intensity from 0.0 to 1.0
        """
        self.current_weather = weather
        self.intensity = intensity

        # Publish event
        from myproject.events import WeatherChangedEvent
        if self.context:
            self.context.event_bus.publish(
                WeatherChangedEvent(weather_type=weather, intensity=intensity)
            )

        # Play weather sounds
        audio = self.context.get_system("audio")
        if audio and weather == "rain":
            audio.play_music("rain_ambient.ogg", volume=intensity * 0.5, loop=True)

    def get_weather(self) -> tuple[str, float]:
        """Get current weather state.

        Returns:
            Tuple of (weather_type, intensity)
        """
        return (self.current_weather, self.intensity)

    # Event handlers
    def _on_time_changed(self, event) -> None:
        """Handle time of day changes."""
        # Change weather based on time
        if event.time == "night":
            self.set_weather("clear", 0.3)
```

### 2. Add Save/Load Support (Optional)

If your system needs to persist state across save/load:

```python
def get_save_state(self) -> dict[str, Any]:
    """Get serializable state for saving.

    Returns:
        Dictionary of state to save
    """
    return {
        "current_weather": self.current_weather,
        "intensity": self.intensity,
    }

def restore_save_state(self, state: dict[str, Any]) -> None:
    """Restore from saved state.

    Args:
        state: Previously saved state dictionary
    """
    self.current_weather = state.get("current_weather", "clear")
    self.intensity = state.get("intensity", 0.0)
```

### 3. Add Scene Caching Support (Optional)

If your system needs to preserve state when transitioning between scenes:

```python
def cache_scene_state(self, scene_name: str) -> dict[str, Any]:
    """Cache system state for a specific scene.

    Args:
        scene_name: Name of the scene being cached

    Returns:
        Dictionary of state to cache
    """
    return {
        "weather": self.current_weather,
        "intensity": self.intensity,
    }

def restore_scene_state(self, scene_name: str, state: dict[str, Any]) -> None:
    """Restore cached scene state.

    Args:
        scene_name: Name of the scene being restored
        state: Previously cached state dictionary
    """
    self.current_weather = state.get("weather", "clear")
    self.intensity = state.get("intensity", 0.0)
```

### 4. Register the System

Add your system to `settings.py`:

```python
# settings.py
from pedre.conf import global_settings

INSTALLED_SYSTEMS = [
    *global_settings.INSTALLED_SYSTEMS,  # Include built-in systems
    "myproject.systems.weather.WeatherManager",
]
```

### 5. Access from Other Systems

```python
# In another system or action
weather = context.get_system("weather")
if weather:
    current_weather, intensity = weather.get_weather()
    weather.set_weather("snow", 0.8)
```

## System Dependencies

Declare dependencies to ensure systems are initialized in the correct order:

```python
class QuestManager(BaseSystem):
    # This system depends on inventory and npc systems
    DEPENDENCIES = ["inventory", "npc"]

    def setup(self, context: GameContext) -> None:
        # These systems are guaranteed to be initialized
        self.inventory = context.get_system("inventory")
        self.npc_manager = context.get_system("npc")
```

The SystemLoader will:

- Initialize dependencies first
- Detect circular dependencies
- Call `setup()` in dependency order

## Tiled Map Integration

Load data from Tiled maps:

```python
def load_from_tiled(
    self,
    tile_map: arcade.TileMap,
    arcade_scene: arcade.Scene
) -> None:
    """Load system data from Tiled map.

    Args:
        tile_map: The loaded Tiled map
        arcade_scene: The Arcade scene
    """
    # Read map properties
    weather = tile_map.properties.get("weather", "clear")
    self.set_weather(weather)

    # Process object layers
    if "Weather" in tile_map.object_lists:
        for obj in tile_map.object_lists["Weather"]:
            # Handle weather zones
            pass
```

## Best Practices

### Naming Conventions

- Class name: `PascalCase` ending in `Manager` (e.g., `WeatherManager`)
- System key: Lowercase version without "Manager" (e.g., "weather")
- The framework automatically converts class names to keys

### State Management

```python
# Good: Use instance variables for state
def __init__(self):
    self.current_weather = "clear"

# Avoid: Global variables or class variables
_current_weather = "clear"  # Don't do this
```

### Event Communication

```python
# Good: Publish events for state changes
def set_weather(self, weather: str):
    self.current_weather = weather
    self.context.event_bus.publish(WeatherChangedEvent(weather))

# Avoid: Direct system coupling
def set_weather(self, weather: str):
    self.current_weather = weather
    self.context.get_system("audio").play_music("rain.ogg")  # Too coupled
```

### Error Handling

```python
# Good: Check for system availability
def update(self, delta_time: float):
    audio = self.context.get_system("audio")
    if audio:
        audio.play_sfx("thunder.wav")

# Avoid: Assuming systems exist
def update(self, delta_time: float):
    self.context.get_system("audio").play_sfx("thunder.wav")  # May crash
```

### Resource Cleanup

```python
def cleanup(self):
    """Always unsubscribe from events."""
    if self.context:
        self.context.event_bus.unsubscribe(MyEvent, self._handler)

    # Clean up other resources
    if self.sprite_list:
        self.sprite_list.clear()
```

## Complete Example: Quest System

```python
from dataclasses import dataclass
from typing import Any
from pedre.systems.base import BaseSystem
from pedre.systems.game_context import GameContext

@dataclass
class Quest:
    id: str
    name: str
    description: str
    stage: int = 0
    completed: bool = False

class QuestManager(BaseSystem):
    """Manages quest state and progression."""

    DEPENDENCIES = ["inventory", "npc"]

    def __init__(self):
        self.quests: dict[str, Quest] = {}
        self.context: GameContext | None = None

    def setup(self, context: GameContext) -> None:
        self.context = context

        # Subscribe to events that affect quests
        from pedre.systems.inventory.events import ItemAcquiredEvent
        context.event_bus.subscribe(ItemAcquiredEvent, self._on_item_acquired)

    def update(self, delta_time: float) -> None:
        # Check quest conditions each frame
        pass

    def reset(self) -> None:
        self.quests.clear()

    def cleanup(self) -> None:
        if self.context:
            from pedre.systems.inventory.events import ItemAcquiredEvent
            self.context.event_bus.unsubscribe(ItemAcquiredEvent, self._on_item_acquired)

    # Public API
    def add_quest(self, quest_id: str, name: str, description: str) -> None:
        """Add a new quest."""
        self.quests[quest_id] = Quest(
            id=quest_id,
            name=name,
            description=description
        )

    def advance_quest(self, quest_id: str) -> None:
        """Advance quest to next stage."""
        if quest_id in self.quests:
            self.quests[quest_id].stage += 1

            # Publish event
            from myproject.events import QuestAdvancedEvent
            self.context.event_bus.publish(
                QuestAdvancedEvent(quest_id=quest_id, stage=self.quests[quest_id].stage)
            )

    def complete_quest(self, quest_id: str) -> None:
        """Mark quest as completed."""
        if quest_id in self.quests:
            self.quests[quest_id].completed = True

            from myproject.events import QuestCompletedEvent
            self.context.event_bus.publish(QuestCompletedEvent(quest_id=quest_id))

    def get_quest(self, quest_id: str) -> Quest | None:
        """Get quest by ID."""
        return self.quests.get(quest_id)

    # Save/Load
    def get_save_state(self) -> dict[str, Any]:
        return {
            "quests": {
                qid: {
                    "name": q.name,
                    "description": q.description,
                    "stage": q.stage,
                    "completed": q.completed,
                }
                for qid, q in self.quests.items()
            }
        }

    def restore_save_state(self, state: dict[str, Any]) -> None:
        self.quests.clear()
        for qid, data in state.get("quests", {}).items():
            self.quests[qid] = Quest(
                id=qid,
                name=data["name"],
                description=data["description"],
                stage=data["stage"],
                completed=data["completed"],
            )

    # Event handlers
    def _on_item_acquired(self, event) -> None:
        """Check if item acquisition advances any quests."""
        for quest in self.quests.values():
            if quest.stage == 1 and event.item_id == "golden_key":
                self.advance_quest(quest.id)
```

## See Also

- [SystemLoader](system-loader.md) - How systems are loaded and initialized
- [Custom Actions](custom-actions.md) - Create actions that use your system
- [Custom Events](custom-events.md) - Define events your system publishes
- [API Reference](../api/index.md) - Framework architecture
