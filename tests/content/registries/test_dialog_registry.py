"""Tests for DialogRegistry."""

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from pedre.content.registries.dialog import DialogRegistry
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
def registry() -> DialogRegistry:
    """Return a fresh DialogRegistry instance."""
    return DialogRegistry()


VALID_DIALOG = {"text": ["Hello, traveller!"]}
VALID_DIALOG_WITH_NAME = {"text": ["Welcome to my shop!"], "name": "Old Merchant"}


class TestDialogRegistryMetadata:
    """Tests for DialogRegistry class-level metadata attributes."""

    def test_name(self) -> None:
        """Registry name is 'dialogs'."""
        assert DialogRegistry.name == "dialogs"

    def test_filename(self) -> None:
        """Registry filename is 'dialogs.json'."""
        assert DialogRegistry.filename == "dialogs.json"

    def test_display_name(self) -> None:
        """Display name used in error messages is 'Dialog'."""
        assert DialogRegistry.display_name == "Dialog"

    def test_registered_in_content_type_registry(self) -> None:
        """DialogRegistry is discoverable by name after registration."""
        ContentTypeRegistry.register(DialogRegistry)
        assert ContentTypeRegistry.is_registered("dialogs")


class TestDialogRegistryValidate:
    """Tests for DialogRegistry.validate()."""

    def test_valid_definition(self, registry: DialogRegistry) -> None:
        """A definition with non-empty text list passes validation."""
        registry.validate("village/merchant/0", VALID_DIALOG)  # Should not raise

    def test_valid_definition_with_name(self, registry: DialogRegistry) -> None:
        """Extra fields beyond 'text' are allowed."""
        registry.validate("village/merchant/0", VALID_DIALOG_WITH_NAME)

    def test_valid_definition_with_conditions(self, registry: DialogRegistry) -> None:
        """Definitions with conditions and on_condition_fail are allowed."""
        registry.validate(
            "village/merchant/0",
            {
                "text": ["Check your inventory!"],
                "conditions": [{"name": "inventory_accessed", "equals": True}],
                "on_condition_fail": [{"name": "dialog", "speaker": "Merchant", "text": ["Not yet!"]}],
            },
        )

    def test_missing_text(self, registry: DialogRegistry) -> None:
        """Missing 'text' raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="missing required field 'text'"):
            registry.validate("village/merchant/0", {"name": "Merchant"})

    def test_empty_definition(self, registry: DialogRegistry) -> None:
        """Empty definition raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="missing required field 'text'"):
            registry.validate("village/merchant/0", {})

    def test_empty_text_list(self, registry: DialogRegistry) -> None:
        """Empty text list raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="missing required field 'text'"):
            registry.validate("village/merchant/0", {"text": []})

    def test_text_not_a_list(self, registry: DialogRegistry) -> None:
        """Non-list 'text' raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="'text' must be a list"):
            registry.validate("village/merchant/0", {"text": "Hello!"})

    def test_text_list_with_non_strings(self, registry: DialogRegistry) -> None:
        """Text list containing non-strings raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="'text' must be a list of strings"):
            registry.validate("village/merchant/0", {"text": [1, 2, 3]})


class TestDialogRegistryRegisterAndGet:
    """Tests for register(), get(), has(), and all() on DialogRegistry."""

    def test_register_and_get(self, registry: DialogRegistry) -> None:
        """Registered dialog can be retrieved by composite ID."""
        registry.register("village/merchant/0", VALID_DIALOG)
        assert registry.get("village/merchant/0") == VALID_DIALOG

    def test_duplicate_raises(self, registry: DialogRegistry) -> None:
        """Registering the same ID twice raises DuplicateIDError."""
        registry.register("village/merchant/0", VALID_DIALOG)
        with pytest.raises(DuplicateIDError):
            registry.register("village/merchant/0", VALID_DIALOG)

    def test_has(self, registry: DialogRegistry) -> None:
        """has() returns True for registered IDs and False for unknown ones."""
        registry.register("village/merchant/0", VALID_DIALOG)
        assert registry.has("village/merchant/0")
        assert not registry.has("village/merchant/1")
        assert not registry.has("unknown")

    def test_all(self, registry: DialogRegistry) -> None:
        """all() returns a dict of all registered dialogs."""
        registry.register("village/merchant/0", VALID_DIALOG)
        registry.register("village/guard/0", {"text": ["Move along."]})
        assert set(registry.all().keys()) == {"village/merchant/0", "village/guard/0"}


class TestDialogRegistryGetDialog:
    """Tests for DialogRegistry.get_dialog()."""

    def test_get_existing_dialog(self, registry: DialogRegistry) -> None:
        """get_dialog() returns the raw dict for a registered entry."""
        registry.register("village/merchant/0", VALID_DIALOG)
        result = registry.get_dialog("village", "merchant", "0")
        assert result == VALID_DIALOG

    def test_get_missing_dialog_returns_none(self, registry: DialogRegistry) -> None:
        """get_dialog() returns None when the entry does not exist."""
        result = registry.get_dialog("village", "merchant", "99")
        assert result is None

    def test_get_dialog_different_scene(self, registry: DialogRegistry) -> None:
        """get_dialog() does not return dialogs from a different scene."""
        registry.register("forest/merchant/0", VALID_DIALOG)
        assert registry.get_dialog("village", "merchant", "0") is None
        assert registry.get_dialog("forest", "merchant", "0") == VALID_DIALOG


class TestDialogRegistryLoadFromFile:
    """Tests for DialogRegistry.load_from_file()."""

    def test_load_valid_file(self, registry: DialogRegistry, tmp_path: Path) -> None:
        """village.json registers entries with scene prefix 'village'."""
        dialog_file = tmp_path / "village.json"
        dialog_file.write_text(
            json.dumps(
                {
                    "merchant/0": {"text": ["Hello!"], "name": "Merchant"},
                    "guard/0": {"text": ["Move along."]},
                }
            )
        )
        registry.load_from_file(dialog_file)
        assert registry.has("village/merchant/0")
        assert registry.has("village/guard/0")
        assert registry.get("village/merchant/0") == {"text": ["Hello!"], "name": "Merchant"}

    def test_scene_extracted_from_stem(self, registry: DialogRegistry, tmp_path: Path) -> None:
        """Scene name is the filename stem."""
        dialog_file = tmp_path / "forest.json"
        dialog_file.write_text(json.dumps({"ranger/0": {"text": ["Welcome to the forest."]}}))
        registry.load_from_file(dialog_file)
        assert registry.has("forest/ranger/0")

    def test_invalid_definition_raises(self, registry: DialogRegistry, tmp_path: Path) -> None:
        """An entry missing 'text' raises InvalidDefinitionError during load."""
        dialog_file = tmp_path / "village.json"
        dialog_file.write_text(json.dumps({"merchant/0": {"name": "No text here"}}))
        with pytest.raises(InvalidDefinitionError, match="missing required field 'text'"):
            registry.load_from_file(dialog_file)

    def test_non_dict_root_raises(self, registry: DialogRegistry, tmp_path: Path) -> None:
        """A file with a JSON array root raises InvalidDefinitionError."""
        dialog_file = tmp_path / "village.json"
        dialog_file.write_text(json.dumps([{"text": ["Hello!"]}]))
        with pytest.raises(InvalidDefinitionError):
            registry.load_from_file(dialog_file)


class TestDialogRegistryLoadFromDirectory:
    """Tests for DialogRegistry.load_from_directory()."""

    def test_loads_all_dialog_files(self, registry: DialogRegistry, tmp_path: Path) -> None:
        """load_from_directory globs dialogs/*.json and loads each file."""
        dialogs_dir = tmp_path / "dialogs"
        dialogs_dir.mkdir()
        (dialogs_dir / "village.json").write_text(json.dumps({"merchant/0": {"text": ["Hello!"]}}))
        (dialogs_dir / "forest.json").write_text(json.dumps({"ranger/0": {"text": ["Welcome."]}}))
        # Sibling files outside dialogs/ should be ignored
        (tmp_path / "npcs.json").write_text(json.dumps({"npc_01": {"sprite_id": "hero"}}))

        registry.load_from_directory(tmp_path)

        assert registry.has("village/merchant/0")
        assert registry.has("forest/ranger/0")
        assert not registry.has("default/npc_01/sprite_id")

    def test_empty_directory_loads_nothing(self, registry: DialogRegistry, tmp_path: Path) -> None:
        """load_from_directory with no dialogs/ subdir registers nothing."""
        registry.load_from_directory(tmp_path)
        assert registry.all() == {}

    def test_no_dialog_files_loads_nothing(self, registry: DialogRegistry, tmp_path: Path) -> None:
        """load_from_directory with an empty dialogs/ subdir registers nothing."""
        (tmp_path / "dialogs").mkdir()
        (tmp_path / "npcs.json").write_text(json.dumps({}))
        registry.load_from_directory(tmp_path)
        assert registry.all() == {}


class TestDialogRegistryValidateCrossReferences:
    """Tests for DialogRegistry.validate_cross_references()."""

    def test_valid_npc_reference(self, registry: DialogRegistry) -> None:
        """No error when each dialog's NPC exists in the npcs sub-registry."""
        registry.register("village/merchant/0", VALID_DIALOG)

        npcs_mock = MagicMock()
        npcs_mock.has.return_value = True

        content_registry = MagicMock()
        content_registry.get_sub_registry.return_value = npcs_mock

        registry.validate_cross_references(content_registry)
        npcs_mock.has.assert_called_once_with("merchant")

    def test_unknown_npc_reference_raises(self, registry: DialogRegistry) -> None:
        """A dialog referencing a non-existent NPC raises InvalidDefinitionError."""
        registry.register("village/ghost_npc/0", VALID_DIALOG)

        npcs_mock = MagicMock()
        npcs_mock.has.return_value = False

        content_registry = MagicMock()
        content_registry.get_sub_registry.return_value = npcs_mock

        with pytest.raises(InvalidDefinitionError, match="references unknown NPC 'ghost_npc'"):
            registry.validate_cross_references(content_registry)

    def test_no_npcs_registry_raises(self, registry: DialogRegistry) -> None:
        """validate_cross_references() raises RegistryError when npcs sub-registry is absent."""
        registry.register("village/merchant/0", VALID_DIALOG)

        content_registry = MagicMock()
        content_registry.get_sub_registry.side_effect = RegistryError("npcs not registered")

        with pytest.raises(RegistryError):
            registry.validate_cross_references(content_registry)

    def test_empty_registry_skips(self, registry: DialogRegistry) -> None:
        """validate_cross_references() is a no-op when no dialogs are registered."""
        npcs_mock = MagicMock()
        content_registry = MagicMock()
        content_registry.get_sub_registry.return_value = npcs_mock

        registry.validate_cross_references(content_registry)
        npcs_mock.has.assert_not_called()
