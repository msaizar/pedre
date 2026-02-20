"""Tests for Condition base class."""

from typing import TYPE_CHECKING, Any

import pytest

from pedre.conditions.base import Condition

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext


class TestConditionInitSubclass:
    """Tests for the __init_subclass__ hook in Condition."""

    def test_subclass_without_name_attribute(self) -> None:
        """Test that subclasses without 'name' attribute don't raise errors.

        This tests line 30 - intermediate base classes that don't declare 'name'.
        """

        # This should not raise an error - it's an intermediate base class
        class IntermediateCondition(Condition):
            """Intermediate base class without name."""

            def check(self, context: GameContext) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> IntermediateCondition:
                return cls()

        # The class should be created successfully
        assert IntermediateCondition is not None

    def test_subclass_with_non_string_name(self) -> None:
        """Test that subclasses with non-string 'name' raise TypeError.

        This tests lines 33-34 - validation that 'name' must be a string.
        """
        with pytest.raises(TypeError, match=r".*\.name must be a string"):

            class InvalidCondition(Condition):
                name = 123  # Intentionally wrong type for testing

                def check(self, context: GameContext) -> bool:
                    return True

                @classmethod
                def from_dict(cls, data: dict[str, Any]) -> InvalidCondition:
                    return cls()

    def test_subclass_with_valid_string_name(self) -> None:
        """Test that subclasses with valid string 'name' work correctly."""

        class ValidCondition(Condition):
            name = "valid_condition"

            def check(self, context: GameContext) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> ValidCondition:
                return cls()

        # The class should be created successfully
        assert ValidCondition.name == "valid_condition"
        instance = ValidCondition()
        assert isinstance(instance, Condition)


class TestConditionMethods:
    """Tests for Condition methods."""

    def test_get_references_returns_empty_set_by_default(self) -> None:
        """Test that get_references returns an empty set by default."""

        class TestCondition(Condition):
            name = "test_condition"

            def check(self, context: GameContext) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

        instance = TestCondition()
        references = instance.get_references()
        assert references == set()
        assert isinstance(references, set)
