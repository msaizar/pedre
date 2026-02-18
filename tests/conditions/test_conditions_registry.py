"""Tests for ConditionRegistry."""

from typing import TYPE_CHECKING, Any
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

        @ConditionRegistry.register
        class TestCondition(Condition):
            name = "test_condition"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

        # Verify condition can be checked
        result = ConditionRegistry.is_registered("test_condition")
        assert result is True

    def test_register_multiple_conditions(self, mock_context: GameContext) -> None:
        """Test registering multiple condition classes."""

        @ConditionRegistry.register
        class Condition1(Condition):
            name = "condition1"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition1:
                return cls()

        @ConditionRegistry.register
        class Condition2(Condition):
            name = "condition2"

            def check(self, context: object) -> bool:
                return False

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition2:
                return cls()

        # Verify both conditions work independently
        assert ConditionRegistry.is_registered("condition1") is True
        assert ConditionRegistry.is_registered("condition2") is True

    def test_register_returns_class(self) -> None:
        """Test that register decorator returns the original class."""

        @ConditionRegistry.register
        class TestCondition(Condition):
            name = "return_test"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

        # The decorator should return the class unchanged
        assert TestCondition.__name__ == "TestCondition"
        # And the class should still be instantiable
        instance = TestCondition()
        assert isinstance(instance, TestCondition)

    def test_register_logs_debug_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that registration logs a debug message."""
        caplog.set_level("DEBUG")

        @ConditionRegistry.register
        class TestCondition(Condition):
            name = "debug_condition"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

        assert "Registered condition: debug_condition" in caplog.text


class TestConditionRegistryClear:
    """Tests for the clear method."""

    def test_clear_removes_all_conditions(self, mock_context: GameContext, caplog: pytest.LogCaptureFixture) -> None:
        """Test that clear removes all registered condition classes."""
        caplog.set_level("DEBUG")

        @ConditionRegistry.register
        class Condition1(Condition):
            name = "condition1"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition1:
                return cls()

        @ConditionRegistry.register
        class Condition2(Condition):
            name = "condition2"

            def check(self, context: object) -> bool:
                return False

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition2:
                return cls()

        # Verify conditions are registered
        assert ConditionRegistry.is_registered("condition1") is True
        assert ConditionRegistry.is_registered("condition2") is True

        # Clear the registry
        ConditionRegistry.clear()

        # Verify conditions are no longer registered (should return False and log warnings)
        caplog.clear()
        assert ConditionRegistry.is_registered("condition1") is False
        assert ConditionRegistry.is_registered("condition2") is False

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

        @ConditionRegistry.register
        class FirstCondition(Condition):
            name = "reusable_condition"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> FirstCondition:
                return cls()

        assert ConditionRegistry.is_registered("reusable_condition") is True

        # Clear and re-register
        ConditionRegistry.clear()
        assert ConditionRegistry.is_registered("reusable_condition") is False

        @ConditionRegistry.register
        class SecondCondition(Condition):
            name = "reusable_condition"

            def check(self, context: object) -> bool:
                return False

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> SecondCondition:
                return cls()

        assert ConditionRegistry.is_registered("reusable_condition") is True


class TestConditionRegistryIntrospection:
    """Tests for registry introspection methods."""

    def test_is_registered_returns_true_for_registered_condition(self) -> None:
        """Test is_registered returns True for registered conditions."""

        @ConditionRegistry.register
        class TestCondition(Condition):
            name = "test_condition"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

        assert ConditionRegistry.is_registered("test_condition") is True

    def test_is_registered_returns_false_for_unregistered_condition(self) -> None:
        """Test is_registered returns False for unregistered conditions."""
        assert ConditionRegistry.is_registered("nonexistent_condition") is False

    def test_get_all_types_returns_empty_list_initially(self) -> None:
        """Test get_all_types returns empty list when no conditions registered."""
        assert ConditionRegistry.get_all_names() == []

    def test_get_all_types_returns_registered_conditions(self) -> None:
        """Test get_all_types returns all registered condition names."""

        @ConditionRegistry.register
        class Condition1(Condition):
            name = "condition1"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition1:
                return cls()

        @ConditionRegistry.register
        class Condition2(Condition):
            name = "condition2"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> Condition2:
                return cls()

        types = ConditionRegistry.get_all_names()
        assert len(types) == 2
        assert "condition1" in types
        assert "condition2" in types

    def test_get_all_types_after_clear_returns_empty_list(self) -> None:
        """Test get_all_types returns empty list after clear."""

        @ConditionRegistry.register
        class TempCondition(Condition):
            name = "temp_condition"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TempCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return []

        assert len(ConditionRegistry.get_all_names()) == 1

        ConditionRegistry.clear()

        assert ConditionRegistry.get_all_names() == []
