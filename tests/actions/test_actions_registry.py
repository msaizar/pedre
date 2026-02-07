"""Tests for ActionRegistry."""

from typing import TYPE_CHECKING

import pytest

from pedre.actions.base import Action
from pedre.actions.registry import ActionRegistry

if TYPE_CHECKING:
    from collections.abc import Generator

    from pedre.plugins.game_context import GameContext


class SimpleAction(Action):
    """Simple test action with from_dict."""

    def __init__(self, value: str) -> None:
        """Initialize the action.

        Args:
            value: Test value for the action.
        """
        self.value = value
        self._executed = False

    @classmethod
    def from_dict(cls, data: dict) -> SimpleAction:
        """Create action from dictionary.

        Args:
            data: Dictionary with action data.

        Returns:
            SimpleAction instance.
        """
        return cls(value=data["value"])

    def execute(self, context: GameContext) -> bool:
        """Execute the action.

        Args:
            context: Game context (unused in test).

        Returns:
            True when complete.
        """
        del context  # Unused in test
        if not self._executed:
            self._executed = True
        return True

    def reset(self) -> None:
        """Reset the action state."""
        self._executed = False


class ActionWithoutParser(Action):
    """Test action without from_dict method."""

    def __init__(self) -> None:
        """Initialize the action."""
        self._executed = False

    def execute(self, context: GameContext) -> bool:
        """Execute the action.

        Args:
            context: Game context (unused in test).

        Returns:
            True when complete.
        """
        del context  # Unused in test
        if not self._executed:
            self._executed = True
        return True

    def reset(self) -> None:
        """Reset the action state."""
        self._executed = False


class FailingParserAction(Action):
    """Test action with from_dict that raises an exception."""

    def __init__(self, value: str) -> None:
        """Initialize the action.

        Args:
            value: Test value for the action.
        """
        self.value = value

    @classmethod
    def from_dict(cls, data: dict) -> FailingParserAction:
        """Create action from dictionary (raises exception).

        Args:
            data: Dictionary with action data (unused).

        Returns:
            Never returns, always raises.

        Raises:
            ValueError: Always raised to simulate parsing error.
        """
        del data  # Unused - always raises
        msg = "Invalid data"
        raise ValueError(msg)

    def execute(self, context: GameContext) -> bool:
        """Execute the action.

        Args:
            context: Game context (unused in test).

        Returns:
            True when complete.
        """
        del context  # Unused in test
        return True

    def reset(self) -> None:
        """Reset the action state."""


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None]:
    """Clear the registry before and after each test."""
    ActionRegistry.clear()
    yield
    ActionRegistry.clear()


class TestActionRegistryRegister:
    """Tests for the register decorator."""

    def test_register_with_from_dict(self) -> None:
        """Test registering an action with from_dict classmethod."""

        @ActionRegistry.register("simple_action")
        class TestAction(SimpleAction):
            pass

        # Verify action is registered
        assert ActionRegistry.is_registered("simple_action")
        assert ActionRegistry.get_action_class("simple_action") == TestAction

        # Verify parser is auto-registered
        action = ActionRegistry.parse({"type": "simple_action", "value": "test"})
        assert action is not None
        assert isinstance(action, TestAction)
        assert action.value == "test"

    def test_register_without_from_dict(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test registering an action without from_dict classmethod."""
        caplog.set_level("DEBUG")

        @ActionRegistry.register("no_parser_action")
        class TestAction(ActionWithoutParser):
            pass

        # Verify action is registered but parser is not
        assert ActionRegistry.is_registered("no_parser_action") is False
        assert ActionRegistry.get_action_class("no_parser_action") == TestAction

        # Verify debug log message
        assert "Registered action without parser: no_parser_action" in caplog.text

    def test_register_multiple_actions(self) -> None:
        """Test registering multiple actions."""

        @ActionRegistry.register("action1")
        class Action1(SimpleAction):
            pass

        @ActionRegistry.register("action2")
        class Action2(SimpleAction):
            pass

        assert ActionRegistry.is_registered("action1")
        assert ActionRegistry.is_registered("action2")
        assert ActionRegistry.get_action_class("action1") == Action1
        assert ActionRegistry.get_action_class("action2") == Action2

    def test_register_returns_class(self) -> None:
        """Test that register decorator returns the original class."""

        @ActionRegistry.register("return_test")
        class TestAction(SimpleAction):
            pass

        # The decorator should return the class unchanged
        assert TestAction.__name__ == "TestAction"


class TestActionRegistryRegisterParser:
    """Tests for the register_parser method."""

    def test_register_custom_parser(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test registering a custom parser function."""
        caplog.set_level("DEBUG")

        def custom_parser(data: dict) -> SimpleAction:
            return SimpleAction(value=data["custom_field"])

        ActionRegistry.register_parser("custom_action", custom_parser)

        # Verify parser is registered
        assert ActionRegistry.is_registered("custom_action")

        # Verify debug log message
        assert "Registered custom parser for action: custom_action" in caplog.text

        # Verify parser works
        action = ActionRegistry.parse({"type": "custom_action", "custom_field": "test_value"})
        assert action is not None
        assert isinstance(action, SimpleAction)
        assert action.value == "test_value"

    def test_register_parser_overrides_from_dict(self) -> None:
        """Test that register_parser can override auto-registered parser."""

        @ActionRegistry.register("override_action")
        class TestAction(SimpleAction):
            pass

        # Custom parser that does something different
        def custom_parser(data: dict) -> SimpleAction:
            return SimpleAction(value="custom_" + data["value"])

        ActionRegistry.register_parser("override_action", custom_parser)

        # Verify custom parser is used
        action = ActionRegistry.parse({"type": "override_action", "value": "test"})
        assert action is not None
        assert isinstance(action, SimpleAction)
        assert action.value == "custom_test"


class TestActionRegistryParse:
    """Tests for the parse method."""

    def test_parse_registered_action(self) -> None:
        """Test parsing a registered action."""

        @ActionRegistry.register("test_action")
        class TestAction(SimpleAction):
            pass

        action = ActionRegistry.parse({"type": "test_action", "value": "test"})
        assert action is not None
        assert isinstance(action, TestAction)
        assert action.value == "test"

    def test_parse_missing_type_key(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing action dict without 'type' key."""
        action = ActionRegistry.parse({"value": "test"})
        assert action is None
        assert "Action dict missing 'type' key" in caplog.text

    def test_parse_unregistered_action(self) -> None:
        """Test parsing an unregistered action type."""
        action = ActionRegistry.parse({"type": "unknown_action", "value": "test"})
        assert action is None

    def test_parse_with_parser_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing when parser raises an exception."""

        @ActionRegistry.register("failing_action")
        class TestAction(FailingParserAction):
            pass

        action = ActionRegistry.parse({"type": "failing_action", "value": "test"})
        assert action is None
        assert "Failed to parse action 'failing_action'" in caplog.text

    def test_parse_with_missing_required_field(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing when required field is missing."""

        @ActionRegistry.register("required_field_action")
        class TestAction(SimpleAction):
            pass

        # Missing 'value' field required by SimpleAction.from_dict
        action = ActionRegistry.parse({"type": "required_field_action"})
        assert action is None
        assert "Failed to parse action 'required_field_action'" in caplog.text


class TestActionRegistryGetActionClass:
    """Tests for the get_action_class method."""

    def test_get_action_class_registered(self) -> None:
        """Test getting a registered action class."""

        @ActionRegistry.register("test_action")
        class TestAction(SimpleAction):
            pass

        action_class = ActionRegistry.get_action_class("test_action")
        assert action_class == TestAction

    def test_get_action_class_unregistered(self) -> None:
        """Test getting an unregistered action class."""
        action_class = ActionRegistry.get_action_class("unknown_action")
        assert action_class is None

    def test_get_action_class_without_parser(self) -> None:
        """Test getting action class for action registered without parser."""

        @ActionRegistry.register("no_parser")
        class TestAction(ActionWithoutParser):
            pass

        action_class = ActionRegistry.get_action_class("no_parser")
        assert action_class == TestAction


class TestActionRegistryGetAllTypes:
    """Tests for the get_all_types method."""

    def test_get_all_types_empty(self) -> None:
        """Test getting all types when registry is empty."""
        types = ActionRegistry.get_all_types()
        assert types == []

    def test_get_all_types_with_actions(self) -> None:
        """Test getting all types with registered actions."""

        @ActionRegistry.register("action1")
        class Action1(SimpleAction):
            pass

        @ActionRegistry.register("action2")
        class Action2(SimpleAction):
            pass

        # Register action without parser
        @ActionRegistry.register("action3")
        class Action3(ActionWithoutParser):
            pass

        types = ActionRegistry.get_all_types()
        # Only actions with parsers should be in the list
        assert "action1" in types
        assert "action2" in types
        assert "action3" not in types
        assert len(types) == 2

    def test_get_all_types_returns_list(self) -> None:
        """Test that get_all_types returns a list."""
        types = ActionRegistry.get_all_types()
        assert isinstance(types, list)


class TestActionRegistryIsRegistered:
    """Tests for the is_registered method."""

    def test_is_registered_true(self) -> None:
        """Test is_registered returns True for registered action."""

        @ActionRegistry.register("test_action")
        class TestAction(SimpleAction):
            pass

        assert ActionRegistry.is_registered("test_action") is True

    def test_is_registered_false(self) -> None:
        """Test is_registered returns False for unregistered action."""
        assert ActionRegistry.is_registered("unknown_action") is False

    def test_is_registered_false_for_action_without_parser(self) -> None:
        """Test is_registered returns False for action without parser."""

        @ActionRegistry.register("no_parser")
        class TestAction(ActionWithoutParser):
            pass

        # Action is registered but has no parser
        assert ActionRegistry.is_registered("no_parser") is False
        # But the action class is still retrievable
        assert ActionRegistry.get_action_class("no_parser") is not None


class TestActionRegistryClear:
    """Tests for the clear method."""

    def test_clear_removes_all_actions(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that clear removes all registered actions and parsers."""
        caplog.set_level("DEBUG")

        @ActionRegistry.register("action1")
        class Action1(SimpleAction):
            pass

        @ActionRegistry.register("action2")
        class Action2(SimpleAction):
            pass

        # Verify actions are registered
        assert ActionRegistry.is_registered("action1")
        assert ActionRegistry.is_registered("action2")
        assert ActionRegistry.get_action_class("action1") is not None
        assert ActionRegistry.get_action_class("action2") is not None

        # Clear the registry
        ActionRegistry.clear()

        # Verify everything is cleared
        assert ActionRegistry.is_registered("action1") is False
        assert ActionRegistry.is_registered("action2") is False
        assert ActionRegistry.get_action_class("action1") is None
        assert ActionRegistry.get_action_class("action2") is None
        assert ActionRegistry.get_all_types() == []

        # Verify debug log message
        assert "Action registry cleared" in caplog.text

    def test_clear_on_empty_registry(self) -> None:
        """Test that clear works on an already empty registry."""
        ActionRegistry.clear()
        ActionRegistry.clear()  # Should not raise
        assert ActionRegistry.get_all_types() == []
