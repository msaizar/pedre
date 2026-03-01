"""Unit tests for NPC actions in src/pedre/plugins/npc/actions.py."""

from unittest.mock import MagicMock

import pytest

from pedre.actions.registry import ActionParseError

# Import actions - this will register them in ActionRegistry
# This is intentional and matches the pattern used in other plugin action tests
from pedre.plugins.npc.actions import (
    AdvanceDialogAction,
    MoveNPCAction,
    SetCurrentNPCAction,
    SetDialogLevelAction,
    StartAppearAnimationAction,
    StartDisappearAnimationAction,
    WaitForNPCMovementAction,
    WaitForNPCsAppearAction,
    WaitForNPCsDisappearAction,
)
from pedre.sprites import AnimatedSprite
from pedre.types import EntityReference


class TestMoveNPCAction:
    """Test Suite for MoveNPCAction."""

    def test_initialization(self) -> None:
        """Test proper initialization of MoveNPCAction."""
        action = MoveNPCAction(npc_names=["martin", "yema"], waypoint="town_square")
        assert action.npc_names == ["martin", "yema"]
        assert action.waypoint == "town_square"
        assert not action.started

    def test_execute_with_valid_waypoint(self) -> None:
        """Test executing move action with a valid waypoint."""
        context = MagicMock()
        context.waypoint_plugin.get_waypoints.return_value = {"town_square": (100.0, 200.0)}
        action = MoveNPCAction(npc_names=["martin"], waypoint="town_square")

        result = action.execute(context)

        assert result is True
        assert action.started is True
        context.npc_plugin.move_npc_to_position.assert_called_once_with("martin", 100.0, 200.0)

    def test_execute_with_multiple_npcs(self) -> None:
        """Test executing move action with multiple NPCs."""
        context = MagicMock()
        context.waypoint_plugin.get_waypoints.return_value = {"forest": (50.0, 75.0)}
        action = MoveNPCAction(npc_names=["martin", "yema", "romi"], waypoint="forest")

        result = action.execute(context)

        assert result is True
        assert action.started is True
        assert context.npc_plugin.move_npc_to_position.call_count == 3
        context.npc_plugin.move_npc_to_position.assert_any_call("martin", 50.0, 75.0)
        context.npc_plugin.move_npc_to_position.assert_any_call("yema", 50.0, 75.0)
        context.npc_plugin.move_npc_to_position.assert_any_call("romi", 50.0, 75.0)

    def test_execute_with_invalid_waypoint(self) -> None:
        """Test executing move action with an invalid waypoint."""
        context = MagicMock()
        context.waypoint_plugin.get_waypoints.return_value = {}
        action = MoveNPCAction(npc_names=["martin"], waypoint="invalid_waypoint")

        result = action.execute(context)

        assert result is True
        context.npc_plugin.move_npc_to_position.assert_not_called()

    def test_execute_idempotent(self) -> None:
        """Test that executing multiple times doesn't repeat the movement."""
        context = MagicMock()
        context.waypoint_plugin.get_waypoints.return_value = {"town_square": (100.0, 200.0)}
        action = MoveNPCAction(npc_names=["martin"], waypoint="town_square")

        action.execute(context)
        action.execute(context)

        context.npc_plugin.move_npc_to_position.assert_called_once()

    def test_reset(self) -> None:
        """Test resetting the action."""
        action = MoveNPCAction(npc_names=["martin"], waypoint="town_square")
        action.started = True

        action.reset()

        assert action.started is False

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npcs": ["martin", "yema"], "waypoint": "town_square"}

        action = MoveNPCAction.from_dict(data)

        assert action.npc_names == ["martin", "yema"]
        assert action.waypoint == "town_square"

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}
        with pytest.raises(ActionParseError):
            MoveNPCAction.from_dict(data)


class TestStartAppearAnimationAction:
    """Test Suite for StartAppearAnimationAction."""

    def test_initialization(self) -> None:
        """Test proper initialization of StartAppearAnimationAction."""
        action = StartAppearAnimationAction(npc_names=["martin", "yema"])
        assert action.npc_names == ["martin", "yema"]
        assert not action.executed

    def test_execute(self) -> None:
        """Test executing appear animation action."""
        context = MagicMock()
        action = StartAppearAnimationAction(npc_names=["martin", "yema"])

        result = action.execute(context)

        assert result is True
        assert action.executed is True
        context.npc_plugin.show_npcs.assert_called_once_with(["martin", "yema"])

    def test_execute_idempotent(self) -> None:
        """Test that executing multiple times doesn't repeat the appear animation."""
        context = MagicMock()
        action = StartAppearAnimationAction(npc_names=["martin"])

        action.execute(context)
        action.execute(context)

        context.npc_plugin.show_npcs.assert_called_once()

    def test_reset(self) -> None:
        """Test resetting the action."""
        action = StartAppearAnimationAction(npc_names=["martin"])
        action.executed = True

        action.reset()

        assert action.executed is False

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npcs": ["martin", "yema", "romi"]}

        action = StartAppearAnimationAction.from_dict(data)

        assert action.npc_names == ["martin", "yema", "romi"]

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}
        with pytest.raises(ActionParseError):
            StartAppearAnimationAction.from_dict(data)


class TestAdvanceDialogAction:
    """Test Suite for AdvanceDialogAction."""

    def test_initialization(self) -> None:
        """Test proper initialization of AdvanceDialogAction."""
        action = AdvanceDialogAction(npc_name="martin")
        assert action.npc_name == "martin"
        assert not action.executed

    def test_execute(self) -> None:
        """Test executing advance dialog action."""
        context = MagicMock()
        action = AdvanceDialogAction(npc_name="martin")

        result = action.execute(context)

        assert result is True
        assert action.executed is True
        context.npc_plugin.advance_dialog.assert_called_once_with("martin")

    def test_execute_idempotent(self) -> None:
        """Test that executing multiple times doesn't repeat the advance."""
        context = MagicMock()
        action = AdvanceDialogAction(npc_name="martin")

        action.execute(context)
        action.execute(context)

        context.npc_plugin.advance_dialog.assert_called_once()

    def test_reset(self) -> None:
        """Test resetting the action."""
        action = AdvanceDialogAction(npc_name="martin")
        action.executed = True

        action.reset()

        assert action.executed is False

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npc": "yema"}

        action = AdvanceDialogAction.from_dict(data)

        assert action.npc_name == "yema"

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}
        with pytest.raises(ActionParseError):
            AdvanceDialogAction.from_dict(data)


class TestSetDialogLevelAction:
    """Test Suite for SetDialogLevelAction."""

    def test_initialization(self) -> None:
        """Test proper initialization of SetDialogLevelAction."""
        action = SetDialogLevelAction(npc_name="martin", level=5)
        assert action.npc_name == "martin"
        assert action.level == 5
        assert not action.executed

    def test_execute_with_valid_npc(self) -> None:
        """Test executing set dialog level action with a valid NPC."""
        context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 1
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = SetDialogLevelAction(npc_name="martin", level=3)

        result = action.execute(context)

        assert result is True
        assert action.executed is True
        assert mock_npc_state.dialog_level == 3

    def test_execute_with_invalid_npc(self) -> None:
        """Test executing set dialog level action with an invalid NPC."""
        context = MagicMock()
        context.npc_plugin.get_npcs.return_value = {}
        action = SetDialogLevelAction(npc_name="invalid_npc", level=5)

        result = action.execute(context)

        assert result is True
        assert action.executed is True

    def test_execute_idempotent(self) -> None:
        """Test that executing multiple times doesn't repeat the set."""
        context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 1
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = SetDialogLevelAction(npc_name="martin", level=5)

        action.execute(context)
        # Change the level to see if it gets set again
        mock_npc_state.dialog_level = 10
        action.execute(context)

        # Should still be 10 (not set again to 5)
        assert mock_npc_state.dialog_level == 10

    def test_reset(self) -> None:
        """Test resetting the action."""
        action = SetDialogLevelAction(npc_name="martin", level=5)
        action.executed = True

        action.reset()

        assert action.executed is False

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npc": "martin", "dialog_level": 7}

        action = SetDialogLevelAction.from_dict(data)

        assert action.npc_name == "martin"
        assert action.level == 7

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}
        with pytest.raises(ActionParseError):
            SetDialogLevelAction.from_dict(data)


class TestSetCurrentNPCAction:
    """Test Suite for SetCurrentNPCAction."""

    def test_initialization(self) -> None:
        """Test proper initialization of SetCurrentNPCAction."""
        action = SetCurrentNPCAction(npc_name="martin")
        assert action.npc_name == "martin"
        assert not action.executed

    def test_execute_with_valid_npc(self) -> None:
        """Test executing set current NPC action with a valid NPC."""
        context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 3
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = SetCurrentNPCAction(npc_name="martin")

        result = action.execute(context)

        assert result is True
        assert action.executed is True
        context.dialog_plugin.set_current_npc_name.assert_called_once_with("martin")
        context.dialog_plugin.set_current_dialog_level.assert_called_once_with(3)

    def test_execute_with_invalid_npc(self) -> None:
        """Test executing set current NPC action with an invalid NPC."""
        context = MagicMock()
        context.npc_plugin.get_npcs.return_value = {}
        action = SetCurrentNPCAction(npc_name="invalid_npc")

        result = action.execute(context)

        assert result is True
        assert action.executed is True
        context.dialog_plugin.set_current_npc_name.assert_not_called()
        context.dialog_plugin.set_current_dialog_level.assert_not_called()

    def test_execute_idempotent(self) -> None:
        """Test that executing multiple times doesn't repeat the set."""
        context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 3
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = SetCurrentNPCAction(npc_name="martin")

        action.execute(context)
        action.execute(context)

        context.dialog_plugin.set_current_npc_name.assert_called_once()
        context.dialog_plugin.set_current_dialog_level.assert_called_once()

    def test_reset(self) -> None:
        """Test resetting the action."""
        action = SetCurrentNPCAction(npc_name="martin")
        action.executed = True

        action.reset()

        assert action.executed is False

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npc": "yema"}

        action = SetCurrentNPCAction.from_dict(data)

        assert action.npc_name == "yema"

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}
        with pytest.raises(ActionParseError):
            SetCurrentNPCAction.from_dict(data)


class TestWaitForNPCMovementAction:
    """Test Suite for WaitForNPCMovementAction."""

    def test_initialization(self) -> None:
        """Test proper initialization of WaitForNPCMovementAction."""
        action = WaitForNPCMovementAction(npc_name="martin")
        assert action.npc_name == "martin"

    def test_execute_npc_not_found(self) -> None:
        """Test executing when NPC is not found."""
        context = MagicMock()
        context.npc_plugin.get_npcs.return_value = {}
        action = WaitForNPCMovementAction(npc_name="martin")

        result = action.execute(context)

        assert result is True

    def test_execute_npc_still_moving(self) -> None:
        """Test executing when NPC is still moving."""
        context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.path = [(10, 10), (20, 20)]
        mock_npc_state.is_moving = True
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = WaitForNPCMovementAction(npc_name="martin")

        result = action.execute(context)

        assert result is False

    def test_execute_npc_has_path(self) -> None:
        """Test executing when NPC has a path but is_moving is False."""
        context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.path = [(10, 10)]
        mock_npc_state.is_moving = False
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = WaitForNPCMovementAction(npc_name="martin")

        result = action.execute(context)

        assert result is False

    def test_execute_npc_movement_complete(self) -> None:
        """Test executing when NPC has completed movement."""
        context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.path = []
        mock_npc_state.is_moving = False
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = WaitForNPCMovementAction(npc_name="martin")

        result = action.execute(context)

        assert result is True

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npc": "yema"}

        action = WaitForNPCMovementAction.from_dict(data)

        assert action.npc_name == "yema"

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}
        with pytest.raises(ActionParseError):
            WaitForNPCMovementAction.from_dict(data)


class TestWaitForNPCsAppearAction:
    """Test Suite for WaitForNPCsAppearAction."""

    def test_initialization(self) -> None:
        """Test proper initialization of WaitForNPCsAppearAction."""
        action = WaitForNPCsAppearAction(npc_names=["martin", "yema"])
        assert action.npc_names == ["martin", "yema"]

    def test_execute_npcs_not_found(self) -> None:
        """Test executing when NPCs are not found."""
        context = MagicMock()
        context.npc_plugin.get_npcs.return_value = {}
        action = WaitForNPCsAppearAction(npc_names=["martin", "yema"])

        result = action.execute(context)

        assert result is True

    def test_execute_animated_npc_still_appearing(self) -> None:
        """Test executing when AnimatedSprite is still appearing."""
        context = MagicMock()
        mock_sprite = MagicMock(spec=AnimatedSprite)
        mock_sprite.has_state.return_value = True
        mock_sprite.is_state_complete.return_value = False
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = WaitForNPCsAppearAction(npc_names=["martin"])

        result = action.execute(context)

        assert result is False

    def test_execute_animated_npc_appear_complete(self) -> None:
        """Test executing when AnimatedSprite has completed appearing."""
        context = MagicMock()
        mock_sprite = MagicMock(spec=AnimatedSprite)
        mock_sprite.has_state.return_value = True
        mock_sprite.is_state_complete.return_value = True
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = WaitForNPCsAppearAction(npc_names=["martin"])

        result = action.execute(context)

        assert result is True

    def test_execute_non_animated_npc(self) -> None:
        """Test executing with non-AnimatedSprite sprite."""
        context = MagicMock()
        mock_sprite = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = WaitForNPCsAppearAction(npc_names=["martin"])

        result = action.execute(context)

        assert result is True

    def test_execute_multiple_npcs_mixed(self) -> None:
        """Test executing with multiple NPCs in different states."""
        context = MagicMock()
        mock_sprite1 = MagicMock(spec=AnimatedSprite)
        mock_sprite1.has_state.return_value = True
        mock_sprite1.is_state_complete.return_value = False
        mock_npc_state1 = MagicMock()
        mock_npc_state1.sprite = mock_sprite1

        mock_sprite2 = MagicMock(spec=AnimatedSprite)
        mock_sprite2.has_state.return_value = True
        mock_sprite2.is_state_complete.return_value = True
        mock_npc_state2 = MagicMock()
        mock_npc_state2.sprite = mock_sprite2

        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state1, "yema": mock_npc_state2}
        action = WaitForNPCsAppearAction(npc_names=["martin", "yema"])

        result = action.execute(context)

        assert result is False

    def test_execute_multiple_npcs_all_complete(self) -> None:
        """Test executing with multiple NPCs all completed."""
        context = MagicMock()
        mock_sprite1 = MagicMock(spec=AnimatedSprite)
        mock_sprite1.has_state.return_value = True
        mock_sprite1.is_state_complete.return_value = True
        mock_npc_state1 = MagicMock()
        mock_npc_state1.sprite = mock_sprite1

        mock_sprite2 = MagicMock(spec=AnimatedSprite)
        mock_sprite2.has_state.return_value = True
        mock_sprite2.is_state_complete.return_value = True
        mock_npc_state2 = MagicMock()
        mock_npc_state2.sprite = mock_sprite2

        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state1, "yema": mock_npc_state2}
        action = WaitForNPCsAppearAction(npc_names=["martin", "yema"])

        result = action.execute(context)

        assert result is True

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npcs": ["martin", "yema", "romi"]}

        action = WaitForNPCsAppearAction.from_dict(data)

        assert action.npc_names == ["martin", "yema", "romi"]

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}
        with pytest.raises(ActionParseError):
            WaitForNPCsAppearAction.from_dict(data)


class TestWaitForNPCsDisappearAction:
    """Test Suite for WaitForNPCsDisappearAction."""

    def test_initialization(self) -> None:
        """Test proper initialization of WaitForNPCsDisappearAction."""
        action = WaitForNPCsDisappearAction(npc_names=["martin", "yema"])
        assert action.npc_names == ["martin", "yema"]

    def test_execute_npcs_not_found(self) -> None:
        """Test executing when NPCs are not found."""
        context = MagicMock()
        context.npc_plugin.get_npcs.return_value = {}
        action = WaitForNPCsDisappearAction(npc_names=["martin", "yema"])

        result = action.execute(context)

        assert result is True

    def test_execute_animated_npc_still_disappearing(self) -> None:
        """Test executing when AnimatedSprite is still disappearing."""
        context = MagicMock()
        mock_sprite = MagicMock(spec=AnimatedSprite)
        mock_sprite.has_state.return_value = True
        mock_sprite.is_state_complete.return_value = False
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = WaitForNPCsDisappearAction(npc_names=["martin"])

        result = action.execute(context)

        assert result is False

    def test_execute_animated_npc_disappear_complete(self) -> None:
        """Test executing when AnimatedSprite has completed disappearing."""
        context = MagicMock()
        mock_sprite = MagicMock(spec=AnimatedSprite)
        mock_sprite.has_state.return_value = True
        mock_sprite.is_state_complete.return_value = True
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = WaitForNPCsDisappearAction(npc_names=["martin"])

        result = action.execute(context)

        assert result is True

    def test_execute_non_animated_npc(self) -> None:
        """Test executing with non-AnimatedSprite sprite."""
        context = MagicMock()
        mock_sprite = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = WaitForNPCsDisappearAction(npc_names=["martin"])

        result = action.execute(context)

        assert result is True

    def test_execute_multiple_npcs_mixed(self) -> None:
        """Test executing with multiple NPCs in different states."""
        context = MagicMock()
        mock_sprite1 = MagicMock(spec=AnimatedSprite)
        mock_sprite1.has_state.return_value = True
        mock_sprite1.is_state_complete.return_value = False
        mock_npc_state1 = MagicMock()
        mock_npc_state1.sprite = mock_sprite1

        mock_sprite2 = MagicMock(spec=AnimatedSprite)
        mock_sprite2.has_state.return_value = True
        mock_sprite2.is_state_complete.return_value = True
        mock_npc_state2 = MagicMock()
        mock_npc_state2.sprite = mock_sprite2

        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state1, "yema": mock_npc_state2}
        action = WaitForNPCsDisappearAction(npc_names=["martin", "yema"])

        result = action.execute(context)

        assert result is False

    def test_execute_multiple_npcs_all_complete(self) -> None:
        """Test executing with multiple NPCs all completed."""
        context = MagicMock()
        mock_sprite1 = MagicMock(spec=AnimatedSprite)
        mock_sprite1.has_state.return_value = True
        mock_sprite1.is_state_complete.return_value = True
        mock_npc_state1 = MagicMock()
        mock_npc_state1.sprite = mock_sprite1

        mock_sprite2 = MagicMock(spec=AnimatedSprite)
        mock_sprite2.has_state.return_value = True
        mock_sprite2.is_state_complete.return_value = True
        mock_npc_state2 = MagicMock()
        mock_npc_state2.sprite = mock_sprite2

        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state1, "yema": mock_npc_state2}
        action = WaitForNPCsDisappearAction(npc_names=["martin", "yema"])

        result = action.execute(context)

        assert result is True

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npcs": ["martin", "yema", "romi"]}

        action = WaitForNPCsDisappearAction.from_dict(data)

        assert action.npc_names == ["martin", "yema", "romi"]

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}
        with pytest.raises(ActionParseError):
            WaitForNPCsDisappearAction.from_dict(data)


class TestStartDisappearAnimationAction:
    """Test Suite for StartDisappearAnimationAction."""

    def test_initialization(self) -> None:
        """Test proper initialization of StartDisappearAnimationAction."""
        action = StartDisappearAnimationAction(npc_names=["martin", "yema"])
        assert action.npc_names == ["martin", "yema"]
        assert not action.animation_started

    def test_execute_starts_animation(self) -> None:
        """Test executing starts the disappear animation."""
        context = MagicMock()
        mock_sprite = MagicMock(spec=AnimatedSprite)
        mock_sprite.has_state.return_value = True
        mock_sprite.is_state_complete.return_value = False
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        mock_npc_state.disappear_event_emitted = True
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = StartDisappearAnimationAction(npc_names=["martin"])

        result = action.execute(context)

        assert action.animation_started is True
        assert result is False
        mock_sprite.request_state.assert_called_once_with("disappear")
        assert mock_npc_state.disappear_event_emitted is False

    def test_execute_waits_for_completion(self) -> None:
        """Test executing waits for animation completion."""
        context = MagicMock()
        mock_sprite = MagicMock(spec=AnimatedSprite)
        mock_sprite.has_state.return_value = True
        mock_sprite.is_state_complete.return_value = True
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        mock_npc_state.disappear_event_emitted = True
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = StartDisappearAnimationAction(npc_names=["martin"])

        result = action.execute(context)

        assert result is True
        context.scene_plugin.remove_from_wall_list.assert_called_once_with(mock_sprite)

    def test_execute_multiple_npcs(self) -> None:
        """Test executing with multiple NPCs."""
        context = MagicMock()
        mock_sprite1 = MagicMock(spec=AnimatedSprite)
        mock_sprite1.has_state.return_value = True
        mock_sprite1.is_state_complete.return_value = True
        mock_npc_state1 = MagicMock()
        mock_npc_state1.sprite = mock_sprite1

        mock_sprite2 = MagicMock(spec=AnimatedSprite)
        mock_sprite2.has_state.return_value = True
        mock_sprite2.is_state_complete.return_value = True
        mock_npc_state2 = MagicMock()
        mock_npc_state2.sprite = mock_sprite2

        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state1, "yema": mock_npc_state2}
        action = StartDisappearAnimationAction(npc_names=["martin", "yema"])

        result = action.execute(context)

        assert result is True
        mock_sprite1.request_state.assert_called_once_with("disappear")
        mock_sprite2.request_state.assert_called_once_with("disappear")
        assert context.scene_plugin.remove_from_wall_list.call_count == 2

    def test_execute_non_animated_npc(self) -> None:
        """Test executing with non-AnimatedSprite sprite."""
        context = MagicMock()
        mock_sprite = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = StartDisappearAnimationAction(npc_names=["martin"])

        result = action.execute(context)

        assert result is True

    def test_execute_npc_not_found(self) -> None:
        """Test executing when NPC is not found."""
        context = MagicMock()
        context.npc_plugin.get_npcs.return_value = {}
        action = StartDisappearAnimationAction(npc_names=["invalid_npc"])

        result = action.execute(context)

        assert result is True

    def test_execute_animation_in_progress(self) -> None:
        """Test executing while animation is in progress."""
        context = MagicMock()
        mock_sprite = MagicMock(spec=AnimatedSprite)
        mock_sprite.has_state.return_value = True
        mock_sprite.is_state_complete.return_value = False
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        context.npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}
        action = StartDisappearAnimationAction(npc_names=["martin"])

        result1 = action.execute(context)
        assert result1 is False

        result2 = action.execute(context)
        assert result2 is False

        mock_sprite.request_state.assert_called_once_with("disappear")

    def test_reset(self) -> None:
        """Test resetting the action."""
        action = StartDisappearAnimationAction(npc_names=["martin"])
        action.animation_started = True

        action.reset()

        assert action.animation_started is False

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npcs": ["martin", "yema", "romi"]}

        action = StartDisappearAnimationAction.from_dict(data)

        assert action.npc_names == ["martin", "yema", "romi"]

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}

        with pytest.raises(ActionParseError):
            StartDisappearAnimationAction.from_dict(data)


class TestNPCActionFromDictValidation:
    """Test from_dict validation errors across NPC actions."""

    # MoveNPCAction
    def test_move_npc_npcs_not_list(self) -> None:
        """Test from_dict npcs is list."""
        with pytest.raises(ActionParseError, match="'npcs' must be a list"):
            MoveNPCAction.from_dict({"npcs": "martin", "waypoint": "town_square"})

    def test_move_npc_npcs_items_not_strings(self) -> None:
        """Test from_dict npcs items are strings."""
        with pytest.raises(ActionParseError, match="'npcs' items must be strings"):
            MoveNPCAction.from_dict({"npcs": ["martin", 42], "waypoint": "town_square"})

    def test_move_npc_missing_waypoint(self) -> None:
        """Test from_dict move npc missing waypoint."""
        with pytest.raises(ActionParseError, match="missing required 'waypoint' field"):
            MoveNPCAction.from_dict({"npcs": ["martin"]})

    def test_move_npc_waypoint_not_string(self) -> None:
        """Test from_dict move npc waypoint is string."""
        with pytest.raises(ActionParseError, match="'waypoint' must be a string"):
            MoveNPCAction.from_dict({"npcs": ["martin"], "waypoint": 123})

    # StartAppearAnimationAction
    def test_start_appear_npcs_not_list(self) -> None:
        """Test StartAppearAnimationAction from_dict npcs must be list."""
        with pytest.raises(ActionParseError, match="'npcs' must be a list"):
            StartAppearAnimationAction.from_dict({"npcs": "martin"})

    def test_start_appear_npcs_items_not_strings(self) -> None:
        """Test StartAppearAnimationAction from_dict npcs items must be string."""
        with pytest.raises(ActionParseError, match="'npcs' items must be strings"):
            StartAppearAnimationAction.from_dict({"npcs": ["martin", 99]})

    # AdvanceDialogAction
    def test_advance_dialog_npc_not_string(self) -> None:
        """Test error when npc is not a string."""
        with pytest.raises(ActionParseError, match="'npc' must be a string"):
            AdvanceDialogAction.from_dict({"npc": 123})

    # SetDialogLevelAction
    def test_set_dialog_level_npc_not_string(self) -> None:
        """Test error when npc is not a string."""
        with pytest.raises(ActionParseError, match="'npc' must be a string"):
            SetDialogLevelAction.from_dict({"npc": 123, "dialog_level": 1})

    def test_set_dialog_level_missing_dialog_level(self) -> None:
        """Test error when dialog_level is missing."""
        with pytest.raises(ActionParseError, match="missing required 'dialog_level' field"):
            SetDialogLevelAction.from_dict({"npc": "martin"})

    def test_set_dialog_level_not_int(self) -> None:
        """Test error when dialog_level is not an int."""
        with pytest.raises(ActionParseError, match="'dialog_level' must be an int"):
            SetDialogLevelAction.from_dict({"npc": "martin", "dialog_level": "five"})

    def test_set_dialog_level_bool_rejected(self) -> None:
        """Test error when dialog_level is a bool (bool is subclass of int, so explicitly rejected)."""
        with pytest.raises(ActionParseError, match="'dialog_level' must be an int"):
            SetDialogLevelAction.from_dict({"npc": "martin", "dialog_level": True})

    # SetCurrentNPCAction
    def test_set_current_npc_not_string(self) -> None:
        """Test error when npc is not a string."""
        with pytest.raises(ActionParseError, match="'npc' must be a string"):
            SetCurrentNPCAction.from_dict({"npc": 123})

    # WaitForNPCMovementAction
    def test_wait_movement_npc_not_string(self) -> None:
        """Test error when npc is not a string."""
        with pytest.raises(ActionParseError, match="'npc' must be a string"):
            WaitForNPCMovementAction.from_dict({"npc": 123})

    # WaitForNPCsAppearAction
    def test_wait_appear_npcs_not_list(self) -> None:
        """Test error when npcs is not a list."""
        with pytest.raises(ActionParseError, match="'npcs' must be a list"):
            WaitForNPCsAppearAction.from_dict({"npcs": "martin"})

    def test_wait_appear_npcs_items_not_strings(self) -> None:
        """Test error when npcs items are not strings."""
        with pytest.raises(ActionParseError, match="'npcs' items must be strings"):
            WaitForNPCsAppearAction.from_dict({"npcs": ["martin", 99]})

    # WaitForNPCsDisappearAction
    def test_wait_disappear_npcs_not_list(self) -> None:
        """Test error when npcs is not a list."""
        with pytest.raises(ActionParseError, match="'npcs' must be a list"):
            WaitForNPCsDisappearAction.from_dict({"npcs": "martin"})

    def test_wait_disappear_npcs_items_not_strings(self) -> None:
        """Test error when npcs items are not strings."""
        with pytest.raises(ActionParseError, match="'npcs' items must be strings"):
            WaitForNPCsDisappearAction.from_dict({"npcs": ["martin", 99]})

    # StartDisappearAnimationAction
    def test_start_disappear_npcs_not_list(self) -> None:
        """Test error when npcs is not a list."""
        with pytest.raises(ActionParseError, match="'npcs' must be a list"):
            StartDisappearAnimationAction.from_dict({"npcs": "martin"})

    def test_start_disappear_npcs_items_not_strings(self) -> None:
        """Test error when npcs items are not strings."""
        with pytest.raises(ActionParseError, match="'npcs' items must be strings"):
            StartDisappearAnimationAction.from_dict({"npcs": ["martin", 99]})


class TestNPCActionGetReferences:
    """Test get_references() on NPC actions."""

    def test_move_npc_references(self) -> None:
        """Test get_references in MoveNPCAction."""
        action = MoveNPCAction(npc_names=["martin", "yema"], waypoint="town_square")
        refs = action.get_references()
        assert EntityReference(type="npc", name="martin") in refs
        assert EntityReference(type="npc", name="yema") in refs
        assert EntityReference(type="waypoint", name="town_square") in refs

    def test_start_appear_references(self) -> None:
        """Test get_references in StartAppearAnimationAction."""
        action = StartAppearAnimationAction(npc_names=["martin", "yema"])
        refs = action.get_references()
        assert EntityReference(type="npc", name="martin") in refs
        assert EntityReference(type="npc", name="yema") in refs

    def test_advance_dialog_references(self) -> None:
        """Test get_references in AdvanceDialogAction."""
        action = AdvanceDialogAction(npc_name="martin")
        refs = action.get_references()
        assert EntityReference(type="npc", name="martin") in refs

    def test_set_dialog_level_references(self) -> None:
        """Test get_references in SetDialogLevelAction."""
        action = SetDialogLevelAction(npc_name="martin", level=3)
        refs = action.get_references()
        assert EntityReference(type="npc", name="martin") in refs

    def test_set_current_npc_references(self) -> None:
        """Test get_references in SetCurrentNPC."""
        action = SetCurrentNPCAction(npc_name="martin")
        refs = action.get_references()
        assert EntityReference(type="npc", name="martin") in refs

    def test_wait_for_movement_references(self) -> None:
        """Test get_references in WaitForNPCMovement."""
        action = WaitForNPCMovementAction(npc_name="martin")
        refs = action.get_references()
        assert EntityReference(type="npc", name="martin") in refs

    def test_wait_npcs_appear_references(self) -> None:
        """Test get_references in WaitForNPCsAppear."""
        action = WaitForNPCsAppearAction(npc_names=["martin", "yema"])
        refs = action.get_references()
        assert EntityReference(type="npc", name="martin") in refs
        assert EntityReference(type="npc", name="yema") in refs

    def test_wait_npcs_disappear_references(self) -> None:
        """Test get_references in WaitForNPCsDisappear."""
        action = WaitForNPCsDisappearAction(npc_names=["martin", "yema"])
        refs = action.get_references()
        assert EntityReference(type="npc", name="martin") in refs
        assert EntityReference(type="npc", name="yema") in refs

    def test_start_disappear_references(self) -> None:
        """Test get_references in StartDisappear."""
        action = StartDisappearAnimationAction(npc_names=["martin", "yema"])
        refs = action.get_references()
        assert EntityReference(type="npc", name="martin") in refs
        assert EntityReference(type="npc", name="yema") in refs
