# Conditions & Registry

Pedre uses an extensible condition system where all script conditions are managed by a central registry. This allows you to create custom conditions that integrate seamlessly with the event-driven scripting plugin.

## How Conditions Are Loaded

Pedre uses a plugin-style architecture for loading conditions. When the game initializes, the `ConditionLoader` automatically imports condition modules specified in your settings, which triggers their `@ConditionRegistry.register` decorators to execute and register the conditions.

### INSTALLED_CONDITIONS Setting

Conditions are configured through the `INSTALLED_CONDITIONS` setting, which is a list of Python module paths containing condition checker functions.

**Default built-in conditions:**

```python
INSTALLED_CONDITIONS = [
    "pedre.plugins.interaction.conditions",
    "pedre.plugins.inventory.conditions",
    "pedre.plugins.npc.conditions",
    "pedre.plugins.script.conditions",
]
```

### Adding Custom Conditions

To add your own custom conditions, extend the list in your project's `settings.py`:

```python
from pedre.conf import global_settings

INSTALLED_CONDITIONS = [
    *global_settings.INSTALLED_CONDITIONS,  # Include built-in conditions
    "myproject.custom_conditions",           # Your custom conditions module
    "myproject.plugins.weather.conditions",  # Plugin-specific conditions
]
```

You can also replace built-in conditions with your own implementations by omitting the built-in module and adding your custom one instead.

## ConditionRegistry

The `ConditionRegistry` maintains a mapping of condition names (like `"inventory_accessed"`, `"script_completed"`) to checker functions. This enables the scripting plugin to evaluate conditions defined in JSON without importing the actual Python functions.

### Location

[src/pedre/conditions/registry.py](https://github.com/msaizar/pedre/blob/main/src/pedre/conditions/registry.py)

## Creating Custom Conditions

To create a new condition checker, define a function and decorate it with `@ConditionRegistry.register`.

### 1. Define the Checker Function

```python
from typing import Any
from pedre.plugins.game_context import GameContext
from pedre.conditions.registry import ConditionRegistry

@ConditionRegistry.register("is_weather")
def check_weather(data: dict[str, Any], context: GameContext) -> bool:
    """Check if the current weather matches the specified type.

    Args:
        data: Condition parameters from JSON (e.g., {"weather": "rain"})
        context: Game context for accessing plugins

    Returns:
        True if the condition is met, False otherwise
    """
    required_weather = data.get("weather")

    weather_plugin = context.get_plugin("weather")
    if not weather_plugin:
        return False

    return weather_plugin.current_weather == required_weather
```

### 2. Use in Scripts

Once registered, your condition can be used in any JSON script:

```json
{
  "farmer_rain_dialog": {
    "trigger": {
      "event": "npc_interacted",
      "npc": "farmer"
    },
    "conditions": [
      {
        "check": "is_weather",
        "weather": "rain"
      }
    ],
    "actions": [
      {
        "name": "dialog",
        "speaker": "Farmer",
        "text": ["Perfect weather for the crops!"]
      }
    ]
  }
}
```

## Advanced Condition Examples

### Numeric Comparisons

```python
@ConditionRegistry.register("player_health")
def check_player_health(data: dict[str, Any], context: GameContext) -> bool:
    """Check if player health meets a condition."""
    player = context.get_plugin("player")
    if not player:
        return False

    current_health = player.health

    # Support multiple comparison operators
    if "equals" in data:
        return current_health == data["equals"]
    if "gte" in data:
        return current_health >= data["gte"]
    if "gt" in data:
        return current_health > data["gt"]
    if "lte" in data:
        return current_health <= data["lte"]
    if "lt" in data:
        return current_health < data["lt"]

    return False
```

Usage:

```json
{
  "conditions": [
    {
      "check": "player_health",
      "lte": 25
    }
  ]
}
```

### Complex State Checks

```python
@ConditionRegistry.register("quest_progress")
def check_quest_progress(data: dict[str, Any], context: GameContext) -> bool:
    """Check if a quest has reached a specific stage."""
    quest_plugin = context.get_plugin("quest")
    if not quest_plugin:
        return False

    quest_id = data.get("quest_id")
    required_stage = data.get("stage")

    quest = quest_plugin.get_quest(quest_id)
    if not quest:
        return False

    return quest.current_stage == required_stage
```

## Best Practices

- **Naming**: Use lowercase, underscore_separated names for condition keys (e.g., `is_weather`, `player_health`).
- **Return Type**: Always return a boolean value (`True` or `False`).
- **Error Handling**: Return `False` if required plugins or data are unavailable, rather than raising exceptions.
- **Documentation**: Include docstrings explaining what the condition checks and what parameters it accepts.
- **Parameters**: Use clear, descriptive parameter names in your condition data dictionary.
- **Plugin Access**: Use `context.get_plugin()` to access game plugins and check if they exist before using them.

## For Script Writers

If you're writing scripts and want to learn about using conditions in your JSON files, see the [Conditions](../scripting/conditions.md) guide in the scripting documentation.
