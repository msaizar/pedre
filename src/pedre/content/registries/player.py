"""Player content type registry."""

from typing import Any, ClassVar

from pedre.content.registry import (
    BaseContentRegistry,
    ContentRegistry,
    ContentTypeRegistry,
    InvalidDefinitionError,
)


@ContentTypeRegistry.register
class PlayerRegistry(BaseContentRegistry):
    """Registry for player definitions."""

    name: ClassVar[str] = "players"
    filename: ClassVar[str] = "players.json"
    display_name: ClassVar[str] = "Player"

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Validate player definitions."""
        if "sprite_id" not in definition:
            msg = f"Player '{definition_id}' missing required field 'sprite_id'."
            raise InvalidDefinitionError(msg)

        if "spawn_at_position" in definition:
            spawn = definition["spawn_at_position"]
            if not isinstance(spawn, list):
                msg = f"Player '{definition_id}' field 'spawn_at_position' must be a list."
                raise InvalidDefinitionError(msg)
            for item in spawn:
                if not isinstance(item, str):
                    msg = f"Player '{definition_id}' field 'spawn_at_position' must contain only strings."
                    raise InvalidDefinitionError(msg)

    def validate_cross_references(self, content_registry: ContentRegistry) -> None:
        """Ensure each player's sprite_id references a valid sprite."""
        sprites = content_registry.get_sub_registry("sprites")
        if sprites is None:
            return
        for player_id, player_def in self.all().items():
            sprite_id = player_def["sprite_id"]
            if not sprites.has(sprite_id):
                msg = f"Player '{player_id}' references unknown sprite '{sprite_id}'."
                raise InvalidDefinitionError(msg)
