"""Scene-related events.

This module contains events published by the scene system.
"""

from dataclasses import dataclass
from typing import Any

from pedre.events import Event
from pedre.events.registry import EventRegistry


@EventRegistry.register("scene_start")
@dataclass
class SceneStartEvent(Event):
    """Fired when a new scene/map starts loading.

    This event is published by the game view after a map is loaded and all systems
    are initialized. It fires on every map transition and when starting a new game,
    making it useful for scene-specific initialization, cutscenes, or gameplay that
    should trigger each time a particular scene is entered.

    Script trigger example:
        {
            "trigger": {
                "event": "scene_start",
                "scene": "forest"
            }
        }

    The scene filter is optional:
    - scene: Only trigger for specific scene name (omit to trigger for any scene)

    Attributes:
        scene_name: Name of the scene/map that just started (e.g., "casa", "forest").
    """

    scene_name: str

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"scene": self.scene_name}
