# Extending Pedre

Pedre is designed for extensibility. You can add custom actions, events, conditions, and even entire game systems without modifying the framework code.

## Extension System Overview

The Pedre extension system uses a **plugin-style architecture** with automatic discovery and registration:

1. **Define** your custom component (action/event/condition/system)
2. **Register** it using decorators (`@ActionRegistry.register`, `@EventRegistry.register`, etc.)
3. **Configure** it in your project's `settings.py` to be loaded
4. **Use** it in your JSON scripts or game code

## What Can You Extend?

### Actions

Create custom script actions that can be triggered from JSON scripts.

**Use Cases:**
- Weather systems (rain, snow, fog)
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

### Systems

Build entire game systems that integrate with the framework lifecycle.

**Use Cases:**
- Quest management
- Combat system
- Crafting system
- Weather/time system
- Relationship/faction system

**Learn More:** [Custom Systems](custom-systems.md)

## Extension Workflow

### 1. Create Your Extension

Define your custom component in a Python module:

```python
# myproject/custom_actions.py
from pedre.actions import Action
from pedre.actions.registry import ActionRegistry

@ActionRegistry.register("custom_action")
class CustomAction(Action):
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
        "type": "custom_action",
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
    "pedre.systems.audio.actions",
    "pedre.systems.camera.actions",
    "pedre.systems.dialog.actions",
    "myproject.custom_actions",  # Your custom actions
]
```

### INSTALLED_EVENTS

List of Python module paths containing event classes.

```python
INSTALLED_EVENTS = [
    "pedre.systems.npc.events",
    "pedre.systems.dialog.events",
    "myproject.custom_events",  # Your custom events
]
```

### INSTALLED_CONDITIONS

List of Python module paths containing condition checker functions.

```python
INSTALLED_CONDITIONS = [
    "pedre.systems.inventory.conditions",
    "pedre.systems.npc.conditions",
    "myproject.custom_conditions",  # Your custom conditions
]
```

### INSTALLED_SYSTEMS

List of Python module paths containing system classes.

```python
INSTALLED_SYSTEMS = [
    "pedre.systems.audio.manager",
    "pedre.systems.dialog.manager",
    "myproject.systems.weather",  # Your custom system
]
```

## Best Practices

### Naming Conventions

- **Actions**: Verb-based, lowercase with underscores (e.g., `set_weather`, `spawn_enemy`)
- **Events**: Past tense, lowercase with underscores (e.g., `weather_changed`, `enemy_spawned`)
- **Conditions**: Question-based, lowercase with underscores (e.g., `is_raining`, `has_quest`)
- **Systems**: Noun-based, PascalCase with "Manager" suffix (e.g., `WeatherManager`, `QuestManager`)

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
- **Systems**: Handle missing dependencies gracefully

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
@ActionRegistry.register("set_weather")
class SetWeatherAction(Action):
    def __init__(self, weather: str):
        self.weather = weather
        self._executed = False

    @classmethod
    def from_dict(cls, data: dict):
        return cls(weather=data["weather"])

    def execute(self, context) -> bool:
        if not self._executed:
            weather_system = context.get_system("weather")
            if weather_system:
                weather_system.set_weather(self.weather)
            self._executed = True
        return True

    def reset(self):
        self._executed = False
```

### Weather Changed Event

```python
@EventRegistry.register("weather_changed")
@dataclass
class WeatherChangedEvent:
    weather_type: str
    intensity: float
```

### Weather Condition Check

```python
@ConditionRegistry.register("is_weather")
def check_weather(data: dict[str, Any], context: GameContext) -> bool:
    weather_system = context.get_system("weather")
    if not weather_system:
        return False
    return weather_system.current_weather == data.get("weather")
```

## System Loader

The [SystemLoader](system-loader.md) handles automatic loading and initialization of all extensions. It manages:

- Dependency resolution
- Initialization order
- Lifecycle management (setup, reset, cleanup)
- Event bus wiring

## Next Steps

- [Custom Actions](custom-actions.md) - Create script actions
- [Custom Events](custom-events.md) - Define game events
- [Custom Conditions](custom-conditions.md) - Add conditional checks
- [Custom Systems](custom-systems.md) - Build complete game systems
- [System Loader](system-loader.md) - Understand the loading process

## See Also

- [API Reference](../api/index.md) - Framework architecture
- [Scripting Guide](../scripting/index.md) - Using extensions in scripts
- [Systems Reference](../systems/index.md) - Built-in systems documentation
