"""Module for content registration."""

import json
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pathlib import Path


class RegistryError(Exception):
    """Base error for content registry issues."""


class DuplicateIDError(RegistryError):
    """Error for duplicate registration."""


class MissingDefinitionError(RegistryError):
    """Error for missing definition."""


class InvalidDefinitionError(RegistryError):
    """Error for invalid definition."""


class BaseContentRegistry:
    """Generic registry mapping string IDs to dict definitions."""

    def __init__(self, name: str) -> None:
        """Initialize class attributes."""
        self._name = name
        self._definitions: dict[str, dict[str, Any]] = {}

    def register(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Register a definition."""
        if definition_id in self._definitions:
            msg = f"{self._name} '{definition_id}' is already registered."
            raise DuplicateIDError(msg)
        self._definitions[definition_id] = definition

    def get(self, definition_id: str) -> dict[str, Any]:
        """Retrieve a definition by id."""
        try:
            return self._definitions[definition_id]
        except KeyError as exc:
            msg = f"{self._name} '{definition_id}' is not registered."
            raise MissingDefinitionError(msg) from exc

    def has(self, definition_id: str) -> bool:
        """Check if a definition exists."""
        return definition_id in self._definitions

    def all(self) -> dict[str, dict[str, Any]]:
        """Return all definitions."""
        return dict(self._definitions)

    def load_from_file(self, file_path: Path) -> None:
        """Load definitions from file."""
        if not file_path.exists():
            msg = f"{self._name} file not found: {file_path}"
            raise RegistryError(msg)

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            msg = f"{self._name} file must contain a JSON object mapping IDs to definitions."
            raise InvalidDefinitionError(msg)

        for definition_id, definition in data.items():
            if not isinstance(definition, dict):
                msg = f"{self._name} '{definition_id}' must be an object."
                raise InvalidDefinitionError(msg)
            self.validate(definition_id, definition)
            self.register(definition_id, definition)

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Override in subclasses."""


class SpriteRegistry(BaseContentRegistry):
    """Class for Sprite registry."""

    VALID_ON_COMPLETE: ClassVar[set[str]] = {"idle", "hide"}

    def __init__(self) -> None:
        """Initialize sprite registry."""
        super().__init__("Sprite")

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Validate sprite definitions including per-state structure."""
        for field in ("sprite_sheet", "frame_width", "frame_height", "states"):
            if field not in definition:
                msg = f"Sprite '{definition_id}' missing required field '{field}'."
                raise InvalidDefinitionError(msg)

        states = definition["states"]
        if not isinstance(states, dict):
            msg = f"Sprite '{definition_id}' states must be a dictionary."
            raise InvalidDefinitionError(msg)

        state_names = set(states.keys())

        for state_name, state_data in states.items():
            prefix = f"Sprite '{definition_id}' state '{state_name}'"

            for req in ("directional", "loop", "priority"):
                if req not in state_data:
                    msg = f"{prefix} missing required field '{req}'."
                    raise InvalidDefinitionError(msg)

            directional = state_data["directional"]
            auto_from = state_data.get("auto_from")
            on_complete = state_data.get("on_complete")

            if on_complete is not None and on_complete not in self.VALID_ON_COMPLETE:
                msg = (
                    f"{prefix} has invalid on_complete '{on_complete}'. "
                    f"Must be one of {sorted(self.VALID_ON_COMPLETE)}."
                )
                raise InvalidDefinitionError(msg)

            if auto_from is not None:
                if auto_from not in state_names:
                    msg = (
                        f"{prefix} auto_from references unknown state '{auto_from}'. "
                        "It must reference another state in the same sprite definition."
                    )
                    raise InvalidDefinitionError(msg)
                # auto_from states don't need explicit frame data
                continue

            if directional:
                directions = state_data.get("directions")
                if not directions or not isinstance(directions, dict):
                    msg = f"{prefix} is directional but missing 'directions' mapping."
                    raise InvalidDefinitionError(msg)
                for dir_name, dir_data in directions.items():
                    for req in ("frames", "row"):
                        if req not in dir_data:
                            msg = f"{prefix} direction '{dir_name}' missing required field '{req}'."
                            raise InvalidDefinitionError(msg)
            else:
                for req in ("frames", "row"):
                    if req not in state_data:
                        msg = f"{prefix} is non-directional but missing required field '{req}'."
                        raise InvalidDefinitionError(msg)


class NPCRegistry(BaseContentRegistry):
    """Class for NPC Registry."""

    def __init__(self) -> None:
        """Initialize NPC registry."""
        super().__init__("NPC")

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Validate NPCs."""
        required = ["sprite_id"]

        for field in required:
            if field not in definition:
                msg = f"NPC '{definition_id}' missing required field '{field}'."
                raise InvalidDefinitionError(msg)


class ContentRegistry:
    """Central content registry owned by the engine.

    Responsible for loading:
        - sprites
        - NPCs

    Can be extended later for enemies, items, etc.
    """

    def __init__(self) -> None:
        """Initialize content registry."""
        self.sprites = SpriteRegistry()
        self.npcs = NPCRegistry()

    def load_from_directory(self, directory: Path) -> None:
        """Load JSON files from directory."""
        sprites_file = directory / "sprites.json"
        npcs_file = directory / "npcs.json"

        if sprites_file.exists():
            self.sprites.load_from_file(sprites_file)

        if npcs_file.exists():
            self.npcs.load_from_file(npcs_file)

    def validate_cross_references(self) -> None:
        """Ensures that NPC.sprite_id references a valid sprite."""
        for npc_id, npc_def in self.npcs.all().items():
            sprite_id = npc_def["sprite_id"]
            if not self.sprites.has(sprite_id):
                msg = f"NPC '{npc_id}' references unknown sprite '{sprite_id}'."
                raise InvalidDefinitionError(msg)
