"""Types for pedre."""

from dataclasses import dataclass
from typing import Literal

ReferenceType = Literal[
    "npc",
    "waypoint",
    "portal",
    "interactive_object",
    "map",
]

ScopeType = Literal["global", "map"]


@dataclass(frozen=True)
class EntityReference:
    """Entity reference."""

    type: ReferenceType
    name: str
    scope: ScopeType = "global"
    target_map: str | None = None
