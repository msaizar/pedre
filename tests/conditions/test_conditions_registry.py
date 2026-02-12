"""Tests for ConditionRegistry."""

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock

import pytest

from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry

if TYPE_CHECKING:
    from collections.abc import Generator

    from pedre.plugins.game_context import GameContext


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None]:
    """Clear the registry before and after each test."""
    ConditionRegistry.clear()
    yield
    ConditionRegistry.clear()


@pytest.fixture
def mock_context() -> GameContext:
    """Create a mock GameContext for testing.

    Returns:
        Mock GameContext instance.
    """
    return MagicMock()


class TestConditionRegistryRegister:
    """Tests for the register decorator."""

    def test_register_condition_class(self, mock_context: GameContext) -> None:
        """Test registering a simple condition class."""

        @ConditionRegistry.register("test_condition")
        class TestCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        # Verify condition can be checked
        result = ConditionRegistry.check("test_condition", {}, mock_context)
        assert result is True

    def test_register_multiple_conditions(self, mock_context: GameContext) -> None:
        """Test registering multiple condition classes."""

        @ConditionRegistry.register("condition1")
        class Condition1(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition1:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        @ConditionRegistry.register("condition2")
        class Condition2(Condition):
            def check(self, context: object) -> bool:
                return False

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition2:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        # Verify both conditions work independently
        assert ConditionRegistry.check("condition1", {}, mock_context) is True
        assert ConditionRegistry.check("condition2", {}, mock_context) is False

    def test_register_returns_class(self) -> None:
        """Test that register decorator returns the original class."""

        @ConditionRegistry.register("return_test")
        class TestCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        # The decorator should return the class unchanged
        assert TestCondition.__name__ == "TestCondition"
        # And the class should still be instantiable
        instance = TestCondition()
        assert isinstance(instance, TestCondition)

    def test_register_logs_debug_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that registration logs a debug message."""
        caplog.set_level("DEBUG")

        @ConditionRegistry.register("debug_condition")
        class TestCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        assert "Registered condition class: debug_condition" in caplog.text

    def test_register_condition_can_override(self, mock_context: GameContext) -> None:
        """Test that re-registering a condition replaces the previous class."""

        @ConditionRegistry.register("override_condition")
        class FirstCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> FirstCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        @ConditionRegistry.register("override_condition")
        class SecondCondition(Condition):
            def check(self, context: object) -> bool:
                return False

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> SecondCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        # Verify the second registration took precedence
        result = ConditionRegistry.check("override_condition", {}, mock_context)
        assert result is False


class TestConditionRegistryCheck:
    """Tests for the check method."""

    def test_check_registered_condition_returns_true(self, mock_context: GameContext) -> None:
        """Test checking a registered condition that returns True."""

        @ConditionRegistry.register("true_condition")
        class TrueCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TrueCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        result = ConditionRegistry.check("true_condition", {}, mock_context)
        assert result is True

    def test_check_registered_condition_returns_false(self, mock_context: GameContext) -> None:
        """Test checking a registered condition that returns False."""

        @ConditionRegistry.register("false_condition")
        class FalseCondition(Condition):
            def check(self, context: object) -> bool:
                return False

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> FalseCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        result = ConditionRegistry.check("false_condition", {}, mock_context)
        assert result is False

    def test_check_passes_condition_data(self, mock_context: GameContext) -> None:
        """Test that check uses condition_data to create the instance."""
        received_data: dict[str, Any] = {}

        @ConditionRegistry.register("data_condition")
        class DataCondition(Condition):
            def __init__(self, data: dict[str, Any]) -> None:
                self.data = data

            def check(self, context: object) -> bool:
                received_data.update(self.data)
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> DataCondition:
                return cls(data)

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        test_data = {"key": "value", "number": 42}
        ConditionRegistry.check("data_condition", test_data, mock_context)

        assert received_data == test_data

    def test_check_passes_context(self, mock_context: GameContext) -> None:
        """Test that check passes context to the check method."""
        received_context: GameContext | None = None

        @ConditionRegistry.register("context_condition")
        class ContextCondition(Condition):
            def check(self, context: object) -> bool:
                nonlocal received_context
                received_context = context
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> ContextCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        ConditionRegistry.check("context_condition", {}, mock_context)

        assert received_context is mock_context

    def test_check_unregistered_condition_returns_false(self, mock_context: GameContext) -> None:
        """Test that checking an unregistered condition returns False."""
        result = ConditionRegistry.check("unknown_condition", {}, mock_context)
        assert result is False

    def test_check_unregistered_condition_logs_warning(
        self, mock_context: GameContext, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that checking an unregistered condition logs a warning."""
        ConditionRegistry.check("unknown_condition", {}, mock_context)

        assert "ConditionRegistry: Unknown condition type: unknown_condition" in caplog.text

    def test_check_with_exception_returns_false(self, mock_context: GameContext) -> None:
        """Test that check returns False when check raises an exception."""

        @ConditionRegistry.register("failing_condition")
        class FailingCondition(Condition):
            def check(self, context: object) -> bool:
                msg = "Test exception"
                raise ValueError(msg)

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> FailingCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        result = ConditionRegistry.check("failing_condition", {}, mock_context)
        assert result is False

    def test_check_with_exception_logs_error(self, mock_context: GameContext, caplog: pytest.LogCaptureFixture) -> None:
        """Test that check logs exception when check raises an error."""

        @ConditionRegistry.register("error_condition")
        class ErrorCondition(Condition):
            def check(self, context: object) -> bool:
                msg = "Test exception"
                raise ValueError(msg)

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> ErrorCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        ConditionRegistry.check("error_condition", {}, mock_context)

        assert "ConditionRegistry: Error evaluating condition 'error_condition'" in caplog.text


class TestConditionRegistryClear:
    """Tests for the clear method."""

    def test_clear_removes_all_conditions(self, mock_context: GameContext, caplog: pytest.LogCaptureFixture) -> None:
        """Test that clear removes all registered condition classes."""
        caplog.set_level("DEBUG")

        @ConditionRegistry.register("condition1")
        class Condition1(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition1:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        @ConditionRegistry.register("condition2")
        class Condition2(Condition):
            def check(self, context: object) -> bool:
                return False

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition2:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        # Verify conditions are registered
        assert ConditionRegistry.check("condition1", {}, mock_context) is True
        assert ConditionRegistry.check("condition2", {}, mock_context) is False

        # Clear the registry
        ConditionRegistry.clear()

        # Verify conditions are no longer registered (should return False and log warnings)
        caplog.clear()
        assert ConditionRegistry.check("condition1", {}, mock_context) is False
        assert ConditionRegistry.check("condition2", {}, mock_context) is False
        assert "Unknown condition type: condition1" in caplog.text
        assert "Unknown condition type: condition2" in caplog.text

    def test_clear_on_empty_registry(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that clear works on an already empty registry."""
        caplog.set_level("DEBUG")

        ConditionRegistry.clear()
        ConditionRegistry.clear()  # Should not raise

        # Verify debug log messages (2 clears)
        assert caplog.text.count("Condition registry cleared") == 2

    def test_clear_logs_debug_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that clear logs a debug message."""
        caplog.set_level("DEBUG")

        ConditionRegistry.clear()

        assert "Condition registry cleared" in caplog.text

    def test_clear_allows_re_registration(self, mock_context: GameContext) -> None:
        """Test that conditions can be re-registered after clear."""

        @ConditionRegistry.register("reusable_condition")
        class FirstCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> FirstCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        assert ConditionRegistry.check("reusable_condition", {}, mock_context) is True

        # Clear and re-register
        ConditionRegistry.clear()

        @ConditionRegistry.register("reusable_condition")
        class SecondCondition(Condition):
            def check(self, context: object) -> bool:
                return False

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> SecondCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        assert ConditionRegistry.check("reusable_condition", {}, mock_context) is False


class TestConditionRegistryIntrospection:
    """Tests for registry introspection methods."""

    def test_is_registered_returns_true_for_registered_condition(self) -> None:
        """Test is_registered returns True for registered conditions."""

        @ConditionRegistry.register("test_condition")
        class TestCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        assert ConditionRegistry.is_registered("test_condition") is True

    def test_is_registered_returns_false_for_unregistered_condition(self) -> None:
        """Test is_registered returns False for unregistered conditions."""
        assert ConditionRegistry.is_registered("nonexistent_condition") is False

    def test_get_all_types_returns_empty_list_initially(self) -> None:
        """Test get_all_types returns empty list when no conditions registered."""
        assert ConditionRegistry.get_all_types() == []

    def test_get_all_types_returns_registered_conditions(self) -> None:
        """Test get_all_types returns all registered condition names."""

        @ConditionRegistry.register("condition1")
        class Condition1(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition1:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        @ConditionRegistry.register("condition2")
        class Condition2(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition2:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        types = ConditionRegistry.get_all_types()
        assert len(types) == 2
        assert "condition1" in types
        assert "condition2" in types

    def test_get_all_types_after_clear_returns_empty_list(self) -> None:
        """Test get_all_types returns empty list after clear."""

        @ConditionRegistry.register("temp_condition")
        class TempCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TempCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        assert len(ConditionRegistry.get_all_types()) == 1

        ConditionRegistry.clear()

        assert ConditionRegistry.get_all_types() == []


class TestConditionRegistryIntegration:
    """Integration tests for ConditionRegistry."""

    def test_realistic_condition_checker(self) -> None:
        """Test a realistic condition checker that uses context."""
        # Create a fresh mock for this test to avoid type issues
        mock_context = MagicMock()

        @ConditionRegistry.register("inventory_has_item")
        class InventoryCondition(Condition):
            def __init__(self, item: str) -> None:
                self.item = item

            def check(self, context: object) -> bool:
                # Mock inventory plugin check
                inventory_plugin = cast("Any", context).inventory_plugin
                return inventory_plugin.has_item(self.item)

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> InventoryCondition:
                return cls(item=data.get("item", ""))

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        # Set up mock
        mock_context.inventory_plugin.has_item.return_value = True

        result = ConditionRegistry.check("inventory_has_item", {"item": "sword"}, mock_context)
        assert result is True
        mock_context.inventory_plugin.has_item.assert_called_once_with("sword")

    def test_condition_quest_check(self, mock_context: GameContext) -> None:
        """Test checking a quest condition."""

        @ConditionRegistry.register("quest_completed")
        class QuestCondition(Condition):
            def __init__(self, quest_id: str) -> None:
                self.quest_id = quest_id

            def check(self, context: object) -> bool:
                return self.quest_id == "main_quest"

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> QuestCondition:
                return cls(quest_id=data.get("quest_id", ""))

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        result = ConditionRegistry.check("quest_completed", {"quest_id": "main_quest"}, mock_context)
        assert result is True

    def test_condition_level_check(self, mock_context: GameContext) -> None:
        """Test checking a level condition."""

        @ConditionRegistry.register("level_requirement")
        class LevelCondition(Condition):
            def __init__(self, level: int) -> None:
                self.level = level

            def check(self, context: object) -> bool:
                return self.level >= 10

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> LevelCondition:
                return cls(level=data.get("level", 0))

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        result = ConditionRegistry.check("level_requirement", {"level": 15}, mock_context)
        assert result is True

    def test_condition_item_check(self, mock_context: GameContext) -> None:
        """Test checking an item condition."""

        @ConditionRegistry.register("item_acquired")
        class ItemCondition(Condition):
            def __init__(self, *, has_item: bool) -> None:
                self.has_item = has_item

            def check(self, context: object) -> bool:
                return self.has_item

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> ItemCondition:
                return cls(has_item=data.get("has_item", False))

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        result = ConditionRegistry.check("item_acquired", {"has_item": True}, mock_context)
        assert result is True

    def test_condition_with_default_values(self, mock_context: GameContext) -> None:
        """Test condition checker that provides default values for missing data."""

        @ConditionRegistry.register("level_check")
        class LevelCheckCondition(Condition):
            def __init__(self, required: int, current: int) -> None:
                self.required = required
                self.current = current

            def check(self, context: object) -> bool:
                return self.current >= self.required

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> LevelCheckCondition:
                return cls(
                    required=data.get("required", 1),
                    current=data.get("current", 0),
                )

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        # Test with all data provided
        assert ConditionRegistry.check("level_check", {"required": 5, "current": 10}, mock_context) is True

        # Test with partial data (should use defaults)
        assert ConditionRegistry.check("level_check", {"current": 10}, mock_context) is True

        # Test with missing current level (should fail)
        assert ConditionRegistry.check("level_check", {"required": 5}, mock_context) is False


class TestConditionRegistryValidate:
    """Tests for the validate method."""

    def test_validate_with_validator(self) -> None:
        """Test validate with a registered condition class."""
        ConditionRegistry.clear()

        @ConditionRegistry.register("test_condition")
        class TestCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                errors = []
                if not data.get("required_field"):
                    errors.append("missing required 'required_field' field")
                return errors

        # Valid data
        errors = ConditionRegistry.validate("test_condition", {"required_field": "value"})
        assert errors == []

        # Invalid data
        errors = ConditionRegistry.validate("test_condition", {})
        assert len(errors) == 1
        assert "missing required 'required_field' field" in errors[0]

    def test_validate_unregistered_condition(self) -> None:
        """Test validate with unregistered condition type."""
        ConditionRegistry.clear()

        # Should return empty list for unregistered condition
        errors = ConditionRegistry.validate("nonexistent_condition", {"data": "value"})
        assert errors == []
