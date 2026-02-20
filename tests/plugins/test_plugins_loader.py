"""Unit tests for PluginLoader."""

import unittest
from typing import ClassVar
from unittest.mock import MagicMock, Mock, patch

import pytest

from pedre.plugins.base import BasePlugin
from pedre.plugins.loader import (
    CircularDependencyError,
    MissingDependencyError,
    PluginLoader,
)
from pedre.plugins.registry import PluginRegistry


# Test plugin classes for dependency resolution tests
class PluginA(BasePlugin):
    """Test plugin with no dependencies."""

    name = "plugin_a"
    dependencies: ClassVar[list[str]] = []


class PluginB(BasePlugin):
    """Test plugin depending on A."""

    name = "plugin_b"
    dependencies: ClassVar[list[str]] = ["plugin_a"]


class PluginC(BasePlugin):
    """Test plugin depending on B."""

    name = "plugin_c"
    dependencies: ClassVar[list[str]] = ["plugin_b"]


class PluginD(BasePlugin):
    """Test plugin depending on A and C."""

    name = "plugin_d"
    dependencies: ClassVar[list[str]] = ["plugin_a", "plugin_c"]


class PluginCircular1(BasePlugin):
    """Test plugin with circular dependency."""

    name = "circular_1"
    dependencies: ClassVar[list[str]] = ["circular_2"]


class PluginCircular2(BasePlugin):
    """Test plugin with circular dependency."""

    name = "circular_2"
    dependencies: ClassVar[list[str]] = ["circular_1"]


class PluginMissingDep(BasePlugin):
    """Test plugin with missing dependency."""

    name = "missing_dep"
    dependencies: ClassVar[list[str]] = ["nonexistent_plugin"]


class TestPluginLoader(unittest.TestCase):
    """Unit test class for PluginLoader."""

    def setUp(self) -> None:
        """Set up PluginLoader for each test."""
        self.loader = PluginLoader()
        # Save original registry and clear it
        self._original_plugins = PluginRegistry._plugins.copy()
        PluginRegistry._plugins = {}

    def tearDown(self) -> None:
        """Clean up after each test."""
        # Restore original registry
        PluginRegistry._plugins = self._original_plugins

    def test_load_modules_success(self) -> None:
        """Test loading plugin modules successfully."""
        with (
            patch("pedre.plugins.loader.settings") as mock_settings,
            patch("pedre.plugins.loader.importlib.import_module") as mock_import,
        ):
            mock_settings.INSTALLED_PLUGINS = [
                "test.module.one",
                "test.module.two",
            ]

            self.loader.load_modules()

            assert mock_import.call_count == 2
            mock_import.assert_any_call("test.module.one")
            mock_import.assert_any_call("test.module.two")

    @patch("pedre.plugins.loader.importlib.import_module")
    def test_load_modules_import_error(self, mock_import: Mock) -> None:
        """Test that load_modules raises ImportError on failure."""
        with patch("pedre.plugins.loader.settings") as mock_settings:
            mock_settings.INSTALLED_PLUGINS = ["nonexistent.module"]
            mock_import.side_effect = ImportError("Module not found")

            with pytest.raises(ImportError):
                self.loader.load_modules()

    def test_instantiate_all_no_plugins(self) -> None:
        """Test instantiate_all with no registered plugins."""
        with patch("pedre.plugins.loader.settings") as mock_settings:
            mock_settings.INSTALLED_PLUGINS = []

            instances = self.loader.instantiate_all()

            assert instances == {}
            assert len(self.loader._instances) == 0
            assert len(self.loader._load_order) == 0

    def test_instantiate_all_with_dependencies(self) -> None:
        """Test instantiate_all resolves dependencies correctly."""
        with patch("pedre.plugins.loader.settings") as mock_settings:
            mock_settings.INSTALLED_PLUGINS = []

            # Register plugins directly
            PluginRegistry._plugins = {
                "plugin_a": PluginA,
                "plugin_b": PluginB,
                "plugin_c": PluginC,
                "plugin_d": PluginD,
            }

            instances = self.loader.instantiate_all()

            # Check all plugins instantiated
            assert len(instances) == 4
            assert "plugin_a" in instances
            assert "plugin_b" in instances
            assert "plugin_c" in instances
            assert "plugin_d" in instances

            # Check dependency order
            load_order = self.loader._load_order
            assert load_order.index("plugin_a") < load_order.index("plugin_b")
            assert load_order.index("plugin_b") < load_order.index("plugin_c")
            assert load_order.index("plugin_a") < load_order.index("plugin_d")
            assert load_order.index("plugin_c") < load_order.index("plugin_d")

    def test_instantiate_all_circular_dependency(self) -> None:
        """Test instantiate_all raises error on circular dependencies."""
        with patch("pedre.plugins.loader.settings") as mock_settings:
            mock_settings.INSTALLED_PLUGINS = []

            # Register plugins with circular dependencies
            PluginRegistry._plugins = {
                "circular_1": PluginCircular1,
                "circular_2": PluginCircular2,
            }

            with pytest.raises(CircularDependencyError) as context:
                self.loader.instantiate_all()

            assert "Circular dependency detected" in str(context.value)

    def test_instantiate_all_missing_dependency(self) -> None:
        """Test instantiate_all raises error on missing dependencies."""
        with patch("pedre.plugins.loader.settings") as mock_settings:
            mock_settings.INSTALLED_PLUGINS = []

            # Register plugin with missing dependency
            PluginRegistry._plugins = {
                "missing_dep": PluginMissingDep,
            }

            with pytest.raises(MissingDependencyError) as context:
                self.loader.instantiate_all()

            assert "depends on 'nonexistent_plugin'" in str(context.value)

    def test_setup_all(self) -> None:
        """Test setup_all calls setup on all plugins."""
        # Create mock plugins
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_b = MagicMock(spec=BasePlugin)

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
        }
        self.loader._load_order = ["plugin_a", "plugin_b"]

        mock_context = MagicMock(spec=["event_bus", "get_plugin"])

        self.loader.setup_all(mock_context)

        plugin_a.setup.assert_called_once_with(mock_context)
        plugin_b.setup.assert_called_once_with(mock_context)

    def test_setup_all_with_missing_plugin(self) -> None:
        """Test setup_all handles missing plugins gracefully."""
        plugin_a = MagicMock(spec=BasePlugin)

        self.loader._instances = {"plugin_a": plugin_a}
        self.loader._load_order = ["plugin_a", "plugin_b"]  # plugin_b doesn't exist

        mock_context = MagicMock(spec=["event_bus", "get_plugin"])

        # Should not raise
        self.loader.setup_all(mock_context)

        plugin_a.setup.assert_called_once_with(mock_context)

    def test_update_all(self) -> None:
        """Test update_all calls update on all plugins."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_b = MagicMock(spec=BasePlugin)

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
        }

        delta_time = 0.016

        self.loader.update_all(delta_time)

        plugin_a.update.assert_called_once_with(delta_time)
        plugin_b.update.assert_called_once_with(delta_time)

    def test_draw_all(self) -> None:
        """Test draw_all calls on_draw on all plugins."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_b = MagicMock(spec=BasePlugin)

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
        }

        self.loader.draw_all()

        plugin_a.on_draw.assert_called_once()
        plugin_b.on_draw.assert_called_once()

    def test_draw_ui_all(self) -> None:
        """Test draw_ui_all calls on_draw_ui on all plugins."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_b = MagicMock(spec=BasePlugin)

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
        }

        self.loader.draw_ui_all()

        plugin_a.on_draw_ui.assert_called_once()
        plugin_b.on_draw_ui.assert_called_once()

    def test_cleanup_all(self) -> None:
        """Test cleanup_all calls cleanup in reverse order."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_b = MagicMock(spec=BasePlugin)
        plugin_c = MagicMock(spec=BasePlugin)

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
            "plugin_c": plugin_c,
        }
        self.loader._load_order = ["plugin_a", "plugin_b", "plugin_c"]

        # Track call order
        call_order = []
        plugin_a.cleanup.side_effect = lambda: call_order.append("a")
        plugin_b.cleanup.side_effect = lambda: call_order.append("b")
        plugin_c.cleanup.side_effect = lambda: call_order.append("c")

        self.loader.cleanup_all()

        # Should be called in reverse order
        assert call_order == ["c", "b", "a"]

    def test_cleanup_all_with_missing_plugin(self) -> None:
        """Test cleanup_all handles missing plugins gracefully."""
        plugin_a = MagicMock(spec=BasePlugin)

        self.loader._instances = {"plugin_a": plugin_a}
        self.loader._load_order = ["plugin_a", "plugin_b"]  # plugin_b doesn't exist

        # Should not raise
        self.loader.cleanup_all()

        plugin_a.cleanup.assert_called_once()

    def test_reset_all(self) -> None:
        """Test reset_all calls reset on all plugins."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_b = MagicMock(spec=BasePlugin)

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
        }
        self.loader._load_order = ["plugin_a", "plugin_b"]

        self.loader.reset_all()

        plugin_a.reset.assert_called_once()
        plugin_b.reset.assert_called_once()

    def test_reset_all_with_missing_plugin(self) -> None:
        """Test reset_all handles missing plugins gracefully."""
        plugin_a = MagicMock(spec=BasePlugin)

        self.loader._instances = {"plugin_a": plugin_a}
        self.loader._load_order = ["plugin_a", "plugin_b"]  # plugin_b doesn't exist

        # Should not raise
        self.loader.reset_all()

        plugin_a.reset.assert_called_once()

    def test_get_plugin_existing(self) -> None:
        """Test get_plugin returns existing plugin."""
        plugin_a = MagicMock(spec=BasePlugin)

        self.loader._instances = {"plugin_a": plugin_a}

        result = self.loader.get_plugin("plugin_a")

        assert result == plugin_a

    def test_get_plugin_nonexistent(self) -> None:
        """Test get_plugin returns None for nonexistent plugin."""
        result = self.loader.get_plugin("nonexistent")

        assert result is None

    def test_get_all_instances(self) -> None:
        """Test get_all_instances returns a copy of instances."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_b = MagicMock(spec=BasePlugin)

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
        }

        instances = self.loader.get_all_instances()

        assert len(instances) == 2
        assert instances["plugin_a"] == plugin_a
        assert instances["plugin_b"] == plugin_b
        # Verify it's a copy
        assert instances is not self.loader._instances

    def test_on_key_press_all_handled(self) -> None:
        """Test on_key_press_all stops propagation when handled."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_a.on_key_press.return_value = False

        plugin_b = MagicMock(spec=BasePlugin)
        plugin_b.on_key_press.return_value = True  # Handles the event

        plugin_c = MagicMock(spec=BasePlugin)
        plugin_c.on_key_press.return_value = False

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
            "plugin_c": plugin_c,
        }
        self.loader._load_order = ["plugin_a", "plugin_b", "plugin_c"]

        # Test key press
        result = self.loader.on_key_press_all(65, 0)  # 'A' key

        # Should return True since plugin_b handled it
        assert result is True

        # Check call order (reversed)
        plugin_c.on_key_press.assert_called_once_with(65, 0)
        plugin_b.on_key_press.assert_called_once_with(65, 0)
        # plugin_a should not be called since plugin_b handled it
        plugin_a.on_key_press.assert_not_called()

    def test_on_key_press_all_not_handled(self) -> None:
        """Test on_key_press_all returns False when not handled."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_a.on_key_press.return_value = False

        plugin_b = MagicMock(spec=BasePlugin)
        plugin_b.on_key_press.return_value = False

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
        }
        self.loader._load_order = ["plugin_a", "plugin_b"]

        result = self.loader.on_key_press_all(65, 0)

        assert result is False

        plugin_a.on_key_press.assert_called_once_with(65, 0)
        plugin_b.on_key_press.assert_called_once_with(65, 0)

    def test_on_key_press_all_with_missing_plugin(self) -> None:
        """Test on_key_press_all handles missing plugins gracefully."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_a.on_key_press.return_value = False

        self.loader._instances = {"plugin_a": plugin_a}
        self.loader._load_order = ["plugin_a", "plugin_b"]  # plugin_b doesn't exist

        # Should not raise
        result = self.loader.on_key_press_all(65, 0)

        assert result is False
        plugin_a.on_key_press.assert_called_once_with(65, 0)

    def test_on_key_release_all_handled(self) -> None:
        """Test on_key_release_all stops propagation when handled."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_a.on_key_release.return_value = False

        plugin_b = MagicMock(spec=BasePlugin)
        plugin_b.on_key_release.return_value = True

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
        }
        self.loader._load_order = ["plugin_a", "plugin_b"]

        result = self.loader.on_key_release_all(65, 0)

        assert result is True

        # Check reversed order
        plugin_b.on_key_release.assert_called_once_with(65, 0)
        plugin_a.on_key_release.assert_not_called()

    def test_on_key_release_all_not_handled(self) -> None:
        """Test on_key_release_all returns False when not handled."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_a.on_key_release.return_value = False

        plugin_b = MagicMock(spec=BasePlugin)
        plugin_b.on_key_release.return_value = False

        self.loader._instances = {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
        }
        self.loader._load_order = ["plugin_a", "plugin_b"]

        result = self.loader.on_key_release_all(65, 0)

        assert result is False

        plugin_a.on_key_release.assert_called_once_with(65, 0)
        plugin_b.on_key_release.assert_called_once_with(65, 0)

    def test_on_key_release_all_with_missing_plugin(self) -> None:
        """Test on_key_release_all handles missing plugins gracefully."""
        plugin_a = MagicMock(spec=BasePlugin)
        plugin_a.on_key_release.return_value = False

        self.loader._instances = {"plugin_a": plugin_a}
        self.loader._load_order = ["plugin_a", "plugin_b"]  # plugin_b doesn't exist

        # Should not raise
        result = self.loader.on_key_release_all(65, 0)

        assert result is False
        plugin_a.on_key_release.assert_called_once_with(65, 0)

    def test_resolve_dependencies_simple(self) -> None:
        """Test dependency resolution with simple chain."""
        plugins = {
            "plugin_a": PluginA,
            "plugin_b": PluginB,
        }

        order = self.loader._resolve_dependencies(plugins)

        assert order == ["plugin_a", "plugin_b"]

    def test_resolve_dependencies_complex(self) -> None:
        """Test dependency resolution with complex graph."""
        plugins = {
            "plugin_c": PluginC,
            "plugin_a": PluginA,
            "plugin_d": PluginD,
            "plugin_b": PluginB,
        }

        order = self.loader._resolve_dependencies(plugins)

        # Verify dependency constraints
        assert order.index("plugin_a") < order.index("plugin_b")
        assert order.index("plugin_b") < order.index("plugin_c")
        assert order.index("plugin_a") < order.index("plugin_d")
        assert order.index("plugin_c") < order.index("plugin_d")

    def test_resolve_dependencies_no_dependencies(self) -> None:
        """Test dependency resolution with no dependencies."""
        plugins = {
            "plugin_a": PluginA,
        }

        order = self.loader._resolve_dependencies(plugins)

        assert order == ["plugin_a"]

    def test_resolve_dependencies_circular(self) -> None:
        """Test dependency resolution detects circular dependencies."""
        plugins = {
            "circular_1": PluginCircular1,
            "circular_2": PluginCircular2,
        }

        with pytest.raises(CircularDependencyError) as context:
            self.loader._resolve_dependencies(plugins)

        assert "circular_1" in str(context.value) or "circular_2" in str(context.value)

    def test_resolve_dependencies_missing(self) -> None:
        """Test dependency resolution detects missing dependencies."""
        plugins = {
            "missing_dep": PluginMissingDep,
        }

        with pytest.raises(MissingDependencyError) as context:
            self.loader._resolve_dependencies(plugins)

        assert "nonexistent_plugin" in str(context.value)
