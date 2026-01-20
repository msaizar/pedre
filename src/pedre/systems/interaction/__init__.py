"""Interaction system for handling interactive objects in the game world.

This package provides:
- InteractionManager: Core system for managing interactive objects
- InteractiveObject: Data class representing an interactive object
- ObjectInteractedEvent: Event fired when player interacts with an object

The interaction system handles player interactions with objects in the game world,
supporting message dialogs, toggle states, and other interactive behaviors configured
via Tiled map properties.
"""

from pedre.systems.interaction.cache import InteractionCacheProvider
from pedre.systems.interaction.conditions import check_object_interacted
from pedre.systems.interaction.events import ObjectInteractedEvent
from pedre.systems.interaction.manager import InteractionManager, InteractiveObject
from pedre.systems.interaction.save import InteractionSaveProvider

__all__ = [
    "InteractionCacheProvider",
    "InteractionManager",
    "InteractionSaveProvider",
    "InteractiveObject",
    "ObjectInteractedEvent",
    "check_object_interacted",
]
