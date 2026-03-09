"""Map content type registry."""

from typing import Any, ClassVar

from pedre.content.registry import (
    BaseContentRegistry,
    ContentTypeRegistry,
    InvalidDefinitionError,
)


@ContentTypeRegistry.register
class MapRegistry(BaseContentRegistry):
    """Registry for map definitions.

    Maps are keyed by their scene name (TMX filename without extension, lowercase).
    All fields are optional — only define what you want to override from Tiled.

    Example maps.json:
        {
            "map": {
                "music": "background.ogg",
                "camera_follow": "player",
                "camera_smooth": true
            },
            "beach": {
                "music": "beach.ogg"
            }
        }
    """

    name: ClassVar[str] = "maps"
    filename: ClassVar[str] = "maps.json"
    display_name: ClassVar[str] = "Map"

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Validate map definitions."""
        if "music" in definition and not isinstance(definition["music"], str):
            msg = f"Map '{definition_id}' field 'music' must be a string."
            raise InvalidDefinitionError(msg)

        if "camera_follow" in definition and not isinstance(definition["camera_follow"], str):
            msg = f"Map '{definition_id}' field 'camera_follow' must be a string."
            raise InvalidDefinitionError(msg)

        if "camera_smooth" in definition and not isinstance(definition["camera_smooth"], bool):
            msg = f"Map '{definition_id}' field 'camera_smooth' must be a boolean."
            raise InvalidDefinitionError(msg)
