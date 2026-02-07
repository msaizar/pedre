"""Unit tests for GameContext in src/pedre/plugins/game_context.py."""

from typing import ClassVar
from unittest.mock import Mock

import pytest

from pedre.events import EventBus
from pedre.plugins.base import BasePlugin
from pedre.plugins.game_context import GameContext


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""

    name = "mock"
    dependencies: ClassVar[list[str]] = []

    def setup(self, context: GameContext) -> None:
        """Set up the plugin.

        Args:
            context: Game context (unused in test).
        """
        del context  # Unused in test

    def update(self, delta_time: float) -> None:
        """Update the plugin.

        Args:
            delta_time: Time since last update (unused in test).
        """
        del delta_time  # Unused in test


class MockPluginWithRole(BasePlugin):
    """Mock plugin with a role attribute for testing."""

    name = "mock_with_role"
    role = "test_plugin"
    dependencies: ClassVar[list[str]] = []

    def setup(self, context: GameContext) -> None:
        """Set up the plugin.

        Args:
            context: Game context (unused in test).
        """
        del context  # Unused in test

    def update(self, delta_time: float) -> None:
        """Update the plugin.

        Args:
            delta_time: Time since last update (unused in test).
        """
        del delta_time  # Unused in test


@pytest.fixture
def event_bus() -> EventBus:
    """Create an event bus for testing.

    Returns:
        EventBus instance.
    """
    return EventBus()


@pytest.fixture
def mock_window() -> Mock:
    """Create a mock window for testing.

    Returns:
        Mock arcade.Window instance.
    """
    return Mock()


@pytest.fixture
def game_context(event_bus: EventBus, mock_window: Mock) -> GameContext:
    """Create a game context for testing.

    Args:
        event_bus: Event bus fixture.
        mock_window: Mock window fixture.

    Returns:
        GameContext instance.
    """
    return GameContext(event_bus=event_bus, window=mock_window)


class TestGameContextInit:
    """Test suite for GameContext initialization."""

    def test_init_with_event_bus_and_window(self, event_bus: EventBus, mock_window: Mock) -> None:
        """Test creating a GameContext with event bus and window."""
        context = GameContext(event_bus=event_bus, window=mock_window)

        assert context.event_bus is event_bus
        assert context.window is mock_window

    def test_init_creates_empty_plugins_registry(self, event_bus: EventBus, mock_window: Mock) -> None:
        """Test that initialization creates an empty plugins registry."""
        context = GameContext(event_bus=event_bus, window=mock_window)

        assert context.get_plugins() == {}

    def test_init_creates_pending_save_data_as_none(self, event_bus: EventBus, mock_window: Mock) -> None:
        """Test that initialization sets pending save data to None."""
        context = GameContext(event_bus=event_bus, window=mock_window)

        assert context.get_pending_save_data() is None


class TestGameContextRegisterPlugin:
    """Test suite for GameContext.register_plugin()."""

    def test_register_plugin_stores_in_registry(self, game_context: GameContext) -> None:
        """Test that registering a plugin stores it in the registry."""
        plugin = MockPlugin()

        game_context.register_plugin("test_plugin", plugin)

        assert game_context.get_plugin("test_plugin") is plugin

    def test_register_multiple_plugins(self, game_context: GameContext) -> None:
        """Test registering multiple plugins."""
        plugin1 = MockPlugin()
        plugin2 = MockPlugin()

        game_context.register_plugin("plugin1", plugin1)
        game_context.register_plugin("plugin2", plugin2)

        assert game_context.get_plugin("plugin1") is plugin1
        assert game_context.get_plugin("plugin2") is plugin2

    def test_register_plugin_with_role(self, game_context: GameContext) -> None:
        """Test that registering a plugin with a role sets it as an attribute."""
        plugin = MockPluginWithRole()

        game_context.register_plugin("test_plugin", plugin)

        # Should be accessible via the role attribute
        assert hasattr(game_context, "test_plugin")
        assert game_context.test_plugin is plugin

    def test_register_plugin_without_role(self, game_context: GameContext) -> None:
        """Test that registering a plugin without a role doesn't set attribute."""
        plugin = MockPlugin()
        plugin.role = None

        game_context.register_plugin("test_plugin", plugin)

        # Should not set an attribute
        assert not hasattr(game_context, "test_plugin")
        # But should still be in registry
        assert game_context.get_plugin("test_plugin") is plugin


class TestGameContextGetPlugin:
    """Test suite for GameContext.get_plugin()."""

    def test_get_registered_plugin(self, game_context: GameContext) -> None:
        """Test getting a registered plugin by name."""
        plugin = MockPlugin()
        game_context.register_plugin("test", plugin)

        result = game_context.get_plugin("test")

        assert result is plugin

    def test_get_unregistered_plugin_returns_none(self, game_context: GameContext) -> None:
        """Test getting an unregistered plugin returns None."""
        result = game_context.get_plugin("nonexistent")

        assert result is None

    def test_get_plugin_after_registration(self, game_context: GameContext) -> None:
        """Test that get_plugin reflects newly registered plugins."""
        assert game_context.get_plugin("test") is None

        plugin = MockPlugin()
        game_context.register_plugin("test", plugin)

        assert game_context.get_plugin("test") is plugin


class TestGameContextGetPlugins:
    """Test suite for GameContext.get_plugins()."""

    def test_get_plugins_empty(self, game_context: GameContext) -> None:
        """Test get_plugins returns empty dict when no plugins registered."""
        result = game_context.get_plugins()

        assert result == {}

    def test_get_plugins_returns_all_registered(self, game_context: GameContext) -> None:
        """Test get_plugins returns all registered plugins."""
        plugin1 = MockPlugin()
        plugin2 = MockPlugin()
        game_context.register_plugin("plugin1", plugin1)
        game_context.register_plugin("plugin2", plugin2)

        result = game_context.get_plugins()

        assert result == {"plugin1": plugin1, "plugin2": plugin2}


class TestGameContextPendingSaveData:
    """Test suite for pending save data methods."""

    def test_set_pending_save_data(self, game_context: GameContext) -> None:
        """Test setting pending save data."""
        mock_save_data = Mock()

        game_context.set_pending_save_data(mock_save_data)

        assert game_context.get_pending_save_data() is mock_save_data

    def test_set_pending_save_data_to_none(self, game_context: GameContext) -> None:
        """Test setting pending save data to None."""
        mock_save_data = Mock()
        game_context.set_pending_save_data(mock_save_data)

        game_context.set_pending_save_data(None)

        assert game_context.get_pending_save_data() is None

    def test_get_pending_save_data_default_none(self, game_context: GameContext) -> None:
        """Test that get_pending_save_data returns None by default."""
        result = game_context.get_pending_save_data()

        assert result is None

    def test_clear_pending_save_data(self, game_context: GameContext) -> None:
        """Test clearing pending save data."""
        mock_save_data = Mock()
        game_context.set_pending_save_data(mock_save_data)

        game_context.clear_pending_save_data()

        assert game_context.get_pending_save_data() is None


class TestGameContextStartNewGame:
    """Test suite for GameContext.start_new_game()."""

    def test_start_new_game_with_game_attribute(self, game_context: GameContext) -> None:
        """Test start_new_game calls window.game.start_new_game()."""
        mock_game = Mock()
        game_context.window.game = mock_game

        game_context.start_new_game()

        mock_game.start_new_game.assert_called_once_with()

    def test_start_new_game_without_game_attribute(self, game_context: GameContext) -> None:
        """Test start_new_game does nothing when window has no game attribute."""
        # Remove the game attribute if it exists
        if hasattr(game_context.window, "game"):
            delattr(game_context.window, "game")

        # Should not raise an error
        game_context.start_new_game()


class TestGameContextLoadGame:
    """Test suite for GameContext.load_game()."""

    def test_load_game_with_game_attribute(self, game_context: GameContext) -> None:
        """Test load_game calls window.game.load_game() with save data."""
        mock_game = Mock()
        mock_save_data = Mock()
        game_context.window.game = mock_game

        game_context.load_game(mock_save_data)

        mock_game.load_game.assert_called_once_with(mock_save_data)

    def test_load_game_without_game_attribute(self, game_context: GameContext) -> None:
        """Test load_game does nothing when window has no game attribute."""
        mock_save_data = Mock()
        # Remove the game attribute if it exists
        if hasattr(game_context.window, "game"):
            delattr(game_context.window, "game")

        # Should not raise an error
        game_context.load_game(mock_save_data)


class TestGameContextContinueGame:
    """Test suite for GameContext.continue_game()."""

    def test_continue_game_with_game_attribute(self, game_context: GameContext) -> None:
        """Test continue_game calls window.game.continue_game()."""
        mock_game = Mock()
        game_context.window.game = mock_game

        game_context.continue_game()

        mock_game.continue_game.assert_called_once_with()

    def test_continue_game_without_game_attribute(self, game_context: GameContext) -> None:
        """Test continue_game does nothing when window has no game attribute."""
        # Remove the game attribute if it exists
        if hasattr(game_context.window, "game"):
            delattr(game_context.window, "game")

        # Should not raise an error
        game_context.continue_game()


class TestGameContextIntegration:
    """Integration tests for GameContext."""

    def test_full_plugin_lifecycle(self, game_context: GameContext) -> None:
        """Test complete plugin registration and retrieval workflow."""
        # Register multiple plugins with and without roles
        plugin1 = MockPlugin()
        plugin2 = MockPluginWithRole()

        game_context.register_plugin("plugin1", plugin1)
        game_context.register_plugin("plugin2", plugin2)

        # Verify retrieval by name
        assert game_context.get_plugin("plugin1") is plugin1
        assert game_context.get_plugin("plugin2") is plugin2

        # Verify get_plugins returns all
        all_plugins = game_context.get_plugins()
        assert len(all_plugins) == 2
        assert all_plugins["plugin1"] is plugin1
        assert all_plugins["plugin2"] is plugin2

    def test_facade_methods_with_game(self, game_context: GameContext) -> None:
        """Test all facade methods work together with a game instance."""
        mock_game = Mock()
        mock_save_data = Mock()
        game_context.window.game = mock_game

        # Test start_new_game
        game_context.start_new_game()
        mock_game.start_new_game.assert_called_once()

        # Test load_game
        game_context.load_game(mock_save_data)
        mock_game.load_game.assert_called_once_with(mock_save_data)

        # Test continue_game
        game_context.continue_game()
        mock_game.continue_game.assert_called_once()

    def test_save_data_workflow(self, game_context: GameContext) -> None:
        """Test the complete save data pending workflow."""
        mock_save_data = Mock()

        # Initially None
        assert game_context.get_pending_save_data() is None

        # Set pending data
        game_context.set_pending_save_data(mock_save_data)
        assert game_context.get_pending_save_data() is mock_save_data

        # Clear pending data
        game_context.clear_pending_save_data()
        assert game_context.get_pending_save_data() is None


if __name__ == "__main__":
    pytest.main([__file__])
