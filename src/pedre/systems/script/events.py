"""Script-related events for the script system."""

from dataclasses import dataclass

from pedre.systems.events import Event


@dataclass
class ScriptCompleteEvent(Event):
    """Fired when a script completes execution.

    This event is published by the script manager when a script's action sequence
    finishes executing. It allows scripts to chain together, where one script waits
    for another to complete before starting.

    This is particularly useful for complex multi-stage sequences where different
    scripts handle different phases of a cutscene or story event.

    Script trigger example:
        {
            "trigger": {
                "event": "script_complete",
                "script": "intro_cutscene"
            }
        }

    The script filter is optional:
    - script: Only trigger when specific script completes (omit to trigger for any script)

    Attributes:
        script_name: Name of the script that completed.
    """

    script_name: str
