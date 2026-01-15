"""Custom types and enumerations."""

from enum import Enum, auto
from typing import TypedDict


class SceneStateCacheDict(TypedDict):
    """TypedDict for scene state cache serialization."""

    npc_states: dict[str, dict[str, dict[str, float | bool | int]]]
    script_states: dict[str, dict[str, list[str]]]


class MenuOption(Enum):
    """Menu options enumeration."""

    CONTINUE = auto()
    NEW_GAME = auto()
    SAVE_GAME = auto()
    LOAD_GAME = auto()
    EXIT = auto()
