"""Tests for PlayerRegistry."""

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from pedre.content.registries.player import PlayerRegistry
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
def registry() -> PlayerRegistry:
    """Return a fresh PlayerRegistry instance."""
    return PlayerRegistry()


VALID_PLAYER = {"sprite_id": "player_sprite"}
VALID_PLAYER_WITH_SPAWN = {"sprite_id": "player_sprite", "spawn_at_position": ["dungeon"]}


class TestPlayerRegistryMetadata:
    """Tests for PlayerRegistry class-level metadata attributes."""

    def test_name(self) -> None:
        """Registry name is 'players'."""
        assert PlayerRegistry.name == "players"

    def test_filename(self) -> None:
        """Registry loads from 'players.json'."""
        assert PlayerRegistry.filename == "players.json"

    def test_display_name(self) -> None:
        """Display name used in error messages is 'Player'."""
        assert PlayerRegistry.display_name == "Player"

    def test_registered_in_content_type_registry(self) -> None:
        """PlayerRegistry is discoverable by name after registration."""
        ContentTypeRegistry.register(PlayerRegistry)
        assert ContentTypeRegistry.is_registered("players")


class TestPlayerRegistryValidate:
    """Tests for PlayerRegistry.validate()."""

    def test_valid_definition(self, registry: PlayerRegistry) -> None:
        """A definition with sprite_id passes validation."""
        registry.validate("player", VALID_PLAYER)  # Should not raise

    def test_valid_definition_with_spawn_at_position(self, registry: PlayerRegistry) -> None:
        """A definition with sprite_id and spawn_at_position passes validation."""
        registry.validate("player", VALID_PLAYER_WITH_SPAWN)

    def test_valid_spawn_at_position_empty_list(self, registry: PlayerRegistry) -> None:
        """spawn_at_position as an empty list is valid."""
        registry.validate("player", {"sprite_id": "player_sprite", "spawn_at_position": []})

    def test_valid_spawn_at_position_multiple_maps(self, registry: PlayerRegistry) -> None:
        """spawn_at_position with multiple scene names is valid."""
        registry.validate(
            "player",
            {"sprite_id": "player_sprite", "spawn_at_position": ["dungeon", "cave"]},
        )

    def test_missing_sprite_id(self, registry: PlayerRegistry) -> None:
        """Missing 'sprite_id' raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="missing required field 'sprite_id'"):
            registry.validate("player", {})

    def test_spawn_at_position_not_a_list(self, registry: PlayerRegistry) -> None:
        """spawn_at_position that is not a list raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="must be a list"):
            registry.validate("player", {"sprite_id": "player_sprite", "spawn_at_position": "dungeon.tmx"})

    def test_spawn_at_position_with_non_string_item(self, registry: PlayerRegistry) -> None:
        """spawn_at_position containing a non-string raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="must contain only strings"):
            registry.validate("player", {"sprite_id": "player_sprite", "spawn_at_position": [42]})


class TestPlayerRegistryRegisterAndGet:
    """Tests for register(), get(), has(), and all() on PlayerRegistry."""

    def test_register_and_get(self, registry: PlayerRegistry) -> None:
        """Registered player can be retrieved by ID."""
        registry.register("player", VALID_PLAYER)
        assert registry.get("player") == VALID_PLAYER

    def test_duplicate_raises(self, registry: PlayerRegistry) -> None:
        """Registering the same ID twice raises DuplicateIDError."""
        registry.register("player", VALID_PLAYER)
        with pytest.raises(DuplicateIDError):
            registry.register("player", VALID_PLAYER)

    def test_has(self, registry: PlayerRegistry) -> None:
        """has() returns True for registered IDs and False for unknown ones."""
        registry.register("player", VALID_PLAYER)
        assert registry.has("player")
        assert not registry.has("unknown")

    def test_all(self, registry: PlayerRegistry) -> None:
        """all() returns a dict of all registered players."""
        registry.register("player", VALID_PLAYER)
        assert set(registry.all().keys()) == {"player"}


class TestPlayerRegistryLoadFromFile:
    """Tests for PlayerRegistry.load_from_file()."""

    def test_load_valid_file(self, registry: PlayerRegistry, tmp_path: Path) -> None:
        """Valid players.json loads all players into the registry."""
        players_file = tmp_path / "players.json"
        players_file.write_text(
            json.dumps(
                {
                    "player": {"sprite_id": "player_sprite", "spawn_at_position": ["dungeon"]},
                }
            )
        )
        registry.load_from_file(players_file)
        assert registry.has("player")
        assert registry.get("player") == {"sprite_id": "player_sprite", "spawn_at_position": ["dungeon"]}

    def test_load_invalid_player_raises(self, registry: PlayerRegistry, tmp_path: Path) -> None:
        """A player missing sprite_id raises InvalidDefinitionError during load."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps({"player": {"spawn_at_position": []}}))
        with pytest.raises(InvalidDefinitionError, match="missing required field 'sprite_id'"):
            registry.load_from_file(players_file)


class TestPlayerRegistryValidateCrossReferences:
    """Tests for PlayerRegistry.validate_cross_references()."""

    def test_valid_sprite_reference(self, registry: PlayerRegistry) -> None:
        """No error when player's sprite_id exists in the sprites sub-registry."""
        registry.register("player", {"sprite_id": "player_sprite"})

        sprites_mock = MagicMock()
        sprites_mock.has.return_value = True

        content_registry = MagicMock()
        content_registry.get_sub_registry.return_value = sprites_mock

        registry.validate_cross_references(content_registry)
        sprites_mock.has.assert_called_once_with("player_sprite")

    def test_unknown_sprite_reference_raises(self, registry: PlayerRegistry) -> None:
        """A player referencing a non-existent sprite raises InvalidDefinitionError."""
        registry.register("player", {"sprite_id": "ghost_sprite"})

        sprites_mock = MagicMock()
        sprites_mock.has.return_value = False

        content_registry = MagicMock()
        content_registry.get_sub_registry.return_value = sprites_mock

        with pytest.raises(InvalidDefinitionError, match="references unknown sprite 'ghost_sprite'"):
            registry.validate_cross_references(content_registry)

    def test_no_sprites_registry_raises(self, registry: PlayerRegistry) -> None:
        """validate_cross_references() raises RegistryError when sprites sub-registry is absent."""
        registry.register("player", {"sprite_id": "player_sprite"})

        content_registry = MagicMock()
        content_registry.get_sub_registry.side_effect = RegistryError("sprites not registered")

        with pytest.raises(RegistryError):
            registry.validate_cross_references(content_registry)

    def test_empty_registry_skips(self, registry: PlayerRegistry) -> None:
        """validate_cross_references() is a no-op when no players are registered."""
        sprites_mock = MagicMock()
        content_registry = MagicMock()
        content_registry.get_sub_registry.return_value = sprites_mock

        registry.validate_cross_references(content_registry)
        sprites_mock.has.assert_not_called()
