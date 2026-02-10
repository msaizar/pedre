"""CLI tests."""

import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from pedre.cli import main, validate_scripts
from pedre.plugins.script.base import ScriptValidationError


class TestCLI:
    """Test CLI commands."""

    def _setup_mocks(
        self,
        mock_path_class: MagicMock,
        mock_scripts_dir: MagicMock,
        mock_event_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_condition_registry: MagicMock,
    ) -> None:
        """Helper to setup common mock configuration."""
        # Mock the path construction: Path.cwd() / assets / scripts
        mock_cwd = MagicMock(spec=Path)

        def truediv_side_effect(_other: str) -> MagicMock:
            mock_intermediate = MagicMock(spec=Path)
            mock_intermediate.__truediv__ = MagicMock(return_value=mock_scripts_dir)
            return mock_intermediate

        mock_cwd.__truediv__ = MagicMock(side_effect=truediv_side_effect)
        mock_path_class.cwd.return_value = mock_cwd

        # Setup default registry responses
        mock_event_registry.get_all_types.return_value = ["valid_event"]
        mock_action_registry.get_all_types.return_value = ["test_action"]
        mock_condition_registry.get_all_types.return_value = ["test_condition"]

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_directory_not_found(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts when scripts directory doesn't exist."""
        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = False

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_no_script_files(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts when no script files found."""
        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = []

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 0

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_unknown_keys(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with unknown keys in script definition."""
        script_data = {
            "test_script": {
                "trigger": {"event": "valid_event"},
                "actions": [{"type": "test_action"}],
                "unknown_key": "value",
                "another_bad_key": 123,
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_event_registry.is_registered.return_value = True
        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_json_decode_error(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with JSON decode error."""
        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data="invalid json {")

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_os_error(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with OS error when opening file."""
        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open.side_effect = OSError("Permission denied")

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_trigger_without_event(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with trigger missing event key."""
        script_data = {
            "test_script": {
                "trigger": {"filter": "value"},
                "actions": [{"type": "test_action"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_with_invalid_event(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with invalid event triggers."""
        script_data = {
            "test_script": {
                "trigger": {"event": "unknown_event"},
                "actions": [{"type": "test_action"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_event_registry.is_registered.return_value = False
        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_trigger_valid_filter_keys(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with valid trigger filter keys."""
        script_data = {
            "test_script": {
                "trigger": {"event": "valid_event", "valid_key": "value"},
                "actions": [{"type": "test_action"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_event_registry.is_registered.return_value = True
        mock_event_registry.get_trigger_keys.return_value = {"valid_key"}
        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []

        # Should succeed - valid filter keys
        validate_scripts()

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_trigger_invalid_filter_keys(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with invalid trigger filter keys."""
        script_data = {
            "test_script": {
                "trigger": {"event": "valid_event", "invalid_filter": "value", "another_bad": 123},
                "actions": [{"type": "test_action"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_event_registry.is_registered.return_value = True
        mock_event_registry.get_trigger_keys.return_value = {"valid_key"}
        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_condition_missing_check(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with condition missing check key."""
        script_data = {
            "test_script": {
                "conditions": [{"param": "value"}],
                "actions": [{"type": "test_action"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_condition_unknown_type(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with unknown condition type."""
        script_data = {
            "test_script": {
                "conditions": [{"check": "unknown_condition"}],
                "actions": [{"type": "test_action"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_condition_registry.is_registered.return_value = False
        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_condition_validation_errors(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with condition parameter validation errors."""
        script_data = {
            "test_script": {
                "conditions": [{"check": "test_condition", "param": "bad_value"}],
                "actions": [{"type": "test_action"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_condition_registry.is_registered.return_value = True
        mock_condition_registry.validate.return_value = ["parameter error"]
        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_empty_actions(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with empty actions list."""
        script_data = {
            "test_script": {
                "trigger": {"event": "valid_event"},
                "actions": [],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_event_registry.is_registered.return_value = True

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_action_missing_type(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with action missing type key."""
        script_data = {
            "test_script": {
                "actions": [{"param": "value"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_action_unknown_type(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with unknown action type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "unknown_action"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_action_registry.is_registered.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_action_validation_errors(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with action parameter validation errors."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action", "param": "bad_value"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = ["parameter error"]

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_on_condition_fail_missing_type(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with on_condition_fail action missing type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"param": "value"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_on_condition_fail_unknown_type(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with on_condition_fail unknown action type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"type": "unknown_action"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        def is_registered_side_effect(action_type: str) -> bool:
            return action_type == "test_action"

        mock_action_registry.is_registered.side_effect = is_registered_side_effect
        mock_action_registry.validate.return_value = []

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_on_condition_fail_validation_errors(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with on_condition_fail action validation errors."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"type": "test_action", "param": "bad_value"}],
            }
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_action_registry.is_registered.return_value = True

        def validate_side_effect(_action_type: str, action: dict) -> list[str]:
            if "param" in action and action["param"] == "bad_value":
                return ["parameter error"]
            return []

        mock_action_registry.validate.side_effect = validate_side_effect

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.EventRegistry")
    @patch("pedre.cli.ActionRegistry")
    @patch("pedre.cli.ConditionRegistry")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_success(
        self,
        mock_path_class: MagicMock,
        mock_condition_registry: MagicMock,
        mock_action_registry: MagicMock,
        mock_event_registry: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with all valid scripts."""
        script_data = {
            "script1": {
                "trigger": {"event": "valid_event"},
                "conditions": [{"check": "test_condition"}],
                "actions": [{"type": "test_action"}],
            },
            "script2": {
                "actions": [{"type": "test_action"}],
            },
        }

        mock_file_path = MagicMock(spec=Path)
        mock_file_path.name = "test_scripts.json"
        mock_file_path.open = mock_open(read_data=json.dumps(script_data))

        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.return_value = [mock_file_path]

        self._setup_mocks(
            mock_path_class,
            mock_scripts_dir,
            mock_event_registry,
            mock_action_registry,
            mock_condition_registry,
        )

        mock_event_registry.is_registered.return_value = True
        mock_event_registry.get_trigger_keys.return_value = None
        mock_condition_registry.is_registered.return_value = True
        mock_condition_registry.validate.return_value = []
        mock_action_registry.is_registered.return_value = True
        mock_action_registry.validate.return_value = []

        # Should not raise, completes successfully
        validate_scripts()

    @patch("pedre.cli.ActionLoader")
    @patch("pedre.cli.EventLoader")
    @patch("pedre.cli.ConditionLoader")
    @patch("pedre.cli.Path")
    @patch("sys.argv", ["pedre-validate"])
    def test_validate_scripts_script_validation_error(
        self,
        mock_path_class: MagicMock,
        mock_condition_loader: MagicMock,  # noqa: ARG002
        mock_event_loader: MagicMock,  # noqa: ARG002
        mock_action_loader: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test validate_scripts with ScriptValidationError."""
        mock_scripts_dir = MagicMock(spec=Path)
        mock_scripts_dir.exists.return_value = True
        mock_scripts_dir.glob.side_effect = ScriptValidationError(["Test validation error"])

        mock_cwd = MagicMock(spec=Path)

        def truediv_side_effect(_other: str) -> MagicMock:
            mock_intermediate = MagicMock(spec=Path)
            mock_intermediate.__truediv__ = MagicMock(return_value=mock_scripts_dir)
            return mock_intermediate

        mock_cwd.__truediv__ = MagicMock(side_effect=truediv_side_effect)
        mock_path_class.cwd.return_value = mock_cwd

        with pytest.raises(SystemExit) as exc_info:
            validate_scripts()

        assert exc_info.value.code == 1

    def test_main(self) -> None:
        """Test main CLI entry point."""
        # Should just print help and not exit
        main()
