"""Interaction system for handling interactive objects in the game world.

This package provides:
- InteractionManager: Core system for managing interactive objects
- InteractiveObject: Data class representing an interactive object

Events (registered via INSTALLED_EVENTS):
- ObjectInteractedEvent: Event fired when player interacts with an object

Conditions (registered via INSTALLED_CONDITIONS):
- check_object_interacted: Check if an object has been interacted with

The interaction system handles player interactions with objects in the game world,
supporting message dialogs, toggle states, and other interactive behaviors configured
via Tiled map properties.
"""

from pedre.systems.interaction.manager import InteractionManager, InteractiveObject

__all__ = [
    "InteractionManager",
    "InteractiveObject",
]
