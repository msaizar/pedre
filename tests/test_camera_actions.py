"""Unit tests for camera actions."""

import unittest
from unittest.mock import MagicMock

from pedre.systems.camera.actions import (
    FollowNPCAction,
    FollowPlayerAction,
    StopCameraFollowAction,
)


class TestFollowPlayerAction(unittest.TestCase):
    """Test FollowPlayerAction."""

    def test_execute_sets_follow_mode(self) -> None:
        """Test that action sets camera to follow player."""
        # Setup
        action = FollowPlayerAction(smooth=True)
        context = MagicMock()
        camera_manager = MagicMock()
        context.camera_manager = camera_manager

        # Execute
        result = action.execute(context)

        # Assert
        assert result is True
        camera_manager.set_follow_player.assert_called_once_with(smooth=True)

    def test_execute_instant_follow(self) -> None:
        """Test instant follow mode."""
        action = FollowPlayerAction(smooth=False)
        context = MagicMock()
        camera_manager = MagicMock()
        context.camera_manager = camera_manager

        result = action.execute(context)

        assert result is True
        camera_manager.set_follow_player.assert_called_once_with(smooth=False)

    def test_execute_no_camera_manager(self) -> None:
        """Test graceful handling when camera manager not available."""
        action = FollowPlayerAction()
        context = MagicMock()
        context.camera_manager = None

        result = action.execute(context)

        assert result is True  # Should still complete

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"smooth": False}
        action = FollowPlayerAction.from_dict(data)

        assert action.smooth is False

    def test_from_dict_defaults(self) -> None:
        """Test defaults when creating from dict."""
        action = FollowPlayerAction.from_dict({})
        assert action.smooth is True

    def test_reset(self) -> None:
        """Test reset clears executed flag."""
        action = FollowPlayerAction()
        context = MagicMock()
        camera_manager = MagicMock()
        context.camera_manager = camera_manager

        action.execute(context)
        assert action.executed is True

        action.reset()
        assert action.executed is False


class TestFollowNPCAction(unittest.TestCase):
    """Test FollowNPCAction."""

    def test_execute_sets_follow_npc(self) -> None:
        """Test that action sets camera to follow NPC."""
        action = FollowNPCAction("martin", smooth=True)
        context = MagicMock()
        camera_manager = MagicMock()
        npc_manager = MagicMock()
        npc_state = MagicMock()

        context.camera_manager = camera_manager
        context.npc_manager = npc_manager

        npc_manager.get_npc_by_name.return_value = npc_state

        result = action.execute(context)

        assert result is True
        camera_manager.set_follow_npc.assert_called_once_with("martin", smooth=True)

    def test_execute_npc_not_found(self) -> None:
        """Test warning when NPC doesn't exist."""
        action = FollowNPCAction("nonexistent")
        context = MagicMock()
        camera_manager = MagicMock()
        npc_manager = MagicMock()

        context.camera_manager = camera_manager
        context.npc_manager = npc_manager
        npc_manager.get_npc_by_name.return_value = None

        result = action.execute(context)

        assert result is True  # Still completes
        camera_manager.set_follow_npc.assert_called_once()

    def test_execute_instant_follow(self) -> None:
        """Test instant follow mode for NPC."""
        action = FollowNPCAction("yema", smooth=False)
        context = MagicMock()
        camera_manager = MagicMock()
        npc_manager = MagicMock()

        context.camera_manager = camera_manager
        context.npc_manager = npc_manager

        result = action.execute(context)

        assert result is True
        camera_manager.set_follow_npc.assert_called_once_with("yema", smooth=False)

    def test_execute_no_camera_manager(self) -> None:
        """Test graceful handling when camera manager not available."""
        action = FollowNPCAction("martin")
        context = MagicMock()
        context.camera_manager = None

        result = action.execute(context)

        assert result is True  # Should still complete

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npc": "yema", "smooth": False}
        action = FollowNPCAction.from_dict(data)

        assert action.npc_name == "yema"
        assert action.smooth is False

    def test_from_dict_defaults(self) -> None:
        """Test defaults when creating from dict."""
        action = FollowNPCAction.from_dict({"npc": "test"})
        assert action.smooth is True

    def test_reset(self) -> None:
        """Test reset clears executed flag."""
        action = FollowNPCAction("martin")
        context = MagicMock()
        camera_manager = MagicMock()
        context.camera_manager = camera_manager

        action.execute(context)
        assert action.executed is True

        action.reset()
        assert action.executed is False


class TestStopCameraFollowAction(unittest.TestCase):
    """Test StopCameraFollowAction."""

    def test_execute_stops_following(self) -> None:
        """Test that action stops camera following."""
        action = StopCameraFollowAction()
        context = MagicMock()
        camera_manager = MagicMock()
        context.camera_manager = camera_manager

        result = action.execute(context)

        assert result is True
        camera_manager.stop_follow.assert_called_once()

    def test_execute_no_camera_manager(self) -> None:
        """Test graceful handling when camera manager not available."""
        action = StopCameraFollowAction()
        context = MagicMock()
        context.camera_manager = None

        result = action.execute(context)

        assert result is True  # Should still complete

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        action = StopCameraFollowAction.from_dict({})
        assert action is not None

    def test_reset(self) -> None:
        """Test reset clears executed flag."""
        action = StopCameraFollowAction()
        context = MagicMock()
        camera_manager = MagicMock()
        context.camera_manager = camera_manager

        action.execute(context)
        assert action.executed is True

        action.reset()
        assert action.executed is False


if __name__ == "__main__":
    unittest.main()
