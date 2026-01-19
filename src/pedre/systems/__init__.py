"""Game systems for managing different aspects of gameplay."""

from pedre.events import EventBus
from pedre.events.registry import EventRegistry
from pedre.systems.action_registry import ActionRegistry
from pedre.systems.audio import AudioManager
from pedre.systems.base import BaseSystem
from pedre.systems.camera import CameraManager
from pedre.systems.debug import DebugManager
from pedre.systems.dialog import DialogManager, DialogPage
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
from pedre.systems.map import MapManager
from pedre.systems.npc import NPCDialogConfig, NPCManager, NPCState
from pedre.systems.particle import EmitParticlesAction, Particle, ParticleManager
from pedre.systems.pathfinding import PathfindingManager  # Now from pathfinding/
from pedre.systems.physics import PhysicsManager
from pedre.systems.player import PlayerManager
from pedre.systems.portal import Portal, PortalEnteredEvent, PortalManager
from pedre.systems.registry import SystemRegistry
from pedre.systems.save import GameSaveData, SaveManager
from pedre.systems.scene import SceneManager
from pedre.systems.script import Script, ScriptCompleteEvent, ScriptManager

__all__ = [
    "AcquireItemAction",
    "ActionRegistry",
    "AudioManager",
    "BaseSystem",
    "CameraManager",
    "CircularDependencyError",
    "DebugManager",
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
    "MapManager",
    "MissingDependencyError",
    "NPCDialogConfig",
    "NPCManager",
    "NPCState",
    "Particle",
    "ParticleManager",
    "PathfindingManager",
    "PhysicsManager",
    "PlayerManager",
    "Portal",
    "PortalEnteredEvent",
    "PortalManager",
    "SaveManager",
    "SceneManager",
    "Script",
    "ScriptCompleteEvent",
    "ScriptManager",
    "SystemLoader",
    "SystemRegistry",
    "WaitForInventoryAccessAction",
]
