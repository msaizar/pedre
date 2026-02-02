"""Base interface for pause menu plugin."""

from abc import abstractmethod

from pedre.plugins.base import BasePlugin


class PauseMenuPluginBase(BasePlugin):
    """Base class for pause menu plugin.

    The pause menu plugin provides an in-game overlay menu that appears when
    the player presses ESC, offering options like Resume, New Game, Load, Save, and Exit.
    """

    role = "pause_menu_plugin"

    @property
    @abstractmethod
    def showing(self) -> bool:
        """Whether the pause menu overlay is currently visible."""
        ...

    @abstractmethod
    def show(self) -> None:
        """Show the pause menu overlay."""
        ...

    @abstractmethod
    def hide(self) -> None:
        """Hide the pause menu overlay."""
        ...
