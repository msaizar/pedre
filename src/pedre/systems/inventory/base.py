"""Base class for InventoryManager."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pedre.systems.base import BaseSystem


@dataclass
class InventoryItem:
    """Represents a collectible item in the player's inventory.

    An InventoryItem contains all the metadata needed to display and track a collectible
    item in the game. Items are defined with their content (name, description, image) and
    state (whether the player has acquired it).

    The dataclass structure makes items easy to define in code or load from data files.
    Items are typically created during game initialization and added to the InventoryManager,
    where they persist throughout the game session.

    The 'acquired' flag determines whether the player currently possesses the item. Items
    can be pre-acquired (starting inventory) or start unacquired and be collected during
    gameplay. This allows for collectathon gameplay where players track their progress
    toward finding all items.

    Attributes:
        id: Unique identifier for this item (e.g., "secret_key", "photo_01").
           Used for lookups, save data, and script references. Should be lowercase
           with underscores for consistency.
        name: Display name shown to the player (e.g., "Rusty Key", "Family Photo").
             Can be in any language and include special characters for presentation.
        description: Flavor text or description shown when examining the item.
                    Can be multiple sentences providing context or story information.
        image_path: Optional path to the item's full-size image file, relative to assets/images/.
                   For example, "items/key.png" or "photos/memory_01.jpg". Set to None
                   for items without visual representation. This is displayed when viewing
                   the item in detail (e.g., full-screen photo view).
        icon_path: Optional path to the item's icon/thumbnail image, relative to assets/images/.
                  For example, "icons/key_icon.png" or "photos/thumbs/memory_01_thumb.jpg".
                  This is displayed in the inventory grid as a preview. If None, the grid
                  slot will be empty (just the background color). Default is None.
        category: Item category for filtering and organization. Common categories include
                 "photo", "note", "key", "general". Categories are user-defined strings
                 and can be extended as needed. Default is "general".
        acquired: Whether the player has collected this item. True means the item is in
                 the player's possession, False means it hasn't been found yet. Can be
                 set to True initially for starting items. Default is False.

    Example:
        # A collectible photograph with icon
        photo = InventoryItem(
            id="beach_memory",
            name="Beach Day",
            description="A sunny day at the coast with friends.",
            image_path="photos/beach.jpg",
            icon_path="photos/icons/beach_icon.png",
            category="photo",
            acquired=False
        )

        # A key item for progression
        key = InventoryItem(
            id="tower_key",
            name="Tower Key",
            description="Opens the old tower door.",
            image_path="items/tower_key.png",
            icon_path="items/icons/key_icon.png",
            category="key",
            acquired=True  # Player starts with this
        )
    """

    id: str  # Unique identifier
    name: str  # Display name
    description: str  # Item description
    image_path: str | None = None  # Path to full-size image file (relative to assets/images/)
    icon_path: str | None = None  # Path to icon/thumbnail image (relative to assets/images/)
    category: str = "general"  # Item category (photo, note, key, etc.)
    acquired: bool = False  # Whether the player has this item


class InventoryBaseManager(BaseSystem, ABC):
    """Base class for InventoryManager."""

    role = "inventory_manager"

    @abstractmethod
    def has_been_accessed(self) -> bool:
        """Check if inventory has been accessed."""
        ...

    @abstractmethod
    def get_icon_path(self, item: InventoryItem) -> str | None:
        """Get the full absolute path to an item's icon/thumbnail image file."""
        ...

    @abstractmethod
    def get_image_path(self, item: InventoryItem) -> str | None:
        """Get the full absolute path to an item's full-size image file."""
        ...

    @abstractmethod
    def get_acquired_items(self, category: str | None = None) -> list[InventoryItem]:
        """Get all items the player has acquired, optionally filtered by category."""
        ...

    @abstractmethod
    def mark_as_accessed(self) -> None:
        """Mark the inventory as having been accessed by the player."""
        ...

    @abstractmethod
    def emit_closed_event(self) -> None:
        """Emit InventoryClosedEvent when inventory view closes."""
        ...

    @abstractmethod
    def has_item(self, item_id: str) -> bool:
        """Check if the player has acquired a specific item."""
        ...
