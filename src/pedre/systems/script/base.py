"""Base class for ScriptManager."""

from typing import Any

from pedre.systems.base import BaseSystem


class ScriptBaseManager(BaseSystem):
    """Base class for ScriptManager."""

    def load_scene_scripts(self, scene_name: str, npc_dialogs_data: dict[str, Any]) -> dict[str, Any]:
        """Load and cache scripts for a specific scene."""
        return {}
