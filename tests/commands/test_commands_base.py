"""Tests for base Command class."""

import argparse

import pytest

from pedre.commands.base import Command


class TestCommandBase:
    """Test base Command class."""

    def test_command_abstract_class(self) -> None:
        """Test that Command is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            Command()

    def test_add_arguments_default_implementation(self) -> None:
        """Test default add_arguments implementation does nothing and returns None."""

        class MinimalCommand(Command):
            """Minimal command implementation for testing."""

            name = "test"
            help = "Test command"
            description = "Test description"

            def execute(self, args: argparse.Namespace) -> None:
                """Execute the command."""

        command = MinimalCommand()
        parser = argparse.ArgumentParser()

        # Call default add_arguments - should return None and not add any arguments
        result = command.add_arguments(parser)

        # Covers line 65 - the return statement
        assert result is None

        # Verify no arguments were added
        args = parser.parse_args([])
        assert vars(args) == {}
