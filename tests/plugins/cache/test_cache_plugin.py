"""Unit tests for CachePlugin."""

from unittest.mock import MagicMock

import pytest

from pedre.plugins.cache.plugin import CachePlugin


class TestCachePlugin:
    """Unit test class for CachePlugin."""

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Fixture for mock context."""
        return MagicMock()

    @pytest.fixture
    def plugin(self, mock_context: MagicMock) -> CachePlugin:
        """Fixture for CachePlugin."""
        p = CachePlugin()
        p.setup(mock_context)
        return p

    def test_setup(self, plugin: CachePlugin, mock_context: MagicMock) -> None:
        """Test setup method stores context."""
        assert plugin.context == mock_context
        assert plugin._cache == {}

    def test_cache_scene_with_plugin_states(self, plugin: CachePlugin, mock_context: MagicMock) -> None:
        """Test caching scene state from plugins."""
        # Create mock plugins
        plugin1 = MagicMock()
        plugin1.name = "plugin1"
        plugin1.cache_scene_state.return_value = {"key1": "value1"}

        plugin2 = MagicMock()
        plugin2.name = "plugin2"
        # plugin2 returns empty state, should not be cached
        plugin2.cache_scene_state.return_value = {}

        plugin3 = MagicMock()
        plugin3.name = "plugin3"
        plugin3.cache_scene_state.return_value = {"key3": "value3"}

        mock_context.get_plugins.return_value = {
            "p1": plugin1,
            "p2": plugin2,
            "p3": plugin3,
        }

        plugin.cache_scene("test_scene")

        # Verify cache structure
        assert "test_scene" in plugin._cache
        scene_cache = plugin._cache["test_scene"]
        assert len(scene_cache) == 2
        assert scene_cache["plugin1"] == {"key1": "value1"}
        assert scene_cache["plugin3"] == {"key3": "value3"}
        assert "plugin2" not in scene_cache

        # Verify plugin methods were called
        plugin1.cache_scene_state.assert_called_once_with("test_scene")
        plugin2.cache_scene_state.assert_called_once_with("test_scene")
        plugin3.cache_scene_state.assert_called_once_with("test_scene")

    def test_restore_scene_success(self, plugin: CachePlugin, mock_context: MagicMock) -> None:
        """Test restoring scene state to plugins."""
        # Setup cache
        plugin._cache = {
            "test_scene": {
                "plugin1": {"key1": "value1"},
                "plugin2": {"key2": "value2"},
            }
        }

        # Create mock plugins
        plugin1 = MagicMock()
        plugin1.name = "plugin1"

        plugin2 = MagicMock()
        plugin2.name = "plugin2"

        plugin3 = MagicMock()
        plugin3.name = "plugin3"  # No cached state for this one

        mock_context.get_plugins.return_value = {
            "p1": plugin1,
            "p2": plugin2,
            "p3": plugin3,
        }

        result = plugin.restore_scene("test_scene")

        assert result is True
        plugin1.restore_scene_state.assert_called_once_with("test_scene", {"key1": "value1"})
        plugin2.restore_scene_state.assert_called_once_with("test_scene", {"key2": "value2"})
        plugin3.restore_scene_state.assert_not_called()

    def test_restore_scene_not_found(self, plugin: CachePlugin) -> None:
        """Test restoring non-existent scene."""
        result = plugin.restore_scene("non_existent_scene")
        assert result is False

    def test_has_cached_state(self, plugin: CachePlugin) -> None:
        """Test checking for cached state."""
        plugin._cache["scene1"] = {}
        assert plugin.has_cached_state("scene1") is True
        assert plugin.has_cached_state("scene2") is False

    def test_clear_and_reset(self, plugin: CachePlugin) -> None:
        """Test clearing the cache."""
        plugin._cache = {"scene1": {"data": 1}}

        # Test clear
        plugin.clear()
        assert plugin._cache == {}

        # Test reset (calls clear)
        plugin._cache = {"scene1": {"data": 1}}
        plugin.reset()
        assert plugin._cache == {}

    def test_save_state_methods(self, plugin: CachePlugin) -> None:
        """Test get_save_state and restore_save_state."""
        original_cache = {
            "scene1": {"p1": {"a": 1}},
            "scene2": {"p2": {"b": 2}},
        }
        plugin._cache = original_cache.copy()

        # Get state
        saved_state = plugin.get_save_state()
        assert saved_state == original_cache
        # Ensure it's a copy
        assert saved_state is not plugin._cache

        # Clear and restore
        plugin.clear()
        plugin.restore_save_state(saved_state)
        assert plugin._cache == original_cache
