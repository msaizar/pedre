"""Dialog system with manager, actions, and events.

This module provides the dialog system for the game, handling NPC conversations,
narration, and player communication with support for multi-page dialogs and
text reveal animations.

The dialog system consists of:
- DialogManager: Main system for displaying and managing dialogs
- DialogAction: Script action to show dialog to the player
- WaitForDialogCloseAction: Script action to wait for dialog dismissal
- DialogClosedEvent: Event fired when a dialog is closed
- DialogOpenedEvent: Event fired when a dialog is opened
- DialogPage: Data class representing a single page of dialog
"""

from pedre.systems.dialog.actions import DialogAction, WaitForDialogCloseAction
from pedre.systems.dialog.events import DialogClosedEvent, DialogOpenedEvent
from pedre.systems.dialog.manager import DialogManager, DialogPage

__all__ = [
    "DialogAction",
    "DialogClosedEvent",
    "DialogManager",
    "DialogOpenedEvent",
    "DialogPage",
    "WaitForDialogCloseAction",
]
