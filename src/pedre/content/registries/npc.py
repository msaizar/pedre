"""NPC content type registry."""

from typing import Any, ClassVar

from pedre.content.registry import (
    BaseContentRegistry,
    ContentRegistry,
    ContentTypeRegistry,
    InvalidDefinitionError,
)


@ContentTypeRegistry.register
class NPCRegistry(BaseContentRegistry):
    """Registry for NPC definitions."""

    name: ClassVar[str] = "npcs"
    filename: ClassVar[str] = "npcs.json"
    display_name: ClassVar[str] = "NPC"

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Validate NPC definitions."""
        for field in ("sprite_id",):
            if field not in definition:
                msg = f"NPC '{definition_id}' missing required field '{field}'."
                raise InvalidDefinitionError(msg)

    def validate_cross_references(self, content_registry: ContentRegistry) -> None:
        """Ensure each NPC's sprite_id references a valid sprite."""
        sprites = content_registry.get_sub_registry("sprites")
        if sprites is None:
            return
        for npc_id, npc_def in self.all().items():
            sprite_id = npc_def["sprite_id"]
            if not sprites.has(sprite_id):
                msg = f"NPC '{npc_id}' references unknown sprite '{sprite_id}'."
                raise InvalidDefinitionError(msg)
