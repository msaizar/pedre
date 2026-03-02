"""Module for content registration."""

import json
import logging
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class RegistryError(Exception):
    """Base error for content registry issues."""


class DuplicateIDError(RegistryError):
    """Error for duplicate registration."""


class MissingDefinitionError(RegistryError):
    """Error for missing definition."""


class InvalidDefinitionError(RegistryError):
    """Error for invalid definition."""


class BaseContentRegistry:
    """Generic registry mapping string IDs to dict definitions.

    Subclasses must define:
        name: The registry name used as the attribute on ContentRegistry (e.g. "sprites").
        filename: The JSON file to load from the content directory (e.g. "sprites.json").
        display_name: Human-readable name used in error messages (e.g. "Sprite").
    """

    name: ClassVar[str]
    filename: ClassVar[str]
    display_name: ClassVar[str]

    def __init__(self) -> None:
        """Initialize class attributes."""
        self._definitions: dict[str, dict[str, Any]] = {}

    def register(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Register a definition."""
        if definition_id in self._definitions:
            msg = f"{self.display_name} '{definition_id}' is already registered."
            raise DuplicateIDError(msg)
        self._definitions[definition_id] = definition

    def get(self, definition_id: str) -> dict[str, Any]:
        """Retrieve a definition by id."""
        try:
            return self._definitions[definition_id]
        except KeyError as exc:
            msg = f"{self.display_name} '{definition_id}' is not registered."
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
            msg = f"{self.display_name} file not found: {file_path}"
            raise RegistryError(msg)

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            msg = f"{self.display_name} file must contain a JSON object mapping IDs to definitions."
            raise InvalidDefinitionError(msg)

        for definition_id, definition in data.items():
            if not isinstance(definition, dict):
                msg = f"{self.display_name} '{definition_id}' must be an object."
                raise InvalidDefinitionError(msg)
            self.validate(definition_id, definition)
            self.register(definition_id, definition)

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Override in subclasses to validate definitions."""

    def validate_cross_references(self, content_registry: ContentRegistry) -> None:
        """Override in subclasses to validate references to other content types."""


class ContentTypeRegistry:
    """Central registry mapping content type names to BaseContentRegistry subclasses.

    Follows the same pattern as ActionRegistry, EventRegistry, etc.

    Example:
        @ContentTypeRegistry.register
        class EnemyRegistry(BaseContentRegistry):
            name = "enemies"
            filename = "enemies.json"
            display_name = "Enemy"
    """

    _content_types: ClassVar[dict[str, type[BaseContentRegistry]]] = {}

    @classmethod
    def register(cls, content_class: type[BaseContentRegistry]) -> type[BaseContentRegistry]:
        """Decorator to register a BaseContentRegistry subclass."""
        content_name = content_class.name

        if content_name in cls._content_types:
            msg = f"Content type '{content_name}' already registered"
            raise ValueError(msg)

        cls._content_types[content_name] = content_class
        logger.debug("Registered content type: %s", content_name)
        return content_class

    @classmethod
    def get(cls, name: str) -> type[BaseContentRegistry] | None:
        """Get a registered content type class by name."""
        return cls._content_types.get(name)

    @classmethod
    def get_all(cls) -> dict[str, type[BaseContentRegistry]]:
        """Return all registered content type classes."""
        return dict(cls._content_types)

    @classmethod
    def get_all_names(cls) -> list[str]:
        """Return all registered content type names."""
        return list(cls._content_types.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a content type is registered."""
        return name in cls._content_types

    @classmethod
    def clear(cls) -> None:
        """Clear the registry. Primarily useful for testing."""
        cls._content_types.clear()
        logger.debug("ContentTypeRegistry cleared")


class ContentRegistry:
    """Central content registry owned by the engine.

    Dynamically builds sub-registries from all registered BaseContentRegistry
    subclasses in ContentTypeRegistry. Each sub-registry is accessible via
    get_sub_registry(name).

    End users can add custom content types by registering BaseContentRegistry
    subclasses via @ContentTypeRegistry.register and listing their modules in
    settings.INSTALLED_CONTENT.
    """

    def __init__(self) -> None:
        """Initialize content registry from registered content types."""
        self._sub_registries: dict[str, BaseContentRegistry] = {}
        for name, registry_cls in ContentTypeRegistry.get_all().items():
            self._sub_registries[name] = registry_cls()

    def get_sub_registry(self, name: str) -> BaseContentRegistry | None:
        """Get a sub-registry by name (e.g. "sprites", "npcs")."""
        return self._sub_registries.get(name)

    def load_from_directory(self, directory: Path) -> None:
        """Load JSON files from directory for each registered content type."""
        for sub_registry in self._sub_registries.values():
            file_path = directory / sub_registry.filename
            if file_path.exists():
                sub_registry.load_from_file(file_path)

    def validate_cross_references(self) -> None:
        """Call validate_cross_references on each sub-registry."""
        for sub_registry in self._sub_registries.values():
            sub_registry.validate_cross_references(self)
