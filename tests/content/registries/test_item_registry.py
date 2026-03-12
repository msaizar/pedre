"""Tests for ItemRegistry."""

import json
from typing import TYPE_CHECKING

import pytest

from pedre.content.registries.item import ItemRegistry
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
def registry() -> ItemRegistry:
    """Return a fresh ItemRegistry instance."""
    return ItemRegistry()


VALID_ITEM = {
    "name": "Rusty Key",
    "description": "Opens the old tower door.",
}


class TestItemRegistryMetadata:
    """Tests for ItemRegistry class-level metadata attributes."""

    def test_name(self) -> None:
        """Registry name is 'items'."""
        assert ItemRegistry.name == "items"

    def test_filename(self) -> None:
        """Registry loads from 'items.json'."""
        assert ItemRegistry.filename == "items.json"

    def test_display_name(self) -> None:
        """Display name used in error messages is 'Item'."""
        assert ItemRegistry.display_name == "Item"

    def test_registered_in_content_type_registry(self) -> None:
        """ItemRegistry is discoverable by name after registration."""
        # Re-register since autouse fixture cleared it
        ContentTypeRegistry.register(ItemRegistry)
        assert ContentTypeRegistry.is_registered("items")


class TestItemRegistryValidate:
    """Tests for ItemRegistry.validate()."""

    def test_valid_minimal(self, registry: ItemRegistry) -> None:
        """A definition with only required fields passes validation."""
        registry.validate("key_01", VALID_ITEM)  # Should not raise

    def test_valid_all_fields(self, registry: ItemRegistry) -> None:
        """A definition with all optional fields passes validation."""
        registry.validate(
            "potion_01",
            {
                "name": "Health Potion",
                "description": "Restores health.",
                "image_path": "items/potion.png",
                "icon_path": "items/icons/potion.png",
                "category": "consumable",
                "acquired": False,
                "consumable": True,
            },
        )

    def test_missing_name(self, registry: ItemRegistry) -> None:
        """Missing 'name' field raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="missing required field 'name'"):
            registry.validate("key_01", {"description": "A key."})

    def test_missing_description(self, registry: ItemRegistry) -> None:
        """Missing 'description' field raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="missing required field 'description'"):
            registry.validate("key_01", {"name": "Key"})

    def test_invalid_acquired_type(self, registry: ItemRegistry) -> None:
        """Non-boolean 'acquired' value raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="'acquired' must be a boolean"):
            registry.validate("key_01", {**VALID_ITEM, "acquired": "yes"})

    def test_invalid_consumable_type(self, registry: ItemRegistry) -> None:
        """Non-boolean 'consumable' value raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="'consumable' must be a boolean"):
            registry.validate("key_01", {**VALID_ITEM, "consumable": 1})

    def test_invalid_image_path_type(self, registry: ItemRegistry) -> None:
        """Non-string 'image_path' value raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="'image_path' must be a string"):
            registry.validate("key_01", {**VALID_ITEM, "image_path": 42})

    def test_invalid_category_type(self, registry: ItemRegistry) -> None:
        """Non-string 'category' value raises InvalidDefinitionError."""
        with pytest.raises(InvalidDefinitionError, match="'category' must be a string"):
            registry.validate("key_01", {**VALID_ITEM, "category": ["general"]})


class TestItemRegistryRegisterAndGet:
    """Tests for register(), get(), has(), and all() on ItemRegistry."""

    def test_register_and_get(self, registry: ItemRegistry) -> None:
        """Registered item can be retrieved by ID."""
        registry.register("key_01", VALID_ITEM)
        assert registry.get("key_01") == VALID_ITEM

    def test_duplicate_raises(self, registry: ItemRegistry) -> None:
        """Registering the same ID twice raises DuplicateIDError."""
        registry.register("key_01", VALID_ITEM)
        with pytest.raises(DuplicateIDError):
            registry.register("key_01", VALID_ITEM)

    def test_has(self, registry: ItemRegistry) -> None:
        """has() returns True for registered IDs and False for unknown ones."""
        registry.register("key_01", VALID_ITEM)
        assert registry.has("key_01")
        assert not registry.has("unknown")

    def test_all(self, registry: ItemRegistry) -> None:
        """all() returns a dict of all registered items."""
        registry.register("key_01", VALID_ITEM)
        registry.register("key_02", {**VALID_ITEM, "name": "Brass Key"})
        assert set(registry.all().keys()) == {"key_01", "key_02"}


class TestItemRegistryLoadFromFile:
    """Tests for ItemRegistry.load_from_file()."""

    def test_load_valid_file(self, registry: ItemRegistry, tmp_path: Path) -> None:
        """Valid items.json loads all items into the registry."""
        items_file = tmp_path / "items.json"
        items_file.write_text(
            json.dumps(
                {
                    "key_01": {"name": "Rusty Key", "description": "Opens the old tower door."},
                    "photo_01": {"name": "Beach Photo", "description": "A sunny day.", "category": "photo"},
                }
            )
        )
        registry.load_from_file(items_file)
        assert registry.has("key_01")
        assert registry.has("photo_01")
        assert registry.get("key_01")["name"] == "Rusty Key"

    def test_load_invalid_item_raises(self, registry: ItemRegistry, tmp_path: Path) -> None:
        """An item missing a required field raises InvalidDefinitionError during load."""
        items_file = tmp_path / "items.json"
        items_file.write_text(json.dumps({"bad_item": {"name": "No description"}}))
        with pytest.raises(InvalidDefinitionError, match="missing required field 'description'"):
            registry.load_from_file(items_file)
