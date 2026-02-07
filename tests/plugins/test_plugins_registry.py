"""Tests for PluginRegistry."""

from typing import TYPE_CHECKING

import pytest

from pedre.plugins.base import BasePlugin
from pedre.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from collections.abc import Generator

    from pedre.plugins.game_context import GameContext


class SimplePlugin(BasePlugin):
    """Simple test plugin."""

    name = "simple"
    dependencies = []

    def setup(self, context: GameContext) -> None:
        """Set up the plugin.

        Args:
            context: Game context (unused in test).
        """
        del context  # Unused in test
        self.setup_called = True

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update the plugin.

        Args:
            delta_time: Time since last update (unused in test).
            context: Game context (unused in test).
        """
        del delta_time, context  # Unused in test


class AnotherPlugin(BasePlugin):
    """Another test plugin."""

    name = "another"
    dependencies = ["simple"]

    def setup(self, context: GameContext) -> None:
        """Set up the plugin.

        Args:
            context: Game context (unused in test).
        """
        del context  # Unused in test

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update the plugin.

        Args:
            delta_time: Time since last update (unused in test).
            context: Game context (unused in test).
        """
        del delta_time, context  # Unused in test


class PluginWithoutName(BasePlugin):
    """Test plugin without a name attribute."""

    dependencies = []

    def setup(self, context: GameContext) -> None:
        """Set up the plugin.

        Args:
            context: Game context (unused in test).
        """
        del context  # Unused in test

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update the plugin.

        Args:
            delta_time: Time since last update (unused in test).
            context: Game context (unused in test).
        """
        del delta_time, context  # Unused in test


class PluginWithEmptyName(BasePlugin):
    """Test plugin with empty name attribute."""

    name = ""
    dependencies = []

    def setup(self, context: GameContext) -> None:
        """Set up the plugin.

        Args:
            context: Game context (unused in test).
        """
        del context  # Unused in test

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update the plugin.

        Args:
            delta_time: Time since last update (unused in test).
            context: Game context (unused in test).
        """
        del delta_time, context  # Unused in test


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None]:
    """Clear the registry before and after each test."""
    PluginRegistry.clear()
    yield
    PluginRegistry.clear()


class TestPluginRegistryRegister:
    """Tests for the register decorator."""

    def test_register_plugin(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test registering a plugin with the decorator."""
        caplog.set_level("DEBUG")

        @PluginRegistry.register
        class TestPlugin(SimplePlugin):
            pass

        # Verify plugin is registered
        assert PluginRegistry.is_registered("simple")
        assert PluginRegistry.get("simple") == TestPlugin

        # Verify debug log message
        assert "Registered plugin: simple" in caplog.text

    def test_register_multiple_plugins(self) -> None:
        """Test registering multiple plugins."""

        @PluginRegistry.register
        class Plugin1(SimplePlugin):
            pass

        @PluginRegistry.register
        class Plugin2(AnotherPlugin):
            pass

        assert PluginRegistry.is_registered("simple")
        assert PluginRegistry.is_registered("another")
        assert PluginRegistry.get("simple") == Plugin1
        assert PluginRegistry.get("another") == Plugin2

    def test_register_returns_class(self) -> None:
        """Test that register decorator returns the original class."""

        @PluginRegistry.register
        class TestPlugin(SimplePlugin):
            pass

        # The decorator should return the class unchanged
        assert TestPlugin.__name__ == "TestPlugin"

    def test_register_without_name_attribute(self) -> None:
        """Test registering a plugin without a name attribute raises ValueError."""
        with pytest.raises(
            ValueError,
            match="Plugin TestPlugin must define a 'name' class attribute",
        ):

            @PluginRegistry.register
            class TestPlugin(PluginWithoutName):
                pass

    def test_register_with_empty_name(self) -> None:
        """Test registering a plugin with empty name raises ValueError."""
        with pytest.raises(
            ValueError,
            match="Plugin TestPlugin must define a 'name' class attribute",
        ):

            @PluginRegistry.register
            class TestPlugin(PluginWithEmptyName):
                pass

    def test_register_duplicate_plugin(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test registering a plugin with a duplicate name logs a warning."""
        caplog.set_level("WARNING")

        @PluginRegistry.register
        class FirstPlugin(SimplePlugin):
            pass

        @PluginRegistry.register
        class SecondPlugin(SimplePlugin):
            pass

        # Second registration should overwrite the first
        assert PluginRegistry.get("simple") == SecondPlugin

        # Verify warning log message
        assert "Plugin 'simple' is being re-registered" in caplog.text
        assert "was FirstPlugin, now SecondPlugin" in caplog.text


class TestPluginRegistryGet:
    """Tests for the get method."""

    def test_get_registered_plugin(self) -> None:
        """Test getting a registered plugin."""

        @PluginRegistry.register
        class TestPlugin(SimplePlugin):
            pass

        plugin_class = PluginRegistry.get("simple")
        assert plugin_class == TestPlugin

    def test_get_unregistered_plugin(self) -> None:
        """Test getting an unregistered plugin returns None."""
        plugin_class = PluginRegistry.get("unknown_plugin")
        assert plugin_class is None

    def test_get_after_clear(self) -> None:
        """Test getting a plugin after clearing the registry returns None."""

        @PluginRegistry.register
        class TestPlugin(SimplePlugin):
            pass

        PluginRegistry.clear()

        plugin_class = PluginRegistry.get("simple")
        assert plugin_class is None


class TestPluginRegistryGetAll:
    """Tests for the get_all method."""

    def test_get_all_empty(self) -> None:
        """Test getting all plugins when registry is empty."""
        plugins = PluginRegistry.get_all()
        assert plugins == {}

    def test_get_all_with_plugins(self) -> None:
        """Test getting all plugins with registered plugins."""

        @PluginRegistry.register
        class Plugin1(SimplePlugin):
            pass

        @PluginRegistry.register
        class Plugin2(AnotherPlugin):
            pass

        plugins = PluginRegistry.get_all()
        assert "simple" in plugins
        assert "another" in plugins
        assert plugins["simple"] == Plugin1
        assert plugins["another"] == Plugin2
        assert len(plugins) == 2

    def test_get_all_returns_copy(self) -> None:
        """Test that get_all returns a copy of the plugins dict."""

        @PluginRegistry.register
        class TestPlugin(SimplePlugin):
            pass

        plugins1 = PluginRegistry.get_all()
        plugins2 = PluginRegistry.get_all()

        # Modifying the returned dict should not affect the registry
        plugins1["modified"] = TestPlugin
        assert "modified" not in plugins2
        assert not PluginRegistry.is_registered("modified")

    def test_get_all_returns_dict(self) -> None:
        """Test that get_all returns a dictionary."""
        plugins = PluginRegistry.get_all()
        assert isinstance(plugins, dict)


class TestPluginRegistryIsRegistered:
    """Tests for the is_registered method."""

    def test_is_registered_true(self) -> None:
        """Test is_registered returns True for registered plugin."""

        @PluginRegistry.register
        class TestPlugin(SimplePlugin):
            pass

        assert PluginRegistry.is_registered("simple") is True

    def test_is_registered_false(self) -> None:
        """Test is_registered returns False for unregistered plugin."""
        assert PluginRegistry.is_registered("unknown_plugin") is False

    def test_is_registered_after_clear(self) -> None:
        """Test is_registered returns False after clearing the registry."""

        @PluginRegistry.register
        class TestPlugin(SimplePlugin):
            pass

        PluginRegistry.clear()

        assert PluginRegistry.is_registered("simple") is False


class TestPluginRegistryClear:
    """Tests for the clear method."""

    def test_clear_removes_all_plugins(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that clear removes all registered plugins."""
        caplog.set_level("DEBUG")

        @PluginRegistry.register
        class Plugin1(SimplePlugin):
            pass

        @PluginRegistry.register
        class Plugin2(AnotherPlugin):
            pass

        # Verify plugins are registered
        assert PluginRegistry.is_registered("simple")
        assert PluginRegistry.is_registered("another")

        # Clear the registry
        PluginRegistry.clear()

        # Verify everything is cleared
        assert PluginRegistry.is_registered("simple") is False
        assert PluginRegistry.is_registered("another") is False
        assert PluginRegistry.get("simple") is None
        assert PluginRegistry.get("another") is None
        assert PluginRegistry.get_all() == {}

        # Verify debug log message
        assert "Plugin registry cleared" in caplog.text

    def test_clear_on_empty_registry(self) -> None:
        """Test that clear works on an already empty registry."""
        PluginRegistry.clear()
        PluginRegistry.clear()  # Should not raise
        assert PluginRegistry.get_all() == {}

    def test_clear_allows_re_registration(self) -> None:
        """Test that plugins can be re-registered after clearing."""

        @PluginRegistry.register
        class FirstPlugin(SimplePlugin):
            pass

        PluginRegistry.clear()

        @PluginRegistry.register
        class SecondPlugin(SimplePlugin):
            pass

        # Should have the new registration
        assert PluginRegistry.get("simple") == SecondPlugin
