"""NPC system with manager, actions, and events.

This module provides the NPC management system for the game, handling NPC state,
movement, dialog, and interactions with support for pathfinding-based movement
and animation state tracking.

The NPC system consists of:
- NPCManager: Main system for managing NPC state and behavior
- NPCState: Runtime state tracking for individual NPCs
- NPCDialogConfig: Configuration for NPC dialog at specific levels
- NPC Actions: Script actions for NPC movement, dialog, and animations
- NPC Events: Events fired for NPC interactions and animation completions
"""

from pedre.systems.npc.actions import (
    AdvanceDialogAction,
    MoveNPCAction,
    RevealNPCsAction,
    SetCurrentNPCAction,
    SetDialogLevelAction,
    StartDisappearAnimationAction,
    WaitForNPCMovementAction,
    WaitForNPCsAppearAction,
    WaitForNPCsDisappearAction,
)
from pedre.systems.npc.cache import NPCCacheProvider
from pedre.systems.npc.conditions import check_npc_dialog_level, check_npc_interacted
from pedre.systems.npc.events import (
    NPCAppearCompleteEvent,
    NPCDisappearCompleteEvent,
    NPCInteractedEvent,
    NPCMovementCompleteEvent,
)
from pedre.systems.npc.manager import NPCDialogConfig, NPCManager, NPCState
from pedre.systems.npc.save import NPCSaveProvider

__all__ = [
    "AdvanceDialogAction",
    "MoveNPCAction",
    "NPCAppearCompleteEvent",
    "NPCCacheProvider",
    "NPCDialogConfig",
    "NPCDisappearCompleteEvent",
    "NPCInteractedEvent",
    "NPCManager",
    "NPCMovementCompleteEvent",
    "NPCSaveProvider",
    "NPCState",
    "RevealNPCsAction",
    "SetCurrentNPCAction",
    "SetDialogLevelAction",
    "StartDisappearAnimationAction",
    "WaitForNPCMovementAction",
    "WaitForNPCsAppearAction",
    "WaitForNPCsDisappearAction",
    "check_npc_dialog_level",
    "check_npc_interacted",
]
