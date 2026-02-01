"""Script plugin for managing game scripts and event-driven sequences.

This package provides:
- ScriptPlugin: Core scripting plugin that loads and executes JSON-based scripts
- Script: Data class for script definitions with triggers and conditions

Events (registered via INSTALLED_EVENTS):
- ScriptCompleteEvent: Event fired when a script completes execution

Conditions (registered via INSTALLED_CONDITIONS):
- check_script_completed: Check if a script has completed execution

The script plugin enables event-driven storytelling, cutscenes, and complex
game sequences through JSON-based script definitions.
"""

from pedre.plugins.script.plugin import Script, ScriptPlugin

__all__ = [
    "Script",
    "ScriptPlugin",
]
