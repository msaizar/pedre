"""Script system for managing game scripts and event-driven sequences.

This package provides:
- ScriptManager: Core scripting system that loads and executes JSON-based scripts
- Script: Data class for script definitions with triggers and conditions
- Events: Script-related events for system communication

The script system enables event-driven storytelling, cutscenes, and complex
game sequences through JSON-based script definitions.
"""

from pedre.systems.script.conditions import check_script_completed
from pedre.systems.script.events import ScriptCompleteEvent
from pedre.systems.script.manager import Script, ScriptManager

__all__ = [
    "Script",
    "ScriptCompleteEvent",
    "ScriptManager",
    "check_script_completed",
]
