"""Item content type registry."""

from typing import Any, ClassVar

from pedre.content.registry import (
    BaseContentRegistry,
    ContentTypeRegistry,
    InvalidDefinitionError,
)


@ContentTypeRegistry.register
class ItemRegistry(BaseContentRegistry):
    """Registry for inventory item definitions."""

    name: ClassVar[str] = "items"
    filename: ClassVar[str] = "items.json"
    display_name: ClassVar[str] = "Item"

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Validate an item definition.

        Required fields: ``name``, ``description``.
        Optional fields: ``image_path``, ``icon_path``, ``category`` (str);
        ``acquired``, ``consumable`` (bool).
        """
        for field in ("name", "description"):
            if field not in definition:
                msg = f"Item '{definition_id}' missing required field '{field}'."
                raise InvalidDefinitionError(msg)

        for bool_field in ("acquired", "consumable"):
            if bool_field in definition and not isinstance(definition[bool_field], bool):
                msg = f"Item '{definition_id}' field '{bool_field}' must be a boolean."
                raise InvalidDefinitionError(msg)

        for str_field in ("image_path", "icon_path", "category"):
            if str_field in definition and not isinstance(definition[str_field], str):
                msg = f"Item '{definition_id}' field '{str_field}' must be a string."
                raise InvalidDefinitionError(msg)
