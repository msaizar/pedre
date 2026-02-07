"""Tests for ConditionRegistry."""

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

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

    def test_register_condition_checker(self, mock_context: GameContext) -> None:
        """Test registering a simple condition checker."""

        @ConditionRegistry.register("test_condition")
        def test_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in simple test
            return True

        # Verify condition can be checked
        result = ConditionRegistry.check("test_condition", {}, mock_context)
        assert result is True

    def test_register_multiple_conditions(self, mock_context: GameContext) -> None:
        """Test registering multiple condition checkers."""

        @ConditionRegistry.register("condition1")
        def checker1(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in simple test
            return True

        @ConditionRegistry.register("condition2")
        def checker2(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in simple test
            return False

        # Verify both conditions work independently
        assert ConditionRegistry.check("condition1", {}, mock_context) is True
        assert ConditionRegistry.check("condition2", {}, mock_context) is False

    def test_register_returns_function(self) -> None:
        """Test that register decorator returns the original function."""

        @ConditionRegistry.register("return_test")
        def test_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in simple test
            return True

        # The decorator should return the function unchanged
        assert test_checker.__name__ == "test_checker"
        # And the function should still be callable
        assert test_checker({}, MagicMock()) is True

    def test_register_logs_debug_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that registration logs a debug message."""
        caplog.set_level("DEBUG")

        @ConditionRegistry.register("debug_condition")
        def test_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in simple test
            return True

        assert "Registered condition checker: debug_condition" in caplog.text

    def test_register_condition_can_override(self, mock_context: GameContext) -> None:
        """Test that re-registering a condition replaces the previous checker."""

        @ConditionRegistry.register("override_condition")
        def first_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in simple test
            return True

        @ConditionRegistry.register("override_condition")
        def second_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in simple test
            return False

        # Verify the second registration took precedence
        result = ConditionRegistry.check("override_condition", {}, mock_context)
        assert result is False


class TestConditionRegistryCheck:
    """Tests for the check method."""

    def test_check_registered_condition_returns_true(self, mock_context: GameContext) -> None:
        """Test checking a registered condition that returns True."""

        @ConditionRegistry.register("true_condition")
        def true_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in simple test
            return True

        result = ConditionRegistry.check("true_condition", {}, mock_context)
        assert result is True

    def test_check_registered_condition_returns_false(self, mock_context: GameContext) -> None:
        """Test checking a registered condition that returns False."""

        @ConditionRegistry.register("false_condition")
        def false_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in simple test
            return False

        result = ConditionRegistry.check("false_condition", {}, mock_context)
        assert result is False

    def test_check_passes_condition_data(self, mock_context: GameContext) -> None:
        """Test that check passes condition_data to the checker function."""
        received_data: dict[str, Any] = {}

        @ConditionRegistry.register("data_condition")
        def data_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del context  # Unused in this test
            received_data.update(condition_data)
            return True

        test_data = {"key": "value", "number": 42}
        ConditionRegistry.check("data_condition", test_data, mock_context)

        assert received_data == test_data

    def test_check_passes_context(self, mock_context: GameContext) -> None:
        """Test that check passes context to the checker function."""
        received_context: GameContext | None = None

        @ConditionRegistry.register("context_condition")
        def context_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data  # Unused in this test
            nonlocal received_context
            received_context = context
            return True

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
        """Test that check returns False when checker raises an exception."""

        @ConditionRegistry.register("failing_condition")
        def failing_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in test
            msg = "Test exception"
            raise ValueError(msg)

        result = ConditionRegistry.check("failing_condition", {}, mock_context)
        assert result is False

    def test_check_with_exception_logs_error(self, mock_context: GameContext, caplog: pytest.LogCaptureFixture) -> None:
        """Test that check logs exception when checker raises an error."""

        @ConditionRegistry.register("error_condition")
        def error_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in test
            msg = "Test exception"
            raise ValueError(msg)

        ConditionRegistry.check("error_condition", {}, mock_context)

        assert "ConditionRegistry: Error evaluating condition 'error_condition'" in caplog.text

    def test_check_with_runtime_error(self, mock_context: GameContext, caplog: pytest.LogCaptureFixture) -> None:
        """Test that check handles RuntimeError gracefully."""

        @ConditionRegistry.register("runtime_error_condition")
        def runtime_error_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in test
            msg = "Runtime error"
            raise RuntimeError(msg)

        result = ConditionRegistry.check("runtime_error_condition", {}, mock_context)
        assert result is False
        assert "ConditionRegistry: Error evaluating condition 'runtime_error_condition'" in caplog.text

    def test_check_with_type_error(self, mock_context: GameContext, caplog: pytest.LogCaptureFixture) -> None:
        """Test that check handles TypeError gracefully."""

        @ConditionRegistry.register("type_error_condition")
        def type_error_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in test
            msg = "Type error"
            raise TypeError(msg)

        result = ConditionRegistry.check("type_error_condition", {}, mock_context)
        assert result is False
        assert "ConditionRegistry: Error evaluating condition 'type_error_condition'" in caplog.text

    def test_check_with_key_error(self, mock_context: GameContext, caplog: pytest.LogCaptureFixture) -> None:
        """Test that check handles KeyError gracefully."""

        @ConditionRegistry.register("key_error_condition")
        def key_error_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del context  # Unused in test
            # Try to access a key that doesn't exist
            return condition_data["missing_key"]

        result = ConditionRegistry.check("key_error_condition", {}, mock_context)
        assert result is False
        assert "ConditionRegistry: Error evaluating condition 'key_error_condition'" in caplog.text

    def test_check_with_empty_condition_data(self, mock_context: GameContext) -> None:
        """Test checking a condition with empty condition_data dict."""

        @ConditionRegistry.register("empty_data_condition")
        def empty_data_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del context  # Unused in test
            return len(condition_data) == 0

        result = ConditionRegistry.check("empty_data_condition", {}, mock_context)
        assert result is True

    def test_check_with_complex_condition_data(self, mock_context: GameContext) -> None:
        """Test checking a condition with complex nested condition_data."""

        @ConditionRegistry.register("complex_data_condition")
        def complex_data_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del context  # Unused in test
            return condition_data.get("level") == 5 and condition_data.get("items", {}).get("sword") is True

        complex_data = {
            "level": 5,
            "items": {"sword": True, "shield": False},
            "flags": ["completed_quest1", "completed_quest2"],
        }

        result = ConditionRegistry.check("complex_data_condition", complex_data, mock_context)
        assert result is True


class TestConditionRegistryClear:
    """Tests for the clear method."""

    def test_clear_removes_all_conditions(self, mock_context: GameContext, caplog: pytest.LogCaptureFixture) -> None:
        """Test that clear removes all registered condition checkers."""
        caplog.set_level("DEBUG")

        @ConditionRegistry.register("condition1")
        def checker1(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in test
            return True

        @ConditionRegistry.register("condition2")
        def checker2(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in test
            return False

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
        def first_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in test
            return True

        assert ConditionRegistry.check("reusable_condition", {}, mock_context) is True

        # Clear and re-register
        ConditionRegistry.clear()

        @ConditionRegistry.register("reusable_condition")
        def second_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del condition_data, context  # Unused in test
            return False

        assert ConditionRegistry.check("reusable_condition", {}, mock_context) is False


class TestConditionRegistryIntegration:
    """Integration tests for ConditionRegistry."""

    def test_realistic_condition_checker(self) -> None:
        """Test a realistic condition checker that uses context."""
        # Create a fresh mock for this test to avoid type issues
        mock_context = MagicMock()

        @ConditionRegistry.register("inventory_has_item")
        def inventory_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            item_name = condition_data.get("item")
            if not item_name:
                return False

            # Mock inventory plugin check
            inventory_plugin = context.inventory_plugin
            return inventory_plugin.has_item(item_name)

        # Set up mock
        mock_context.inventory_plugin.has_item.return_value = True

        result = ConditionRegistry.check("inventory_has_item", {"item": "sword"}, mock_context)
        assert result is True
        mock_context.inventory_plugin.has_item.assert_called_once_with("sword")

    def test_multiple_conditions_in_sequence(self, mock_context: GameContext) -> None:
        """Test checking multiple conditions in sequence."""

        @ConditionRegistry.register("quest_completed")
        def quest_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del context  # Unused in test
            return condition_data.get("quest_id") == "main_quest"

        @ConditionRegistry.register("level_requirement")
        def level_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del context  # Unused in test
            return condition_data.get("level", 0) >= 10

        @ConditionRegistry.register("item_acquired")
        def item_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del context  # Unused in test
            return condition_data.get("has_item") is True

        # Check all conditions
        quest_result = ConditionRegistry.check("quest_completed", {"quest_id": "main_quest"}, mock_context)
        level_result = ConditionRegistry.check("level_requirement", {"level": 15}, mock_context)
        item_result = ConditionRegistry.check("item_acquired", {"has_item": True}, mock_context)

        assert quest_result is True
        assert level_result is True
        assert item_result is True

    def test_condition_with_default_values(self, mock_context: GameContext) -> None:
        """Test condition checker that provides default values for missing data."""

        @ConditionRegistry.register("level_check")
        def level_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del context  # Unused in test
            required_level = condition_data.get("required", 1)
            current_level = condition_data.get("current", 0)
            return current_level >= required_level

        # Test with all data provided
        assert ConditionRegistry.check("level_check", {"required": 5, "current": 10}, mock_context) is True

        # Test with partial data (should use defaults)
        assert ConditionRegistry.check("level_check", {"current": 10}, mock_context) is True

        # Test with missing current level (should fail)
        assert ConditionRegistry.check("level_check", {"required": 5}, mock_context) is False

    def test_condition_with_boolean_logic(self, mock_context: GameContext) -> None:
        """Test condition checker with complex boolean logic."""

        @ConditionRegistry.register("complex_condition")
        def complex_checker(condition_data: dict[str, Any], context: GameContext) -> bool:
            del context  # Unused in test
            has_key = condition_data.get("has_key", False)
            level = condition_data.get("level", 0)
            quest_complete = condition_data.get("quest_complete", False)

            # Must have key OR (level >= 10 AND quest complete)
            return has_key or (level >= 10 and quest_complete)

        # Test various combinations
        assert (
            ConditionRegistry.check(
                "complex_condition",
                {"has_key": True, "level": 5, "quest_complete": False},
                mock_context,
            )
            is True
        )
        assert (
            ConditionRegistry.check(
                "complex_condition",
                {"has_key": False, "level": 15, "quest_complete": True},
                mock_context,
            )
            is True
        )
        assert (
            ConditionRegistry.check(
                "complex_condition",
                {"has_key": False, "level": 15, "quest_complete": False},
                mock_context,
            )
            is False
        )
        assert (
            ConditionRegistry.check(
                "complex_condition",
                {"has_key": False, "level": 5, "quest_complete": True},
                mock_context,
            )
            is False
        )
