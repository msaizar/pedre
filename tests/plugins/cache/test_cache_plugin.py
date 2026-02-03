"""Unit tests for CachePlugin."""

import unittest
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

from pedre.plugins.cache.plugin import CachePlugin

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext


class TestCachePlugin(unittest.TestCase):
    """Unit test class for CachePlugin."""

    def setUp(self) -> None:
        """Set up CachePlugin for each test."""
        self.plugin = CachePlugin()
        self.mock_context = MagicMock()
        self.plugin.setup(self.mock_context)

    def test_setup(self) -> None:
        """Test setup method stores context."""
        assert self.plugin.context == self.mock_context
        assert self.plugin._cache == {}

    def test_cache_scene_with_plugin_states(self) -> None:
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

        self.mock_context.get_plugins.return_value = {
            "p1": plugin1,
            "p2": plugin2,
            "p3": plugin3,
        }

        self.plugin.cache_scene("test_scene")

        # Verify cache structure
        assert "test_scene" in self.plugin._cache
        scene_cache = self.plugin._cache["test_scene"]
        assert len(scene_cache) == 2
        assert scene_cache["plugin1"] == {"key1": "value1"}
        assert scene_cache["plugin3"] == {"key3": "value3"}
        assert "plugin2" not in scene_cache

        # Verify plugin methods were called
        plugin1.cache_scene_state.assert_called_once_with("test_scene")
        plugin2.cache_scene_state.assert_called_once_with("test_scene")
        plugin3.cache_scene_state.assert_called_once_with("test_scene")

    def test_restore_scene_success(self) -> None:
        """Test restoring scene state to plugins."""
        # Setup cache
        self.plugin._cache = {
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

        self.mock_context.get_plugins.return_value = {
            "p1": plugin1,
            "p2": plugin2,
            "p3": plugin3,
        }

        result = self.plugin.restore_scene("test_scene")

        assert result is True
        plugin1.restore_scene_state.assert_called_once_with("test_scene", {"key1": "value1"})
        plugin2.restore_scene_state.assert_called_once_with("test_scene", {"key2": "value2"})
        plugin3.restore_scene_state.assert_not_called()

    def test_restore_scene_not_found(self) -> None:
        """Test restoring non-existent scene."""
        result = self.plugin.restore_scene("non_existent_scene")
        assert result is False

    def test_has_cached_state(self) -> None:
        """Test checking for cached state."""
        self.plugin._cache["scene1"] = {}
        assert self.plugin.has_cached_state("scene1") is True
        assert self.plugin.has_cached_state("scene2") is False

    def test_clear_and_reset(self) -> None:
        """Test clearing the cache."""
        self.plugin._cache = {"scene1": {"data": 1}}

        # Test clear
        self.plugin.clear()
        assert self.plugin._cache == {}

        # Test reset (calls clear)
        self.plugin._cache = {"scene1": {"data": 1}}
        self.plugin.reset()
        assert self.plugin._cache == {}

    def test_save_state_methods(self) -> None:
        """Test get_save_state and restore_save_state."""
        original_cache = {
            "scene1": {"p1": {"a": 1}},
            "scene2": {"p2": {"b": 2}},
        }
        self.plugin._cache = original_cache.copy()

        # Get state
        saved_state = self.plugin.get_save_state()
        assert saved_state == original_cache
        # Ensure it's a copy
        assert saved_state is not self.plugin._cache

        # Clear and restore
        self.plugin.clear()
        self.plugin.restore_save_state(saved_state)
        assert self.plugin._cache == original_cache


if __name__ == "__main__":
    unittest.main()
