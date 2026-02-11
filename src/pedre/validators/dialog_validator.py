"""Dialog validator for NPC dialogs."""

import json

from pedre.actions.registry import ActionRegistry
from pedre.conditions.registry import ConditionRegistry
from pedre.validators.base import ValidationResult, Validator


class DialogValidator(Validator):
    """Validates NPC dialog files."""

    @property
    def name(self) -> str:
        """Return validator name."""
        return "Dialogs"

    def validate(self) -> ValidationResult:
        """Validate all dialog files in the configured directory.

        Returns:
            ValidationResult with errors and metadata
        """
        if not self.path.exists():
            return ValidationResult(
                errors=[f"Dialogs directory not found: {self.path}"],
                item_count=0,
                metadata={},
            )

        # Find all dialog files (*_dialogs.json or *_dialog.json)
        dialog_files = list(self.path.glob("*_dialogs.json")) + list(self.path.glob("*_dialog.json"))

        if not dialog_files:
            return ValidationResult(
                errors=[],
                item_count=0,
                metadata={},
            )

        errors: list[str] = []
        total_dialogs = 0
        total_conditions = 0
        total_actions = 0

        for dialog_file in dialog_files:
            try:
                with dialog_file.open() as f:
                    data = json.load(f)

                # Validate structure: should be dict[str, dict[str | int, dict]]
                if not isinstance(data, dict):
                    errors.append(f"Dialog file '{dialog_file.name}': root must be a dictionary")
                    continue

                # Iterate through NPCs
                for npc_name, npc_dialogs in data.items():
                    if not isinstance(npc_dialogs, dict):
                        errors.append(
                            f"Dialog file '{dialog_file.name}': NPC '{npc_name}' dialogs must be a dictionary"
                        )
                        continue

                    # Iterate through dialog levels
                    for level, dialog_data in npc_dialogs.items():
                        total_dialogs += 1

                        if not isinstance(dialog_data, dict):
                            errors.append(f"Dialog '{npc_name}' level {level}: dialog data must be a dictionary")
                            continue

                        # Validate required 'text' field
                        if "text" not in dialog_data:
                            errors.append(f"Dialog '{npc_name}' level {level}: missing required 'text' field")
                        elif not isinstance(dialog_data["text"], list):
                            errors.append(f"Dialog '{npc_name}' level {level}: 'text' must be a list")
                        elif not dialog_data["text"]:
                            errors.append(f"Dialog '{npc_name}' level {level}: 'text' list cannot be empty")
                        else:
                            # Check all text items are strings
                            for i, text_item in enumerate(dialog_data["text"]):
                                if not isinstance(text_item, str):
                                    errors.append(
                                        f"Dialog '{npc_name}' level {level}: 'text[{i}]' must be a string, "
                                        f"got {type(text_item).__name__}"
                                    )

                        # Validate optional 'name' field
                        if "name" in dialog_data and not isinstance(dialog_data["name"], str):
                            errors.append(
                                f"Dialog '{npc_name}' level {level}: 'name' must be a string, "
                                f"got {type(dialog_data['name']).__name__}"
                            )

                        # Validate optional 'conditions' field
                        if "conditions" in dialog_data:
                            conditions = dialog_data["conditions"]
                            if not isinstance(conditions, list):
                                errors.append(f"Dialog '{npc_name}' level {level}: 'conditions' must be a list")
                            else:
                                total_conditions += len(conditions)
                                for i, condition in enumerate(conditions):
                                    if not isinstance(condition, dict):
                                        errors.append(
                                            f"Dialog '{npc_name}' level {level}: condition {i} must be a dictionary"
                                        )
                                        continue

                                    check_type = condition.get("check")
                                    if not check_type:
                                        errors.append(
                                            f"Dialog '{npc_name}' level {level}: "
                                            f"condition {i} missing required 'check' key"
                                        )
                                    elif not ConditionRegistry.is_registered(check_type):
                                        errors.append(
                                            f"Dialog '{npc_name}' level {level}: "
                                            f"condition {i} has unknown type '{check_type}' "
                                            f"(registered conditions: {', '.join(ConditionRegistry.get_all_types())})"
                                        )
                                    else:
                                        # Validate condition parameters
                                        param_errors = ConditionRegistry.validate(check_type, condition)
                                        errors.extend(
                                            f"Dialog '{npc_name}' level {level}: condition {i} ({check_type}): {err}"
                                            for err in param_errors
                                        )

                        # Validate optional 'on_condition_fail' field
                        if "on_condition_fail" in dialog_data:
                            on_condition_fail = dialog_data["on_condition_fail"]
                            if not isinstance(on_condition_fail, list):
                                errors.append(f"Dialog '{npc_name}' level {level}: 'on_condition_fail' must be a list")
                            else:
                                total_actions += len(on_condition_fail)
                                for i, action in enumerate(on_condition_fail):
                                    if not isinstance(action, dict):
                                        errors.append(
                                            f"Dialog '{npc_name}' level {level}: "
                                            f"on_condition_fail action {i} must be a dictionary"
                                        )
                                        continue

                                    action_type = action.get("type")
                                    if not action_type:
                                        errors.append(
                                            f"Dialog '{npc_name}' level {level}: "
                                            f"on_condition_fail action {i} missing required 'type' key"
                                        )
                                    elif not ActionRegistry.is_registered(action_type):
                                        errors.append(
                                            f"Dialog '{npc_name}' level {level}: "
                                            f"on_condition_fail action {i} has unknown type '{action_type}' "
                                            f"(registered actions: {', '.join(ActionRegistry.get_all_types())})"
                                        )
                                    else:
                                        # Validate action parameters
                                        param_errors = ActionRegistry.validate(action_type, action)
                                        errors.extend(
                                            f"Dialog '{npc_name}' level {level}: "
                                            f"on_condition_fail action {i} ({action_type}): {err}"
                                            for err in param_errors
                                        )

                        # Check for unknown keys
                        valid_keys = {"text", "name", "conditions", "on_condition_fail"}
                        unknown_keys = set(dialog_data.keys()) - valid_keys
                        if unknown_keys:
                            errors.append(
                                f"Dialog '{npc_name}' level {level}: unknown keys {sorted(unknown_keys)} "
                                f"(valid keys: {sorted(valid_keys)})"
                            )

            except json.JSONDecodeError as e:
                errors.append(f"Failed to parse {dialog_file.name}: {e}")
            except OSError as e:
                errors.append(f"Failed to load {dialog_file.name}: {e}")

        return ValidationResult(
            errors=errors,
            item_count=total_dialogs,
            metadata={
                "Total Conditions": total_conditions,
                "Total Actions": total_actions,
            },
        )
