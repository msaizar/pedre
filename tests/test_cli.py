"""Tests for main CLI entry point and command routing."""

from unittest.mock import MagicMock, patch

from pedre.cli import main


class TestCLI:
    """Test CLI command routing."""

    @patch("sys.argv", ["pedre"])
    @patch("pedre.cli.console")
    def test_main_no_command(self, mock_console: MagicMock) -> None:
        """Test main CLI entry point with no command shows help."""
        # Create mock commands to ensure the help loop executes
        mock_command_instance = MagicMock()
        mock_command_class = MagicMock(return_value=mock_command_instance)
        mock_command_instance.name = "testcmd"
        mock_command_instance.help = "Test command"
        mock_command_instance.description = "Test description"

        with patch("pedre.cli.CommandRegistry.get_all_commands", return_value={"testcmd": mock_command_class}):
            main()

        # Should print help text when no command is provided
        assert mock_console.print.called
        # Verify the command list is printed (lines 83-84)
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("testcmd" in call for call in print_calls)

    @patch("sys.argv", ["pedre", "somecommand"])
    def test_main_routes_to_command(self) -> None:
        """Test main CLI routes to registered commands."""
        # Create a mock command
        mock_command_instance = MagicMock()
        mock_command_class = MagicMock(return_value=mock_command_instance)
        mock_command_instance.name = "somecommand"
        mock_command_instance.help = "Test command"
        mock_command_instance.description = "Test description"

        with patch("pedre.cli.CommandRegistry.get_all_commands", return_value={"somecommand": mock_command_class}):
            main()

        # Verify the command was instantiated and executed
        mock_command_class.assert_called()
        mock_command_instance.execute.assert_called_once()
