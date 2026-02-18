"""Inventory items validator for pedre."""

import json

from pedre.validators.base import ValidationResult, Validator


class InventoryItemsValidator(Validator):
    """Validates inventory_items.json and registers items in context."""

    @property
    def name(self) -> str:
        """Return validator name."""
        return "Inventory Items"

    def validate(self) -> ValidationResult:
        """Validate inventory_items.json and populate context.

        Loads the inventory items data file, validates the structure of each item,
        and registers valid item IDs in the ValidationContext for cross-reference
        validation by ScriptValidator and DialogValidator.

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
                errors=[f"Inventory items file '{self.path.name}': root must be a dictionary"],
                item_count=0,
                metadata={},
            )

        items = data.get("items")
        if items is None:
            return ValidationResult(
                errors=[f"Inventory items file '{self.path.name}': missing required 'items' key"],
                item_count=0,
                metadata={},
            )

        if not isinstance(items, list):
            return ValidationResult(
                errors=[f"Inventory items file '{self.path.name}': 'items' must be a list"],
                item_count=0,
                metadata={},
            )

        errors: list[str] = []
        valid_count = 0

        for i, item_data in enumerate(items):
            if not isinstance(item_data, dict):
                errors.append(f"Inventory item [{i}]: must be a dictionary")
                continue

            item_id = item_data.get("id")
            if not item_id:
                errors.append(f"Inventory item [{i}]: missing required 'id' field")
                continue

            if not isinstance(item_id, str):
                errors.append(f"Inventory item [{i}]: 'id' must be a string")
                continue

            item_name = item_data.get("name")
            if not item_name:
                errors.append(f"Inventory item '{item_id}': missing required 'name' field")
                continue

            if not isinstance(item_name, str):
                errors.append(f"Inventory item '{item_id}': 'name' must be a string")
                continue

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
