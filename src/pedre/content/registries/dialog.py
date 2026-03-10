"""Dialog content type registry."""

import json
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pedre.content.registry import (
    BaseContentRegistry,
    ContentRegistry,
    ContentTypeRegistry,
    InvalidDefinitionError,
    RegistryError,
)

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


@ContentTypeRegistry.register
class DialogRegistry(BaseContentRegistry):
    """Registry for NPC dialog definitions.

    Dialog files live in a ``dialogs/`` subdirectory of the content directory,
    one file per scene named ``{scene}.json``:

    .. code-block:: text

        data/content/dialogs/
            village.json
            forest.json

    Each file contains flat composite keys of the form ``"{npc_name}/{level}"``:

    .. code-block:: json

        {
          "merchant/0": {"text": ["Hello, traveller!"], "name": "Old Merchant"},
          "merchant/1": {"text": ["Come back when you have coin."]},
          "guard/0":    {"text": ["Move along."]}
        }

    Entries are stored internally as ``"{scene}/{npc_name}/{level}"`` where
    ``scene`` is the filename stem.
    """

    name: ClassVar[str] = "dialogs"
    filename: ClassVar[str] = "dialogs.json"
    display_name: ClassVar[str] = "Dialog"

    def load_from_directory(self, directory: Path) -> None:
        """Load all ``dialogs/*.json`` files from the given content directory."""
        for file_path in sorted((directory / "dialogs").glob("*.json")):
            self.load_from_file(file_path)

    def load_from_file(self, file_path: Path) -> None:
        """Load dialog definitions from a single ``{scene}.json`` file.

        Args:
            file_path: Path to the dialog JSON file. The scene name is taken
                from the filename stem (e.g. ``village.json`` → ``"village"``).

        Raises:
            RegistryError: If the file does not exist.
            InvalidDefinitionError: If the file is not a valid JSON object or
                any definition fails validation.
        """
        if not file_path.exists():
            msg = f"{self.display_name} file not found: {file_path}"
            raise RegistryError(msg)

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            msg = f"{self.display_name} file must contain a JSON object mapping IDs to definitions."
            raise InvalidDefinitionError(msg)

        scene = file_path.stem

        for composite_key, definition in data.items():
            if not isinstance(definition, dict):
                msg = f"{self.display_name} '{composite_key}' must be an object."
                raise InvalidDefinitionError(msg)
            registry_id = f"{scene}/{composite_key}"
            self.validate(registry_id, definition)
            self.register(registry_id, definition)

    def get_dialog(self, scene: str, npc_name: str, level: int | str) -> dict[str, Any] | None:
        """Return the raw dialog definition for a scene/npc/level, or None if absent."""
        return self._definitions.get(f"{scene}/{npc_name}/{level}")

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Validate that a dialog definition has a non-empty list of text strings."""
        text = definition.get("text")
        if not text:
            msg = f"Dialog '{definition_id}' missing required field 'text'."
            raise InvalidDefinitionError(msg)
        if not isinstance(text, list):
            msg = f"Dialog '{definition_id}' field 'text' must be a list."
            raise InvalidDefinitionError(msg)
        if not all(isinstance(t, str) for t in text):
            msg = f"Dialog '{definition_id}' field 'text' must be a list of strings."
            raise InvalidDefinitionError(msg)

    def validate_cross_references(self, content_registry: ContentRegistry) -> None:
        """Ensure each dialog entry's NPC exists in the NPC registry."""
        npcs = content_registry.get_sub_registry("npcs")
        for dialog_id in self._definitions:
            # key format: "{scene}/{npc_name}/{level}"
            parts = dialog_id.split("/")
            if len(parts) < 3:
                continue
            npc_name = parts[1]
            if not npcs.has(npc_name):
                msg = f"Dialog '{dialog_id}' references unknown NPC '{npc_name}'."
                raise InvalidDefinitionError(msg)
