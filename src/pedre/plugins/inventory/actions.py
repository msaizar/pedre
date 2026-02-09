"""Script actions for inventory plugin operations.

These actions allow scripts to manipulate inventory state,
such as acquiring items or waiting for inventory access.
"""

import logging
import uuid
from typing import TYPE_CHECKING, Any

from pedre.actions import Action, WaitForConditionAction
from pedre.actions.registry import ActionRegistry
from pedre.plugins.inventory.base import InventoryItem

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


@ActionRegistry.register("wait_for_inventory_access")
class WaitForInventoryAccessAction(WaitForConditionAction):
    """Wait for inventory to be accessed.

    This action pauses script execution until the player opens their inventory
    for the first time. It's useful for tutorial sequences or quests that require
    the player to check their items.

    The inventory plugin tracks whether it has been accessed via the has_been_accessed
    flag, which this action monitors.

    Example usage in a tutorial sequence:
        [
            {"type": "dialog", "speaker": "martin", "text": ["Check your inventory!"]},
            {"type": "wait_for_dialog_close"},
            {"type": "wait_for_inventory_access"},
            {"type": "dialog", "speaker": "martin", "text": ["Great job!"]}
        ]
    """

    def __init__(self) -> None:
        """Initialize inventory access wait action."""
        super().__init__(lambda ctx: ctx.inventory_plugin.has_been_accessed, "Inventory accessed")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WaitForInventoryAccessAction:  # noqa: ARG003
        """Create WaitForInventoryAccessAction from a dictionary."""
        return cls()


@ActionRegistry.register("acquire_item")
class AcquireItemAction(Action):
    """Give an item to the player's inventory.

    This action adds a specified item to the player's inventory by calling the
    inventory plugin's acquire_item() method. The item must already be defined
    in the inventory plugin - this action only marks it as acquired.

    When the item is successfully acquired, an ItemAcquiredEvent is published.
    If acquisition fails (inventory full, unknown item, or already owned), an
    ItemAcquisitionFailedEvent is published instead, and the action returns False,
    blocking script progression.

    Scripts can listen for ItemAcquisitionFailedEvent to show appropriate feedback
    to the player (e.g., "Your inventory is full!").

    Example usage:
        {
            "type": "acquire_item",
            "item_id": "rusty_key"
        }

        # In a script after finding a treasure chest
        {
            "actions": [
                {"type": "dialog", "speaker": "Narrator", "text": ["You found a key!"]},
                {"type": "acquire_item", "item_id": "tower_key"},
                {"type": "wait_for_dialog_close"}
            ]
        }

        # Script that listens for failure and shows message
        {
            "trigger": {
                "event": "item_acquisition_failed",
                "reason": "capacity"
            },
            "actions": [
                {"type": "dialog", "speaker": "Narrator", "text": ["Your inventory is full!"]}
            ]
        }
    """

    def __init__(self, item_id: str) -> None:
        """Initialize acquire item action.

        Args:
            item_id: Unique identifier of the item to acquire. Must match an item
                    ID in the inventory plugin's registry.
        """
        self.item_id = item_id
        self.started = False
        self.success = False

    def execute(self, context: GameContext) -> bool:
        """Acquire the item if not already started.

        Returns:
            True if item was successfully acquired, False otherwise (blocks script progression).
        """
        if not self.started:
            inventory_plugin = context.inventory_plugin
            self.success = inventory_plugin.acquire_item(self.item_id)
            self.started = True

            if self.success:
                logger.debug("AcquireItemAction: Successfully acquired item %s", self.item_id)
            else:
                logger.debug("AcquireItemAction: Failed to acquire item %s", self.item_id)

        return self.success

    def reset(self) -> None:
        """Reset the action."""
        self.started = False
        self.success = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AcquireItemAction:
        """Create AcquireItemAction from a dictionary."""
        return cls(item_id=data.get("item_id", ""))

    @classmethod
    def validate_params(cls, data: dict[str, Any]) -> list[str]:
        """Validate acquire_item action parameters.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors = []
        item_id = data.get("item_id")
        if not item_id:
            errors.append("missing required 'item_id' field")
        elif not isinstance(item_id, str):
            errors.append("'item_id' must be a string")
        return errors


@ActionRegistry.register("add_item")
class AddItemAction(Action):
    """Add a new item to the inventory plugin.

    This action dynamically creates and adds a new item to the inventory plugin without
    requiring it to be defined in inventory_items.json. This is useful for consumable items
    like potions that can be obtained through gameplay actions.

    The item is created from the provided metadata and added to the inventory. If acquired=True,
    it will be immediately available in the player's inventory and an ItemAcquiredEvent will
    be published. If acquired=False, the item is registered but not yet in the player's possession.

    If item_id is not provided or is empty, a unique UUID will be automatically generated to
    avoid ID conflicts. This is useful when adding multiple instances of the same consumable
    (e.g., multiple health potions).

    Example usage:
        # Without item_id - UUID auto-generated for each potion
        {
            "type": "add_item",
            "name": "Health Potion",
            "description": "Restores 50 HP",
            "icon_path": "items/potion.png",
            "category": "potion",
            "consumable": true,
            "acquired": true
        }

        # With explicit item_id (for unique items)
        {
            "type": "add_item",
            "item_id": "rusty_key",
            "name": "Rusty Key",
            "description": "Opens an old door",
            "icon_path": "items/key.png",
            "category": "key",
            "acquired": true
        }

        # In a script for finding a potion
        {
            "actions": [
                {"type": "dialog", "speaker": "Narrator", "text": ["You found a health potion!"]},
                {
                    "type": "add_item",
                    "name": "Health Potion",
                    "description": "Restores 50 HP",
                    "icon_path": "items/icons/potion.png",
                    "image_path": "items/potion.png",
                    "category": "potion",
                    "consumable": true,
                    "acquired": true
                },
                {"type": "wait_for_dialog_close"}
            ]
        }
    """

    def __init__(
        self,
        name: str,
        description: str,
        item_id: str | None = None,
        image_path: str | None = None,
        icon_path: str | None = None,
        category: str = "general",
        *,
        acquired: bool = True,
        consumable: bool = False,
    ) -> None:
        """Initialize add item action.

        Args:
            name: Display name of the item.
            description: Description text for the item.
            item_id: Optional unique identifier for the item. If not provided or empty,
                    a UUID will be auto-generated to ensure uniqueness.
            image_path: Optional path to full-size image (relative to assets/images/).
            icon_path: Optional path to icon/thumbnail (relative to assets/images/).
            category: Item category (e.g., "potion", "key", "photo"). Default is "general".
                     Used to identify item types for script filtering and effects.
            acquired: Whether the item should be immediately acquired. Default is True.
            consumable: Whether the item can be consumed from the inventory overlay. Default is False.
        """
        self.item_id = item_id if item_id else str(uuid.uuid4())
        self.name = name
        self.description = description
        self.image_path = image_path
        self.icon_path = icon_path
        self.category = category
        self.acquired = acquired
        self.consumable = consumable
        self.started = False
        self.success = False

    def execute(self, context: GameContext) -> bool:
        """Add the item if not already started.

        Returns:
            True if item was successfully added, False otherwise (blocks script progression).
        """
        if not self.started:
            item = InventoryItem(
                id=self.item_id,
                name=self.name,
                description=self.description,
                image_path=self.image_path,
                icon_path=self.icon_path,
                category=self.category,
                acquired=self.acquired,
                consumable=self.consumable,
            )

            inventory_plugin = context.inventory_plugin
            self.success = inventory_plugin.add_item(item)
            self.started = True

            if self.success:
                logger.debug("AddItemAction: Successfully added item %s (%s)", self.item_id, self.name)
            else:
                logger.debug("AddItemAction: Failed to add item %s (may already exist)", self.item_id)

        return self.success

    def reset(self) -> None:
        """Reset the action."""
        self.started = False
        self.success = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AddItemAction:
        """Create AddItemAction from a dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            item_id=data.get("item_id") if data.get("item_id") else None,
            image_path=data.get("image_path"),
            icon_path=data.get("icon_path"),
            category=data.get("category", "general"),
            acquired=data.get("acquired", True),
            consumable=data.get("consumable", False),
        )

    @classmethod
    def validate_params(cls, data: dict[str, Any]) -> list[str]:
        """Validate add_item action parameters.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors = []
        name = data.get("name")
        if not name:
            errors.append("missing required 'name' field")
        elif not isinstance(name, str):
            errors.append("'name' must be a string")

        if "description" in data and not isinstance(data["description"], str):
            errors.append("'description' must be a string")

        if "item_id" in data and data["item_id"] is not None and not isinstance(data["item_id"], str):
            errors.append("'item_id' must be a string")

        if "image_path" in data and data["image_path"] is not None and not isinstance(data["image_path"], str):
            errors.append("'image_path' must be a string")

        if "icon_path" in data and data["icon_path"] is not None and not isinstance(data["icon_path"], str):
            errors.append("'icon_path' must be a string")

        if "category" in data and not isinstance(data["category"], str):
            errors.append("'category' must be a string")

        if "acquired" in data and not isinstance(data["acquired"], bool):
            errors.append("'acquired' must be a bool")

        if "consumable" in data and not isinstance(data["consumable"], bool):
            errors.append("'consumable' must be a bool")

        return errors


@ActionRegistry.register("consume_item")
class ConsumeItemAction(Action):
    """Consume an item from the player's inventory.

    This action consumes a specified item by calling the inventory plugin's consume_item()
    method. The item must already be acquired and not previously consumed. Once consumed,
    the item will no longer appear in the inventory display.

    Consuming an item is typically used for:
    - Consumable items (health potions, food, temporary buffs)
    - Quest items that are used once (key cards, tokens)
    - Resources that get depleted (ammunition, materials)

    The action completes immediately after attempting to consume the item. It returns True
    regardless of whether the item was successfully consumed, so it can be used safely in
    scripts without blocking progression.

    Example usage:
        {
            "type": "consume_item",
            "item_id": "health_potion"
        }

        # In a script for using a consumable
        {
            "actions": [
                {"type": "consume_item", "item_id": "ancient_key"},
                {"type": "dialog", "speaker": "Narrator", "text": ["The key dissolves into dust..."]},
                {"type": "wait_for_dialog_close"}
            ]
        }
    """

    def __init__(self, item_id: str) -> None:
        """Initialize consume item action.

        Args:
            item_id: Unique identifier of the item to consume. Must match an item
                    ID in the inventory plugin's registry.
        """
        self.item_id = item_id
        self.started = False

    def execute(self, context: GameContext) -> bool:
        """Consume the item if not already started."""
        if not self.started:
            inventory_plugin = context.inventory_plugin
            inventory_plugin.consume_item(self.item_id)
            self.started = True
            logger.debug("ConsumeItemAction: Consumed item %s", self.item_id)

        # Action completes immediately
        return True

    def reset(self) -> None:
        """Reset the action."""
        self.started = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConsumeItemAction:
        """Create ConsumeItemAction from a dictionary."""
        return cls(item_id=data.get("item_id", ""))

    @classmethod
    def validate_params(cls, data: dict[str, Any]) -> list[str]:
        """Validate consume_item action parameters.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors = []
        item_id = data.get("item_id")
        if not item_id:
            errors.append("missing required 'item_id' field")
        elif not isinstance(item_id, str):
            errors.append("'item_id' must be a string")
        return errors
