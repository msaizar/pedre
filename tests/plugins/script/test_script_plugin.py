"""Unit tests for ScriptPlugin in src/pedre/plugins/script/plugin.py."""

import json
import unittest
from unittest.mock import MagicMock, mock_open, patch

import pytest

from pedre.plugins.script.base import Script, ScriptValidationError
from pedre.plugins.script.events import ScriptCompleteEvent
from pedre.plugins.script.plugin import ScriptPlugin


class TestScriptPlugin(unittest.TestCase):
    """Test Suite for ScriptPlugin."""

    def setUp(self) -> None:
        """Set up the ScriptPlugin and mock context."""
        self.plugin = ScriptPlugin()
        self.mock_context = MagicMock()

        # Mock event bus
        self.mock_event_bus = MagicMock()
        self.mock_context.event_bus = self.mock_event_bus

        # Mock scene plugin
        self.mock_scene_plugin = MagicMock()
        self.mock_scene_plugin.get_current_scene.return_value = "test_scene"
        self.mock_context.scene_plugin = self.mock_scene_plugin

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        plugin = ScriptPlugin()
        assert plugin.name == "script"
        assert plugin.dependencies == []
        assert plugin.scripts == {}
        assert plugin.active_sequences == []
        assert plugin._pending_script_checks == []
        assert plugin._subscribed_events == set()

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_setup_no_scripts_dir(self, mock_asset_path: MagicMock) -> None:
        """Test setup when scripts directory doesn't exist."""
        # Create a mock Path that doesn't exist
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_asset_path.return_value = "/fake/scripts"

        with (
            patch("pedre.plugins.script.plugin.Path") as mock_path_class,
            patch("pedre.plugins.script.plugin.logger") as mock_logger,
        ):
            mock_path_class.return_value = mock_path

            self.plugin.setup(self.mock_context)

            assert self.plugin.context == self.mock_context
            mock_logger.warning.assert_called_once()

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_setup_no_script_files(self, mock_asset_path: MagicMock) -> None:
        """Test setup when no script files exist."""
        # Create a mock Path that exists but has no script files
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = []
        mock_asset_path.return_value = "/fake/scripts"

        with (
            patch("pedre.plugins.script.plugin.Path") as mock_path_class,
            patch("pedre.plugins.script.plugin.logger") as mock_logger,
        ):
            mock_path_class.return_value = mock_path

            self.plugin.setup(self.mock_context)

            mock_logger.info.assert_any_call("No script files found in %s", mock_path)

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_setup_loads_scripts(self, mock_asset_path: MagicMock) -> None:
        """Test setup successfully loads scripts from file."""
        # Mock script data
        script_data = {
            "test_script": {
                "trigger": {"event": "test_event"},
                "conditions": [],
                "actions": [{"type": "test_action"}],
                "run_once": True,
                "scene": "test_scene",
            }
        }

        # Create mock script file
        mock_file = MagicMock()
        mock_file.name = "test_scripts.json"
        m_open = mock_open(read_data=json.dumps(script_data))
        mock_file.open = m_open

        # Create mock Path that exists and has script files
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = [mock_file]
        mock_asset_path.return_value = "/fake/scripts"

        # Mock registries for validation
        with (
            patch("pedre.plugins.script.plugin.Path") as mock_path_class,
            patch("pedre.plugins.script.plugin.EventRegistry") as mock_event_registry,
            patch("pedre.plugins.script.plugin.ActionRegistry") as mock_action_registry,
        ):
            mock_path_class.return_value = mock_path
            mock_event_class = MagicMock()
            mock_event_registry.get.return_value = mock_event_class
            mock_event_registry.is_registered.return_value = True
            mock_event_registry.get_trigger_keys.return_value = None  # No trigger validation
            mock_action_registry.is_registered.return_value = True
            mock_action_registry.validate.return_value = []  # No validation errors

            self.plugin.setup(self.mock_context)

            # Verify script was loaded
            assert "test_script" in self.plugin.scripts
            assert self.plugin.scripts["test_script"].run_once is True
            assert self.plugin.scripts["test_script"].scene == "test_scene"

            # Verify event handler was registered
            self.mock_event_bus.subscribe.assert_called_once()

    def test_cleanup(self) -> None:
        """Test cleanup clears all resources."""
        self.plugin.scripts = {"test": Script()}
        self.plugin.active_sequences = [("test", MagicMock())]
        self.plugin._subscribed_events = {"test_event"}

        self.plugin.setup(self.mock_context)
        self.plugin.cleanup()

        self.mock_event_bus.unregister_all.assert_called_once_with(self.plugin)
        assert self.plugin.scripts == {}
        assert self.plugin.active_sequences == []
        assert self.plugin._subscribed_events == set()

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_reset_reloads_scripts(
        self,
        mock_asset_path: MagicMock,
    ) -> None:
        """Test reset clears state and reloads scripts."""
        # Create mock Path that exists but has no script files
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = []
        mock_asset_path.return_value = "/fake/scripts"

        # Setup initial state
        with patch("pedre.plugins.script.plugin.Path") as mock_path_class:
            mock_path_class.return_value = mock_path
            self.plugin.setup(self.mock_context)
            self.plugin.scripts = {"old_script": Script()}
            self.plugin.active_sequences = [("old", MagicMock())]
            self.plugin._subscribed_events = {"old_event"}

            self.plugin.reset()

            # Verify state was cleared
            assert self.plugin.active_sequences == []
            assert self.plugin._subscribed_events == set()
            self.mock_event_bus.unregister_all.assert_called()

    def test_get_scripts(self) -> None:
        """Test getting scripts dictionary."""
        test_script = Script()
        self.plugin.scripts = {"test": test_script}

        result = self.plugin.get_scripts()

        assert result == {"test": test_script}

    def test_get_save_state_empty(self) -> None:
        """Test get save state with no scripts."""
        state = self.plugin.get_save_state()

        assert state["completed_scripts"] == []
        assert state["run_once_scripts"] == []
        assert state["active_scripts"] == []

    def test_get_save_state_with_scripts(self) -> None:
        """Test get save state with completed and run-once scripts."""
        # Create scripts with different states
        completed_script = Script()
        completed_script.completed = True

        run_once_script = Script(run_once=True)
        run_once_script.has_run = True

        self.plugin.scripts = {
            "completed": completed_script,
            "run_once": run_once_script,
        }

        state = self.plugin.get_save_state()

        assert "completed" in state["completed_scripts"]
        assert "run_once" in state["run_once_scripts"]

    def test_get_save_state_with_active_sequences(self) -> None:
        """Test get save state with active sequences."""
        mock_sequence = MagicMock()
        mock_sequence.current_index = 5

        self.plugin.active_sequences = [("active_script", mock_sequence)]

        state = self.plugin.get_save_state()

        assert len(state["active_scripts"]) == 1
        assert state["active_scripts"][0]["script_name"] == "active_script"
        assert state["active_scripts"][0]["current_index"] == 5
        assert state["active_scripts"][0]["is_fail_sequence"] is False

    def test_get_save_state_with_fail_sequence(self) -> None:
        """Test get save state with fail sequence."""
        mock_sequence = MagicMock()
        mock_sequence.current_index = 3

        self.plugin.active_sequences = [("test_script_fail", mock_sequence)]

        state = self.plugin.get_save_state()

        assert len(state["active_scripts"]) == 1
        assert state["active_scripts"][0]["script_name"] == "test_script"
        assert state["active_scripts"][0]["is_fail_sequence"] is True

    def test_restore_save_state_completed_scripts(self) -> None:
        """Test restoring completed scripts."""
        script = Script()
        self.plugin.scripts = {"test_script": script}

        state = {"completed_scripts": ["test_script"]}

        self.plugin.restore_save_state(state)

        assert self.plugin.scripts["test_script"].completed is True

    def test_restore_save_state_run_once_scripts(self) -> None:
        """Test restoring run-once scripts."""
        script = Script(run_once=True)
        self.plugin.scripts = {"test_script": script}

        state = {"run_once_scripts": ["test_script"]}

        self.plugin.restore_save_state(state)

        assert self.plugin.scripts["test_script"].has_run is True

    def test_restore_save_state_completed_script_not_in_registry(self) -> None:
        """Test restoring completed script that's not in registry."""
        state = {"completed_scripts": ["nonexistent_script"]}

        # Should not crash, just skip the missing script
        self.plugin.restore_save_state(state)

    def test_restore_save_state_run_once_script_not_in_registry(self) -> None:
        """Test restoring run-once script that's not in registry."""
        state = {"run_once_scripts": ["nonexistent_script"]}

        # Should not crash, just skip the missing script
        self.plugin.restore_save_state(state)

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_restore_save_state_active_scripts(self, mock_action_registry: MagicMock) -> None:
        """Test restoring active scripts."""
        script = Script(actions=[{"type": "test_action"}])
        self.plugin.scripts = {"test_script": script}

        # Mock action parsing
        mock_action = MagicMock()
        mock_action_registry.parse.return_value = mock_action

        state = {
            "active_scripts": [
                {
                    "script_name": "test_script",
                    "current_index": 0,
                    "is_fail_sequence": False,
                }
            ]
        }

        self.plugin.restore_save_state(state)

        assert len(self.plugin.active_sequences) == 1
        assert self.plugin.active_sequences[0][0] == "test_script"

    def test_restore_save_state_clears_existing_sequences(self) -> None:
        """Test restoring state clears existing active sequences."""
        # Add existing active sequence
        self.plugin.active_sequences = [("old_script", MagicMock())]

        state = {"active_scripts": []}

        self.plugin.restore_save_state(state)

        assert len(self.plugin.active_sequences) == 0

    def test_calculate_resume_index_wait_action(self) -> None:
        """Test resume index backs up past wait actions."""
        actions = [
            {"type": "move_npc"},
            {"type": "wait_for_movement"},
            {"type": "dialog"},
        ]

        # If saved at wait action, should resume at preceding non-wait
        resume_index = self.plugin._calculate_resume_index(actions, 1)
        assert resume_index == 0

    def test_calculate_resume_index_non_wait_action(self) -> None:
        """Test resume index stays at non-wait actions."""
        actions = [
            {"type": "move_npc"},
            {"type": "dialog"},
            {"type": "wait_for_dialog"},
        ]

        resume_index = self.plugin._calculate_resume_index(actions, 1)
        assert resume_index == 1

    def test_calculate_resume_index_at_start(self) -> None:
        """Test resume index at start doesn't go negative."""
        actions = [
            {"type": "wait_for_dialog"},
            {"type": "dialog"},
        ]

        resume_index = self.plugin._calculate_resume_index(actions, 0)
        assert resume_index == 0

    def test_update_no_context(self) -> None:
        """Test update does nothing without context."""
        self.plugin.context = None
        self.plugin.update(0.016)
        # Should not crash

    def test_update_executes_sequences(self) -> None:
        """Test update executes active sequences."""
        self.plugin.setup(self.mock_context)

        # Create mock sequence
        mock_sequence = MagicMock()
        mock_sequence.execute.return_value = False  # Not completed

        self.plugin.active_sequences = [("test_script", mock_sequence)]

        self.plugin.update(0.016)

        mock_sequence.execute.assert_called_once_with(self.mock_context)
        assert len(self.plugin.active_sequences) == 1

    def test_update_removes_completed_sequences(self) -> None:
        """Test update removes completed sequences."""
        script = Script()
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        # Create mock completed sequence
        mock_sequence = MagicMock()
        mock_sequence.execute.return_value = True  # Completed

        self.plugin.active_sequences = [("test_script", mock_sequence)]

        self.plugin.update(0.016)

        assert len(self.plugin.active_sequences) == 0
        assert script.completed is True
        self.mock_event_bus.publish.assert_called_once()

    def test_update_completed_sequence_not_in_scripts(self) -> None:
        """Test update handles completed sequence not in scripts registry."""
        self.plugin.setup(self.mock_context)

        # Create mock completed sequence for a script not in registry
        mock_sequence = MagicMock()
        mock_sequence.execute.return_value = True  # Completed

        self.plugin.active_sequences = [("nonexistent_script", mock_sequence)]

        self.plugin.update(0.016)

        # Should still remove sequence and publish event
        assert len(self.plugin.active_sequences) == 0
        self.mock_event_bus.publish.assert_called_once()

    def test_update_publishes_completion_event(self) -> None:
        """Test update publishes ScriptCompleteEvent."""
        script = Script()
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        mock_sequence = MagicMock()
        mock_sequence.execute.return_value = True

        self.plugin.active_sequences = [("test_script", mock_sequence)]

        self.plugin.update(0.016)

        # Verify event was published
        assert self.mock_event_bus.publish.called
        published_event = self.mock_event_bus.publish.call_args[0][0]
        assert isinstance(published_event, ScriptCompleteEvent)
        assert published_event.script_name == "test_script"

    def test_update_processes_pending_checks(self) -> None:
        """Test update processes pending script checks."""
        script = Script(conditions=[{"check": "test", "value": True}])
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._pending_script_checks = ["test_script"]

        with (
            patch.object(self.plugin, "_check_conditions", return_value=True),
            patch.object(self.plugin, "_execute_script"),
        ):
            self.plugin.update(0.016)

            assert len(self.plugin._pending_script_checks) == 0

    def test_parse_scripts(self) -> None:
        """Test parsing script data into Script objects."""
        script_data = {
            "test_script": {
                "trigger": {"event": "test_event"},
                "conditions": [{"check": "test"}],
                "scene": "test_scene",
                "run_once": True,
                "actions": [{"type": "action1"}],
                "on_condition_fail": [{"type": "fail_action"}],
            }
        }

        self.plugin._parse_scripts(script_data)

        assert "test_script" in self.plugin.scripts
        script = self.plugin.scripts["test_script"]
        assert script.trigger == {"event": "test_event"}
        assert script.conditions == [{"check": "test"}]
        assert script.scene == "test_scene"
        assert script.run_once is True
        assert script.actions == [{"type": "action1"}]
        assert script.on_condition_fail == [{"type": "fail_action"}]

    @patch("pedre.plugins.script.plugin.ConditionRegistry")
    def test_check_conditions_all_pass(self, mock_condition_registry: MagicMock) -> None:
        """Test check conditions when all pass."""
        self.plugin.setup(self.mock_context)
        mock_condition_registry.check.return_value = True

        conditions = [
            {"check": "condition1"},
            {"check": "condition2"},
        ]

        result = self.plugin._check_conditions(conditions)

        assert result is True
        assert mock_condition_registry.check.call_count == 2

    @patch("pedre.plugins.script.plugin.ConditionRegistry")
    def test_check_conditions_one_fails(self, mock_condition_registry: MagicMock) -> None:
        """Test check conditions when one fails."""
        self.plugin.setup(self.mock_context)
        mock_condition_registry.check.side_effect = [True, False]

        conditions = [
            {"check": "condition1"},
            {"check": "condition2"},
        ]

        result = self.plugin._check_conditions(conditions)

        assert result is False

    def test_check_conditions_no_context(self) -> None:
        """Test check conditions without context."""
        self.plugin.context = None

        result = self.plugin._check_conditions([{"check": "test"}])

        assert result is False

    def test_check_single_condition_missing_check(self) -> None:
        """Test check single condition with missing check field."""
        self.plugin.setup(self.mock_context)

        condition = {"value": "test"}  # Missing 'check' field

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            result = self.plugin._check_single_condition(condition)

            assert result is False
            mock_logger.warning.assert_called_once()

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_execute_script(self, mock_action_registry: MagicMock) -> None:
        """Test executing a script."""
        self.plugin.setup(self.mock_context)

        mock_action = MagicMock()
        mock_action_registry.parse.return_value = mock_action

        script = Script(actions=[{"type": "test_action"}])

        self.plugin._execute_script("test_script", script)

        assert len(self.plugin.active_sequences) == 1
        assert self.plugin.active_sequences[0][0] == "test_script"

    def test_execute_actions_no_context(self) -> None:
        """Test execute actions without context."""
        self.plugin.context = None

        self.plugin._execute_actions("test", [{"type": "action"}])

        # Should not crash
        assert len(self.plugin.active_sequences) == 0

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_execute_actions_invalid_action(self, mock_action_registry: MagicMock) -> None:
        """Test execute actions with invalid action."""
        self.plugin.setup(self.mock_context)
        mock_action_registry.parse.return_value = None  # Invalid action

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            self.plugin._execute_actions("test", [{"type": "invalid"}])

            mock_logger.warning.assert_called()
            assert len(self.plugin.active_sequences) == 0

    def test_execute_actions_empty_list(self) -> None:
        """Test execute actions with empty list."""
        self.plugin.setup(self.mock_context)

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            self.plugin._execute_actions("test", [])

            mock_logger.warning.assert_called()
            assert len(self.plugin.active_sequences) == 0

    def test_process_pending_checks_no_context(self) -> None:
        """Test process pending checks without context."""
        self.plugin.context = None
        self.plugin._pending_script_checks = ["test"]

        self.plugin._process_pending_checks()

        # Should not crash, checks should remain
        assert self.plugin._pending_script_checks == ["test"]

    def test_process_pending_checks_empty_list(self) -> None:
        """Test process pending checks with empty list."""
        self.plugin.setup(self.mock_context)
        self.plugin._pending_script_checks = []

        self.plugin._process_pending_checks()

        # Should not crash

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_process_pending_checks_executes_matching_scripts(self, mock_action_registry: MagicMock) -> None:
        """Test process pending checks executes scripts with passing conditions."""
        script = Script(conditions=[{"check": "test"}], actions=[{"type": "action"}])
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        mock_action = MagicMock()
        mock_action_registry.parse.return_value = mock_action

        self.plugin._pending_script_checks = ["test_script"]

        with patch.object(self.plugin, "_check_conditions", return_value=True):
            self.plugin._process_pending_checks()

            assert len(self.plugin._pending_script_checks) == 0
            assert len(self.plugin.active_sequences) == 1

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_process_pending_checks_marks_run_once(self, mock_action_registry: MagicMock) -> None:
        """Test process pending checks marks run_once scripts."""
        script = Script(run_once=True, conditions=[{"check": "test"}], actions=[{"type": "action"}])
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        mock_action = MagicMock()
        mock_action_registry.parse.return_value = mock_action

        self.plugin._pending_script_checks = ["test_script"]

        with patch.object(self.plugin, "_check_conditions", return_value=True):
            self.plugin._process_pending_checks()

            assert script.has_run is True

    def test_process_pending_checks_script_not_in_registry(self) -> None:
        """Test process pending checks when script not in registry."""
        self.plugin.setup(self.mock_context)
        self.plugin._pending_script_checks = ["nonexistent_script"]

        # Should not crash, just skip the missing script
        self.plugin._process_pending_checks()

        assert len(self.plugin._pending_script_checks) == 0

    def test_process_pending_checks_conditions_fail(self) -> None:
        """Test process pending checks when conditions fail."""
        script = Script(conditions=[{"check": "test"}], actions=[{"type": "action"}])
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._pending_script_checks = ["test_script"]

        with patch.object(self.plugin, "_check_conditions", return_value=False):
            self.plugin._process_pending_checks()

            # Should not execute script
            assert len(self.plugin.active_sequences) == 0

    def test_trigger_matches_event_correct_match(self) -> None:
        """Test trigger matches event correctly."""
        trigger = {"event": "test_event", "npc": "martin"}
        event_data = {"npc": "martin"}

        result = self.plugin._trigger_matches_event(trigger, "test_event", event_data)

        assert result is True

    def test_trigger_matches_event_wrong_event_type(self) -> None:
        """Test trigger doesn't match wrong event type."""
        trigger = {"event": "test_event"}

        result = self.plugin._trigger_matches_event(trigger, "other_event", {})

        assert result is False

    def test_trigger_matches_event_missing_filter(self) -> None:
        """Test trigger doesn't match when event data missing filter."""
        trigger = {"event": "test_event", "npc": "martin"}
        event_data = {"npc": "john"}  # Different NPC

        result = self.plugin._trigger_matches_event(trigger, "test_event", event_data)

        assert result is False

    def test_trigger_matches_event_no_filters(self) -> None:
        """Test trigger matches event with no additional filters."""
        trigger = {"event": "test_event"}
        event_data = {"npc": "martin", "other": "data"}

        result = self.plugin._trigger_matches_event(trigger, "test_event", event_data)

        assert result is True

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_handle_event_trigger_executes_matching_script(self, mock_action_registry: MagicMock) -> None:
        """Test handle event trigger executes matching scripts."""
        script = Script(
            trigger={"event": "test_event"},
            conditions=[],
            actions=[{"type": "action"}],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        mock_action = MagicMock()
        mock_action_registry.parse.return_value = mock_action

        self.plugin._handle_event_trigger("test_event", {})

        assert len(self.plugin.active_sequences) == 1

    def test_handle_event_trigger_skips_wrong_scene(self) -> None:
        """Test handle event trigger skips scripts in wrong scene."""
        script = Script(
            trigger={"event": "test_event"},
            scene="other_scene",
            actions=[{"type": "action"}],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.mock_scene_plugin.get_current_scene.return_value = "current_scene"

        self.plugin._handle_event_trigger("test_event", {})

        assert len(self.plugin.active_sequences) == 0

    def test_handle_event_trigger_skips_already_run(self) -> None:
        """Test handle event trigger skips run_once scripts that ran."""
        script = Script(
            trigger={"event": "test_event"},
            run_once=True,
            actions=[{"type": "action"}],
        )
        script.has_run = True
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._handle_event_trigger("test_event", {})

        assert len(self.plugin.active_sequences) == 0

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_handle_event_trigger_marks_run_once(self, mock_action_registry: MagicMock) -> None:
        """Test handle event trigger marks run_once scripts."""
        script = Script(
            trigger={"event": "test_event"},
            run_once=True,
            conditions=[],
            actions=[{"type": "action"}],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        mock_action = MagicMock()
        mock_action_registry.parse.return_value = mock_action

        self.plugin._handle_event_trigger("test_event", {})

        assert script.has_run is True

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_handle_event_trigger_executes_on_condition_fail(self, mock_action_registry: MagicMock) -> None:
        """Test handle event trigger executes on_condition_fail actions."""
        script = Script(
            trigger={"event": "test_event"},
            conditions=[{"check": "test"}],
            actions=[{"type": "success_action"}],
            on_condition_fail=[{"type": "fail_action"}],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        mock_action = MagicMock()
        mock_action_registry.parse.return_value = mock_action

        with patch.object(self.plugin, "_check_conditions", return_value=False):
            self.plugin._handle_event_trigger("test_event", {})

            # Should execute fail sequence, not main sequence
            assert len(self.plugin.active_sequences) == 1
            assert self.plugin.active_sequences[0][0] == "test_script_fail"

    def test_handle_event_trigger_no_trigger(self) -> None:
        """Test handle event trigger skips scripts with no trigger."""
        script = Script(trigger=None, actions=[{"type": "action"}])
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._handle_event_trigger("test_event", {})

        assert len(self.plugin.active_sequences) == 0

    def test_handle_event_trigger_mismatched_trigger(self) -> None:
        """Test handle event trigger skips scripts with mismatched triggers."""
        script = Script(
            trigger={"event": "other_event", "npc": "bob"},
            actions=[{"type": "action"}],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        # Trigger with different event type
        self.plugin._handle_event_trigger("test_event", {"npc": "bob"})

        # Should not execute because trigger doesn't match
        assert len(self.plugin.active_sequences) == 0

    @patch("pedre.plugins.script.plugin.EventRegistry")
    def test_register_event_handlers_subscribes_to_events(self, mock_event_registry: MagicMock) -> None:
        """Test register event handlers subscribes to all required events."""
        mock_event_class = MagicMock()
        mock_event_registry.get.return_value = mock_event_class

        script1 = Script(trigger={"event": "event1"})
        script2 = Script(trigger={"event": "event2"})
        script3 = Script(trigger={"event": "event1"})  # Duplicate

        self.plugin.scripts = {
            "script1": script1,
            "script2": script2,
            "script3": script3,
        }

        self.plugin.setup(self.mock_context)
        self.plugin._register_event_handlers()

        # Should subscribe twice (once per unique event)
        assert self.mock_event_bus.subscribe.call_count == 2
        assert "event1" in self.plugin._subscribed_events
        assert "event2" in self.plugin._subscribed_events

    def test_register_event_handlers_skips_already_subscribed(self) -> None:
        """Test register event handlers doesn't duplicate subscriptions."""
        script = Script(trigger={"event": "test_event"})
        self.plugin.scripts = {"script": script}
        self.plugin._subscribed_events = {"test_event"}  # Already subscribed

        self.plugin.setup(self.mock_context)
        self.plugin._register_event_handlers()

        # Should not subscribe again
        self.mock_event_bus.subscribe.assert_not_called()

    @patch("pedre.plugins.script.plugin.EventRegistry")
    def test_register_event_handlers_warns_unregistered_event(self, mock_event_registry: MagicMock) -> None:
        """Test register event handlers warns about unregistered events."""
        mock_event_registry.get.return_value = None  # Event not registered

        script = Script(trigger={"event": "unknown_event"})
        self.plugin.scripts = {"script": script}

        self.plugin.setup(self.mock_context)

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            self.plugin._register_event_handlers()

            mock_logger.warning.assert_called_once()

    @patch("pedre.plugins.script.plugin.EventRegistry")
    def test_on_generic_event_calls_handle_event_trigger(self, mock_event_registry: MagicMock) -> None:
        """Test on_generic_event calls handle_event_trigger."""
        mock_event_registry.get_name.return_value = "test_event"

        mock_event = MagicMock()
        mock_event.get_script_data.return_value = {"npc": "martin"}

        self.plugin.setup(self.mock_context)

        with patch.object(self.plugin, "_handle_event_trigger") as mock_handle:
            self.plugin._on_generic_event(mock_event)

            mock_handle.assert_called_once_with("test_event", {"npc": "martin"})

    @patch("pedre.plugins.script.plugin.EventRegistry")
    def test_on_generic_event_uses_asdict_fallback(self, mock_event_registry: MagicMock) -> None:
        """Test on_generic_event falls back to asdict if no get_script_data."""
        mock_event_registry.get_name.return_value = "test_event"

        # Use MagicMock instead of creating a dataclass to avoid type issues
        mock_event = MagicMock()
        del mock_event.get_script_data  # Remove get_script_data to trigger fallback

        self.plugin.setup(self.mock_context)

        with (
            patch("pedre.plugins.script.plugin.asdict", return_value={"npc": "martin"}),
            patch.object(self.plugin, "_handle_event_trigger") as mock_handle,
        ):
            self.plugin._on_generic_event(mock_event)

            mock_handle.assert_called_once()
            call_args = mock_handle.call_args[0]
            assert call_args[0] == "test_event"
            assert "npc" in call_args[1]

    @patch("pedre.plugins.script.plugin.EventRegistry")
    def test_on_generic_event_no_event_name(self, mock_event_registry: MagicMock) -> None:
        """Test on_generic_event does nothing if event name not found."""
        mock_event_registry.get_name.return_value = None

        mock_event = MagicMock()

        self.plugin.setup(self.mock_context)

        with patch.object(self.plugin, "_handle_event_trigger") as mock_handle:
            self.plugin._on_generic_event(mock_event)

            mock_handle.assert_not_called()

    def test_restore_save_state_script_not_found(self) -> None:
        """Test restoring active script that doesn't exist warns."""
        state = {
            "active_scripts": [
                {
                    "script_name": "nonexistent_script",
                    "current_index": 0,
                    "is_fail_sequence": False,
                }
            ]
        }

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            self.plugin.restore_save_state(state)

            mock_logger.warning.assert_called_once()
            assert len(self.plugin.active_sequences) == 0

    def test_restore_save_state_empty_action_list(self) -> None:
        """Test restoring script with empty action list."""
        script = Script(actions=[])
        self.plugin.scripts = {"test_script": script}

        state = {
            "active_scripts": [
                {
                    "script_name": "test_script",
                    "current_index": 0,
                    "is_fail_sequence": False,
                }
            ]
        }

        self.plugin.restore_save_state(state)

        # Should not add to active sequences
        assert len(self.plugin.active_sequences) == 0

    def test_restore_save_state_empty_fail_sequence(self) -> None:
        """Test restoring fail sequence with empty on_condition_fail."""
        script = Script(on_condition_fail=[])
        self.plugin.scripts = {"test_script": script}

        state = {
            "active_scripts": [
                {
                    "script_name": "test_script",
                    "current_index": 0,
                    "is_fail_sequence": True,
                }
            ]
        }

        self.plugin.restore_save_state(state)

        # Should not add to active sequences
        assert len(self.plugin.active_sequences) == 0

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_restore_save_state_no_valid_actions(self, mock_action_registry: MagicMock) -> None:
        """Test restoring script when all actions fail to parse."""
        script = Script(actions=[{"type": "invalid_action"}])
        self.plugin.scripts = {"test_script": script}

        # Mock action parsing to return None (failed parse)
        mock_action_registry.parse.return_value = None

        state = {
            "active_scripts": [
                {
                    "script_name": "test_script",
                    "current_index": 0,
                    "is_fail_sequence": False,
                }
            ]
        }

        self.plugin.restore_save_state(state)

        # Should not add to active sequences when no valid actions
        assert len(self.plugin.active_sequences) == 0

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_setup_json_decode_error(self, mock_asset_path: MagicMock) -> None:
        """Test setup handles JSON decode errors gracefully."""
        # Create mock script file with invalid JSON
        mock_file = MagicMock()
        mock_file.name = "invalid_scripts.json"
        m_open = mock_open(read_data="invalid json{")
        mock_file.open = m_open

        # Create mock Path
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = [mock_file]
        mock_asset_path.return_value = "/fake/scripts"

        with (
            patch("pedre.plugins.script.plugin.Path") as mock_path_class,
            patch("pedre.plugins.script.plugin.logger") as mock_logger,
        ):
            mock_path_class.return_value = mock_path

            self.plugin.setup(self.mock_context)

            # Should log the exception
            mock_logger.exception.assert_called()

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_setup_generic_exception_in_file_load(self, mock_asset_path: MagicMock) -> None:
        """Test setup handles generic exceptions during file load."""
        # Create mock script file that raises exception on open
        mock_file = MagicMock()
        mock_file.name = "error_scripts.json"
        mock_file.open.side_effect = OSError("Cannot read file")

        # Create mock Path
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = [mock_file]
        mock_asset_path.return_value = "/fake/scripts"

        with (
            patch("pedre.plugins.script.plugin.Path") as mock_path_class,
            patch("pedre.plugins.script.plugin.logger") as mock_logger,
        ):
            mock_path_class.return_value = mock_path

            self.plugin.setup(self.mock_context)

            # Should log the exception
            mock_logger.exception.assert_called()

    def test_check_single_condition_no_context(self) -> None:
        """Test check single condition without context."""
        self.plugin.context = None

        result = self.plugin._check_single_condition({"check": "test"})

        assert result is False

    def test_handle_event_trigger_conditions_fail_no_fail_actions(self) -> None:
        """Test handle event trigger logs when conditions fail with no fail actions."""
        script = Script(
            trigger={"event": "test_event"},
            conditions=[{"check": "test"}],
            actions=[{"type": "success_action"}],
            on_condition_fail=[],  # No fail actions
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        with (
            patch.object(self.plugin, "_check_conditions", return_value=False),
            patch("pedre.plugins.script.plugin.logger") as mock_logger,
        ):
            self.plugin._handle_event_trigger("test_event", {})

            # Should log that conditions failed with no fail actions
            mock_logger.debug.assert_called()
            assert len(self.plugin.active_sequences) == 0


class TestScript(unittest.TestCase):
    """Test Suite for Script dataclass."""

    def test_initialization_defaults(self) -> None:
        """Test Script initializes with defaults."""
        script = Script()

        assert script.trigger is None
        assert script.conditions == []
        assert script.scene is None
        assert script.run_once is False
        assert script.actions == []
        assert script.on_condition_fail == []
        assert script.has_run is False
        assert script.completed is False

    def test_initialization_with_values(self) -> None:
        """Test Script initializes with provided values."""
        trigger = {"event": "test"}
        conditions = [{"check": "test"}]
        actions = [{"type": "action"}]
        on_condition_fail = [{"type": "fail"}]

        script = Script(
            trigger=trigger,
            conditions=conditions,
            scene="test_scene",
            run_once=True,
            actions=actions,
            on_condition_fail=on_condition_fail,
        )

        assert script.trigger == trigger
        assert script.conditions == conditions
        assert script.scene == "test_scene"
        assert script.run_once is True
        assert script.actions == actions
        assert script.on_condition_fail == on_condition_fail

    def test_has_run_flag(self) -> None:
        """Test has_run flag can be set."""
        script = Script()
        assert script.has_run is False

        script.has_run = True
        assert script.has_run is True

    def test_completed_flag(self) -> None:
        """Test completed flag can be set."""
        script = Script()
        assert script.completed is False

        script.completed = True
        assert script.completed is True


class TestScriptValidation(unittest.TestCase):
    """Test Suite for script validation functionality."""

    def setUp(self) -> None:
        """Set up test plugin."""
        self.plugin = ScriptPlugin()
        self.mock_context = MagicMock()

    @patch("pedre.plugins.script.plugin.EventRegistry")
    @patch("pedre.plugins.script.plugin.ConditionRegistry")
    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_validate_scripts_success(
        self,
        mock_action_registry: MagicMock,
        mock_condition_registry: MagicMock,
        mock_event_registry: MagicMock,
    ) -> None:
        """Test validate_scripts passes with valid scripts."""
        # Mock registries to return True for all checks
        mock_event_registry.is_registered.return_value = True
        mock_event_registry.get_trigger_keys.return_value = None  # No trigger key validation
        mock_condition_registry.is_registered.return_value = True
        mock_condition_registry.validate.return_value = []  # No validation errors
        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []  # No validation errors

        script = Script(
            trigger={"event": "test_event"},
            conditions=[{"check": "test_condition"}],
            actions=[{"type": "test_action"}],
            on_condition_fail=[{"type": "fail_action"}],
        )
        self.plugin.scripts = {"test_script": script}

        # Should not raise
        self.plugin.validate_scripts()

    @patch("pedre.plugins.script.plugin.EventRegistry")
    def test_validate_scripts_unknown_event(self, mock_event_registry: MagicMock) -> None:
        """Test validate_scripts detects unknown events."""
        mock_event_registry.is_registered.return_value = False
        mock_event_registry.get_all_types.return_value = ["event1", "event2"]

        script = Script(
            trigger={"event": "unknown_event"},
            actions=[{"type": "test_action"}],
        )
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        assert "unknown event 'unknown_event'" in str(cm.value)
        assert "test_script" in str(cm.value)

    @patch("pedre.plugins.script.plugin.ConditionRegistry")
    def test_validate_scripts_unknown_condition(self, mock_condition_registry: MagicMock) -> None:
        """Test validate_scripts detects unknown conditions."""
        mock_condition_registry.is_registered.return_value = False
        mock_condition_registry.get_all_types.return_value = ["cond1", "cond2"]

        script = Script(
            conditions=[{"check": "unknown_condition"}],
            actions=[{"type": "test_action"}],
        )
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        assert "unknown condition 'unknown_condition'" in str(cm.value)
        assert "test_script" in str(cm.value)

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_validate_scripts_unknown_action(self, mock_action_registry: MagicMock) -> None:
        """Test validate_scripts detects unknown actions."""
        mock_action_registry.is_registered.return_value = False
        mock_action_registry.get_all_types.return_value = ["action1", "action2"]

        script = Script(actions=[{"type": "unknown_action"}])
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        assert "unknown action type 'unknown_action'" in str(cm.value)
        assert "test_script" in str(cm.value)

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_validate_scripts_unknown_fail_action(self, mock_action_registry: MagicMock) -> None:
        """Test validate_scripts detects unknown on_condition_fail actions."""
        mock_action_registry.is_registered.side_effect = lambda t: t != "unknown_fail_action"
        mock_action_registry.get_all_types.return_value = ["action1", "action2"]

        script = Script(
            actions=[{"type": "action1"}],
            on_condition_fail=[{"type": "unknown_fail_action"}],
        )
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        assert "on_condition_fail" in str(cm.value)
        assert "unknown_fail_action" in str(cm.value)
        assert "test_script" in str(cm.value)

    def test_validate_scripts_empty_actions(self) -> None:
        """Test validate_scripts detects empty actions list."""
        script = Script(actions=[])
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        assert "'actions' list is empty" in str(cm.value)
        assert "test_script" in str(cm.value)

    def test_validate_scripts_trigger_missing_event(self) -> None:
        """Test validate_scripts detects trigger without event key."""
        script = Script(
            trigger={"npc": "martin"},  # Missing 'event' key
            actions=[{"type": "test_action"}],
        )
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        assert "trigger missing required 'event' key" in str(cm.value)
        assert "test_script" in str(cm.value)

    def test_validate_scripts_condition_missing_check(self) -> None:
        """Test validate_scripts detects condition without check key."""
        script = Script(
            conditions=[{"value": "test"}],  # Missing 'check' key
            actions=[{"type": "test_action"}],
        )
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        assert "condition 0 missing required 'check' key" in str(cm.value)
        assert "test_script" in str(cm.value)

    def test_validate_scripts_action_missing_type(self) -> None:
        """Test validate_scripts detects action without type key."""
        script = Script(actions=[{"speaker": "martin"}])  # Missing 'type' key
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        assert "action 0 missing required 'type' key" in str(cm.value)
        assert "test_script" in str(cm.value)

    def test_validate_scripts_on_condition_fail_action_missing_type(self) -> None:
        """Test validate_scripts detects on_condition_fail action without type key."""
        script = Script(
            actions=[{"type": "test_action"}],
            on_condition_fail=[{"speaker": "martin"}],  # Missing 'type' key
        )
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        assert "on_condition_fail action 0 missing required 'type' key" in str(cm.value)
        assert "test_script" in str(cm.value)

    @patch("pedre.plugins.script.plugin.EventRegistry")
    @patch("pedre.plugins.script.plugin.ConditionRegistry")
    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_validate_scripts_multiple_errors(
        self,
        mock_action_registry: MagicMock,
        mock_condition_registry: MagicMock,
        mock_event_registry: MagicMock,
    ) -> None:
        """Test validate_scripts collects multiple errors."""
        mock_event_registry.is_registered.return_value = False
        mock_event_registry.get_all_types.return_value = []
        mock_condition_registry.is_registered.return_value = False
        mock_condition_registry.get_all_types.return_value = []
        mock_action_registry.is_registered.return_value = False
        mock_action_registry.get_all_types.return_value = []

        script = Script(
            trigger={"event": "bad_event"},
            conditions=[{"check": "bad_condition"}],
            actions=[{"type": "bad_action"}],
        )
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        error_msg = str(cm.value)
        assert "unknown event 'bad_event'" in error_msg
        assert "unknown condition 'bad_condition'" in error_msg
        assert "unknown action type 'bad_action'" in error_msg
        # Check that it reports 3 errors
        assert "3 script validation error(s)" in error_msg

    def test_validate_scripts_includes_parsing_errors(self) -> None:
        """Test validate_scripts includes errors from _validation_errors."""
        self.plugin._validation_errors = ["Script 'foo': unknown key 'bad_key'"]
        script = Script(actions=[{"type": "test_action"}])
        self.plugin.scripts = {"test_script": script}

        with patch("pedre.plugins.script.plugin.ActionRegistry") as mock_action_registry:
            mock_action_registry.is_registered.return_value = False
            mock_action_registry.get_all_types.return_value = []

            with pytest.raises(ScriptValidationError) as cm:
                self.plugin.validate_scripts()

        error_msg = str(cm.value)
        assert "unknown key 'bad_key'" in error_msg

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_validate_scripts_invalid_action_parameters(self, mock_action_registry: MagicMock) -> None:
        """Test validate_scripts detects invalid action parameters."""
        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = ["missing required 'text' field"]

        script = Script(actions=[{"type": "dialog"}])  # Missing text parameter
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        error_msg = str(cm.value)
        assert "missing required 'text' field" in error_msg
        assert "test_script" in error_msg
        assert "action 0 (dialog)" in error_msg

    @patch("pedre.plugins.script.plugin.ConditionRegistry")
    def test_validate_scripts_invalid_condition_parameters(self, mock_condition_registry: MagicMock) -> None:
        """Test validate_scripts detects invalid condition parameters."""
        mock_condition_registry.is_registered.return_value = True
        mock_condition_registry.validate.return_value = ["missing required 'npc' field"]

        script = Script(
            conditions=[{"check": "npc_interacted"}],  # Missing npc parameter
            actions=[{"type": "test"}],
        )
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        error_msg = str(cm.value)
        assert "missing required 'npc' field" in error_msg
        assert "test_script" in error_msg
        assert "condition 0 (npc_interacted)" in error_msg

    @patch("pedre.plugins.script.plugin.EventRegistry")
    def test_validate_scripts_unknown_trigger_filter_keys(self, mock_event_registry: MagicMock) -> None:
        """Test validate_scripts detects unknown trigger filter keys."""
        mock_event_registry.is_registered.return_value = True
        mock_event_registry.get_trigger_keys.return_value = frozenset({"npc", "dialog_level"})

        script = Script(
            trigger={"event": "npc_interacted", "name": "martin"},  # 'name' is invalid, should be 'npc'
            actions=[{"type": "test"}],
        )
        self.plugin.scripts = {"test_script": script}

        with pytest.raises(ScriptValidationError) as cm:
            self.plugin.validate_scripts()

        error_msg = str(cm.value)
        assert "unknown filter keys ['name']" in error_msg
        assert "valid keys: ['dialog_level', 'npc']" in error_msg
        assert "test_script" in error_msg

    @patch("pedre.plugins.script.plugin.EventRegistry")
    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_validate_scripts_skips_validation_when_no_validator(
        self, mock_action_registry: MagicMock, mock_event_registry: MagicMock
    ) -> None:
        """Test validate_scripts skips parameter validation when validator not available."""
        mock_event_registry.is_registered.return_value = True
        mock_event_registry.get_trigger_keys.return_value = None  # No trigger keys defined
        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []  # No validator defined

        script = Script(
            trigger={"event": "some_event", "random_key": "value"},  # Unknown key but no validation
            actions=[{"type": "some_action", "bad_param": "value"}],  # Bad param but no validator
        )
        self.plugin.scripts = {"test_script": script}

        # Should not raise because validators aren't defined (opt-in validation)
        self.plugin.validate_scripts()

    def test_parse_scripts_detects_unknown_keys(self) -> None:
        """Test _parse_scripts detects unknown top-level keys."""
        script_data = {
            "test_script": {
                "trigger": {"event": "test_event"},
                "actions": [{"type": "test_action"}],
                "unknown_key": "value",
                "another_bad_key": 123,
            }
        }

        self.plugin._parse_scripts(script_data)

        assert len(self.plugin._validation_errors) == 1
        assert "test_script" in self.plugin._validation_errors[0]
        assert "unknown_key" in self.plugin._validation_errors[0]
        assert "another_bad_key" in self.plugin._validation_errors[0]

    @patch("pedre.plugins.script.plugin.asset_path")
    @patch("pedre.plugins.script.plugin.EventRegistry")
    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_load_all_scripts_validates(
        self,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_asset_path: MagicMock,
    ) -> None:
        """Test _load_all_scripts calls validate_scripts."""
        # Setup invalid script
        script_data = {
            "test_script": {
                "trigger": {"event": "unknown_event"},
                "actions": [{"type": "test_action"}],
            }
        }

        mock_file = MagicMock()
        mock_file.name = "test_scripts.json"
        m_open = mock_open(read_data=json.dumps(script_data))
        mock_file.open = m_open

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = [mock_file]
        mock_asset_path.return_value = "/fake/scripts"

        # Mock registries - event is invalid, action is valid
        mock_event_registry.is_registered.return_value = False
        mock_event_registry.get_all_types.return_value = []
        mock_action_registry.is_registered.return_value = True

        with patch("pedre.plugins.script.plugin.Path") as mock_path_class:
            mock_path_class.return_value = mock_path

            with pytest.raises(ScriptValidationError) as cm:
                self.plugin._load_all_scripts()

        assert "unknown event 'unknown_event'" in str(cm.value)


if __name__ == "__main__":
    unittest.main()
