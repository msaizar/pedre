"""NPC system with manager, actions, and events.

This module provides the NPC management system for the game, handling NPC state,
movement, dialog, and interactions with support for pathfinding-based movement
and animation state tracking.

The NPC system consists of:
- NPCManager: Main system for managing NPC state and behavior
- NPCState: Runtime state tracking for individual NPCs
- NPCDialogConfig: Configuration for NPC dialog at specific levels
- AnimatedNPC: Animated sprite class for NPCs with special animations

Actions (registered via INSTALLED_ACTIONS):
- AdvanceDialogAction, MoveNPCAction, RevealNPCsAction, SetCurrentNPCAction
- SetDialogLevelAction, StartDisappearAnimationAction, WaitForNPCMovementAction
- WaitForNPCsAppearAction, WaitForNPCsDisappearAction

Events (registered via INSTALLED_EVENTS):
- NPCAppearCompleteEvent, NPCDisappearCompleteEvent, NPCInteractedEvent
- NPCMovementCompleteEvent

Conditions (registered via INSTALLED_CONDITIONS):
- check_npc_dialog_level: Check NPC's current dialog level
- check_npc_interacted: Check if an NPC has been interacted with
"""

from pedre.systems.npc.base import NPCBaseManager, NPCState
from pedre.systems.npc.manager import NPCDialogConfig, NPCManager

__all__ = [
    "NPCBaseManager",
    "NPCDialogConfig",
    "NPCManager",
    "NPCState",
]
