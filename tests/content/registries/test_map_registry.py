"""Tests for MapRegistry."""

import json
from typing import TYPE_CHECKING

import pytest

from pedre.content.registries.map import MapRegistry
from pedre.content.registry import (
    ContentTypeRegistry,
    DuplicateIDError,
    InvalidDefinitionError,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None]:
    """Clear ContentTypeRegistry before and after each test."""
    ContentTypeRegistry.clear()
    yield
    ContentTypeRegistry.clear()


@pytest.fixture
def registry() -> MapRegistry:
    """Return a fresh MapRegistry instance."""
    return MapRegistry()


VALID_MAP_FULL = {
    "music": "background.ogg",
    "camera_follow": "player",
    "camera_smooth": True,
}

VALID_MAP_MINIMAL = {}


class TestMapRegistryMetadata:
    """Tests for MapRegistry class-level metadata attributes."""

    def test_name(self) -> None:
        """Registry name is 'maps'."""
        assert MapRegistry.name == "maps"

    def test_filename(self) -> None:
        """Registry loads from 'maps.json'."""
        assert MapRegistry.filename == "maps.json"

    def test_display_name(self) -> None:
        """Display name used in error messages is 'Map'."""
        assert MapRegistry.display_name == "Map"

    def test_registered_in_content_type_registry(self) -> None:
        """MapRegistry is discoverable by name after registration."""
        ContentTypeRegistry.register(MapRegistry)
        assert ContentTypeRegistry.is_registered("maps")


class TestMapRegistryValidate:
    """Tests for MapRegistry.validate()."""

    def test_empty_definition_is_valid(self, registry: MapRegistry) -> None:
        """An empty definition (no fields) is valid — all fields are optional."""
        registry.validate("map", {})  # Should not raise

    def test_full_definition_is_valid(self, registry: MapRegistry) -> None:
        """A definition with all fields passes validation."""
        registry.validate("map", VALID_MAP_FULL)

    def test_music_only(self, registry: MapRegistry) -> None:
        """A definition with only 'music' is valid."""
        registry.validate("map", {"music": "beach.ogg"})

    def test_camera_follow_only(self, registry: MapRegistry) -> None:
        """A definition with only 'camera_follow' is valid."""
        registry.validate("map", {"camera_follow": "player"})

    def test_camera_smooth_false(self, registry: MapRegistry) -> None:
        """camera_smooth=False is a valid boolean value."""
        registry.validate("map", {"camera_smooth": False})

    def test_invalid_music_type(self, registry: MapRegistry) -> None:
        """Non-string 'music' raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="'music' must be a string"):
            registry.validate("map", {"music": 123})

    def test_invalid_camera_follow_type(self, registry: MapRegistry) -> None:
        """Non-string 'camera_follow' raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="'camera_follow' must be a string"):
            registry.validate("map", {"camera_follow": True})

    def test_invalid_camera_smooth_type(self, registry: MapRegistry) -> None:
        """Non-bool 'camera_smooth' raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="'camera_smooth' must be a boolean"):
            registry.validate("map", {"camera_smooth": "yes"})

    def test_extra_fields_allowed(self, registry: MapRegistry) -> None:
        """Unknown extra fields are allowed."""
        registry.validate("map", {"music": "bgm.ogg", "custom_field": "value"})


class TestMapRegistryRegisterAndGet:
    """Tests for register(), get(), has(), and all() on MapRegistry."""

    def test_register_and_get(self, registry: MapRegistry) -> None:
        """Registered map can be retrieved by ID."""
        registry.register("map", VALID_MAP_FULL)
        assert registry.get("map") == VALID_MAP_FULL

    def test_duplicate_raises(self, registry: MapRegistry) -> None:
        """Registering the same ID twice raises DuplicateIDError."""
        registry.register("map", VALID_MAP_FULL)
        with pytest.raises(DuplicateIDError):
            registry.register("map", VALID_MAP_FULL)

    def test_has(self, registry: MapRegistry) -> None:
        """has() returns True for registered IDs and False for unknown ones."""
        registry.register("map", VALID_MAP_FULL)
        assert registry.has("map")
        assert not registry.has("unknown")

    def test_all(self, registry: MapRegistry) -> None:
        """all() returns a dict of all registered maps."""
        registry.register("map", {"music": "bgm.ogg"})
        registry.register("beach", {"music": "beach.ogg"})
        assert set(registry.all().keys()) == {"map", "beach"}


class TestMapRegistryLoadFromFile:
    """Tests for MapRegistry.load_from_file()."""

    def test_load_valid_file(self, registry: MapRegistry, tmp_path: Path) -> None:
        """Valid maps.json loads all maps into the registry."""
        maps_file = tmp_path / "maps.json"
        maps_file.write_text(
            json.dumps(
                {
                    "map": {"music": "background.ogg", "camera_follow": "player", "camera_smooth": True},
                    "beach": {"music": "beach.ogg"},
                }
            )
        )
        registry.load_from_file(maps_file)
        assert registry.has("map")
        assert registry.has("beach")
        assert registry.get("map")["music"] == "background.ogg"
        assert registry.get("beach") == {"music": "beach.ogg"}

    def test_load_empty_definitions(self, registry: MapRegistry, tmp_path: Path) -> None:
        """Maps with empty definitions (no properties) are valid."""
        maps_file = tmp_path / "maps.json"
        maps_file.write_text(json.dumps({"dungeon": {}}))
        registry.load_from_file(maps_file)
        assert registry.has("dungeon")
        assert registry.get("dungeon") == {}

    def test_load_invalid_music_type_raises(self, registry: MapRegistry, tmp_path: Path) -> None:
        """A map with non-string 'music' raises InvalidDefinitionError during load."""
        maps_file = tmp_path / "maps.json"
        maps_file.write_text(json.dumps({"map": {"music": 42}}))
        with pytest.raises(InvalidDefinitionError, match="'music' must be a string"):
            registry.load_from_file(maps_file)

    def test_load_invalid_camera_smooth_type_raises(self, registry: MapRegistry, tmp_path: Path) -> None:
        """A map with non-bool 'camera_smooth' raises InvalidDefinitionError during load."""
        maps_file = tmp_path / "maps.json"
        maps_file.write_text(json.dumps({"map": {"camera_smooth": "true"}}))
        with pytest.raises(InvalidDefinitionError, match="'camera_smooth' must be a boolean"):
            registry.load_from_file(maps_file)
