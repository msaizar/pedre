"""Tests for NPCRegistry."""

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from pedre.content.registries.npc import NPCRegistry
from pedre.content.registry import (
    ContentTypeRegistry,
    DuplicateIDError,
    InvalidDefinitionError,
    RegistryError,
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
def registry() -> NPCRegistry:
    """Return a fresh NPCRegistry instance."""
    return NPCRegistry()


VALID_NPC = {"sprite_id": "villager"}


class TestNPCRegistryMetadata:
    """Tests for NPCRegistry class-level metadata attributes."""

    def test_name(self) -> None:
        """Registry name is 'npcs'."""
        assert NPCRegistry.name == "npcs"

    def test_filename(self) -> None:
        """Registry loads from 'npcs.json'."""
        assert NPCRegistry.filename == "npcs.json"

    def test_display_name(self) -> None:
        """Display name used in error messages is 'NPC'."""
        assert NPCRegistry.display_name == "NPC"

    def test_registered_in_content_type_registry(self) -> None:
        """NPCRegistry is discoverable by name after registration."""
        ContentTypeRegistry.register(NPCRegistry)
        assert ContentTypeRegistry.is_registered("npcs")


class TestNPCRegistryValidate:
    """Tests for NPCRegistry.validate()."""

    def test_valid_definition(self, registry: NPCRegistry) -> None:
        """A definition with sprite_id passes validation."""
        registry.validate("npc_01", VALID_NPC)  # Should not raise

    def test_valid_definition_with_extra_fields(self, registry: NPCRegistry) -> None:
        """Extra fields beyond sprite_id are allowed."""
        registry.validate("npc_01", {"sprite_id": "guard", "name": "Guard", "level": 5})

    def test_missing_sprite_id(self, registry: NPCRegistry) -> None:
        """Missing 'sprite_id' raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="missing required field 'sprite_id'"):
            registry.validate("npc_01", {"name": "Villager"})

    def test_empty_definition(self, registry: NPCRegistry) -> None:
        """Empty definition raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="missing required field 'sprite_id'"):
            registry.validate("npc_01", {})


class TestNPCRegistryRegisterAndGet:
    """Tests for register(), get(), has(), and all() on NPCRegistry."""

    def test_register_and_get(self, registry: NPCRegistry) -> None:
        """Registered NPC can be retrieved by ID."""
        registry.register("npc_01", VALID_NPC)
        assert registry.get("npc_01") == VALID_NPC

    def test_duplicate_raises(self, registry: NPCRegistry) -> None:
        """Registering the same ID twice raises DuplicateIDError."""
        registry.register("npc_01", VALID_NPC)
        with pytest.raises(DuplicateIDError):
            registry.register("npc_01", VALID_NPC)

    def test_has(self, registry: NPCRegistry) -> None:
        """has() returns True for registered IDs and False for unknown ones."""
        registry.register("npc_01", VALID_NPC)
        assert registry.has("npc_01")
        assert not registry.has("unknown")

    def test_all(self, registry: NPCRegistry) -> None:
        """all() returns a dict of all registered NPCs."""
        registry.register("npc_01", VALID_NPC)
        registry.register("npc_02", {"sprite_id": "guard"})
        assert set(registry.all().keys()) == {"npc_01", "npc_02"}


class TestNPCRegistryLoadFromFile:
    """Tests for NPCRegistry.load_from_file()."""

    def test_load_valid_file(self, registry: NPCRegistry, tmp_path: Path) -> None:
        """Valid npcs.json loads all NPCs into the registry."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(
            json.dumps(
                {
                    "villager_01": {"sprite_id": "villager"},
                    "guard_01": {"sprite_id": "guard"},
                }
            )
        )
        registry.load_from_file(npcs_file)
        assert registry.has("villager_01")
        assert registry.has("guard_01")
        assert registry.get("villager_01") == {"sprite_id": "villager"}

    def test_load_invalid_npc_raises(self, registry: NPCRegistry, tmp_path: Path) -> None:
        """An NPC missing sprite_id raises InvalidDefinitionError during load."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps({"bad_npc": {"name": "No sprite"}}))
        with pytest.raises(InvalidDefinitionError, match="missing required field 'sprite_id'"):
            registry.load_from_file(npcs_file)


class TestNPCRegistryValidateCrossReferences:
    """Tests for NPCRegistry.validate_cross_references()."""

    def test_valid_sprite_reference(self, registry: NPCRegistry) -> None:
        """No error when each NPC's sprite_id exists in the sprites sub-registry."""
        registry.register("npc_01", {"sprite_id": "villager"})

        sprites_mock = MagicMock()
        sprites_mock.has.return_value = True

        content_registry = MagicMock()
        content_registry.get_sub_registry.return_value = sprites_mock

        registry.validate_cross_references(content_registry)
        sprites_mock.has.assert_called_once_with("villager")

    def test_unknown_sprite_reference_raises(self, registry: NPCRegistry) -> None:
        """An NPC referencing a non-existent sprite raises InvalidDefinitionError."""
        registry.register("npc_01", {"sprite_id": "ghost_sprite"})

        sprites_mock = MagicMock()
        sprites_mock.has.return_value = False

        content_registry = MagicMock()
        content_registry.get_sub_registry.return_value = sprites_mock

        with pytest.raises(InvalidDefinitionError, match="references unknown sprite 'ghost_sprite'"):
            registry.validate_cross_references(content_registry)

    def test_no_sprites_registry_raises(self, registry: NPCRegistry) -> None:
        """validate_cross_references() raises RegistryError when sprites sub-registry is absent."""
        registry.register("npc_01", {"sprite_id": "villager"})

        content_registry = MagicMock()
        content_registry.get_sub_registry.side_effect = RegistryError("sprites not registered")

        with pytest.raises(RegistryError):
            registry.validate_cross_references(content_registry)

    def test_empty_registry_skips(self, registry: NPCRegistry) -> None:
        """validate_cross_references() is a no-op when no NPCs are registered."""
        sprites_mock = MagicMock()
        content_registry = MagicMock()
        content_registry.get_sub_registry.return_value = sprites_mock

        registry.validate_cross_references(content_registry)
        sprites_mock.has.assert_not_called()
