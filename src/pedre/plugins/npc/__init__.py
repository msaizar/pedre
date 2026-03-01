"""NPC plugin with plugin, actions, and events.

This module provides the NPC management plugin for the game, handling NPC state,
movement, dialog, and interactions with support for pathfinding-based movement
and animation state tracking.

The NPC plugin consists of:
- NPCPlugin: Main plugin for managing NPC state and behavior
- NPCState: Runtime state tracking for individual NPCs
- NPCDialogConfig: Configuration for NPC dialog at specific levels
Actions (registered via INSTALLED_ACTIONS):
- AdvanceDialogAction, MoveNPCAction, StartAppearAnimationAction, SetCurrentNPCAction
- SetDialogLevelAction, StartDisappearAnimationAction, WaitForNPCMovementAction
- WaitForNPCsAppearAction, WaitForNPCsDisappearAction

Events (registered via INSTALLED_EVENTS):
- NPCAppearCompleteEvent, NPCDisappearCompleteEvent, NPCInteractedEvent
- NPCMovementCompleteEvent

Conditions (registered via INSTALLED_CONDITIONS):
- check_npc_dialog_level: Check NPC's current dialog level
- check_npc_interacted: Check if an NPC has been interacted with
"""

from pedre.plugins.npc.base import NPCBasePlugin, NPCState
from pedre.plugins.npc.plugin import NPCDialogConfig, NPCPlugin

__all__ = [
    "NPCBasePlugin",
    "NPCDialogConfig",
    "NPCPlugin",
    "NPCState",
]
