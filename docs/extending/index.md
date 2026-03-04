# Extending Pedre

Pedre is designed for extensibility. You can add custom actions, events, conditions, and even entire game plugins without modifying the framework code.

## Extension System Overview

The Pedre extension system uses a **plugin-style architecture** with automatic discovery and registration:

1. **Define** your custom component (action/event/condition/plugin)
2. **Register** it using decorators (`@ActionRegistry.register`, `@EventRegistry.register`, etc.)
3. **Configure** it in your project's `settings.py` to be loaded
4. **Use** it in your JSON scripts or game code

## What Can You Extend?

### Actions

Create custom script actions that can be triggered from JSON scripts.

**Use Cases:**

- Weather plugins (rain, snow, fog)
- Custom UI elements (tooltips, notifications)
- Game mechanics (crafting, combat, puzzles)
- External integrations (analytics, achievements)

**Learn More:** [Custom Actions](custom-actions.md)

### Events

Define custom events that scripts can listen for and react to.

**Use Cases:**

- Custom player actions (jumping, crouching)
- Environmental changes (time of day, weather)
- Game state changes (level up, quest complete)
- System notifications (achievement unlocked)

**Learn More:** [Custom Events](custom-events.md)

### Conditions

Create conditional checks for script execution.

**Use Cases:**

- Player stats (health, level, attributes)
- Time-based conditions (day/night, season)
- Complex game state (quest progress, relationships)
- Resource checks (money, items, energy)

**Learn More:** [Custom Conditions](custom-conditions.md)

### Plugins

Build entire game plugins that integrate with the framework lifecycle.

**Use Cases:**

- Quest management
- Combat plugin
- Crafting plugin
- Weather/time plugin
- Relationship/faction plugin

**Learn More:** [Custom Plugins](custom-plugins.md)

### Content Types

Register custom content type registries for loading and validating JSON-driven game data.

**Use Cases:**

- Enemy definitions (stats, spawn rules, loot tables)
- Quest data (objectives, rewards, requirements)
- Equipment and weapon schemas
- Level or map configuration data

**Learn More:** [Custom Content Types](content-registry.md)

### CLI Commands

Create project-specific CLI commands or distribute commands as installable packages.

**Use Cases:**

- Build and packaging scripts
- Deployment automation
- Testing utilities
- Development tools

**Learn More:** [Custom Commands](custom-commands.md)

## Extension Workflow

### 1. Create Your Extension

Define your custom component in a Python module:

```python
# myproject/custom_actions.py
from pedre.actions import Action
from pedre.actions.registry import ActionRegistry

@ActionRegistry.register
class CustomAction(Action):

    name = "custom_action"

    def __init__(self, param: str):
        self.param = param
        self._executed = False

    @classmethod
    def from_dict(cls, data: dict):
        return cls(param=data["param"])

    def execute(self, context) -> bool:
        if not self._executed:
            # Your custom logic here
            self._executed = True
        return True

    def reset(self):
        self._executed = False
```

### 2. Register in Settings

Add your module to the appropriate `INSTALLED_*` setting:

```python
# settings.py
from pedre.conf import global_settings

INSTALLED_ACTIONS = [
    *global_settings.INSTALLED_ACTIONS,  # Include built-in actions
    "myproject.custom_actions",           # Your custom actions
]
```

### 3. Use in Scripts

Your extension is now available in JSON scripts:

```json
{
  "my_script": {
    "trigger": {"event": "scene_start"},
    "actions": [
      {
        "name": "custom_action",
        "param": "value"
      }
    ]
  }
}
```

## Configuration Settings

### INSTALLED_ACTIONS

List of Python module paths containing action classes.

```python
INSTALLED_ACTIONS = [
    "pedre.plugins.audio.actions",
    "pedre.plugins.camera.actions",
    "pedre.plugins.dialog.actions",
    "myproject.custom_actions",  # Your custom actions
]
```

### INSTALLED_EVENTS

List of Python module paths containing event classes.

```python
INSTALLED_EVENTS = [
    "pedre.plugins.npc.events",
    "pedre.plugins.dialog.events",
    "myproject.custom_events",  # Your custom events
]
```

### INSTALLED_CONDITIONS

List of Python module paths containing condition checker functions.

```python
INSTALLED_CONDITIONS = [
    "pedre.plugins.inventory.conditions",
    "pedre.plugins.npc.conditions",
    "myproject.custom_conditions",  # Your custom conditions
]
```

### INSTALLED_PLUGINS

List of Python module paths containing plugin classes.

```python
INSTALLED_PLUGINS = [
    "pedre.plugins.audio.plugin",
    "pedre.plugins.dialog.plugin",
    "myproject.plugins.weather",  # Your custom plugin
]
```

## Best Practices

### Naming Conventions

- **Actions**: Verb-based, lowercase with underscores (e.g., `set_weather`, `spawn_enemy`)
- **Events**: Past tense, lowercase with underscores (e.g., `weather_changed`, `enemy_spawned`)
- **Conditions**: Question-based, lowercase with underscores (e.g., `is_raining`, `has_quest`)
- **Plugins**: Noun-based, PascalCase with "Plugin" suffix (e.g., `WeatherPlugin`, `QuestPlugin`)

### Documentation

Always include docstrings explaining:

- What the component does
- What parameters it accepts
- Return values and side effects
- Usage examples

### Error Handling

- **Actions**: Return `False` to keep action active, `True` when complete
- **Conditions**: Return `False` if checks fail, don't raise exceptions
- **Events**: Use dataclasses for clear data structures
- **Plugins**: Handle missing dependencies gracefully

### Testing

Create unit tests for your extensions:

```python
# tests/test_custom_actions.py
def test_custom_action():
    action = CustomAction(param="test")
    result = action.execute(mock_context)
    assert result == True
```

## Examples

### Simple Weather Action

```python
@ActionRegistry.register
class SetWeatherAction(Action):

    name = "set_weather"

    def __init__(self, weather: str):
        self.weather = weather
        self._executed = False

    @classmethod
    def from_dict(cls, data: dict):
        return cls(weather=data["weather"])

    def execute(self, context) -> bool:
        if not self._executed:
            weather_plugin = context.get_plugin("weather")
            if weather_plugin:
                weather_plugin.set_weather(self.weather)
            self._executed = True
        return True

    def reset(self):
        self._executed = False
```

### Weather Changed Event

```python
from dataclasses import dataclass
from pedre.events import Event
from pedre.events.registry import EventRegistry

@EventRegistry.register
@dataclass
class WeatherChangedEvent(Event):
    name = "weather_changed"
    weather_type: str
    intensity: float
```

### Weather Condition Check

```python
from typing import TYPE_CHECKING, Any, Self
from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

@ConditionRegistry.register
class IsWeatherCondition(Condition):
    name = "is_weather"

    def __init__(self, weather: str) -> None:
        self.weather = weather

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(weather=data.get("weather", ""))

    def check(self, context: GameContext) -> bool:
        weather_plugin = context.get_plugin("weather")
        if not weather_plugin:
            return False
        return weather_plugin.current_weather == self.weather
```

## Next Steps

- [Custom Actions](custom-actions.md) - Create script actions
- [Custom Events](custom-events.md) - Define game events
- [Custom Conditions](custom-conditions.md) - Add conditional checks
- [Custom Plugins](custom-plugins.md) - Build complete game plugins
- [Custom Commands](custom-commands.md) - Add CLI commands

## See Also

- [API Reference](../api/index.md) - Framework architecture
- [Scripting Guide](../scripting/index.md) - Using extensions in scripts
- [Plugins Reference](../plugins/index.md) - Built-in plugins documentation
