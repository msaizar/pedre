"""NPCs validator for pedre."""

import json

from pedre.content.registries.npc import NPCRegistry
from pedre.content.registry import InvalidDefinitionError
from pedre.validators.base import ValidationResult, Validator


class NPCsValidator(Validator):
    """Validates npcs.json (content registry format) and registers NPC IDs in context."""

    @property
    def name(self) -> str:
        """Return validator name."""
        return "NPCs"

    def validate(self) -> ValidationResult:
        """Validate npcs.json and populate context.

        Loads the NPCs data file, delegates structural validation to
        NPCRegistry.validate(), and registers valid NPC IDs in the
        ValidationContext.

        Returns:
            ValidationResult with errors and metadata
        """
        if not self.path.exists():
            return ValidationResult(
                errors=[f"NPCs file not found: {self.path}"],
                item_count=0,
                metadata={},
            )

        try:
            with self.path.open() as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(
                errors=[f"Failed to parse {self.path.name}: {e}"],
                item_count=0,
                metadata={},
            )
        except OSError as e:
            return ValidationResult(
                errors=[f"Failed to load {self.path.name}: {e}"],
                item_count=0,
                metadata={},
            )

        if not isinstance(data, dict):
            return ValidationResult(
                errors=[f"NPCs file '{self.path.name}': root must be a dictionary mapping IDs to definitions"],
                item_count=0,
                metadata={},
            )

        registry = NPCRegistry()
        errors: list[str] = []
        valid_count = 0

        for npc_id, npc_data in data.items():
            if not isinstance(npc_data, dict):
                errors.append(f"NPC '{npc_id}': must be a dictionary")
                continue

            try:
                registry.validate(npc_id, npc_data)
            except InvalidDefinitionError as e:
                errors.append(str(e))
                continue

            self.context.add_npc_id(npc_id)
            valid_count += 1

        return ValidationResult(
            errors=errors,
            item_count=valid_count,
            metadata={},
        )

    def validate_cross_references(self) -> ValidationResult:
        """Validate that each NPC's sprite_id exists in the registered sprite IDs.

        Requires SpritesValidator to have run first so that context.sprite_ids
        is populated.

        Returns:
            ValidationResult with cross-reference errors
        """
        if not self.path.exists():
            return ValidationResult(errors=[], item_count=0, metadata={})

        try:
            with self.path.open() as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return ValidationResult(errors=[], item_count=0, metadata={})

        if not isinstance(data, dict):
            return ValidationResult(errors=[], item_count=0, metadata={})

        errors: list[str] = []
        sprite_ids = self.context.get_sprite_ids()

        for npc_id in self.context.get_npc_ids():
            npc_data = data.get(npc_id)
            if not isinstance(npc_data, dict):
                continue
            sprite_id = npc_data.get("sprite_id")
            if sprite_id and sprite_id not in sprite_ids:
                errors.append(f"NPC '{npc_id}' references unknown sprite '{sprite_id}'.")

        return ValidationResult(errors=errors, item_count=0, metadata={})
