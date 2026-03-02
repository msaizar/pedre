"""Tests for ContentTypeRegistry and ContentRegistry."""

import json
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

from pedre.content.registry import (
    BaseContentRegistry,
    ContentRegistry,
    ContentTypeRegistry,
    DuplicateIDError,
    InvalidDefinitionError,
    MissingDefinitionError,
)

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None]:
    """Clear ContentTypeRegistry before and after each test."""
    ContentTypeRegistry.clear()
    yield
    ContentTypeRegistry.clear()


class MinimalRegistry(BaseContentRegistry):
    """Minimal concrete registry for testing."""

    name: ClassVar[str] = "minimal"
    filename: ClassVar[str] = "minimal.json"
    display_name: ClassVar[str] = "Minimal"


class TestContentTypeRegistryRegister:
    """Tests for ContentTypeRegistry.register decorator."""

    def test_register_adds_content_type(self) -> None:
        """Test that registering a subclass makes it discoverable by name."""

        @ContentTypeRegistry.register
        class MyRegistry(MinimalRegistry):
            name = "mytype"
            filename = "mytype.json"
            display_name = "MyType"

        assert ContentTypeRegistry.is_registered("mytype")
        assert ContentTypeRegistry.get("mytype") is MyRegistry

    def test_register_returns_class_unchanged(self) -> None:
        """Test that the register decorator returns the original class unmodified."""

        @ContentTypeRegistry.register
        class MyRegistry(MinimalRegistry):
            name = "mytype"
            filename = "mytype.json"
            display_name = "MyType"

        assert MyRegistry.__name__ == "MyRegistry"

    def test_register_duplicate_raises_error(self) -> None:
        """Test that registering a second class with the same name raises ValueError."""

        @ContentTypeRegistry.register
        class First(MinimalRegistry):
            name = "dup"
            filename = "dup.json"
            display_name = "Dup"

        with pytest.raises(ValueError, match="Content type 'dup' already registered"):

            @ContentTypeRegistry.register
            class Second(MinimalRegistry):
                name = "dup"
                filename = "dup.json"
                display_name = "Dup"

    def test_register_multiple_types(self) -> None:
        """Test that multiple distinct content types can all be registered."""

        @ContentTypeRegistry.register
        class TypeA(MinimalRegistry):
            name = "type_a"
            filename = "a.json"
            display_name = "A"

        @ContentTypeRegistry.register
        class TypeB(MinimalRegistry):
            name = "type_b"
            filename = "b.json"
            display_name = "B"

        assert ContentTypeRegistry.is_registered("type_a")
        assert ContentTypeRegistry.is_registered("type_b")


class TestContentTypeRegistryQuery:
    """Tests for ContentTypeRegistry query methods."""

    def test_get_unregistered_returns_none(self) -> None:
        """Test that get() returns None for an unregistered content type name."""
        assert ContentTypeRegistry.get("nonexistent") is None

    def test_get_all_empty(self) -> None:
        """Test that get_all() returns an empty dict when nothing is registered."""
        assert ContentTypeRegistry.get_all() == {}

    def test_get_all_names_empty(self) -> None:
        """Test that get_all_names() returns an empty list when nothing is registered."""
        assert ContentTypeRegistry.get_all_names() == []

    def test_get_all_names_returns_registered(self) -> None:
        """Test that get_all_names() includes names of all registered types."""

        @ContentTypeRegistry.register
        class TypeA(MinimalRegistry):
            name = "type_a"
            filename = "a.json"
            display_name = "A"

        assert "type_a" in ContentTypeRegistry.get_all_names()

    def test_is_registered_false_for_unknown(self) -> None:
        """Test that is_registered() returns False for an unregistered name."""
        assert ContentTypeRegistry.is_registered("unknown") is False

    def test_get_all_returns_copy(self) -> None:
        """Mutating get_all() result should not affect the registry."""
        result = ContentTypeRegistry.get_all()
        result["injected"] = MinimalRegistry
        assert not ContentTypeRegistry.is_registered("injected")


class TestContentTypeRegistryClear:
    """Tests for ContentTypeRegistry.clear."""

    def test_clear_removes_all_types(self) -> None:
        """Test that clear() removes all registered content types."""

        @ContentTypeRegistry.register
        class TypeA(MinimalRegistry):
            name = "type_a"
            filename = "a.json"
            display_name = "A"

        ContentTypeRegistry.clear()
        assert not ContentTypeRegistry.is_registered("type_a")
        assert ContentTypeRegistry.get_all_names() == []

    def test_clear_on_empty_is_safe(self) -> None:
        """Test that calling clear() on an already-empty registry does not raise."""
        ContentTypeRegistry.clear()
        ContentTypeRegistry.clear()
        assert ContentTypeRegistry.get_all_names() == []


class TestContentRegistryDynamic:
    """Tests for ContentRegistry building from ContentTypeRegistry."""

    def test_empty_registry_has_no_sub_registries(self) -> None:
        """Test that ContentRegistry has no sub-registries when none are registered."""
        registry = ContentRegistry()
        assert registry.get_sub_registry("sprites") is None
        assert registry.get_sub_registry("npcs") is None

    def test_builds_sub_registries_from_registered_types(self) -> None:
        """Test that ContentRegistry instantiates a sub-registry for each registered type."""

        @ContentTypeRegistry.register
        class TypeA(MinimalRegistry):
            name = "type_a"
            filename = "a.json"
            display_name = "A"

        registry = ContentRegistry()
        sub = registry.get_sub_registry("type_a")
        assert sub is not None
        assert isinstance(sub, TypeA)

    def test_multiple_sub_registries(self) -> None:
        """Test that ContentRegistry builds sub-registries for all registered types."""

        @ContentTypeRegistry.register
        class TypeA(MinimalRegistry):
            name = "type_a"
            filename = "a.json"
            display_name = "A"

        @ContentTypeRegistry.register
        class TypeB(MinimalRegistry):
            name = "type_b"
            filename = "b.json"
            display_name = "B"

        registry = ContentRegistry()
        assert registry.get_sub_registry("type_a") is not None
        assert registry.get_sub_registry("type_b") is not None

    def test_get_sub_registry_unknown_returns_none(self) -> None:
        """Test that get_sub_registry() returns None for an unregistered name."""
        registry = ContentRegistry()
        assert registry.get_sub_registry("nonexistent") is None


class TestContentRegistryLoadFromDirectory:
    """Tests for ContentRegistry.load_from_directory."""

    def test_loads_json_for_registered_type(self, tmp_path: pathlib.Path) -> None:
        """Test that load_from_directory reads the correct JSON file for each type."""

        @ContentTypeRegistry.register
        class TypeA(MinimalRegistry):
            name = "type_a"
            filename = "type_a.json"
            display_name = "TypeA"

        data = {"item1": {"value": 1}, "item2": {"value": 2}}
        (tmp_path / "type_a.json").write_text(json.dumps(data))

        registry = ContentRegistry()
        registry.load_from_directory(tmp_path)

        sub = registry.get_sub_registry("type_a")
        assert sub is not None
        assert sub.has("item1")
        assert sub.has("item2")
        assert sub.get("item1") == {"value": 1}

    def test_skips_missing_files(self, tmp_path: pathlib.Path) -> None:
        """Test that load_from_directory silently skips types whose JSON file is absent."""

        @ContentTypeRegistry.register
        class TypeA(MinimalRegistry):
            name = "type_a"
            filename = "type_a.json"
            display_name = "TypeA"

        # No file written — should not raise
        registry = ContentRegistry()
        registry.load_from_directory(tmp_path)
        sub = registry.get_sub_registry("type_a")
        assert sub is not None
        assert sub.all() == {}


class TestContentRegistryValidateCrossReferences:
    """Tests for ContentRegistry.validate_cross_references delegation."""

    def test_calls_each_sub_registry(self) -> None:
        """Test that validate_cross_references() is called on every sub-registry."""
        called: list[str] = []

        @ContentTypeRegistry.register
        class TypeA(MinimalRegistry):
            name = "type_a"
            filename = "a.json"
            display_name = "A"

            def validate_cross_references(self, content_registry: ContentRegistry) -> None:
                called.append("type_a")

        @ContentTypeRegistry.register
        class TypeB(MinimalRegistry):
            name = "type_b"
            filename = "b.json"
            display_name = "B"

            def validate_cross_references(self, content_registry: ContentRegistry) -> None:
                called.append("type_b")

        registry = ContentRegistry()
        registry.validate_cross_references()
        assert "type_a" in called
        assert "type_b" in called

    def test_cross_reference_error_propagates(self) -> None:
        """Test that an InvalidDefinitionError raised in a sub-registry propagates."""

        @ContentTypeRegistry.register
        class TypeA(MinimalRegistry):
            name = "type_a"
            filename = "a.json"
            display_name = "A"

            def validate_cross_references(self, content_registry: ContentRegistry) -> None:
                msg = "broken reference"
                raise InvalidDefinitionError(msg)

        registry = ContentRegistry()
        with pytest.raises(InvalidDefinitionError, match="broken reference"):
            registry.validate_cross_references()


class TestBaseContentRegistry:
    """Tests for BaseContentRegistry core methods."""

    def test_register_and_get(self) -> None:
        """Test that a registered definition can be retrieved by its ID."""
        reg = MinimalRegistry()
        reg.register("item1", {"key": "value"})
        assert reg.get("item1") == {"key": "value"}

    def test_has_true(self) -> None:
        """Test that has() returns True for a registered definition ID."""
        reg = MinimalRegistry()
        reg.register("item1", {})
        assert reg.has("item1") is True

    def test_has_false(self) -> None:
        """Test that has() returns False for an unregistered definition ID."""
        reg = MinimalRegistry()
        assert reg.has("missing") is False

    def test_all_returns_copy(self) -> None:
        """Test that mutating the dict returned by all() does not affect the registry."""
        reg = MinimalRegistry()
        reg.register("item1", {"a": 1})
        result = reg.all()
        result["injected"] = {}
        assert not reg.has("injected")

    def test_duplicate_register_raises(self) -> None:
        """Test that registering a definition ID twice raises DuplicateIDError."""
        reg = MinimalRegistry()
        reg.register("item1", {})
        with pytest.raises(DuplicateIDError, match="Minimal 'item1' is already registered"):
            reg.register("item1", {})

    def test_get_missing_raises(self) -> None:
        """Test that get() raises MissingDefinitionError for an unregistered ID."""
        reg = MinimalRegistry()
        with pytest.raises(MissingDefinitionError, match="Minimal 'missing' is not registered"):
            reg.get("missing")

    def test_load_from_file(self, tmp_path: pathlib.Path) -> None:
        """Test that load_from_file() registers all definitions from a JSON file."""
        data = {"a": {"x": 1}, "b": {"x": 2}}
        f = tmp_path / "minimal.json"
        f.write_text(json.dumps(data))
        reg = MinimalRegistry()
        reg.load_from_file(f)
        assert reg.has("a")
        assert reg.has("b")

    def test_load_from_file_not_dict_raises(self, tmp_path: pathlib.Path) -> None:
        """Test that load_from_file() raises InvalidDefinitionError when root is not a dict."""
        f = tmp_path / "minimal.json"
        f.write_text(json.dumps([1, 2, 3]))
        reg = MinimalRegistry()
        with pytest.raises(InvalidDefinitionError):
            reg.load_from_file(f)

    def test_load_from_file_entry_not_dict_raises(self, tmp_path: pathlib.Path) -> None:
        """Test that load_from_file() raises InvalidDefinitionError when an entry is not a dict."""
        f = tmp_path / "minimal.json"
        f.write_text(json.dumps({"item": "not a dict"}))
        reg = MinimalRegistry()
        with pytest.raises(InvalidDefinitionError):
            reg.load_from_file(f)


class TestCustomContentType:
    """Integration test: end-user defined custom content type."""

    def test_custom_type_loaded_and_accessible(self, tmp_path: pathlib.Path) -> None:
        """Test that a user-defined content type is registered, loaded, and accessible."""

        @ContentTypeRegistry.register
        class EnemyRegistry(BaseContentRegistry):
            name: ClassVar[str] = "enemies"
            filename: ClassVar[str] = "enemies.json"
            display_name: ClassVar[str] = "Enemy"

            def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
                if "health" not in definition:
                    msg = f"Enemy '{definition_id}' missing required field 'health'."
                    raise InvalidDefinitionError(msg)

        enemy_data = {"goblin": {"health": 30}, "orc": {"health": 100}}
        (tmp_path / "enemies.json").write_text(json.dumps(enemy_data))

        registry = ContentRegistry()
        registry.load_from_directory(tmp_path)

        enemies = registry.get_sub_registry("enemies")
        assert enemies is not None
        assert enemies.has("goblin")
        assert enemies.get("goblin") == {"health": 30}
        assert enemies.has("orc")

    def test_custom_type_validation_error(self, tmp_path: pathlib.Path) -> None:
        """Test that validation errors in a custom type propagate during load."""

        @ContentTypeRegistry.register
        class EnemyRegistry(BaseContentRegistry):
            name: ClassVar[str] = "enemies"
            filename: ClassVar[str] = "enemies.json"
            display_name: ClassVar[str] = "Enemy"

            def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
                if "health" not in definition:
                    msg = f"Enemy '{definition_id}' missing required field 'health'."
                    raise InvalidDefinitionError(msg)

        bad_data = {"goblin": {"name": "goblin"}}  # missing "health"
        (tmp_path / "enemies.json").write_text(json.dumps(bad_data))

        registry = ContentRegistry()
        with pytest.raises(InvalidDefinitionError, match="missing required field 'health'"):
            registry.load_from_directory(tmp_path)
