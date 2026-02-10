"""Tests for init command."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pedre.commands.init import InitCommand


class TestInitCommand:
    """Test init command."""

    @patch("pedre.commands.init.console")
    def test_init_creates_project_structure(
        self,
        mock_console: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test init command creates the project structure."""
        command = InitCommand()
        args = argparse.Namespace(path=tmp_path)

        # Should complete successfully
        command.execute(args)

        # Verify directories were created
        assert (tmp_path / "assets").exists()
        assert (tmp_path / "assets" / "audio").exists()
        assert (tmp_path / "main.py").exists()
        assert (tmp_path / "settings.py").exists()

    @patch("pedre.commands.init.Path")
    @patch("pedre.commands.init.console")
    def test_init_with_custom_path(
        self,
        mock_console: MagicMock,
        mock_path_class: MagicMock,
    ) -> None:
        """Test init command with custom project path."""
        custom_path = MagicMock(spec=Path)
        custom_path.exists.return_value = False

        # Mock mkdir to prevent actual directory creation
        mock_folder = MagicMock(spec=Path)
        mock_folder.mkdir = MagicMock()
        custom_path.__truediv__ = MagicMock(return_value=mock_folder)

        # Mock file creation
        mock_file = MagicMock(spec=Path)
        mock_file.write_text = MagicMock()
        mock_folder.__truediv__ = MagicMock(return_value=mock_file)

        command = InitCommand()
        args = argparse.Namespace(path=custom_path)

        # Should complete successfully
        command.execute(args)

        # Verify folders were created
        assert mock_folder.mkdir.called

    @patch("pedre.commands.init.console")
    def test_init_fails_with_existing_critical_files(
        self,
        mock_console: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test init command fails when critical files exist."""
        # Create an existing main.py file
        (tmp_path / "main.py").write_text("existing content")

        command = InitCommand()
        args = argparse.Namespace(path=tmp_path)

        # Should exit with error code 1 (covers lines 73-78)
        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)
        assert exc_info.value.code == 1

    @patch("pedre.commands.init.console")
    def test_init_succeeds_with_non_critical_files(
        self,
        mock_console: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test init command succeeds when non-critical files exist."""
        # Create some non-critical files
        (tmp_path / "README.md").write_text("readme")
        (tmp_path / "other.txt").write_text("other")

        command = InitCommand()
        args = argparse.Namespace(path=tmp_path)

        # Should complete successfully (covers the False branch of line 73)
        command.execute(args)

        # Verify project structure was created
        assert (tmp_path / "assets").exists()
        assert (tmp_path / "main.py").exists()
        assert (tmp_path / "settings.py").exists()

    def test_add_arguments_without_path(self) -> None:
        """Test add_arguments method adds path argument with default None."""
        command = InitCommand()
        parser = argparse.ArgumentParser()

        # Add arguments (covers line 30 default=None)
        command.add_arguments(parser)

        # Parse with no arguments - should use default
        args = parser.parse_args([])
        assert args.path is None

    def test_add_arguments_with_path(self, tmp_path: Path) -> None:
        """Test add_arguments method accepts path argument."""
        command = InitCommand()
        parser = argparse.ArgumentParser()

        command.add_arguments(parser)

        # Parse with path argument
        test_dir = tmp_path / "test"
        args = parser.parse_args(["--path", str(test_dir)])
        assert args.path == test_dir

    @patch("pedre.commands.init.console")
    def test_init_handles_folder_creation_error(
        self,
        mock_console: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test init command handles OSError when creating folders."""
        command = InitCommand()
        args = argparse.Namespace(path=tmp_path)

        # Mock mkdir to raise OSError on first call
        with patch.object(Path, "mkdir") as mock_mkdir:
            mock_mkdir.side_effect = OSError("Permission denied")

            # Should exit with error when mkdir fails (covers lines 107-109)
            with pytest.raises(SystemExit) as exc_info:
                command.execute(args)
            assert exc_info.value.code == 1

    @patch("pedre.commands.init.console")
    def test_init_handles_main_py_write_error(
        self,
        mock_console: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test init command handles OSError when writing main.py."""
        command = InitCommand()
        args = argparse.Namespace(path=tmp_path)

        # Mock write_text to raise OSError for main.py
        with patch.object(Path, "write_text") as mock_write:
            mock_write.side_effect = OSError("Permission denied")

            # Should exit with error (covers lines 123-125)
            with pytest.raises(SystemExit) as exc_info:
                command.execute(args)
            assert exc_info.value.code == 1

    @patch("pedre.commands.init.console")
    def test_init_handles_settings_py_write_error(
        self,
        mock_console: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test init command handles OSError when writing settings.py."""
        command = InitCommand()
        args = argparse.Namespace(path=tmp_path)

        # Mock write_text to succeed for main.py but fail for settings.py
        original_write_text = Path.write_text
        call_count = [0]

        def mock_write_text(self: Path, content: str, *args, **kwargs) -> int:  # noqa: ANN002, ANN003
            call_count[0] += 1
            if call_count[0] == 2:  # Second call is for settings.py
                msg = "Permission denied"
                raise OSError(msg)
            return original_write_text(self, content, *args, **kwargs)

        with patch.object(Path, "write_text", mock_write_text):
            # Should exit with error (covers lines 140-142)
            with pytest.raises(SystemExit) as exc_info:
                command.execute(args)
            assert exc_info.value.code == 1
