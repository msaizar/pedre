"""Events for NPC system."""

from dataclasses import dataclass

from pedre.systems.events import Event


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

    npc_name: str
    dialog_level: int


@dataclass
class NPCMovementCompleteEvent(Event):
    """Fired when an NPC completes movement to target.

    This event is published by the NPC manager when an NPC finishes pathfinding and
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

    npc_name: str


@dataclass
class NPCAppearCompleteEvent(Event):
    """Fired when an NPC completes appear animation.

    This event is published by the NPC manager when an AnimatedNPC finishes its appear
    animation. AnimatedNPCs play a special animation when they're revealed, and this
    event signals that the animation has completed.

    This event is typically used internally by wait actions (WaitForNPCsAppearAction)
    rather than as a direct script trigger, but it's available for custom event handling.

    Note: This event is not currently used for script triggers, but is available
    for programmatic event handling.

    Attributes:
        npc_name: Name of the NPC that appeared.
    """

    npc_name: str


@dataclass
class NPCDisappearCompleteEvent(Event):
    """Fired when an NPC completes disappear animation.

    This event is published by the NPC manager when an AnimatedNPC finishes its disappear
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

    npc_name: str
