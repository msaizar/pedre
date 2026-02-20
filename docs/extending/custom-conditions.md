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

To create a new condition, define a class that inherits from `Condition` and decorate it with `@ConditionRegistry.register`. The registry uses the class's `name` attribute as the key.

### 1. Define the Condition Class

```python
from typing import TYPE_CHECKING, Any, Self
from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

@ConditionRegistry.register
class IsWeatherCondition(Condition):
    """Check if the current weather matches the specified type.

    Args:
        weather: The weather type to check for (e.g., "rain")
    """

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
        "name": "is_weather",
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
@ConditionRegistry.register
class PlayerHealthCondition(Condition):
    """Check if player health meets a condition."""

    name = "player_health"

    def __init__(self, equals: int | None = None, gte: int | None = None,
                 gt: int | None = None, lte: int | None = None, lt: int | None = None) -> None:
        self.equals = equals
        self.gte = gte
        self.gt = gt
        self.lte = lte
        self.lt = lt

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            equals=data.get("equals"),
            gte=data.get("gte"),
            gt=data.get("gt"),
            lte=data.get("lte"),
            lt=data.get("lt"),
        )

    def check(self, context: GameContext) -> bool:
        player = context.get_plugin("player")
        if not player:
            return False

        current_health = player.health

        # Support multiple comparison operators
        if self.equals is not None:
            return current_health == self.equals
        if self.gte is not None:
            return current_health >= self.gte
        if self.gt is not None:
            return current_health > self.gt
        if self.lte is not None:
            return current_health <= self.lte
        if self.lt is not None:
            return current_health < self.lt

        return False
```

Usage:

```json
{
  "conditions": [
    {
      "name": "player_health",
      "lte": 25
    }
  ]
}
```

### Complex State Checks

```python
@ConditionRegistry.register
class QuestProgressCondition(Condition):
    """Check if a quest has reached a specific stage."""

    name = "quest_progress"

    def __init__(self, quest_id: str, stage: str) -> None:
        self.quest_id = quest_id
        self.stage = stage

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(quest_id=data.get("quest_id", ""), stage=data.get("stage", ""))

    def check(self, context: GameContext) -> bool:
        quest_plugin = context.get_plugin("quest")
        if not quest_plugin:
            return False

        quest = quest_plugin.get_quest(self.quest_id)
        if not quest:
            return False

        return quest.current_stage == self.stage
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
