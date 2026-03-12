"""Sprite content type registry."""

from typing import Any, ClassVar

from pedre.content.registry import (
    BaseContentRegistry,
    ContentTypeRegistry,
    InvalidDefinitionError,
)


@ContentTypeRegistry.register
class SpriteRegistry(BaseContentRegistry):
    """Registry for sprite definitions."""

    name: ClassVar[str] = "sprites"
    filename: ClassVar[str] = "sprites.json"
    display_name: ClassVar[str] = "Sprite"

    VALID_ON_COMPLETE: ClassVar[set[str]] = {"idle", "hide"}

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Validate sprite definitions including per-state structure."""
        for field in ("sprite_sheet", "frame_width", "frame_height", "states"):
            if field not in definition:
                msg = f"Sprite '{definition_id}' missing required field '{field}'."
                raise InvalidDefinitionError(msg)

        states = definition["states"]
        if not isinstance(states, dict):
            msg = f"Sprite '{definition_id}' states must be a dictionary."
            raise InvalidDefinitionError(msg)

        state_names = set(states.keys())

        for state_name, state_data in states.items():
            prefix = f"Sprite '{definition_id}' state '{state_name}'"

            for req in ("directional", "loop", "priority"):
                if req not in state_data:
                    msg = f"{prefix} missing required field '{req}'."
                    raise InvalidDefinitionError(msg)

            directional = state_data["directional"]
            auto_from = state_data.get("auto_from")
            on_complete = state_data.get("on_complete")

            if on_complete is not None and on_complete not in self.VALID_ON_COMPLETE:
                msg = (
                    f"{prefix} has invalid on_complete '{on_complete}'. "
                    f"Must be one of {sorted(self.VALID_ON_COMPLETE)}."
                )
                raise InvalidDefinitionError(msg)

            if auto_from is not None:
                if auto_from not in state_names:
                    msg = (
                        f"{prefix} auto_from references unknown state '{auto_from}'. "
                        "It must reference another state in the same sprite definition."
                    )
                    raise InvalidDefinitionError(msg)
                # auto_from states don't need explicit frame data
                continue

            if directional:
                directions = state_data.get("directions")
                if not directions or not isinstance(directions, dict):
                    msg = f"{prefix} is directional but missing 'directions' mapping."
                    raise InvalidDefinitionError(msg)
                for dir_name, dir_data in directions.items():
                    for req in ("frames", "row"):
                        if req not in dir_data:
                            msg = f"{prefix} direction '{dir_name}' missing required field '{req}'."
                            raise InvalidDefinitionError(msg)
            else:
                for req in ("frames", "row"):
                    if req not in state_data:
                        msg = f"{prefix} is non-directional but missing required field '{req}'."
                        raise InvalidDefinitionError(msg)
