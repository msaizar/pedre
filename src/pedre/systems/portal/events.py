"""Portal-related events.

This module contains events published by the portal system when players interact
with portals in the game world.
"""

from dataclasses import dataclass
from typing import Any

from pedre.systems.event_registry import EventRegistry
from pedre.systems.events import Event


@EventRegistry.register("portal_entered")
@dataclass
class PortalEnteredEvent(Event):
    """Fired when player enters a portal zone.

    This event is published by the portal manager when the player walks into a portal's
    activation zone. Scripts can subscribe to this event to handle portal transitions,
    including conditional checks, cutscenes, and map transitions.

    Unlike the legacy portal system which handled transitions directly, this event-based
    approach allows full flexibility through the script system. Scripts can check conditions,
    play animations, show dialog, and ultimately use the change_scene action to transition.

    Script trigger example:
        {
            "trigger": {
                "event": "portal_entered",
                "portal": "forest_gate"
            },
            "actions": [
                {"type": "change_scene", "target_map": "Forest.tmx", "spawn_waypoint": "entrance"}
            ]
        }

    The portal filter is optional:
    - portal: Only trigger for specific portal name (omit to trigger for any portal)

    Attributes:
        portal_name: Name of the portal the player entered.
    """

    portal_name: str

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"portal": self.portal_name}
