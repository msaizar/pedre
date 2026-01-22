# Events & Registry

The Pedre framework uses an event-driven architecture to decouple systems. The `EventRegistry` allows dynamic discovery and registration of event types by name.

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
