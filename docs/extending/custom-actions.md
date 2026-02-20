# Actions & Registry

Pedre uses an extensible action system where all script actions are managed by a central registry. This allows you to create custom actions that integrate seamlessly with the event-driven scripting plugin.

## How Actions Are Loaded

Pedre uses a plugin-style architecture for loading actions. When the game initializes, the `ActionLoader` automatically imports action modules specified in your settings, which triggers their `@ActionRegistry.register` decorators to execute and register the actions.

### INSTALLED_ACTIONS Setting

Actions are configured through the `INSTALLED_ACTIONS` setting, which is a list of Python module paths containing action classes.

**Default built-in actions:**

```python
INSTALLED_ACTIONS = [
    "pedre.plugins.audio.actions",
    "pedre.plugins.camera.actions",
    "pedre.plugins.dialog.actions",
    "pedre.plugins.inventory.actions",
    "pedre.plugins.particle.actions",
    "pedre.plugins.scene.actions",
    "pedre.plugins.npc.actions",
]
```

### Adding Custom Actions

To add your own custom actions, extend the list in your project's `settings.py`:

```python
from pedre.conf import global_settings

INSTALLED_ACTIONS = [
    *global_settings.INSTALLED_ACTIONS,  # Include built-in actions
    "myproject.custom_actions",           # Your custom actions module
    "myproject.plugins.weather.actions",  # Plugin-specific actions
]
```

You can also replace built-in actions with your own implementations by omitting the built-in module and adding your custom one instead.

## ActionRegistry

The `ActionRegistry` maps action strings (like `"dialog"`, `"move_npc"`) to Action classes.

### Location

[src/pedre/actions/registry.py](https://github.com/msaizar/pedre/blob/main/src/pedre/actions/registry.py)

## Creating Custom Actions

To create a new action, subclass `Action` and decorate it with `@ActionRegistry.register`.

### 1. Define the Action Class

```python
from pedre.actions import Action
from pedre.actions.registry import ActionRegistry

@ActionRegistry.register
class SetWeatherAction(Action):

    name = "set_weather"

    def __init__(self, weather: str, intensity: float = 1.0):
        self.weather = weather
        self.intensity = intensity
        self._executed = False

    @classmethod
    def from_dict(cls, data: dict) -> "SetWeatherAction":
        """Parse JSON data into an action instance."""
        return cls(
            weather=data["weather"],
            intensity=data.get("intensity", 1.0)
        )

    def execute(self, context) -> bool:
        """Execute the action logic."""
        if not self._executed:
            weather_plugin = context.get_plugin("weather")
            if weather_plugin:
                weather_plugin.set_weather(self.weather, self.intensity)
            self._executed = True

        # Return True to indicate the action is complete.
        # Return False to keep it active (e.g. waiting for something).
        return True

    def reset(self):
        """Reset state for reuse."""
        self._executed = False
```

### 2. Use in Scripts

Once registered, your action can be used in any JSON script:

```json
{
  "start_rain": {
    "trigger": {"event": "scene_start"},
    "actions": [
      {
        "name": "set_weather",
        "weather": "rain",
        "intensity": 0.8
      }
    ]
  }
}
```

## Advanced Parsing

For complex parsing logic, you can register a custom parser function instead of using `from_dict`.

```python
def parse_complex_action(data: dict) -> MyAction:
    # Custom validation or logic
    return MyAction(...)

ActionRegistry.register_parser("complex_action", parse_complex_action)
```
