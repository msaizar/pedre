"""Unit tests for camera actions."""

from unittest.mock import MagicMock

from pedre.plugins.camera.actions import (
    FollowNPCAction,
    FollowPlayerAction,
    StopCameraFollowAction,
)


class TestFollowPlayerAction:
    """Test FollowPlayerAction."""

    def test_execute_sets_follow_mode(self) -> None:
        """Test that action sets camera to follow player."""
        # Setup
        action = FollowPlayerAction(smooth=True)
        context = MagicMock()
        camera_plugin = MagicMock()
        context.camera_plugin = camera_plugin

        # Execute
        result = action.execute(context)

        # Assert
        assert result is True
        camera_plugin.set_follow_player.assert_called_once_with(smooth=True)

    def test_execute_instant_follow(self) -> None:
        """Test instant follow mode."""
        action = FollowPlayerAction(smooth=False)
        context = MagicMock()
        camera_plugin = MagicMock()
        context.camera_plugin = camera_plugin

        result = action.execute(context)

        assert result is True
        camera_plugin.set_follow_player.assert_called_once_with(smooth=False)

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
        camera_plugin = MagicMock()
        context.camera_plugin = camera_plugin

        action.execute(context)
        assert action.executed is True

        action.reset()
        assert action.executed is False

    def test_execute_twice_only_runs_once(self) -> None:
        """Test that executing twice only calls plugin once."""
        action = FollowPlayerAction(smooth=True)
        context = MagicMock()
        camera_plugin = MagicMock()
        context.camera_plugin = camera_plugin

        # Execute twice
        action.execute(context)
        action.execute(context)

        # Should only be called once
        camera_plugin.set_follow_player.assert_called_once_with(smooth=True)


class TestFollowNPCAction:
    """Test FollowNPCAction."""

    def test_execute_sets_follow_npc(self) -> None:
        """Test that action sets camera to follow NPC."""
        action = FollowNPCAction("martin", smooth=True)
        context = MagicMock()
        camera_plugin = MagicMock()
        npc_plugin = MagicMock()
        npc_state = MagicMock()

        context.camera_plugin = camera_plugin
        context.npc_plugin = npc_plugin

        npc_plugin.get_npc_by_name.return_value = npc_state

        result = action.execute(context)

        assert result is True
        camera_plugin.set_follow_npc.assert_called_once_with("martin", smooth=True)

    def test_execute_npc_not_found(self) -> None:
        """Test warning when NPC doesn't exist."""
        action = FollowNPCAction("nonexistent")
        context = MagicMock()
        camera_plugin = MagicMock()
        npc_plugin = MagicMock()

        context.camera_plugin = camera_plugin
        context.npc_plugin = npc_plugin
        npc_plugin.get_npc_by_name.return_value = None

        result = action.execute(context)

        assert result is True  # Still completes
        camera_plugin.set_follow_npc.assert_called_once()

    def test_execute_instant_follow(self) -> None:
        """Test instant follow mode for NPC."""
        action = FollowNPCAction("yema", smooth=False)
        context = MagicMock()
        camera_plugin = MagicMock()
        npc_plugin = MagicMock()

        context.camera_plugin = camera_plugin
        context.npc_plugin = npc_plugin

        result = action.execute(context)

        assert result is True
        camera_plugin.set_follow_npc.assert_called_once_with("yema", smooth=False)

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
        camera_plugin = MagicMock()
        npc_plugin = MagicMock()
        context.camera_plugin = camera_plugin
        context.npc_plugin = npc_plugin

        action.execute(context)
        assert action.executed is True

        action.reset()
        assert action.executed is False

    def test_execute_twice_only_runs_once(self) -> None:
        """Test that executing twice only calls plugin once."""
        action = FollowNPCAction("martin", smooth=True)
        context = MagicMock()
        camera_plugin = MagicMock()
        npc_plugin = MagicMock()
        context.camera_plugin = camera_plugin
        context.npc_plugin = npc_plugin
        npc_plugin.get_npc_by_name.return_value = MagicMock()

        # Execute twice
        action.execute(context)
        action.execute(context)

        # Should only be called once
        camera_plugin.set_follow_npc.assert_called_once_with("martin", smooth=True)


class TestStopCameraFollowAction:
    """Test StopCameraFollowAction."""

    def test_execute_stops_following(self) -> None:
        """Test that action stops camera following."""
        action = StopCameraFollowAction()
        context = MagicMock()
        camera_plugin = MagicMock()
        context.camera_plugin = camera_plugin

        result = action.execute(context)

        assert result is True
        camera_plugin.stop_follow.assert_called_once()

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        action = StopCameraFollowAction.from_dict({})
        assert action is not None

    def test_reset(self) -> None:
        """Test reset clears executed flag."""
        action = StopCameraFollowAction()
        context = MagicMock()
        camera_plugin = MagicMock()
        context.camera_plugin = camera_plugin

        action.execute(context)
        assert action.executed is True

        action.reset()
        assert action.executed is False

    def test_execute_twice_only_runs_once(self) -> None:
        """Test that executing twice only calls plugin once."""
        action = StopCameraFollowAction()
        context = MagicMock()
        camera_plugin = MagicMock()
        context.camera_plugin = camera_plugin

        # Execute twice
        action.execute(context)
        action.execute(context)

        # Should only be called once
        camera_plugin.stop_follow.assert_called_once()
