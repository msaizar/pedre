"""Unit tests for ScriptPlugin in src/pedre/plugins/script/plugin.py."""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from pedre.actions.registry import ActionParseError
from pedre.conditions.registry import ConditionParseError
from pedre.plugins.script.base import Script, ScriptTrigger
from pedre.plugins.script.events import ScriptCompleteEvent
from pedre.plugins.script.plugin import ScriptPlugin

ScriptPluginCtx = tuple[ScriptPlugin, MagicMock]


@pytest.fixture
def script_plugin_ctx() -> ScriptPluginCtx:
    """Create a fresh ScriptPlugin with a mock context."""
    plugin = ScriptPlugin()
    mock_context = MagicMock()
    mock_context.event_bus = MagicMock()
    mock_context.scene_plugin = MagicMock()
    mock_context.scene_plugin.get_current_scene.return_value = "test_scene"
    return plugin, mock_context


class TestScriptPlugin:
    """Test Suite for ScriptPlugin."""

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
    def test_setup_no_scripts_dir(self, mock_asset_path: MagicMock, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test setup when scripts directory doesn't exist."""
        plugin, mock_context = script_plugin_ctx
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_asset_path.return_value = "/fake/scripts"

        with (
            patch("pedre.plugins.script.plugin.Path") as mock_path_class,
            patch("pedre.plugins.script.plugin.logger") as mock_logger,
        ):
            mock_path_class.return_value = mock_path

            plugin.setup(mock_context)

            assert plugin.context == mock_context
            mock_logger.warning.assert_called_once()

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_setup_no_script_files(self, mock_asset_path: MagicMock, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test setup when no script files exist."""
        plugin, mock_context = script_plugin_ctx
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = []
        mock_asset_path.return_value = "/fake/scripts"

        with (
            patch("pedre.plugins.script.plugin.Path") as mock_path_class,
            patch("pedre.plugins.script.plugin.logger") as mock_logger,
        ):
            mock_path_class.return_value = mock_path

            plugin.setup(mock_context)

            mock_logger.info.assert_any_call("No script files found in %s", mock_path)

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_setup_loads_scripts(self, mock_asset_path: MagicMock, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test setup successfully loads scripts from file."""
        plugin, mock_context = script_plugin_ctx

        script_data = {
            "test_script": {
                "trigger": {"event": "test_event"},
                "conditions": [],
                "actions": [{"name": "test_action"}],
                "run_once": True,
                "scene": "test_scene",
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

        with (
            patch("pedre.plugins.script.plugin.Path") as mock_path_class,
            patch("pedre.plugins.script.plugin.EventRegistry") as mock_event_registry,
            patch("pedre.plugins.script.plugin.ActionRegistry") as mock_action_registry,
        ):
            mock_path_class.return_value = mock_path
            mock_event_class = MagicMock()
            mock_event_registry.get.return_value = mock_event_class
            mock_event_registry.is_registered.return_value = True
            mock_event_registry.get_trigger_keys.return_value = None
            mock_action_registry.is_registered.return_value = True
            mock_action_registry.validate.return_value = []

            plugin.setup(mock_context)

            assert "test_script" in plugin.scripts
            assert plugin.scripts["test_script"].run_once is True
            assert plugin.scripts["test_script"].scene == "test_scene"

            mock_context.event_bus.subscribe.assert_called_once()

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_cleanup(self, mock_asset_path: MagicMock, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test cleanup clears all resources."""
        plugin, mock_context = script_plugin_ctx
        plugin.scripts = {
            "test": Script(
                trigger=None,
                conditions=[],
                scene=None,
                run_once=False,
                actions=[],
                on_condition_fail=[],
            )
        }
        plugin.active_sequences = [("test", MagicMock())]
        plugin._subscribed_events = {"test_event"}

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_asset_path.return_value = "/fake/scripts"
        with patch("pedre.plugins.script.plugin.Path") as mock_path_class:
            mock_path_class.return_value = mock_path
            plugin.setup(mock_context)

        mock_event_bus = mock_context.event_bus
        plugin.cleanup()

        mock_event_bus.unregister_all.assert_called_once_with(plugin)
        assert plugin.scripts == {}
        assert plugin.active_sequences == []
        assert plugin._subscribed_events == set()

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_reset_reloads_scripts(self, mock_asset_path: MagicMock, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test reset clears state and reloads scripts."""
        plugin, mock_context = script_plugin_ctx
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = []
        mock_asset_path.return_value = "/fake/scripts"

        with patch("pedre.plugins.script.plugin.Path") as mock_path_class:
            mock_path_class.return_value = mock_path
            plugin.setup(mock_context)
            plugin.scripts = {
                "old_script": Script(
                    trigger=None,
                    conditions=[],
                    scene=None,
                    run_once=False,
                    actions=[],
                    on_condition_fail=[],
                )
            }
            plugin.active_sequences = [("old", MagicMock())]
            plugin._subscribed_events = {"old_event"}

            plugin.reset()

            assert plugin.active_sequences == []
            assert plugin._subscribed_events == set()
            mock_context.event_bus.unregister_all.assert_called()

    def test_get_scripts(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test getting scripts dictionary."""
        plugin, _ = script_plugin_ctx
        test_script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        plugin.scripts = {"test": test_script}

        result = plugin.get_scripts()

        assert result == {"test": test_script}

    def test_get_save_state_empty(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test get save state with no scripts."""
        plugin, _ = script_plugin_ctx
        state = plugin.get_save_state()

        assert state["completed_scripts"] == []
        assert state["run_once_scripts"] == []
        assert state["active_scripts"] == []

    def test_get_save_state_with_scripts(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test get save state with completed and run-once scripts."""
        plugin, _ = script_plugin_ctx
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

        plugin.scripts = {
            "completed": completed_script,
            "run_once": run_once_script,
        }

        state = plugin.get_save_state()

        assert "completed" in state["completed_scripts"]
        assert "run_once" in state["run_once_scripts"]

    def test_get_save_state_with_active_sequences(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test get save state with active sequences."""
        plugin, _ = script_plugin_ctx
        mock_sequence = MagicMock()
        mock_sequence.current_index = 5

        plugin.active_sequences = [("active_script", mock_sequence)]

        state = plugin.get_save_state()

        assert len(state["active_scripts"]) == 1
        assert state["active_scripts"][0]["script_name"] == "active_script"
        assert state["active_scripts"][0]["current_index"] == 5
        assert state["active_scripts"][0]["is_fail_sequence"] is False

    def test_get_save_state_with_fail_sequence(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test get save state with fail sequence."""
        plugin, _ = script_plugin_ctx
        mock_sequence = MagicMock()
        mock_sequence.current_index = 3

        plugin.active_sequences = [("test_script_fail", mock_sequence)]

        state = plugin.get_save_state()

        assert len(state["active_scripts"]) == 1
        assert state["active_scripts"][0]["script_name"] == "test_script"
        assert state["active_scripts"][0]["is_fail_sequence"] is True

    def test_restore_save_state_completed_scripts(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test restoring completed scripts."""
        plugin, _ = script_plugin_ctx
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}

        plugin.restore_save_state({"completed_scripts": ["test_script"]})

        assert plugin.scripts["test_script"].completed is True

    def test_restore_save_state_run_once_scripts(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test restoring run-once scripts."""
        plugin, _ = script_plugin_ctx
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=True,
            actions=[],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}

        plugin.restore_save_state({"run_once_scripts": ["test_script"]})

        assert plugin.scripts["test_script"].has_run is True

    def test_restore_save_state_completed_script_not_in_registry(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test restoring completed script that's not in registry."""
        plugin, _ = script_plugin_ctx
        # Should not crash, just skip the missing script
        plugin.restore_save_state({"completed_scripts": ["nonexistent_script"]})

    def test_restore_save_state_run_once_script_not_in_registry(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test restoring run-once script that's not in registry."""
        plugin, _ = script_plugin_ctx
        # Should not crash, just skip the missing script
        plugin.restore_save_state({"run_once_scripts": ["nonexistent_script"]})

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_restore_save_state_active_scripts(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test restoring active scripts."""
        plugin, _ = script_plugin_ctx
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
        plugin.scripts = {"test_script": script}

        state = {
            "active_scripts": [
                {
                    "script_name": "test_script",
                    "current_index": 0,
                    "is_fail_sequence": False,
                }
            ]
        }

        plugin.restore_save_state(state)

        assert len(plugin.active_sequences) == 1
        assert plugin.active_sequences[0][0] == "test_script"

    def test_restore_save_state_clears_existing_sequences(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test restoring state clears existing active sequences."""
        plugin, _ = script_plugin_ctx
        plugin.active_sequences = [("old_script", MagicMock())]

        plugin.restore_save_state({"active_scripts": []})

        assert len(plugin.active_sequences) == 0

    def test_calculate_resume_index_wait_action(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test resume index backs up past wait actions."""
        plugin, _ = script_plugin_ctx
        mock_action_1 = MagicMock()
        mock_action_1.name = "move_npc"
        mock_action_2 = MagicMock()
        mock_action_2.name = "wait_for_movement"
        mock_action_3 = MagicMock()
        mock_action_3.name = "dialog"

        actions = [mock_action_1, mock_action_2, mock_action_3]

        resume_index = plugin._calculate_resume_index(actions, 1)
        assert resume_index == 0

    def test_calculate_resume_index_non_wait_action(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test resume index stays at non-wait actions."""
        plugin, _ = script_plugin_ctx
        mock_action_1 = MagicMock()
        mock_action_1.name = "move_npc"
        mock_action_2 = MagicMock()
        mock_action_2.name = "dialog"
        mock_action_3 = MagicMock()
        mock_action_3.name = "wait_for_dialog"

        actions = [mock_action_1, mock_action_2, mock_action_3]

        resume_index = plugin._calculate_resume_index(actions, 1)
        assert resume_index == 1

    def test_calculate_resume_index_at_start(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test resume index at start doesn't go negative."""
        plugin, _ = script_plugin_ctx
        mock_action_1 = MagicMock()
        mock_action_1.name = "wait_for_dialog"
        mock_action_2 = MagicMock()
        mock_action_2.name = "dialog"

        actions = [mock_action_1, mock_action_2]

        resume_index = plugin._calculate_resume_index(actions, 0)
        assert resume_index == 0

    def test_update_no_context(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test update does nothing without context."""
        plugin, _ = script_plugin_ctx
        plugin.context = None
        plugin.update(0.016)
        # Should not crash

    def test_update_executes_sequences(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test update executes active sequences."""
        plugin, mock_context = script_plugin_ctx
        plugin.setup(mock_context)

        mock_sequence = MagicMock()
        mock_sequence.execute.return_value = False  # Not completed

        plugin.active_sequences = [("test_script", mock_sequence)]

        plugin.update(0.016)

        mock_sequence.execute.assert_called_once_with(mock_context)
        assert len(plugin.active_sequences) == 1

    def test_update_removes_completed_sequences(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test update removes completed sequences."""
        plugin, mock_context = script_plugin_ctx
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        mock_sequence = MagicMock()
        mock_sequence.execute.return_value = True  # Completed

        plugin.active_sequences = [("test_script", mock_sequence)]

        plugin.update(0.016)

        assert len(plugin.active_sequences) == 0
        assert script.completed is True
        mock_context.event_bus.publish.assert_called_once()

    def test_update_completed_sequence_not_in_scripts(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test update handles completed sequence not in scripts registry."""
        plugin, mock_context = script_plugin_ctx
        plugin.setup(mock_context)

        mock_sequence = MagicMock()
        mock_sequence.execute.return_value = True  # Completed

        plugin.active_sequences = [("nonexistent_script", mock_sequence)]

        plugin.update(0.016)

        assert len(plugin.active_sequences) == 0
        mock_context.event_bus.publish.assert_called_once()

    def test_update_publishes_completion_event(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test update publishes ScriptCompleteEvent."""
        plugin, mock_context = script_plugin_ctx
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        mock_sequence = MagicMock()
        mock_sequence.execute.return_value = True

        plugin.active_sequences = [("test_script", mock_sequence)]

        plugin.update(0.016)

        assert mock_context.event_bus.publish.called
        published_event = mock_context.event_bus.publish.call_args[0][0]
        assert isinstance(published_event, ScriptCompleteEvent)
        assert published_event.script_name == "test_script"

    def test_update_processes_pending_checks(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test update processes pending script checks."""
        plugin, mock_context = script_plugin_ctx
        mock_condition = MagicMock()
        script = Script(
            trigger=None,
            conditions=[mock_condition],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        plugin._pending_script_checks = ["test_script"]

        with (
            patch.object(plugin, "_check_conditions", return_value=True),
            patch.object(plugin, "_execute_script"),
        ):
            plugin.update(0.016)

            assert len(plugin._pending_script_checks) == 0

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    @patch("pedre.plugins.script.plugin.ConditionRegistry")
    def test_parse_scripts(
        self,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        script_plugin_ctx: ScriptPluginCtx,
    ) -> None:
        """Test parsing script data into Script objects."""
        plugin, _ = script_plugin_ctx
        mock_condition = MagicMock()
        mock_action = MagicMock()
        mock_fail_action = MagicMock()

        mock_condition_registry.create.return_value = mock_condition
        mock_action_registry.create.side_effect = [mock_action, mock_fail_action]

        script_data = {
            "test_script": {
                "trigger": {"event": "test_event"},
                "conditions": [{"name": "test"}],
                "scene": "test_scene",
                "run_once": True,
                "actions": [{"name": "action1"}],
                "on_condition_fail": [{"name": "fail_action"}],
            }
        }

        plugin._parse_scripts(script_data)

        assert "test_script" in plugin.scripts
        script = plugin.scripts["test_script"]
        assert script.trigger == ScriptTrigger(event_name="test_event", filters={})
        assert script.conditions == [mock_condition]
        assert script.scene == "test_scene"
        assert script.run_once is True
        assert script.actions == [mock_action]
        assert script.on_condition_fail == [mock_fail_action]

    def test_check_conditions_all_pass(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test check conditions when all pass."""
        plugin, mock_context = script_plugin_ctx
        plugin.setup(mock_context)

        mock_condition_1 = MagicMock()
        mock_condition_1.check.return_value = True
        mock_condition_2 = MagicMock()
        mock_condition_2.check.return_value = True

        result = plugin._check_conditions([mock_condition_1, mock_condition_2])

        assert result is True
        assert mock_condition_1.check.call_count == 1
        assert mock_condition_2.check.call_count == 1

    def test_check_conditions_one_fails(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test check conditions when one fails."""
        plugin, mock_context = script_plugin_ctx
        plugin.setup(mock_context)

        mock_condition_1 = MagicMock()
        mock_condition_1.check.return_value = True
        mock_condition_2 = MagicMock()
        mock_condition_2.check.return_value = False

        result = plugin._check_conditions([mock_condition_1, mock_condition_2])

        assert result is False

    def test_check_conditions_no_context(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test check conditions without context."""
        plugin, _ = script_plugin_ctx
        plugin.context = None

        mock_condition = MagicMock()
        result = plugin._check_conditions([mock_condition])

        assert result is False

    def test_check_single_condition_no_context(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test check single condition without context."""
        plugin, _ = script_plugin_ctx
        plugin.context = None

        mock_condition = MagicMock()
        result = plugin._check_single_condition(mock_condition)

        assert result is False

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_execute_script(self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test executing a script."""
        plugin, mock_context = script_plugin_ctx
        plugin.setup(mock_context)

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

        plugin._execute_script("test_script", script)

        assert len(plugin.active_sequences) == 1
        assert plugin.active_sequences[0][0] == "test_script"

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_execute_actions_no_context(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test execute actions without context."""
        plugin, _ = script_plugin_ctx
        plugin.context = None

        mock_action = MagicMock()
        plugin._execute_actions("test", [mock_action])

        assert len(plugin.active_sequences) == 0
        mock_sequence_class.assert_not_called()

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_execute_actions_with_actions(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test execute actions with valid actions."""
        plugin, mock_context = script_plugin_ctx
        plugin.setup(mock_context)

        mock_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        plugin._execute_actions("test", [mock_action])

        assert len(plugin.active_sequences) == 1
        assert plugin.active_sequences[0][0] == "test"
        assert plugin.active_sequences[0][1] == mock_sequence

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_execute_actions_empty_list(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test execute actions with empty list."""
        plugin, mock_context = script_plugin_ctx
        plugin.setup(mock_context)

        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        plugin._execute_actions("test", [])

        # Empty list should still create a sequence
        assert len(plugin.active_sequences) == 1
        mock_sequence_class.assert_called_once_with([])

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_run_actions_delegates_to_execute_actions(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test run_actions queues the action list as an active sequence."""
        plugin, mock_context = script_plugin_ctx
        plugin.setup(mock_context)

        mock_action = MagicMock()
        mock_sequence = MagicMock()
        mock_sequence_class.return_value = mock_sequence

        plugin.run_actions("my_sequence", [mock_action])

        assert len(plugin.active_sequences) == 1
        assert plugin.active_sequences[0][0] == "my_sequence"
        assert plugin.active_sequences[0][1] == mock_sequence
        mock_sequence_class.assert_called_once_with([mock_action])

    def test_process_pending_checks_no_context(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test process pending checks without context."""
        plugin, _ = script_plugin_ctx
        plugin.context = None
        plugin._pending_script_checks = ["test"]

        plugin._process_pending_checks()

        # Should not crash, checks should remain
        assert plugin._pending_script_checks == ["test"]

    def test_process_pending_checks_empty_list(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test process pending checks with empty list."""
        plugin, mock_context = script_plugin_ctx
        plugin.setup(mock_context)
        plugin._pending_script_checks = []

        plugin._process_pending_checks()
        # Should not crash

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_process_pending_checks_executes_matching_scripts(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test process pending checks executes scripts with passing conditions."""
        plugin, mock_context = script_plugin_ctx
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
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        plugin._pending_script_checks = ["test_script"]

        with patch.object(plugin, "_check_conditions", return_value=True):
            plugin._process_pending_checks()

            assert len(plugin._pending_script_checks) == 0
            assert len(plugin.active_sequences) == 1

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_process_pending_checks_marks_run_once(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test process pending checks marks run_once scripts."""
        plugin, mock_context = script_plugin_ctx
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
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        plugin._pending_script_checks = ["test_script"]

        with patch.object(plugin, "_check_conditions", return_value=True):
            plugin._process_pending_checks()

            assert script.has_run is True

    def test_process_pending_checks_script_not_in_registry(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test process pending checks when script not in registry."""
        plugin, mock_context = script_plugin_ctx
        plugin.setup(mock_context)
        plugin._pending_script_checks = ["nonexistent_script"]

        # Should not crash, just skip the missing script
        plugin._process_pending_checks()

        assert len(plugin._pending_script_checks) == 0

    def test_process_pending_checks_conditions_fail(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test process pending checks when conditions fail."""
        plugin, mock_context = script_plugin_ctx
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
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        plugin._pending_script_checks = ["test_script"]

        with patch.object(plugin, "_check_conditions", return_value=False):
            plugin._process_pending_checks()

            assert len(plugin.active_sequences) == 0

    def test_trigger_matches_event_correct_match(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test trigger matches event correctly."""
        plugin, _ = script_plugin_ctx
        trigger = ScriptTrigger(event_name="test_event", filters={"npc": "martin"})
        event_data = {"npc": "martin"}

        result = plugin._trigger_matches_event(trigger, "test_event", event_data)

        assert result is True

    def test_trigger_matches_event_wrong_event_type(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test trigger doesn't match wrong event type."""
        plugin, _ = script_plugin_ctx
        trigger = ScriptTrigger(event_name="test_event", filters={})

        result = plugin._trigger_matches_event(trigger, "other_event", {})

        assert result is False

    def test_trigger_matches_event_missing_filter(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test trigger doesn't match when event data missing filter."""
        plugin, _ = script_plugin_ctx
        trigger = ScriptTrigger(event_name="test_event", filters={"npc": "martin"})
        event_data = {"npc": "john"}

        result = plugin._trigger_matches_event(trigger, "test_event", event_data)

        assert result is False

    def test_trigger_matches_event_no_filters(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test trigger matches event with no additional filters."""
        plugin, _ = script_plugin_ctx
        trigger = ScriptTrigger(event_name="test_event", filters={})
        event_data = {"npc": "martin", "other": "data"}

        result = plugin._trigger_matches_event(trigger, "test_event", event_data)

        assert result is True

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_handle_event_trigger_executes_matching_script(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test handle event trigger executes matching scripts."""
        plugin, mock_context = script_plugin_ctx
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
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        plugin._handle_event_trigger("test_event", {})

        assert len(plugin.active_sequences) == 1

    def test_handle_event_trigger_skips_wrong_scene(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test handle event trigger skips scripts in wrong scene."""
        plugin, mock_context = script_plugin_ctx
        mock_action = MagicMock()
        script = Script(
            trigger=ScriptTrigger(event_name="test_event", filters={}),
            conditions=[],
            scene="other_scene",
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        mock_context.scene_plugin.get_current_scene.return_value = "current_scene"

        plugin._handle_event_trigger("test_event", {})

        assert len(plugin.active_sequences) == 0

    def test_handle_event_trigger_skips_already_run(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test handle event trigger skips run_once scripts that ran."""
        plugin, mock_context = script_plugin_ctx
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
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        plugin._handle_event_trigger("test_event", {})

        assert len(plugin.active_sequences) == 0

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_handle_event_trigger_marks_run_once(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test handle event trigger marks run_once scripts."""
        plugin, mock_context = script_plugin_ctx
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
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        plugin._handle_event_trigger("test_event", {})

        assert script.has_run is True

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_handle_event_trigger_executes_on_condition_fail(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test handle event trigger executes on_condition_fail actions."""
        plugin, mock_context = script_plugin_ctx
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
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        with patch.object(plugin, "_check_conditions", return_value=False):
            plugin._handle_event_trigger("test_event", {})

            assert len(plugin.active_sequences) == 1
            assert plugin.active_sequences[0][0] == "test_script_fail"

    def test_handle_event_trigger_no_trigger(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test handle event trigger skips scripts with no trigger."""
        plugin, mock_context = script_plugin_ctx
        mock_action = MagicMock()
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        plugin._handle_event_trigger("test_event", {})

        assert len(plugin.active_sequences) == 0

    def test_handle_event_trigger_mismatched_trigger(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test handle event trigger skips scripts with mismatched triggers."""
        plugin, mock_context = script_plugin_ctx
        mock_action = MagicMock()
        script = Script(
            trigger=ScriptTrigger(event_name="other_event", filters={"npc": "bob"}),
            conditions=[],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        plugin._handle_event_trigger("test_event", {"npc": "bob"})

        assert len(plugin.active_sequences) == 0

    @patch("pedre.plugins.script.plugin.EventRegistry")
    def test_register_event_handlers_subscribes_to_events(
        self, mock_event_registry: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test register event handlers subscribes to all required events."""
        plugin, mock_context = script_plugin_ctx
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

        plugin.scripts = {
            "script1": script1,
            "script2": script2,
            "script3": script3,
        }

        plugin.setup(mock_context)
        plugin._register_event_handlers()

        assert mock_context.event_bus.subscribe.call_count == 2
        assert "event1" in plugin._subscribed_events
        assert "event2" in plugin._subscribed_events

    def test_register_event_handlers_skips_already_subscribed(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test register event handlers doesn't duplicate subscriptions."""
        plugin, mock_context = script_plugin_ctx
        script = Script(
            trigger=ScriptTrigger(event_name="test_event", filters={}),
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        plugin.scripts = {"script": script}
        plugin._subscribed_events = {"test_event"}  # Already subscribed

        plugin.setup(mock_context)
        plugin._register_event_handlers()

        mock_context.event_bus.subscribe.assert_not_called()

    @patch("pedre.plugins.script.plugin.EventRegistry")
    def test_register_event_handlers_warns_unregistered_event(
        self, mock_event_registry: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test register event handlers warns about unregistered events."""
        plugin, mock_context = script_plugin_ctx
        mock_event_registry.get.return_value = None  # Event not registered

        script = Script(
            trigger=ScriptTrigger(event_name="unknown_event", filters={}),
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        plugin.scripts = {"script": script}

        plugin.setup(mock_context)

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            plugin._register_event_handlers()

            mock_logger.warning.assert_called_once()

    def test_restore_save_state_script_not_found(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test restoring active script that doesn't exist warns."""
        plugin, _ = script_plugin_ctx
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
            plugin.restore_save_state(state)

            mock_logger.warning.assert_called_once()
            assert len(plugin.active_sequences) == 0

    def test_restore_save_state_empty_action_list(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test restoring script with empty action list."""
        plugin, _ = script_plugin_ctx
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}

        state = {
            "active_scripts": [
                {
                    "script_name": "test_script",
                    "current_index": 0,
                    "is_fail_sequence": False,
                }
            ]
        }

        plugin.restore_save_state(state)

        assert len(plugin.active_sequences) == 0

    def test_restore_save_state_empty_fail_sequence(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test restoring fail sequence with empty on_condition_fail."""
        plugin, _ = script_plugin_ctx
        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}

        state = {
            "active_scripts": [
                {
                    "script_name": "test_script",
                    "current_index": 0,
                    "is_fail_sequence": True,
                }
            ]
        }

        plugin.restore_save_state(state)

        assert len(plugin.active_sequences) == 0

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_restore_save_state_no_valid_actions(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test restoring script when all actions fail to parse."""
        plugin, _ = script_plugin_ctx
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
        plugin.scripts = {"test_script": script}

        state = {
            "active_scripts": [
                {
                    "script_name": "test_script",
                    "current_index": 0,
                    "is_fail_sequence": False,
                }
            ]
        }

        plugin.restore_save_state(state)

        assert len(plugin.active_sequences) == 1

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_setup_json_decode_error(self, mock_asset_path: MagicMock, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test setup handles JSON decode errors gracefully."""
        plugin, mock_context = script_plugin_ctx
        mock_file = MagicMock()
        mock_file.name = "invalid_scripts.json"
        m_open = mock_open(read_data="invalid json{")
        mock_file.open = m_open

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = [mock_file]
        mock_asset_path.return_value = "/fake/scripts"

        with (
            patch("pedre.plugins.script.plugin.Path") as mock_path_class,
            patch("pedre.plugins.script.plugin.logger") as mock_logger,
        ):
            mock_path_class.return_value = mock_path

            plugin.setup(mock_context)

            mock_logger.exception.assert_called()

    @patch("pedre.plugins.script.plugin.asset_path")
    def test_setup_generic_exception_in_file_load(
        self, mock_asset_path: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test setup handles generic exceptions during file load."""
        plugin, mock_context = script_plugin_ctx
        mock_file = MagicMock()
        mock_file.name = "error_scripts.json"
        mock_file.open.side_effect = OSError("Cannot read file")

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = [mock_file]
        mock_asset_path.return_value = "/fake/scripts"

        with (
            patch("pedre.plugins.script.plugin.Path") as mock_path_class,
            patch("pedre.plugins.script.plugin.logger") as mock_logger,
        ):
            mock_path_class.return_value = mock_path

            plugin.setup(mock_context)

            mock_logger.exception.assert_called()

    def test_handle_event_trigger_conditions_fail_no_fail_actions(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test handle event trigger logs when conditions fail with no fail actions."""
        plugin, mock_context = script_plugin_ctx
        mock_condition = MagicMock()
        mock_success_action = MagicMock()
        script = Script(
            trigger=ScriptTrigger(event_name="test_event", filters={}),
            conditions=[mock_condition],
            scene=None,
            run_once=False,
            actions=[mock_success_action],
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}
        plugin.setup(mock_context)

        with (
            patch.object(plugin, "_check_conditions", return_value=False),
            patch("pedre.plugins.script.plugin.logger") as mock_logger,
        ):
            plugin._handle_event_trigger("test_event", {})

            mock_logger.debug.assert_called()
            assert len(plugin.active_sequences) == 0

    def test_on_generic_event_no_event_name(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test generic event handler with no event name."""
        plugin, mock_context = script_plugin_ctx
        mock_event = MagicMock()
        mock_event.name = None

        plugin.setup(mock_context)
        plugin._on_generic_event(mock_event)
        # Should exit early, no script trigger handling

    def test_on_generic_event_with_get_script_data(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test generic event handler using get_script_data protocol."""
        plugin, mock_context = script_plugin_ctx
        mock_event = MagicMock()
        mock_event.name = "test_event"
        mock_event.get_script_data.return_value = {"key": "value"}

        plugin.setup(mock_context)

        with patch.object(plugin, "_handle_event_trigger") as mock_handle:
            plugin._on_generic_event(mock_event)

            mock_handle.assert_called_once_with("test_event", {"key": "value"})

    @patch("pedre.plugins.script.plugin.ConditionRegistry")
    def test_parse_scripts_condition_parse_error(
        self, mock_condition_registry: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test parsing script with condition parse error."""
        plugin, _ = script_plugin_ctx
        mock_condition_registry.create.side_effect = ConditionParseError("Invalid condition")

        script_data = {
            "test_script": {
                "conditions": [{"name": "invalid"}],
                "actions": [],
            }
        }

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            plugin._parse_scripts(script_data)

            mock_logger.warning.assert_called()

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_parse_scripts_action_parse_error(
        self, mock_action_registry: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test parsing script with action parse error."""
        plugin, _ = script_plugin_ctx
        mock_action_registry.create.side_effect = ActionParseError("Invalid action")

        script_data = {
            "test_script": {
                "actions": [{"name": "invalid"}],
            }
        }

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            plugin._parse_scripts(script_data)

            mock_logger.warning.assert_called()

    @patch("pedre.plugins.script.plugin.ActionRegistry")
    def test_parse_scripts_fail_action_parse_error(
        self, mock_action_registry: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test parsing script with on_condition_fail action parse error."""
        plugin, _ = script_plugin_ctx
        mock_action_registry.create.side_effect = ActionParseError("Invalid fail action")

        script_data = {
            "test_script": {
                "actions": [],
                "on_condition_fail": [{"name": "invalid"}],
            }
        }

        with patch("pedre.plugins.script.plugin.logger") as mock_logger:
            plugin._parse_scripts(script_data)

            mock_logger.warning.assert_called()

    def test_parse_scripts_unknown_keys(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test parsing script with unknown keys."""
        plugin, _ = script_plugin_ctx
        script_data = {
            "test_script": {
                "actions": [],
                "unknown_key": "value",
                "another_unknown": 123,
            }
        }

        plugin._parse_scripts(script_data)

        assert len(plugin._validation_errors) > 0
        assert "unknown keys" in plugin._validation_errors[0]

    def test_parse_scripts_no_trigger_event(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test parsing script with trigger but no event field."""
        plugin, _ = script_plugin_ctx
        script_data = {
            "test_script": {
                "trigger": {"filter": "value"},  # Missing 'event'
                "actions": [],
            }
        }

        plugin._parse_scripts(script_data)

        assert "test_script" in plugin.scripts
        assert plugin.scripts["test_script"].trigger is None

    def test_parse_scripts_trigger_with_filters(self, script_plugin_ctx: ScriptPluginCtx) -> None:
        """Test parsing script with trigger including filters."""
        plugin, _ = script_plugin_ctx
        script_data = {
            "test_script": {
                "trigger": {"event": "test_event", "npc": "martin", "level": 5},
                "actions": [],
            }
        }

        plugin._parse_scripts(script_data)

        assert "test_script" in plugin.scripts
        script = plugin.scripts["test_script"]
        assert script.trigger is not None
        assert script.trigger.event_name == "test_event"
        assert script.trigger.filters == {"npc": "martin", "level": 5}

    @patch("pedre.plugins.script.plugin.ActionSequence")
    def test_restore_save_state_actions_list_becomes_empty(
        self, mock_sequence_class: MagicMock, script_plugin_ctx: ScriptPluginCtx
    ) -> None:
        """Test restoring script when list() conversion results in empty list."""
        plugin, _ = script_plugin_ctx
        mock_action_data = MagicMock()
        mock_action_data.__bool__.return_value = True
        mock_action_data.__iter__.return_value = iter([])

        script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=mock_action_data,
            on_condition_fail=[],
        )
        plugin.scripts = {"test_script": script}

        state = {
            "active_scripts": [
                {
                    "script_name": "test_script",
                    "current_index": 0,
                    "is_fail_sequence": False,
                }
            ]
        }

        plugin.restore_save_state(state)

        assert len(plugin.active_sequences) == 0
        mock_sequence_class.assert_not_called()
