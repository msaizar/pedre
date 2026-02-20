"""Unit tests for ScriptPlugin in src/pedre/plugins/script/plugin.py."""

import json
import unittest
from unittest.mock import MagicMock, mock_open, patch

from pedre.actions.registry import ActionParseError
from pedre.conditions.registry import ConditionParseError
from pedre.plugins.script.base import Script, ScriptTrigger
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
        self.plugin.scripts = {
            "test": Script(
                trigger=None,
                conditions=[],
                scene=None,
                run_once=False,
                actions=[],
                on_condition_fail=[],
            )
        }
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
            self.plugin.scripts = {
                "old_script": Script(
                    trigger=None,
                    conditions=[],
                    scene=None,
                    run_once=False,
                    actions=[],
                    on_condition_fail=[],
                )
            }
            self.plugin.active_sequences = [("old", MagicMock())]
            self.plugin._subscribed_events = {"old_event"}

            self.plugin.reset()

            # Verify state was cleared
            assert self.plugin.active_sequences == []
            assert self.plugin._subscribed_events == set()
            self.mock_event_bus.unregister_all.assert_called()

    def test_get_scripts(self) -> None:
        """Test getting scripts dictionary."""
        test_script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
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
        completed_script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        completed_script.completed = True

        run_once_script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=True,
            actions=[],
            on_condition_fail=[],
        )
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
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        self.plugin.scripts = {"test_script": script}

        state = {"completed_scripts": ["test_script"]}

        self.plugin.restore_save_state(state)

        assert self.plugin.scripts["test_script"].completed is True

    def test_restore_save_state_run_once_scripts(self) -> None:
        """Test restoring run-once scripts."""
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=True,
            actions=[],
            on_condition_fail=[],
        )
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

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_restore_save_state_active_scripts(self, mock_sequence_class: MagicMock) -> None:
        """Test restoring active scripts."""
        mock_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )
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
        mock_action_1 = MagicMock()
        mock_action_1.name = "move_npc"
        mock_action_2 = MagicMock()
        mock_action_2.name = "wait_for_movement"
        mock_action_3 = MagicMock()
        mock_action_3.name = "dialog"

        actions = [
            mock_action_1,
            mock_action_2,
            mock_action_3,
        ]

        # If saved at wait action, should resume at preceding non-wait
        resume_index = self.plugin._calculate_resume_index(actions, 1)
        assert resume_index == 0

    def test_calculate_resume_index_non_wait_action(self) -> None:
        """Test resume index stays at non-wait actions."""
        mock_action_1 = MagicMock()
        mock_action_1.name = "move_npc"
        mock_action_2 = MagicMock()
        mock_action_2.name = "dialog"
        mock_action_3 = MagicMock()
        mock_action_3.name = "wait_for_dialog"

        actions = [
            mock_action_1,
            mock_action_2,
            mock_action_3,
        ]

        resume_index = self.plugin._calculate_resume_index(actions, 1)
        assert resume_index == 1

    def test_calculate_resume_index_at_start(self) -> None:
        """Test resume index at start doesn't go negative."""
        mock_action_1 = MagicMock()
        mock_action_1.name = "wait_for_dialog"
        mock_action_2 = MagicMock()
        mock_action_2.name = "dialog"

        actions = [
            mock_action_1,
            mock_action_2,
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
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
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
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
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
        mock_condition = MagicMock()
        script = Script(
            trigger=None,
            conditions=[mock_condition],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._pending_script_checks = ["test_script"]

        with (
            patch.object(self.plugin, "_check_conditions", return_value=True),
            patch.object(self.plugin, "_execute_script"),
        ):
            self.plugin.update(0.016)

            assert len(self.plugin._pending_script_checks) == 0

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    @patch("pedre.plugins.script.plugin.ConditionRegistry")
    def test_parse_scripts(self, mock_condition_registry: MagicMock, mock_action_registry: MagicMock) -> None:
        """Test parsing script data into Script objects."""
        # Mock condition and action creation
        mock_condition = MagicMock()
        mock_action = MagicMock()
        mock_fail_action = MagicMock()

        mock_condition_registry.create.return_value = mock_condition
        mock_action_registry.create.side_effect = [mock_action, mock_fail_action]

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
        assert script.trigger == ScriptTrigger(event_name="test_event", filters={})
        assert script.conditions == [mock_condition]
        assert script.scene == "test_scene"
        assert script.run_once is True
        assert script.actions == [mock_action]
        assert script.on_condition_fail == [mock_fail_action]

    def test_check_conditions_all_pass(self) -> None:
        """Test check conditions when all pass."""
        self.plugin.setup(self.mock_context)

        mock_condition_1 = MagicMock()
        mock_condition_1.check.return_value = True
        mock_condition_2 = MagicMock()
        mock_condition_2.check.return_value = True

        conditions = [
            mock_condition_1,
            mock_condition_2,
        ]

        result = self.plugin._check_conditions(conditions)

        assert result is True
        assert mock_condition_1.check.call_count == 1
        assert mock_condition_2.check.call_count == 1

    def test_check_conditions_one_fails(self) -> None:
        """Test check conditions when one fails."""
        self.plugin.setup(self.mock_context)

        mock_condition_1 = MagicMock()
        mock_condition_1.check.return_value = True
        mock_condition_2 = MagicMock()
        mock_condition_2.check.return_value = False

        conditions = [
            mock_condition_1,
            mock_condition_2,
        ]

        result = self.plugin._check_conditions(conditions)

        assert result is False

    def test_check_conditions_no_context(self) -> None:
        """Test check conditions without context."""
        self.plugin.context = None

        mock_condition = MagicMock()
        result = self.plugin._check_conditions([mock_condition])

        assert result is False

    def test_check_single_condition_no_context(self) -> None:
        """Test check single condition without context."""
        self.plugin.context = None

        mock_condition = MagicMock()
        result = self.plugin._check_single_condition(mock_condition)

        assert result is False

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_execute_script(self, mock_sequence_class: MagicMock) -> None:
        """Test executing a script."""
        self.plugin.setup(self.mock_context)

        mock_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )

        self.plugin._execute_script("test_script", script)

        assert len(self.plugin.active_sequences) == 1
        assert self.plugin.active_sequences[0][0] == "test_script"

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_execute_actions_no_context(self, mock_sequence_class: MagicMock) -> None:
        """Test execute actions without context."""
        self.plugin.context = None

        mock_action = MagicMock()
        self.plugin._execute_actions("test", [mock_action])

        # Should not crash and not create sequence
        assert len(self.plugin.active_sequences) == 0
        mock_sequence_class.assert_not_called()

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_execute_actions_with_actions(self, mock_sequence_class: MagicMock) -> None:
        """Test execute actions with valid actions."""
        self.plugin.setup(self.mock_context)

        mock_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        self.plugin._execute_actions("test", [mock_action])

        assert len(self.plugin.active_sequences) == 1
        assert self.plugin.active_sequences[0][0] == "test"
        assert self.plugin.active_sequences[0][1] == mock_sequence

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_execute_actions_empty_list(self, mock_sequence_class: MagicMock) -> None:
        """Test execute actions with empty list."""
        self.plugin.setup(self.mock_context)

        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        self.plugin._execute_actions("test", [])

        # Empty list should still create a sequence
        assert len(self.plugin.active_sequences) == 1
        mock_sequence_class.assert_called_once_with([])

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

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_process_pending_checks_executes_matching_scripts(self, mock_sequence_class: MagicMock) -> None:
        """Test process pending checks executes scripts with passing conditions."""
        mock_condition = MagicMock()
        mock_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        script = Script(
            trigger=None,
            conditions=[mock_condition],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._pending_script_checks = ["test_script"]

        with patch.object(self.plugin, "_check_conditions", return_value=True):
            self.plugin._process_pending_checks()

            assert len(self.plugin._pending_script_checks) == 0
            assert len(self.plugin.active_sequences) == 1

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_process_pending_checks_marks_run_once(self, mock_sequence_class: MagicMock) -> None:
        """Test process pending checks marks run_once scripts."""
        mock_condition = MagicMock()
        mock_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        script = Script(
            trigger=None,
            conditions=[mock_condition],
            scene=None,
            run_once=True,
            actions=[mock_action],
            on_condition_fail=[],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

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
        mock_condition = MagicMock()
        mock_action = MagicMock()
        script = Script(
            trigger=None,
            conditions=[mock_condition],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._pending_script_checks = ["test_script"]

        with patch.object(self.plugin, "_check_conditions", return_value=False):
            self.plugin._process_pending_checks()

            # Should not execute script
            assert len(self.plugin.active_sequences) == 0

    def test_trigger_matches_event_correct_match(self) -> None:
        """Test trigger matches event correctly."""
        trigger = ScriptTrigger(event_name="test_event", filters={"npc": "martin"})
        event_data = {"npc": "martin"}

        result = self.plugin._trigger_matches_event(trigger, "test_event", event_data)

        assert result is True

    def test_trigger_matches_event_wrong_event_type(self) -> None:
        """Test trigger doesn't match wrong event type."""
        trigger = ScriptTrigger(event_name="test_event", filters={})

        result = self.plugin._trigger_matches_event(trigger, "other_event", {})

        assert result is False

    def test_trigger_matches_event_missing_filter(self) -> None:
        """Test trigger doesn't match when event data missing filter."""
        trigger = ScriptTrigger(event_name="test_event", filters={"npc": "martin"})
        event_data = {"npc": "john"}  # Different NPC

        result = self.plugin._trigger_matches_event(trigger, "test_event", event_data)

        assert result is False

    def test_trigger_matches_event_no_filters(self) -> None:
        """Test trigger matches event with no additional filters."""
        trigger = ScriptTrigger(event_name="test_event", filters={})
        event_data = {"npc": "martin", "other": "data"}

        result = self.plugin._trigger_matches_event(trigger, "test_event", event_data)

        assert result is True

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_handle_event_trigger_executes_matching_script(self, mock_sequence_class: MagicMock) -> None:
        """Test handle event trigger executes matching scripts."""
        mock_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        script = Script(
            trigger=ScriptTrigger(event_name="test_event", filters={}),
            conditions=[],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._handle_event_trigger("test_event", {})

        assert len(self.plugin.active_sequences) == 1

    def test_handle_event_trigger_skips_wrong_scene(self) -> None:
        """Test handle event trigger skips scripts in wrong scene."""
        mock_action = MagicMock()
        script = Script(
            trigger=ScriptTrigger(event_name="test_event", filters={}),
            conditions=[],
            scene="other_scene",
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.mock_scene_plugin.get_current_scene.return_value = "current_scene"

        self.plugin._handle_event_trigger("test_event", {})

        assert len(self.plugin.active_sequences) == 0

    def test_handle_event_trigger_skips_already_run(self) -> None:
        """Test handle event trigger skips run_once scripts that ran."""
        mock_action = MagicMock()
        script = Script(
            trigger=ScriptTrigger(event_name="test_event", filters={}),
            conditions=[],
            scene=None,
            run_once=True,
            actions=[mock_action],
            on_condition_fail=[],
        )
        script.has_run = True
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._handle_event_trigger("test_event", {})

        assert len(self.plugin.active_sequences) == 0

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_handle_event_trigger_marks_run_once(self, mock_sequence_class: MagicMock) -> None:
        """Test handle event trigger marks run_once scripts."""
        mock_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        script = Script(
            trigger=ScriptTrigger(event_name="test_event", filters={}),
            conditions=[],
            scene=None,
            run_once=True,
            actions=[mock_action],
            on_condition_fail=[],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._handle_event_trigger("test_event", {})

        assert script.has_run is True

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_handle_event_trigger_executes_on_condition_fail(self, mock_sequence_class: MagicMock) -> None:
        """Test handle event trigger executes on_condition_fail actions."""
        mock_condition = MagicMock()
        mock_success_action = MagicMock()
        mock_fail_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        script = Script(
            trigger=ScriptTrigger(event_name="test_event", filters={}),
            conditions=[mock_condition],
            scene=None,
            run_once=False,
            actions=[mock_success_action],
            on_condition_fail=[mock_fail_action],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        with patch.object(self.plugin, "_check_conditions", return_value=False):
            self.plugin._handle_event_trigger("test_event", {})

            # Should execute fail sequence, not main sequence
            assert len(self.plugin.active_sequences) == 1
            assert self.plugin.active_sequences[0][0] == "test_script_fail"

    def test_handle_event_trigger_no_trigger(self) -> None:
        """Test handle event trigger skips scripts with no trigger."""
        mock_action = MagicMock()
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )
        self.plugin.scripts = {"test_script": script}
        self.plugin.setup(self.mock_context)

        self.plugin._handle_event_trigger("test_event", {})

        assert len(self.plugin.active_sequences) == 0

    def test_handle_event_trigger_mismatched_trigger(self) -> None:
        """Test handle event trigger skips scripts with mismatched triggers."""
        mock_action = MagicMock()
        script = Script(
            trigger=ScriptTrigger(event_name="other_event", filters={"npc": "bob"}),
            conditions=[],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
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

        script1 = Script(
            trigger=ScriptTrigger(event_name="event1", filters={}),
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        script2 = Script(
            trigger=ScriptTrigger(event_name="event2", filters={}),
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        script3 = Script(
            trigger=ScriptTrigger(event_name="event1", filters={}),
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )  # Duplicate

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
        script = Script(
            trigger=ScriptTrigger(event_name="test_event", filters={}),
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
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

        script = Script(
            trigger=ScriptTrigger(event_name="unknown_event", filters={}),
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        self.plugin.scripts = {"script": script}

        self.plugin.setup(self.mock_context)

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            self.plugin._register_event_handlers()

            mock_logger.warning.assert_called_once()

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
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
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
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
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

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_restore_save_state_no_valid_actions(self, mock_sequence_class: MagicMock) -> None:
        """Test restoring script when all actions fail to parse."""
        mock_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )
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

        # Should add to active sequences
        assert len(self.plugin.active_sequences) == 1

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

    def test_handle_event_trigger_conditions_fail_no_fail_actions(self) -> None:
        """Test handle event trigger logs when conditions fail with no fail actions."""
        mock_condition = MagicMock()
        mock_success_action = MagicMock()
        script = Script(
            trigger=ScriptTrigger(event_name="test_event", filters={}),
            conditions=[mock_condition],
            scene=None,
            run_once=False,
            actions=[mock_success_action],
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

    def test_on_generic_event_no_event_name(self) -> None:
        """Test generic event handler with no event name."""
        mock_event = MagicMock()
        mock_event.name = None

        self.plugin.setup(self.mock_context)
        self.plugin._on_generic_event(mock_event)

        # Should exit early, no script trigger handling
        # No assertion needed, just verify no crash

    def test_on_generic_event_with_get_script_data(self) -> None:
        """Test generic event handler using get_script_data protocol."""
        mock_event = MagicMock()
        mock_event.name = "test_event"
        mock_event.get_script_data.return_value = {"key": "value"}

        self.plugin.setup(self.mock_context)

        with patch.object(self.plugin, "_handle_event_trigger") as mock_handle:
            self.plugin._on_generic_event(mock_event)

            mock_handle.assert_called_once_with("test_event", {"key": "value"})

    @patch("pedre.plugins.script.plugin.ConditionRegistry")
    def test_parse_scripts_condition_parse_error(self, mock_condition_registry: MagicMock) -> None:
        """Test parsing script with condition parse error."""
        mock_condition_registry.create.side_effect = ConditionParseError("Invalid condition")

        script_data = {
            "test_script": {
                "conditions": [{"check": "invalid"}],
                "actions": [],
            }
        }

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            self.plugin._parse_scripts(script_data)

            # Should log warning about failed condition parse
            mock_logger.warning.assert_called()

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_parse_scripts_action_parse_error(self, mock_action_registry: MagicMock) -> None:
        """Test parsing script with action parse error."""
        mock_action_registry.create.side_effect = ActionParseError("Invalid action")

        script_data = {
            "test_script": {
                "actions": [{"type": "invalid"}],
            }
        }

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            self.plugin._parse_scripts(script_data)

            # Should log warning about failed action parse
            mock_logger.warning.assert_called()

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_parse_scripts_fail_action_parse_error(self, mock_action_registry: MagicMock) -> None:
        """Test parsing script with on_condition_fail action parse error."""
        mock_action_registry.create.side_effect = ActionParseError("Invalid fail action")

        script_data = {
            "test_script": {
                "actions": [],
                "on_condition_fail": [{"type": "invalid"}],
            }
        }

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            self.plugin._parse_scripts(script_data)

            # Should log warning about failed on_condition_fail action parse
            mock_logger.warning.assert_called()

    def test_parse_scripts_unknown_keys(self) -> None:
        """Test parsing script with unknown keys."""
        script_data = {
            "test_script": {
                "actions": [],
                "unknown_key": "value",
                "another_unknown": 123,
            }
        }

        self.plugin._parse_scripts(script_data)

        # Should add validation error
        assert len(self.plugin._validation_errors) > 0
        assert "unknown keys" in self.plugin._validation_errors[0]

    def test_parse_scripts_no_trigger_event(self) -> None:
        """Test parsing script with trigger but no event field."""
        script_data = {
            "test_script": {
                "trigger": {"filter": "value"},  # Missing 'event'
                "actions": [],
            }
        }

        self.plugin._parse_scripts(script_data)

        # Script should be created with no trigger
        assert "test_script" in self.plugin.scripts
        assert self.plugin.scripts["test_script"].trigger is None

    def test_parse_scripts_trigger_with_filters(self) -> None:
        """Test parsing script with trigger including filters."""
        script_data = {
            "test_script": {
                "trigger": {"event": "test_event", "npc": "martin", "level": 5},
                "actions": [],
            }
        }

        self.plugin._parse_scripts(script_data)

        # Script trigger should have event and filters
        assert "test_script" in self.plugin.scripts
        script = self.plugin.scripts["test_script"]
        assert script.trigger is not None
        assert script.trigger.event_name == "test_event"
        assert script.trigger.filters == {"npc": "martin", "level": 5}

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_restore_save_state_actions_list_becomes_empty(self, mock_sequence_class: MagicMock) -> None:
        """Test restoring script when list() conversion results in empty list."""
        # Create a mock iterator that appears to have items but list() returns empty
        # This tests the edge case where action_data_list is truthy but list(action_data_list) is empty
        mock_action_data = MagicMock()
        mock_action_data.__bool__.return_value = True  # Passes the first check
        mock_action_data.__iter__.return_value = iter([])  # But list() gives empty

        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=mock_action_data,
            on_condition_fail=[],
        )
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

        # Should not add to active sequences due to empty list after conversion
        assert len(self.plugin.active_sequences) == 0
        mock_sequence_class.assert_not_called()
