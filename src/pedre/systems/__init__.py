"""Game systems for managing different aspects of gameplay."""

from pedre.systems.action_registry import ActionRegistry
from pedre.systems.audio import AudioManager
from pedre.systems.base import BaseSystem
from pedre.systems.camera import CameraManager
from pedre.systems.dialog import DialogManager, DialogPage
from pedre.systems.event_registry import EventRegistry
from pedre.systems.events import EventBus
from pedre.systems.game_context import GameContext
from pedre.systems.input import InputManager
from pedre.systems.interaction import InteractionManager, InteractiveObject
from pedre.systems.inventory import (
    AcquireItemAction,
    InventoryClosedEvent,
    InventoryItem,
    InventoryManager,
    ItemAcquiredEvent,
    WaitForInventoryAccessAction,
)
from pedre.systems.loader import CircularDependencyError, MissingDependencyError, SystemLoader
from pedre.systems.npc import NPCDialogConfig, NPCManager, NPCState
from pedre.systems.particle import EmitParticlesAction, Particle, ParticleManager
from pedre.systems.pathfinding import PathfindingManager  # Now from pathfinding/
from pedre.systems.portal import Portal, PortalEnteredEvent, PortalManager
from pedre.systems.registry import SystemRegistry
from pedre.systems.save import GameSaveData, SaveManager
from pedre.systems.scene_state import SceneStateCache
from pedre.systems.script import Script, ScriptCompleteEvent, ScriptManager

__all__ = [
    "AcquireItemAction",
    "ActionRegistry",
    "AudioManager",
    "BaseSystem",
    "CameraManager",
    "CircularDependencyError",
    "DialogManager",
    "DialogPage",
    "EmitParticlesAction",
    "EventBus",
    "EventRegistry",
    "GameContext",
    "GameSaveData",
    "InputManager",
    "InteractionManager",
    "InteractiveObject",
    "InventoryClosedEvent",
    "InventoryItem",
    "InventoryManager",
    "ItemAcquiredEvent",
    "MissingDependencyError",
    "NPCDialogConfig",
    "NPCManager",
    "NPCState",
    "Particle",
    "ParticleManager",
    "PathfindingManager",
    "Portal",
    "PortalEnteredEvent",
    "PortalManager",
    "SaveManager",
    "SceneStateCache",
    "Script",
    "ScriptCompleteEvent",
    "ScriptManager",
    "SystemLoader",
    "SystemRegistry",
    "WaitForInventoryAccessAction",
]
