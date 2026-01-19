"""Custom types and enumerations."""

from enum import Enum, auto


class MenuOption(Enum):
    """Menu options enumeration."""

    CONTINUE = auto()
    NEW_GAME = auto()
    SAVE_GAME = auto()
    LOAD_GAME = auto()
    EXIT = auto()
