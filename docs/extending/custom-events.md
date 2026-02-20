# Events & Registry

The Pedre framework uses an event-driven architecture to decouple plugins. The `EventRegistry` allows dynamic discovery and registration of event types by name.

## How Events Are Loaded

Pedre uses a plugin-style architecture for loading events. When the game initializes, the `EventLoader` automatically imports event modules specified in your settings, which triggers their `@EventRegistry.register` decorators to execute and register the events.

### INSTALLED_EVENTS Setting

Events are configured through the `INSTALLED_EVENTS` setting, which is a list of Python module paths containing event classes.

**Default built-in events:**

```python
INSTALLED_EVENTS = [
    "pedre.plugins.audio.events",
    "pedre.plugins.camera.events",
    "pedre.plugins.dialog.events",
    "pedre.plugins.inventory.events",
    "pedre.plugins.particle.events",
    "pedre.plugins.scene.events",
    "pedre.plugins.npc.events",
]
```

### Adding Custom Events

To add your own custom events, extend the list in your project's `settings.py`:

```python
from pedre.conf import global_settings

INSTALLED_EVENTS = [
    *global_settings.INSTALLED_EVENTS,  # Include built-in events
    "myproject.custom_events",           # Your custom events module
    "myproject.plugins.weather.events",  # Plugin-specific events
]
```

You can also replace built-in events with your own implementations by omitting the built-in module and adding your custom one instead.

## EventRegistry

The `EventRegistry` maps string names (like `"npc_interacted"`) to Event classes. This enables the scripting plugin to subscribe to events defined in JSON without importing the actual Python classes.

### Location

[src/pedre/events/registry.py](https://github.com/msaizar/pedre/blob/main/src/pedre/events/registry.py)

## Creating Custom Events

To add a new event type that scripts can listen for:

### 1. Define the Event Class

Use the `@EventRegistry.register` decorator to register your event class. The registry uses the class's `name` attribute as the key.

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

### 2. Publish the Event

Publish the event from your plugin using the context's event bus.

```python
def set_weather(self, type, intensity):
    self.current_weather = type
    # ... apply changes ...

    # Notify other plugins/scripts
    self.context.event_bus.publish(WeatherChangedEvent(type, intensity))
```

### 3. Use in Scripts

Scripts can now trigger on this event using the registered name:

```json
{
  "react_to_rain": {
    "trigger": {
      "event": "weather_changed",
      "weather_type": "rain"
    },
    "actions": [
      {
        "name": "dialog",
        "speaker": "Villager",
        "text": ["Looks like rain again..."]
      }
    ]
  }
}
```

## Best Practices

- **Naming**: Use lowercase, underscore_separated names for event keys (e.g. `item_dropped`).
- **Data**: Keep event classes simple (dataclasses are recommended).
- **Scope**: Events should represent significant state changes or interactions, not every frame update.
