# Actions & Registry

Pedre uses an extensible action system where all script actions are managed by a central registry. This allows you to create custom actions that integrate seamlessly with the event-driven scripting system.

## ActionRegistry

The `ActionRegistry` maps action type strings (like `"dialog"`, `"move_npc"`) to Action classes.

### Location

`src/pedre/actions/registry.py`

## Creating Custom Actions

To create a new action type, subclass `Action` and decorate it with `@ActionRegistry.register`.

### 1. Define the Action Class

```python
from pedre.actions import Action
from pedre.actions.registry import ActionRegistry

@ActionRegistry.register("set_weather")
class SetWeatherAction(Action):
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
            weather_system = context.get_system("weather")
            if weather_system:
                weather_system.set_weather(self.weather, self.intensity)
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
        "type": "set_weather",
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
