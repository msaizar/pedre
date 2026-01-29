# Events & Registry

The Pedre framework uses an event-driven architecture to decouple systems. The `EventRegistry` allows dynamic discovery and registration of event types by name.

## How Events Are Loaded

Pedre uses a plugin-style architecture for loading events. When the game initializes, the `EventLoader` automatically imports event modules specified in your settings, which triggers their `@EventRegistry.register` decorators to execute and register the events.

### INSTALLED_EVENTS Setting

Events are configured through the `INSTALLED_EVENTS` setting, which is a list of Python module paths containing event classes.

**Default built-in events:**

```python
INSTALLED_EVENTS = [
    "pedre.systems.audio.events",
    "pedre.systems.camera.events",
    "pedre.systems.dialog.events",
    "pedre.systems.inventory.events",
    "pedre.systems.particle.events",
    "pedre.systems.scene.events",
    "pedre.systems.npc.events",
]
```

### Adding Custom Events

To add your own custom events, extend the list in your project's `settings.py`:

```python
from pedre.conf import global_settings

INSTALLED_EVENTS = [
    *global_settings.INSTALLED_EVENTS,  # Include built-in events
    "myproject.custom_events",           # Your custom events module
    "myproject.systems.weather.events",  # System-specific events
]
```

You can also replace built-in events with your own implementations by omitting the built-in module and adding your custom one instead.

## EventRegistry

The `EventRegistry` maps string names (like `"npc_interacted"`) to Event classes. This enables the scripting system to subscribe to events defined in JSON without importing the actual Python classes.

### Location

`src/pedre/events/registry.py`

## Creating Custom Events

To add a new event type that scripts can listen for:

### 1. Define the Event Class

Use the `@EventRegistry.register` decorator to associate a unique name with your event class.

```python
from dataclasses import dataclass
from pedre.events.registry import EventRegistry

@EventRegistry.register("weather_changed")
@dataclass
class WeatherChangedEvent:
    weather_type: str
    intensity: float
```

### 2. Publish the Event

Publish the event from your system using the context's event bus.

```python
def set_weather(self, type, intensity):
    self.current_weather = type
    # ... apply changes ...

    # Notify other systems/scripts
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
        "type": "dialog",
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
