"""Events for dialog system."""

from dataclasses import dataclass
from typing import Any

from pedre.events import Event
from pedre.events.registry import EventRegistry


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

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"npc": self.npc_name, "dialog_level": self.dialog_level}


@EventRegistry.register("dialog_opened")
@dataclass
class DialogOpenedEvent(Event):
    """Fired when a dialog is opened.

    This event is published by the dialog manager when a dialog window is shown to
    the player. It's commonly used to trigger scripts that should run when a conversation
    begins, such as playing sound effects, pausing music, or coordinating other systems.

    The event includes both the NPC name and their dialog level at the time the dialog
    was shown, allowing scripts to trigger on specific conversation stages.

    Script trigger example:
        {
            "trigger": {
                "event": "dialog_opened",
                "npc": "martin",
                "dialog_level": 1
            }
        }

    The trigger filters are optional:
    - npc: Only trigger for specific NPC (omit to trigger for any NPC)
    - dialog_level: Only trigger at specific dialog level (omit to trigger at any level)

    Attributes:
        npc_name: Name of the NPC whose dialog was opened.
        dialog_level: Conversation level at the time dialog was shown.
    """

    npc_name: str
    dialog_level: int

    def get_script_data(self) -> dict[str, Any]:
        """Get data for script triggers."""
        return {"npc": self.npc_name, "dialog_level": self.dialog_level}
