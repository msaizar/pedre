"""Tests for command registry."""

from typing import TYPE_CHECKING

import pytest

from pedre.commands.base import Command
from pedre.commands.registry import CommandRegistry

if TYPE_CHECKING:
    import argparse


class TestCommandRegistry:
    """Test command registry functionality."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        CommandRegistry.clear()

    def teardown_method(self) -> None:
        """Clear registry after each test."""
        CommandRegistry.clear()

    def test_register_command(self) -> None:
        """Test registering a command."""

        @CommandRegistry.register
        class TestCommand(Command):
            name = "test"
            help = "Test command"
            description = "Test description"

            def add_arguments(self, parser: argparse.ArgumentParser) -> None:
                pass

            def execute(self, args: argparse.Namespace) -> None:
                pass

        # Verify command is registered
        assert CommandRegistry.is_registered("test")
        assert CommandRegistry.get_command("test") is TestCommand

    def test_register_duplicate_command_raises(self) -> None:
        """Test registering a command with a duplicate name raises ValueError."""

        @CommandRegistry.register
        class TestCommand(Command):
            name = "test"
            help = "Test command"
            description = "Test description"

            def add_arguments(self, parser: argparse.ArgumentParser) -> None:
                pass

            def execute(self, args: argparse.Namespace) -> None:
                pass

        with pytest.raises(ValueError, match="already registered"):

            @CommandRegistry.register
            class DuplicateCommand(Command):
                name = "test"
                help = "Duplicate"
                description = "Duplicate"

                def add_arguments(self, parser: argparse.ArgumentParser) -> None:
                    pass

                def execute(self, args: argparse.Namespace) -> None:
                    pass

    def test_get_command_returns_none_for_unregistered(self) -> None:
        """Test get_command returns None for unregistered command."""
        # Covers line 133 - get with no match
        result = CommandRegistry.get_command("nonexistent")
        assert result is None

    def test_get_all_commands(self) -> None:
        """Test getting all registered commands."""

        @CommandRegistry.register
        class Command1(Command):
            name = "cmd1"
            help = "Command 1"
            description = "Description 1"

            def add_arguments(self, parser: argparse.ArgumentParser) -> None:
                pass

            def execute(self, args: argparse.Namespace) -> None:
                pass

        @CommandRegistry.register
        class Command2(Command):
            name = "cmd2"
            help = "Command 2"
            description = "Description 2"

            def add_arguments(self, parser: argparse.ArgumentParser) -> None:
                pass

            def execute(self, args: argparse.Namespace) -> None:
                pass

        # Covers line 142 - get_all_commands returns copy
        commands = CommandRegistry.get_all_commands()
        assert len(commands) == 2
        assert "cmd1" in commands
        assert "cmd2" in commands
        assert commands["cmd1"] is Command1
        assert commands["cmd2"] is Command2

    def test_get_all_commands_returns_copy(self) -> None:
        """Test that get_all_commands returns a copy."""

        @CommandRegistry.register
        class TestCommand(Command):
            name = "test"
            help = "Test command"
            description = "Test description"

            def add_arguments(self, parser: argparse.ArgumentParser) -> None:
                pass

            def execute(self, args: argparse.Namespace) -> None:
                pass

        # Get commands and modify the result
        commands = CommandRegistry.get_all_commands()

        # Create a fake command class for testing
        class FakeCommand(Command):
            name = "fake"
            help = "Fake"
            description = "Fake"

            def execute(self, args: argparse.Namespace) -> None:
                pass

        commands["fake"] = FakeCommand

        # Original registry should be unchanged
        assert "fake" not in CommandRegistry.get_all_commands()
        assert len(CommandRegistry.get_all_commands()) == 1

    def test_is_registered(self) -> None:
        """Test checking if a command is registered."""

        @CommandRegistry.register
        class TestCommand(Command):
            name = "test"
            help = "Test command"
            description = "Test description"

            def add_arguments(self, parser: argparse.ArgumentParser) -> None:
                pass

            def execute(self, args: argparse.Namespace) -> None:
                pass

        assert CommandRegistry.is_registered("test")
        assert not CommandRegistry.is_registered("nonexistent")

    def test_clear(self) -> None:
        """Test clearing the registry."""

        @CommandRegistry.register
        class TestCommand(Command):
            name = "test"
            help = "Test command"
            description = "Test description"

            def add_arguments(self, parser: argparse.ArgumentParser) -> None:
                pass

            def execute(self, args: argparse.Namespace) -> None:
                pass

        # Verify command is registered
        assert CommandRegistry.is_registered("test")

        # Clear registry
        CommandRegistry.clear()

        # Verify command is no longer registered
        assert not CommandRegistry.is_registered("test")
        assert len(CommandRegistry.get_all_commands()) == 0
