"""Base class for InteractionManager."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    import arcade


@dataclass
class InteractiveObject:
    """Represents an interactive object in the game world.

    An InteractiveObject wraps an arcade Sprite with metadata that defines how the
    object behaves when the player interacts with it. These objects are typically
    created from Tiled map data where designers define interactive elements with
    custom properties.

    The properties dictionary contains all custom properties from the Tiled object,
    allowing designers to configure behavior without code changes. Common properties
    include message text, interaction effects, state values, and trigger flags.

    Attributes:
        sprite: The arcade Sprite representing this object in the game world.
               Used for position, rendering, and distance calculations.
        name: Unique identifier for this object. Used to track interaction state
             and reference the object in scripts or events.
        properties: Dictionary of custom properties from Tiled or code. Contains
                   configuration like message text, state values, and behavior flags.

    Example from Tiled:
        Object properties:
        - name: "mysterious_lever"
    """

    sprite: arcade.Sprite
    name: str
    properties: dict


class InteractionBaseManager(BaseSystem, ABC):
    """Base class for InteractionManager."""

    role = "interaction_manager"

    @abstractmethod
    def get_interactive_objects(self) -> dict[str, InteractiveObject]:
        """Get interactive objects."""
        ...

    @abstractmethod
    def has_interacted_with(self, object_name: str) -> bool:
        """Check if an object has been interacted with."""
        ...
