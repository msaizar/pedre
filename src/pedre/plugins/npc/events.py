"""Events for NPC plugin."""

from dataclasses import dataclass
from typing import Any, ClassVar

from pedre.events import Event
from pedre.events.registry import EventRegistry


@EventRegistry.register
@dataclass
class NPCInteractedEvent(Event):
    """Fired when player interacts with an NPC.

    This event is published when the player presses the interaction key while facing
    an NPC. It triggers before any dialog is shown, making it useful for scripts that
    need to run custom logic at the start of an NPC interaction.

    The event is published even if the NPC has no dialog configured, allowing scripts
    to handle the interaction completely.

    Script trigger example:
        {
            "trigger": {
                "event": "npc_interacted",
                "npc": "martin"
            }
        }

    The npc filter is optional:
    - npc: Only trigger for specific NPC (omit to trigger for any NPC)

    Attributes:
        npc_name: Name of the NPC that was interacted with.
        dialog_level: Current conversation level.
    """

    name: ClassVar[str] = "npc_interacted"

    trigger_keys: ClassVar[frozenset[str]] = frozenset({"npc", "dialog_level"})
    reference_fields: ClassVar[dict[str, str]] = {"npc": "npc"}
    npc_name: str
    dialog_level: int

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"npc": self.npc_name, "dialog_level": self.dialog_level}


@EventRegistry.register
@dataclass
class NPCMovementCompleteEvent(Event):
    """Fired when an NPC completes movement to target.

    This event is published by the NPC plugin when an NPC finishes pathfinding and
    arrives at their destination. It's useful for chaining actions that should occur
    after an NPC reaches a specific location.

    The event is emitted when both the NPC's path is empty and the is_moving flag
    becomes False, ensuring movement is fully complete.

    Script trigger example:
        {
            "trigger": {
                "event": "npc_movement_complete",
                "npc": "martin"
            }
        }

    The npc filter is optional:
    - npc: Only trigger for specific NPC (omit to trigger for any NPC)

    Attributes:
        npc_name: Name of the NPC that completed movement.
    """

    name: ClassVar[str] = "npc_movement_complete"

    trigger_keys: ClassVar[frozenset[str]] = frozenset({"npc"})
    reference_fields: ClassVar[dict[str, str]] = {"npc": "npc"}
    npc_name: str

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"npc": self.npc_name}


@EventRegistry.register
@dataclass
class NPCAppearCompleteEvent(Event):
    """Fired when an NPC completes appear animation.

    This event is published by the NPC plugin when an AnimatedNPC finishes its appear
    animation. AnimatedNPCs play a special animation when they're revealed, and this
    event signals that the animation has completed.

    This event is typically used internally by wait actions (WaitForNPCsAppearAction),
    but can also be used as a script trigger for custom logic after NPCs appear.

    Script trigger example:
        {
            "trigger": {
                "event": "npc_appear_complete",
                "npc": "spirit"
            }
        }

    The npc filter is optional:
    - npc: Only trigger for specific NPC (omit to trigger for any NPC)

    Attributes:
        npc_name: Name of the NPC that appeared.
    """

    name: ClassVar[str] = "npc_appear_complete"

    trigger_keys: ClassVar[frozenset[str]] = frozenset({"npc"})
    reference_fields: ClassVar[dict[str, str]] = {"npc": "npc"}
    npc_name: str

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"npc": self.npc_name}


@EventRegistry.register
@dataclass
class NPCDisappearCompleteEvent(Event):
    """Fired when an NPC completes disappear animation.

    This event is published by the NPC plugin when an AnimatedNPC finishes its disappear
    animation. The disappear animation is triggered by the StartDisappearAnimationAction,
    and this event signals when it's safe to perform cleanup or trigger follow-up actions.

    The NPC sprite is automatically hidden after the animation completes, just before
    this event is published.

    Script trigger example:
        {
            "trigger": {
                "event": "npc_disappear_complete",
                "npc": "martin"
            }
        }

    The npc filter is optional:
    - npc: Only trigger for specific NPC (omit to trigger for any NPC)

    Attributes:
        npc_name: Name of the NPC that disappeared.
    """

    name: ClassVar[str] = "npc_disappear_complete"

    trigger_keys: ClassVar[frozenset[str]] = frozenset({"npc"})
    npc_name: str
    reference_fields: ClassVar[dict[str, str]] = {"npc": "npc"}

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"npc": self.npc_name}
