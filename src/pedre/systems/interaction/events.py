"""Events for the interaction system."""

from dataclasses import dataclass
from typing import Any

from pedre.systems.event_registry import EventRegistry
from pedre.systems.events import Event


@EventRegistry.register("object_interacted")
@dataclass
class ObjectInteractedEvent(Event):
    """Fired when player interacts with an interactive object.

    This event is published when the player presses the interaction key while facing
    an interactive object in the game world. Objects are tiles or sprites marked as
    interactive in the map data.

    The script manager tracks which objects have been interacted with, allowing
    conditions to check if an object was previously activated.

    Script trigger example:
        {
            "trigger": {
                "event": "object_interacted",
                "object_name": "treasure_chest"
            }
        }

    The object_name filter is optional:
    - object_name: Only trigger for specific object (omit to trigger for any object)

    Attributes:
        object_name: Name of the object that was interacted with.
    """

    object_name: str

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"object_name": self.object_name}
