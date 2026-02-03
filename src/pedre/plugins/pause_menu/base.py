"""Base interface for pause menu plugin."""

from abc import abstractmethod
from enum import Enum

from pedre.plugins.base import BasePlugin


class PauseMenuState(Enum):
    """States for the pause menu."""

    MAIN_MENU = "main_menu"
    LOAD_SLOTS = "load_slots"
    SAVE_SLOTS = "save_slots"
    CONFIRMATION = "confirmation"


class PauseMenuOption(Enum):
    """Main menu options."""

    RESUME = 0
    NEW_GAME = 1
    LOAD_GAME = 2
    SAVE_GAME = 3
    EXIT = 4


class PauseMenuBasePlugin(BasePlugin):
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
