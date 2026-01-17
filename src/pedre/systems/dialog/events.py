"""Events for dialog system."""

from dataclasses import dataclass

from pedre.systems.event_registry import EventRegistry
from pedre.systems.events import Event


@EventRegistry.register("dialog_closed")
@dataclass
class DialogClosedEvent(Event):
    """Fired when a dialog is closed.

    This event is published by the dialog manager when the player dismisses a dialog
    window. It's commonly used to trigger scripts that should run after a conversation,
    such as advancing the story or showing follow-up actions.

    The event includes both the NPC name and their dialog level at the time the dialog
    was shown, allowing scripts to trigger on specific conversation stages.

    Script trigger example:
        {
            "trigger": {
                "event": "dialog_closed",
                "npc": "martin",
                "dialog_level": 1
            }
        }

    The trigger filters are optional:
    - npc: Only trigger for specific NPC (omit to trigger for any NPC)
    - dialog_level: Only trigger at specific dialog level (omit to trigger at any level)

    Attributes:
        npc_name: Name of the NPC whose dialog was closed.
        dialog_level: Conversation level at the time dialog was shown.
    """

    npc_name: str
    dialog_level: int


@EventRegistry.register("dialog_opened")
@dataclass
class DialogOpenedEvent(Event):
    """Fired when a dialog is opened.

    This event is published by the dialog manager when a dialog window is shown to
    the player. It can be used to track when conversations begin or to coordinate
    other systems with dialog display.

    Note: This event is not currently used for script triggers, but is available
    for programmatic event handling.

    Attributes:
        npc_name: Name of the NPC whose dialog was opened.
        dialog_level: Current conversation level.
    """

    npc_name: str
    dialog_level: int
