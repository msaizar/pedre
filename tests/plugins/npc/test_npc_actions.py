"""Unit tests for NPC actions in src/pedre/plugins/npc/actions.py."""

import unittest
from unittest.mock import MagicMock

# Import actions - this will register them in ActionRegistry
# This is intentional and matches the pattern used in other plugin action tests
from pedre.plugins.npc.actions import (
    AdvanceDialogAction,
    MoveNPCAction,
    RevealNPCsAction,
    SetCurrentNPCAction,
    SetDialogLevelAction,
    StartDisappearAnimationAction,
    WaitForNPCMovementAction,
    WaitForNPCsAppearAction,
    WaitForNPCsDisappearAction,
)
from pedre.plugins.npc.sprites import AnimatedNPC


class TestMoveNPCAction(unittest.TestCase):
    """Test Suite for MoveNPCAction."""

    def setUp(self) -> None:
        """Set up the test context."""
        self.mock_context = MagicMock()
        self.mock_waypoint_plugin = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.waypoint_plugin = self.mock_waypoint_plugin
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_initialization(self) -> None:
        """Test proper initialization of MoveNPCAction."""
        action = MoveNPCAction(npc_names=["martin", "yema"], waypoint="town_square")
        assert action.npc_names == ["martin", "yema"]
        assert action.waypoint == "town_square"
        assert not action.started

    def test_execute_with_valid_waypoint(self) -> None:
        """Test executing move action with a valid waypoint."""
        action = MoveNPCAction(npc_names=["martin"], waypoint="town_square")

        # Mock waypoint plugin to return valid waypoint
        self.mock_waypoint_plugin.get_waypoints.return_value = {"town_square": (100.0, 200.0)}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately
        assert result is True
        assert action.started is True

        # Should have called move_npc_to_position
        self.mock_npc_plugin.move_npc_to_position.assert_called_once_with("martin", 100.0, 200.0)

    def test_execute_with_multiple_npcs(self) -> None:
        """Test executing move action with multiple NPCs."""
        action = MoveNPCAction(npc_names=["martin", "yema", "romi"], waypoint="forest")

        # Mock waypoint plugin to return valid waypoint
        self.mock_waypoint_plugin.get_waypoints.return_value = {"forest": (50.0, 75.0)}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately
        assert result is True
        assert action.started is True

        # Should have called move_npc_to_position for each NPC
        assert self.mock_npc_plugin.move_npc_to_position.call_count == 3
        self.mock_npc_plugin.move_npc_to_position.assert_any_call("martin", 50.0, 75.0)
        self.mock_npc_plugin.move_npc_to_position.assert_any_call("yema", 50.0, 75.0)
        self.mock_npc_plugin.move_npc_to_position.assert_any_call("romi", 50.0, 75.0)

    def test_execute_with_invalid_waypoint(self) -> None:
        """Test executing move action with an invalid waypoint."""
        action = MoveNPCAction(npc_names=["martin"], waypoint="invalid_waypoint")

        # Mock waypoint plugin to return empty waypoints
        self.mock_waypoint_plugin.get_waypoints.return_value = {}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately even on error
        assert result is True

        # Should NOT have called move_npc_to_position
        self.mock_npc_plugin.move_npc_to_position.assert_not_called()

    def test_execute_idempotent(self) -> None:
        """Test that executing multiple times doesn't repeat the movement."""
        action = MoveNPCAction(npc_names=["martin"], waypoint="town_square")

        # Mock waypoint plugin
        self.mock_waypoint_plugin.get_waypoints.return_value = {"town_square": (100.0, 200.0)}

        # Execute twice
        action.execute(self.mock_context)
        action.execute(self.mock_context)

        # Should only have called move_npc_to_position once
        self.mock_npc_plugin.move_npc_to_position.assert_called_once()

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

        action = MoveNPCAction.from_dict(data)

        assert action.npc_names == []
        assert action.waypoint == ""


class TestRevealNPCsAction(unittest.TestCase):
    """Test Suite for RevealNPCsAction."""

    def setUp(self) -> None:
        """Set up the test context."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_initialization(self) -> None:
        """Test proper initialization of RevealNPCsAction."""
        action = RevealNPCsAction(npc_names=["martin", "yema"])
        assert action.npc_names == ["martin", "yema"]
        assert not action.executed

    def test_execute(self) -> None:
        """Test executing reveal action."""
        action = RevealNPCsAction(npc_names=["martin", "yema"])

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately
        assert result is True
        assert action.executed is True

        # Should have called show_npcs
        self.mock_npc_plugin.show_npcs.assert_called_once_with(["martin", "yema"])

    def test_execute_idempotent(self) -> None:
        """Test that executing multiple times doesn't repeat the reveal."""
        action = RevealNPCsAction(npc_names=["martin"])

        # Execute twice
        action.execute(self.mock_context)
        action.execute(self.mock_context)

        # Should only have called show_npcs once
        self.mock_npc_plugin.show_npcs.assert_called_once()

    def test_reset(self) -> None:
        """Test resetting the action."""
        action = RevealNPCsAction(npc_names=["martin"])
        action.executed = True

        action.reset()

        assert action.executed is False

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npcs": ["martin", "yema", "romi"]}

        action = RevealNPCsAction.from_dict(data)

        assert action.npc_names == ["martin", "yema", "romi"]

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}

        action = RevealNPCsAction.from_dict(data)

        assert action.npc_names == []


class TestAdvanceDialogAction(unittest.TestCase):
    """Test Suite for AdvanceDialogAction."""

    def setUp(self) -> None:
        """Set up the test context."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_initialization(self) -> None:
        """Test proper initialization of AdvanceDialogAction."""
        action = AdvanceDialogAction(npc_name="martin")
        assert action.npc_name == "martin"
        assert not action.executed

    def test_execute(self) -> None:
        """Test executing advance dialog action."""
        action = AdvanceDialogAction(npc_name="martin")

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately
        assert result is True
        assert action.executed is True

        # Should have called advance_dialog
        self.mock_npc_plugin.advance_dialog.assert_called_once_with("martin")

    def test_execute_idempotent(self) -> None:
        """Test that executing multiple times doesn't repeat the advance."""
        action = AdvanceDialogAction(npc_name="martin")

        # Execute twice
        action.execute(self.mock_context)
        action.execute(self.mock_context)

        # Should only have called advance_dialog once
        self.mock_npc_plugin.advance_dialog.assert_called_once()

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

        action = AdvanceDialogAction.from_dict(data)

        assert action.npc_name == ""


class TestSetDialogLevelAction(unittest.TestCase):
    """Test Suite for SetDialogLevelAction."""

    def setUp(self) -> None:
        """Set up the test context."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_initialization(self) -> None:
        """Test proper initialization of SetDialogLevelAction."""
        action = SetDialogLevelAction(npc_name="martin", level=5)
        assert action.npc_name == "martin"
        assert action.level == 5
        assert not action.executed

    def test_execute_with_valid_npc(self) -> None:
        """Test executing set dialog level action with a valid NPC."""
        action = SetDialogLevelAction(npc_name="martin", level=3)

        # Mock NPC state
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 1
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately
        assert result is True
        assert action.executed is True

        # Should have set dialog level
        assert mock_npc_state.dialog_level == 3

    def test_execute_with_invalid_npc(self) -> None:
        """Test executing set dialog level action with an invalid NPC."""
        action = SetDialogLevelAction(npc_name="invalid_npc", level=5)

        # Mock empty NPC list
        self.mock_npc_plugin.get_npcs.return_value = {}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately even with invalid NPC
        assert result is True
        assert action.executed is True

    def test_execute_idempotent(self) -> None:
        """Test that executing multiple times doesn't repeat the set."""
        action = SetDialogLevelAction(npc_name="martin", level=5)

        # Mock NPC state
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 1
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute twice
        action.execute(self.mock_context)
        # Change the level to see if it gets set again
        mock_npc_state.dialog_level = 10
        action.execute(self.mock_context)

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

        action = SetDialogLevelAction.from_dict(data)

        assert action.npc_name == ""
        assert action.level == 0


class TestSetCurrentNPCAction(unittest.TestCase):
    """Test Suite for SetCurrentNPCAction."""

    def setUp(self) -> None:
        """Set up the test context."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_dialog_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin
        self.mock_context.dialog_plugin = self.mock_dialog_plugin

    def test_initialization(self) -> None:
        """Test proper initialization of SetCurrentNPCAction."""
        action = SetCurrentNPCAction(npc_name="martin")
        assert action.npc_name == "martin"
        assert not action.executed

    def test_execute_with_valid_npc(self) -> None:
        """Test executing set current NPC action with a valid NPC."""
        action = SetCurrentNPCAction(npc_name="martin")

        # Mock NPC state
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 3
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately
        assert result is True
        assert action.executed is True

        # Should have set current NPC name and dialog level
        self.mock_dialog_plugin.set_current_npc_name.assert_called_once_with("martin")
        self.mock_dialog_plugin.set_current_dialog_level.assert_called_once_with(3)

    def test_execute_with_invalid_npc(self) -> None:
        """Test executing set current NPC action with an invalid NPC."""
        action = SetCurrentNPCAction(npc_name="invalid_npc")

        # Mock empty NPC list
        self.mock_npc_plugin.get_npcs.return_value = {}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately even with invalid NPC
        assert result is True
        assert action.executed is True

        # Should not have called set methods since NPC doesn't exist
        self.mock_dialog_plugin.set_current_npc_name.assert_not_called()
        self.mock_dialog_plugin.set_current_dialog_level.assert_not_called()

    def test_execute_idempotent(self) -> None:
        """Test that executing multiple times doesn't repeat the set."""
        action = SetCurrentNPCAction(npc_name="martin")

        # Mock NPC state
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 3
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute twice
        action.execute(self.mock_context)
        action.execute(self.mock_context)

        # Should only have called set methods once
        self.mock_dialog_plugin.set_current_npc_name.assert_called_once()
        self.mock_dialog_plugin.set_current_dialog_level.assert_called_once()

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

        action = SetCurrentNPCAction.from_dict(data)

        assert action.npc_name == ""


class TestWaitForNPCMovementAction(unittest.TestCase):
    """Test Suite for WaitForNPCMovementAction."""

    def setUp(self) -> None:
        """Set up the test context."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_initialization(self) -> None:
        """Test proper initialization of WaitForNPCMovementAction."""
        action = WaitForNPCMovementAction(npc_name="martin")
        assert action.npc_name == "martin"

    def test_execute_npc_not_found(self) -> None:
        """Test executing when NPC is not found."""
        action = WaitForNPCMovementAction(npc_name="martin")

        # Mock empty NPC list
        self.mock_npc_plugin.get_npcs.return_value = {}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately when NPC not found
        assert result is True

    def test_execute_npc_still_moving(self) -> None:
        """Test executing when NPC is still moving."""
        action = WaitForNPCMovementAction(npc_name="martin")

        # Mock NPC state that is moving
        mock_npc_state = MagicMock()
        mock_npc_state.path = [(10, 10), (20, 20)]
        mock_npc_state.is_moving = True
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should not complete while NPC is moving
        assert result is False

    def test_execute_npc_has_path(self) -> None:
        """Test executing when NPC has a path but is_moving is False."""
        action = WaitForNPCMovementAction(npc_name="martin")

        # Mock NPC state with path but not moving
        mock_npc_state = MagicMock()
        mock_npc_state.path = [(10, 10)]
        mock_npc_state.is_moving = False
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should not complete while NPC has a path
        assert result is False

    def test_execute_npc_movement_complete(self) -> None:
        """Test executing when NPC has completed movement."""
        action = WaitForNPCMovementAction(npc_name="martin")

        # Mock NPC state that has completed movement
        mock_npc_state = MagicMock()
        mock_npc_state.path = []
        mock_npc_state.is_moving = False
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete when path is empty and not moving
        assert result is True

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npc": "yema"}

        action = WaitForNPCMovementAction.from_dict(data)

        assert action.npc_name == "yema"

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}

        action = WaitForNPCMovementAction.from_dict(data)

        assert action.npc_name == ""


class TestWaitForNPCsAppearAction(unittest.TestCase):
    """Test Suite for WaitForNPCsAppearAction."""

    def setUp(self) -> None:
        """Set up the test context."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_initialization(self) -> None:
        """Test proper initialization of WaitForNPCsAppearAction."""
        action = WaitForNPCsAppearAction(npc_names=["martin", "yema"])
        assert action.npc_names == ["martin", "yema"]

    def test_execute_npcs_not_found(self) -> None:
        """Test executing when NPCs are not found."""
        action = WaitForNPCsAppearAction(npc_names=["martin", "yema"])

        # Mock empty NPC list
        self.mock_npc_plugin.get_npcs.return_value = {}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately when NPCs not found
        assert result is True

    def test_execute_animated_npc_still_appearing(self) -> None:
        """Test executing when AnimatedNPC is still appearing."""
        action = WaitForNPCsAppearAction(npc_names=["martin"])

        # Mock AnimatedNPC that hasn't completed appear animation
        mock_sprite = MagicMock(spec=AnimatedNPC)
        mock_sprite.appear_complete = False
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should not complete while NPC is still appearing
        assert result is False

    def test_execute_animated_npc_appear_complete(self) -> None:
        """Test executing when AnimatedNPC has completed appearing."""
        action = WaitForNPCsAppearAction(npc_names=["martin"])

        # Mock AnimatedNPC that has completed appear animation
        mock_sprite = MagicMock(spec=AnimatedNPC)
        mock_sprite.appear_complete = True
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete when appear animation is done
        assert result is True

    def test_execute_non_animated_npc(self) -> None:
        """Test executing with non-AnimatedNPC sprite."""
        action = WaitForNPCsAppearAction(npc_names=["martin"])

        # Mock regular sprite (not AnimatedNPC)
        mock_sprite = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately for non-animated NPCs
        assert result is True

    def test_execute_multiple_npcs_mixed(self) -> None:
        """Test executing with multiple NPCs in different states."""
        action = WaitForNPCsAppearAction(npc_names=["martin", "yema"])

        # Martin is an AnimatedNPC still appearing
        mock_sprite1 = MagicMock(spec=AnimatedNPC)
        mock_sprite1.appear_complete = False
        mock_npc_state1 = MagicMock()
        mock_npc_state1.sprite = mock_sprite1

        # Yema is an AnimatedNPC that has completed
        mock_sprite2 = MagicMock(spec=AnimatedNPC)
        mock_sprite2.appear_complete = True
        mock_npc_state2 = MagicMock()
        mock_npc_state2.sprite = mock_sprite2

        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state1, "yema": mock_npc_state2}

        # Execute action
        result = action.execute(self.mock_context)

        # Should not complete while martin is still appearing
        assert result is False

    def test_execute_multiple_npcs_all_complete(self) -> None:
        """Test executing with multiple NPCs all completed."""
        action = WaitForNPCsAppearAction(npc_names=["martin", "yema"])

        # Both are AnimatedNPCs that have completed
        mock_sprite1 = MagicMock(spec=AnimatedNPC)
        mock_sprite1.appear_complete = True
        mock_npc_state1 = MagicMock()
        mock_npc_state1.sprite = mock_sprite1

        mock_sprite2 = MagicMock(spec=AnimatedNPC)
        mock_sprite2.appear_complete = True
        mock_npc_state2 = MagicMock()
        mock_npc_state2.sprite = mock_sprite2

        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state1, "yema": mock_npc_state2}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete when all NPCs have appeared
        assert result is True

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npcs": ["martin", "yema", "romi"]}

        action = WaitForNPCsAppearAction.from_dict(data)

        assert action.npc_names == ["martin", "yema", "romi"]

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}

        action = WaitForNPCsAppearAction.from_dict(data)

        assert action.npc_names == []


class TestWaitForNPCsDisappearAction(unittest.TestCase):
    """Test Suite for WaitForNPCsDisappearAction."""

    def setUp(self) -> None:
        """Set up the test context."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_initialization(self) -> None:
        """Test proper initialization of WaitForNPCsDisappearAction."""
        action = WaitForNPCsDisappearAction(npc_names=["martin", "yema"])
        assert action.npc_names == ["martin", "yema"]

    def test_execute_npcs_not_found(self) -> None:
        """Test executing when NPCs are not found."""
        action = WaitForNPCsDisappearAction(npc_names=["martin", "yema"])

        # Mock empty NPC list
        self.mock_npc_plugin.get_npcs.return_value = {}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately when NPCs not found
        assert result is True

    def test_execute_animated_npc_still_disappearing(self) -> None:
        """Test executing when AnimatedNPC is still disappearing."""
        action = WaitForNPCsDisappearAction(npc_names=["martin"])

        # Mock AnimatedNPC that hasn't completed disappear animation
        mock_sprite = MagicMock(spec=AnimatedNPC)
        mock_sprite.disappear_complete = False
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should not complete while NPC is still disappearing
        assert result is False

    def test_execute_animated_npc_disappear_complete(self) -> None:
        """Test executing when AnimatedNPC has completed disappearing."""
        action = WaitForNPCsDisappearAction(npc_names=["martin"])

        # Mock AnimatedNPC that has completed disappear animation
        mock_sprite = MagicMock(spec=AnimatedNPC)
        mock_sprite.disappear_complete = True
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete when disappear animation is done
        assert result is True

    def test_execute_non_animated_npc(self) -> None:
        """Test executing with non-AnimatedNPC sprite."""
        action = WaitForNPCsDisappearAction(npc_names=["martin"])

        # Mock regular sprite (not AnimatedNPC)
        mock_sprite = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately for non-animated NPCs
        assert result is True

    def test_execute_multiple_npcs_mixed(self) -> None:
        """Test executing with multiple NPCs in different states."""
        action = WaitForNPCsDisappearAction(npc_names=["martin", "yema"])

        # Martin is an AnimatedNPC still disappearing
        mock_sprite1 = MagicMock(spec=AnimatedNPC)
        mock_sprite1.disappear_complete = False
        mock_npc_state1 = MagicMock()
        mock_npc_state1.sprite = mock_sprite1

        # Yema is an AnimatedNPC that has completed
        mock_sprite2 = MagicMock(spec=AnimatedNPC)
        mock_sprite2.disappear_complete = True
        mock_npc_state2 = MagicMock()
        mock_npc_state2.sprite = mock_sprite2

        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state1, "yema": mock_npc_state2}

        # Execute action
        result = action.execute(self.mock_context)

        # Should not complete while martin is still disappearing
        assert result is False

    def test_execute_multiple_npcs_all_complete(self) -> None:
        """Test executing with multiple NPCs all completed."""
        action = WaitForNPCsDisappearAction(npc_names=["martin", "yema"])

        # Both are AnimatedNPCs that have completed
        mock_sprite1 = MagicMock(spec=AnimatedNPC)
        mock_sprite1.disappear_complete = True
        mock_npc_state1 = MagicMock()
        mock_npc_state1.sprite = mock_sprite1

        mock_sprite2 = MagicMock(spec=AnimatedNPC)
        mock_sprite2.disappear_complete = True
        mock_npc_state2 = MagicMock()
        mock_npc_state2.sprite = mock_sprite2

        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state1, "yema": mock_npc_state2}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete when all NPCs have disappeared
        assert result is True

    def test_from_dict(self) -> None:
        """Test creating action from dictionary."""
        data = {"npcs": ["martin", "yema", "romi"]}

        action = WaitForNPCsDisappearAction.from_dict(data)

        assert action.npc_names == ["martin", "yema", "romi"]

    def test_from_dict_with_defaults(self) -> None:
        """Test creating action from dictionary with missing fields."""
        data = {}

        action = WaitForNPCsDisappearAction.from_dict(data)

        assert action.npc_names == []


class TestStartDisappearAnimationAction(unittest.TestCase):
    """Test Suite for StartDisappearAnimationAction."""

    def setUp(self) -> None:
        """Set up the test context."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_scene_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin
        self.mock_context.scene_plugin = self.mock_scene_plugin

    def test_initialization(self) -> None:
        """Test proper initialization of StartDisappearAnimationAction."""
        action = StartDisappearAnimationAction(npc_names=["martin", "yema"])
        assert action.npc_names == ["martin", "yema"]
        assert not action.animation_started

    def test_execute_starts_animation(self) -> None:
        """Test executing starts the disappear animation."""
        action = StartDisappearAnimationAction(npc_names=["martin"])

        # Mock AnimatedNPC
        mock_sprite = MagicMock(spec=AnimatedNPC)
        mock_sprite.disappear_complete = False
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        mock_npc_state.disappear_event_emitted = True
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Animation started but not complete
        assert action.animation_started is True
        assert result is False  # Not complete yet

        # Should have called start_disappear_animation
        mock_sprite.start_disappear_animation.assert_called_once()
        # Should have reset disappear event flag
        assert mock_npc_state.disappear_event_emitted is False

    def test_execute_waits_for_completion(self) -> None:
        """Test executing waits for animation completion."""
        action = StartDisappearAnimationAction(npc_names=["martin"])

        # Mock AnimatedNPC
        mock_sprite = MagicMock(spec=AnimatedNPC)
        mock_sprite.disappear_complete = True
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        mock_npc_state.disappear_event_emitted = True
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately
        assert result is True

        # Should have removed NPC from wall list
        self.mock_scene_plugin.remove_from_wall_list.assert_called_once_with(mock_sprite)

    def test_execute_multiple_npcs(self) -> None:
        """Test executing with multiple NPCs."""
        action = StartDisappearAnimationAction(npc_names=["martin", "yema"])

        # Mock AnimatedNPCs
        mock_sprite1 = MagicMock(spec=AnimatedNPC)
        mock_sprite1.disappear_complete = True
        mock_npc_state1 = MagicMock()
        mock_npc_state1.sprite = mock_sprite1

        mock_sprite2 = MagicMock(spec=AnimatedNPC)
        mock_sprite2.disappear_complete = True
        mock_npc_state2 = MagicMock()
        mock_npc_state2.sprite = mock_sprite2

        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state1, "yema": mock_npc_state2}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete when all animations are done
        assert result is True

        # Should have called start_disappear_animation for both
        mock_sprite1.start_disappear_animation.assert_called_once()
        mock_sprite2.start_disappear_animation.assert_called_once()

        # Should have removed both from wall list
        assert self.mock_scene_plugin.remove_from_wall_list.call_count == 2

    def test_execute_non_animated_npc(self) -> None:
        """Test executing with non-AnimatedNPC sprite."""
        action = StartDisappearAnimationAction(npc_names=["martin"])

        # Mock regular sprite (not AnimatedNPC)
        mock_sprite = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately even though NPC is not AnimatedNPC
        assert result is True

    def test_execute_npc_not_found(self) -> None:
        """Test executing when NPC is not found."""
        action = StartDisappearAnimationAction(npc_names=["invalid_npc"])

        # Mock empty NPC list
        self.mock_npc_plugin.get_npcs.return_value = {}

        # Execute action
        result = action.execute(self.mock_context)

        # Should complete immediately
        assert result is True

    def test_execute_animation_in_progress(self) -> None:
        """Test executing while animation is in progress."""
        action = StartDisappearAnimationAction(npc_names=["martin"])

        # Mock AnimatedNPC with animation in progress
        mock_sprite = MagicMock(spec=AnimatedNPC)
        mock_sprite.disappear_complete = False
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_sprite
        self.mock_npc_plugin.get_npcs.return_value = {"martin": mock_npc_state}

        # First execute to start animation
        result1 = action.execute(self.mock_context)
        assert result1 is False

        # Second execute while still in progress
        result2 = action.execute(self.mock_context)
        assert result2 is False

        # Should only have called start_disappear_animation once
        mock_sprite.start_disappear_animation.assert_called_once()

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

        action = StartDisappearAnimationAction.from_dict(data)

        assert action.npc_names == []


if __name__ == "__main__":
    unittest.main()
