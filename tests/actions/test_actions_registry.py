"""Tests for ActionRegistry."""

from typing import TYPE_CHECKING

import pytest

from pedre.actions.base import Action
from pedre.actions.registry import ActionParseError, ActionRegistry

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

        @ActionRegistry.register
        class TestAction(SimpleAction):
            name = "simple_action"

        # Verify action is registered
        assert ActionRegistry.is_registered("simple_action")
        assert ActionRegistry.get("simple_action") == TestAction

        # Verify parser is auto-registered
        action = ActionRegistry.create({"name": "simple_action", "value": "test"})
        assert action is not None
        assert isinstance(action, TestAction)
        assert action.value == "test"

    def test_register_multiple_actions(self) -> None:
        """Test registering multiple actions."""

        @ActionRegistry.register
        class Action1(SimpleAction):
            name = "action1"

        @ActionRegistry.register
        class Action2(SimpleAction):
            name = "action2"

        assert ActionRegistry.is_registered("action1")
        assert ActionRegistry.is_registered("action2")
        assert ActionRegistry.get("action1") == Action1
        assert ActionRegistry.get("action2") == Action2

    def test_register_returns_class(self) -> None:
        """Test that register decorator returns the original class."""

        @ActionRegistry.register
        class TestAction(SimpleAction):
            name = "return_test"

        # The decorator should return the class unchanged
        assert TestAction.__name__ == "TestAction"

    def test_register_duplicate_raises_error(self) -> None:
        """Test that registering an action with a duplicate name raises ValueError."""

        @ActionRegistry.register
        class TestAction1(SimpleAction):
            name = "duplicate_action"

        # Try to register another action with the same name
        with pytest.raises(ValueError, match="Action 'duplicate_action' already registered"):

            @ActionRegistry.register
            class TestAction2(SimpleAction):
                name = "duplicate_action"


class TestActionRegistryCreate:
    """Tests for the create method."""

    def test_create_missing_name_field(self) -> None:
        """Test that create raises ActionParseError when 'name' field is missing."""
        with pytest.raises(ActionParseError, match="Action missing 'name' field"):
            ActionRegistry.create({"value": "test"})

    def test_create_unknown_action(self) -> None:
        """Test that create raises ActionParseError for unknown action name."""
        with pytest.raises(ActionParseError, match="Unknown action 'nonexistent_action'"):
            ActionRegistry.create({"name": "nonexistent_action", "value": "test"})

    def test_create_from_dict_raises_exception(self) -> None:
        """Test that create wraps exceptions from from_dict in ActionParseError."""

        @ActionRegistry.register
        class FailingAction(FailingParserAction):
            name = "failing_action"

        with pytest.raises(ActionParseError, match="Failed to parse action 'failing_action': Invalid data"):
            ActionRegistry.create({"name": "failing_action", "value": "test"})

    def test_create_success(self) -> None:
        """Test successful action creation."""

        @ActionRegistry.register
        class TestAction(SimpleAction):
            name = "test_create"

        action = ActionRegistry.create({"name": "test_create", "value": "test_value"})
        assert isinstance(action, TestAction)
        assert action.value == "test_value"


class TestActionRegistryGet:
    """Tests for the get method."""

    def test_get_registered(self) -> None:
        """Test getting a registered action class."""

        @ActionRegistry.register
        class TestAction(SimpleAction):
            name = "test_action"

        action_class = ActionRegistry.get("test_action")
        assert action_class == TestAction

    def test_get_unregistered(self) -> None:
        """Test getting an unregistered action class."""
        action_class = ActionRegistry.get("unknown_action")
        assert action_class is None


class TestActionRegistryGetAllNames:
    """Tests for the get_all_names method."""

    def test_get_all_names_empty(self) -> None:
        """Test getting all names when registry is empty."""
        names = ActionRegistry.get_all_names()
        assert names == []

    def test_get_all_names_with_actions(self) -> None:
        """Test getting all names with registered actions."""

        @ActionRegistry.register
        class Action1(SimpleAction):
            name = "action1"

        @ActionRegistry.register
        class Action2(SimpleAction):
            name = "action2"

        names = ActionRegistry.get_all_names()
        assert "action1" in names
        assert "action2" in names
        assert len(names) == 2

    def test_get_all_names_returns_list(self) -> None:
        """Test that get_all_names returns a list."""
        names = ActionRegistry.get_all_names()
        assert isinstance(names, list)


class TestActionRegistryIsRegistered:
    """Tests for the is_registered method."""

    def test_is_registered_true(self) -> None:
        """Test is_registered returns True for registered action."""

        @ActionRegistry.register
        class TestAction(SimpleAction):
            name = "test_action"

        assert ActionRegistry.is_registered("test_action") is True

    def test_is_registered_false(self) -> None:
        """Test is_registered returns False for unregistered action."""
        assert ActionRegistry.is_registered("unknown_action") is False


class TestActionRegistryClear:
    """Tests for the clear method."""

    def test_clear_removes_all_actions(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that clear removes all registered actions and parsers."""
        caplog.set_level("DEBUG")

        @ActionRegistry.register
        class Action1(SimpleAction):
            name = "action1"

        @ActionRegistry.register
        class Action2(SimpleAction):
            name = "action2"

        # Verify actions are registered
        assert ActionRegistry.is_registered("action1")
        assert ActionRegistry.is_registered("action2")
        assert ActionRegistry.get("action1") is not None
        assert ActionRegistry.get("action2") is not None

        # Clear the registry
        ActionRegistry.clear()

        # Verify everything is cleared
        assert ActionRegistry.is_registered("action1") is False
        assert ActionRegistry.is_registered("action2") is False
        assert ActionRegistry.get("action1") is None
        assert ActionRegistry.get("action2") is None
        assert ActionRegistry.get_all_names() == []

        # Verify debug log message
        assert "Action registry cleared" in caplog.text

    def test_clear_on_empty_registry(self) -> None:
        """Test that clear works on an already empty registry."""
        ActionRegistry.clear()
        ActionRegistry.clear()  # Should not raise
        assert ActionRegistry.get_all_names() == []
