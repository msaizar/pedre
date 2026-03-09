"""Player validator for pedre."""

import json

from pedre.content.registries.player import PlayerRegistry
from pedre.content.registry import InvalidDefinitionError
from pedre.validators.base import ValidationResult, Validator


class PlayerValidator(Validator):
    """Validates players.json (content registry format) and registers player IDs in context."""

    @property
    def name(self) -> str:
        """Return validator name."""
        return "Players"

    def validate(self) -> ValidationResult:
        """Validate players.json and populate context.

        Loads the players data file, delegates structural validation to
        PlayerRegistry.validate(), and registers valid player IDs in the
        ValidationContext.

        Returns:
            ValidationResult with errors and metadata
        """
        if not self.path.exists():
            return ValidationResult(
                errors=[f"Players file not found: {self.path}"],
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
                errors=[f"Players file '{self.path.name}': root must be a dictionary mapping IDs to definitions"],
                item_count=0,
                metadata={},
            )

        registry = PlayerRegistry()
        errors: list[str] = []
        valid_count = 0

        for player_id, player_data in data.items():
            if not isinstance(player_data, dict):
                errors.append(f"Player '{player_id}': must be a dictionary")
                continue

            try:
                registry.validate(player_id, player_data)
            except InvalidDefinitionError as e:
                errors.append(str(e))
                continue

            self.context.add_player_id(player_id)
            valid_count += 1

        return ValidationResult(
            errors=errors,
            item_count=valid_count,
            metadata={},
        )

    def validate_cross_references(self) -> ValidationResult:
        """Validate that each player's sprite_id exists in the registered sprite IDs.

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

        for player_id in self.context.get_player_ids():
            player_data = data.get(player_id)
            if not isinstance(player_data, dict):
                continue
            sprite_id = player_data.get("sprite_id")
            if sprite_id and sprite_id not in sprite_ids:
                errors.append(f"Player '{player_id}' references unknown sprite '{sprite_id}'.")

        return ValidationResult(errors=errors, item_count=0, metadata={})
