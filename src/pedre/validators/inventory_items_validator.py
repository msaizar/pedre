"""Inventory items validator for pedre."""

import json

from pedre.validators.base import ValidationResult, Validator


class InventoryItemsValidator(Validator):
    """Validates items.json (content registry format) and registers items in context."""

    @property
    def name(self) -> str:
        """Return validator name."""
        return "Inventory Items"

    def validate(self) -> ValidationResult:
        """Validate items.json and populate context.

        Loads the items data file (content registry dict format), validates the
        structure of each item, and registers valid item IDs in the
        ValidationContext for cross-reference validation by ScriptValidator and
        DialogValidator.

        Returns:
            ValidationResult with errors and metadata
        """
        if not self.path.exists():
            return ValidationResult(
                errors=[f"Inventory items file not found: {self.path}"],
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
                errors=[
                    f"Inventory items file '{self.path.name}': root must be a dictionary mapping IDs to definitions"
                ],
                item_count=0,
                metadata={},
            )

        errors: list[str] = []
        valid_count = 0

        for item_id, item_data in data.items():
            if not isinstance(item_data, dict):
                errors.append(f"Inventory item '{item_id}': must be a dictionary")
                continue

            for field in ("name", "description"):
                if field not in item_data:
                    errors.append(f"Inventory item '{item_id}': missing required '{field}' field")
                    break
            else:
                self.context.add_inventory_item(item_id)
                valid_count += 1

        return ValidationResult(
            errors=errors,
            item_count=valid_count,
            metadata={},
        )

    def validate_cross_references(self) -> ValidationResult:
        """No cross-references needed - inventory items are the authority.

        Returns:
            Empty ValidationResult
        """
        return ValidationResult(errors=[], item_count=0, metadata={})
