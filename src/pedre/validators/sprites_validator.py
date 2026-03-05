"""Sprites validator for pedre."""

import json

from pedre.content.registries.sprite import SpriteRegistry
from pedre.content.registry import InvalidDefinitionError
from pedre.validators.base import ValidationResult, Validator


class SpritesValidator(Validator):
    """Validates sprites.json (content registry format) and registers sprite IDs in context."""

    @property
    def name(self) -> str:
        """Return validator name."""
        return "Sprites"

    def validate(self) -> ValidationResult:
        """Validate sprites.json and populate context.

        Loads the sprites data file, delegates structural validation to
        SpriteRegistry.validate(), and registers valid sprite IDs in the
        ValidationContext for cross-reference validation by NPCsValidator.

        Returns:
            ValidationResult with errors and metadata
        """
        if not self.path.exists():
            return ValidationResult(
                errors=[f"Sprites file not found: {self.path}"],
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
                errors=[f"Sprites file '{self.path.name}': root must be a dictionary mapping IDs to definitions"],
                item_count=0,
                metadata={},
            )

        registry = SpriteRegistry()
        errors: list[str] = []
        valid_count = 0

        for sprite_id, sprite_data in data.items():
            if not isinstance(sprite_data, dict):
                errors.append(f"Sprite '{sprite_id}': must be a dictionary")
                continue

            try:
                registry.validate(sprite_id, sprite_data)
            except InvalidDefinitionError as e:
                errors.append(str(e))
                continue

            self.context.add_sprite_id(sprite_id)
            valid_count += 1

        return ValidationResult(
            errors=errors,
            item_count=valid_count,
            metadata={},
        )

    def validate_cross_references(self) -> ValidationResult:
        """No cross-references needed - sprites are the authority.

        Returns:
            Empty ValidationResult
        """
        return ValidationResult(errors=[], item_count=0, metadata={})
