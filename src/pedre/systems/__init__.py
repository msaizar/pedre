"""Game systems for managing different aspects of gameplay."""

from pedre.systems.audio import AudioManager
from pedre.systems.camera import CameraManager
from pedre.systems.dialog import DialogManager
from pedre.systems.events import EventBus
from pedre.systems.game_context import GameContext
from pedre.systems.input import InputManager
from pedre.systems.interaction import InteractionManager, InteractiveObject
from pedre.systems.inventory import InventoryItem, InventoryManager
from pedre.systems.npc import NPCManager
from pedre.systems.particle import ParticleManager
from pedre.systems.pathfinding import PathfindingManager
from pedre.systems.portal import Portal, PortalManager
from pedre.systems.save import GameSaveData, SaveManager
from pedre.systems.scene_state import SceneStateCache
from pedre.systems.script import ScriptManager

__all__ = [
    "AudioManager",
    "CameraManager",
    "DialogManager",
    "EventBus",
    "GameContext",
    "GameSaveData",
    "InputManager",
    "InteractionManager",
    "InteractiveObject",
    "InventoryItem",
    "InventoryManager",
    "NPCManager",
    "ParticleManager",
    "PathfindingManager",
    "Portal",
    "PortalManager",
    "SaveManager",
    "SceneStateCache",
    "ScriptManager",
]
