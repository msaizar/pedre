"""Unit tests for scene action classes."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.scene.actions import ChangeSceneAction


class TestChangeSceneAction(unittest.TestCase):
    """Unit test class for ChangeSceneAction."""

    def test_init_with_target_map_only(self) -> None:
        """Test ChangeSceneAction initialization with only target_map."""
        action = ChangeSceneAction("Forest.tmx")

        assert action.target_map == "Forest.tmx"
        assert action.spawn_waypoint is None
        assert action.executed is False

    def test_init_with_spawn_waypoint(self) -> None:
        """Test ChangeSceneAction initialization with spawn_waypoint."""
        action = ChangeSceneAction("Tower.tmx", spawn_waypoint="tower_entrance")

        assert action.target_map == "Tower.tmx"
        assert action.spawn_waypoint == "tower_entrance"
        assert action.executed is False

    def test_execute_requests_transition(self) -> None:
        """Test that execute requests a scene transition."""
        action = ChangeSceneAction("Forest.tmx")

        # Create mock context with scene plugin
        mock_context = MagicMock()
        mock_scene_plugin = MagicMock()
        mock_context.scene_plugin = mock_scene_plugin

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_scene_plugin.request_transition.assert_called_once_with("Forest.tmx", None)
        assert action.executed is True

    def test_execute_with_spawn_waypoint(self) -> None:
        """Test execute with a specific spawn waypoint."""
        action = ChangeSceneAction("Castle.tmx", spawn_waypoint="main_gate")

        # Create mock context
        mock_context = MagicMock()
        mock_scene_plugin = MagicMock()
        mock_context.scene_plugin = mock_scene_plugin

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_scene_plugin.request_transition.assert_called_once_with("Castle.tmx", "main_gate")
        assert action.executed is True

    def test_execute_only_once(self) -> None:
        """Test that execute only requests transition once."""
        action = ChangeSceneAction("Dungeon.tmx")

        # Create mock context
        mock_context = MagicMock()
        mock_scene_plugin = MagicMock()
        mock_context.scene_plugin = mock_scene_plugin

        # Execute multiple times
        action.execute(mock_context)
        action.execute(mock_context)
        action.execute(mock_context)

        # Should only request transition once
        mock_scene_plugin.request_transition.assert_called_once()

    def test_reset(self) -> None:
        """Test that reset allows re-execution."""
        action = ChangeSceneAction("Village.tmx")

        # Create mock context
        mock_context = MagicMock()
        mock_scene_plugin = MagicMock()
        mock_context.scene_plugin = mock_scene_plugin

        # Execute, reset, execute again
        action.execute(mock_context)
        assert action.executed is True

        action.reset()
        assert action.executed is False

        action.execute(mock_context)

        # Should have been called twice (once before reset, once after)
        assert mock_scene_plugin.request_transition.call_count == 2

    def test_from_dict_with_target_map(self) -> None:
        """Test creating ChangeSceneAction from dictionary with target_map."""
        data = {"target_map": "Beach.tmx"}

        action = ChangeSceneAction.from_dict(data)

        assert isinstance(action, ChangeSceneAction)
        assert action.target_map == "Beach.tmx"
        assert action.spawn_waypoint == ""

    def test_from_dict_with_spawn_waypoint(self) -> None:
        """Test creating ChangeSceneAction with spawn_waypoint."""
        data = {"target_map": "Mountain.tmx", "spawn_waypoint": "peak"}

        action = ChangeSceneAction.from_dict(data)

        assert isinstance(action, ChangeSceneAction)
        assert action.target_map == "Mountain.tmx"
        assert action.spawn_waypoint == "peak"

    def test_from_dict_missing_target_map(self) -> None:
        """Test creating ChangeSceneAction with missing target_map key."""
        data = {"spawn_waypoint": "entrance"}

        action = ChangeSceneAction.from_dict(data)

        assert isinstance(action, ChangeSceneAction)
        assert action.target_map == ""
        assert action.spawn_waypoint == "entrance"

    def test_from_dict_empty_dict(self) -> None:
        """Test creating ChangeSceneAction from empty dictionary."""
        data = {}

        action = ChangeSceneAction.from_dict(data)

        assert isinstance(action, ChangeSceneAction)
        assert action.target_map == ""
        assert action.spawn_waypoint == ""

    def test_from_dict_with_extra_keys(self) -> None:
        """Test that from_dict ignores extra keys."""
        data = {
            "target_map": "Desert.tmx",
            "spawn_waypoint": "oasis",
            "extra_key": "ignored",
            "another_extra": 123,
        }

        action = ChangeSceneAction.from_dict(data)

        assert action.target_map == "Desert.tmx"
        assert action.spawn_waypoint == "oasis"

    def test_execute_returns_true_always(self) -> None:
        """Test that execute always returns True."""
        action = ChangeSceneAction("Test.tmx")
        mock_context = MagicMock()
        mock_scene_plugin = MagicMock()
        mock_context.scene_plugin = mock_scene_plugin

        # First execution
        result1 = action.execute(mock_context)
        assert result1 is True

        # Second execution (should still return True even if not transitioning)
        result2 = action.execute(mock_context)
        assert result2 is True

    def test_reset_clears_executed_flag(self) -> None:
        """Test that reset properly clears the executed flag."""
        action = ChangeSceneAction("Cave.tmx")

        # Set executed to True
        action.executed = True
        assert action.executed is True

        # Reset
        action.reset()
        assert action.executed is False


if __name__ == "__main__":
    unittest.main()
