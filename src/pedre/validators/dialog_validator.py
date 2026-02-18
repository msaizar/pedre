"""Dialog validator for NPC dialogs."""

import json
from typing import TYPE_CHECKING, Any

from pedre.actions.registry import ActionParseError, ActionRegistry
from pedre.conditions.registry import ConditionParseError, ConditionRegistry
from pedre.types import EntityReference
from pedre.validators.base import ValidationResult, Validator

if TYPE_CHECKING:
    from pedre.actions.base import Action
    from pedre.conditions.base import Condition


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

        dialog_files = list(self.path.glob("*_dialogs.json")) + list(self.path.glob("*_dialog.json"))

        if not dialog_files:
            return ValidationResult(errors=[], item_count=0, metadata={})

        errors: list[str] = []
        total_dialogs = 0
        total_conditions = 0
        total_actions = 0

        for dialog_file in dialog_files:
            try:
                with dialog_file.open() as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"Failed to parse {dialog_file.name}: {e}")
                continue
            except OSError as e:
                errors.append(f"Failed to load {dialog_file.name}: {e}")
                continue

            if not isinstance(data, dict):
                errors.append(f"Dialog file '{dialog_file.name}': root must be a dictionary")
                continue

            scene_name = dialog_file.stem.replace("_dialogs", "").replace("_dialog", "")

            for npc_name, npc_dialogs in data.items():
                if not isinstance(npc_dialogs, dict):
                    errors.append(f"Dialog file '{dialog_file.name}': NPC '{npc_name}' dialogs must be a dictionary")
                    continue

                for level, dialog_data in npc_dialogs.items():
                    total_dialogs += 1

                    if not isinstance(dialog_data, dict):
                        errors.append(f"Dialog '{npc_name}' level {level}: dialog data must be a dictionary")
                        continue

                    # ---- Validate text ----
                    text = dialog_data.get("text")
                    if not isinstance(text, list) or not text:
                        errors.append(f"Dialog '{npc_name}' level {level}: 'text' must be a non-empty list")
                        continue

                    for i, line in enumerate(text):
                        if not isinstance(line, str):
                            errors.append(f"Dialog '{npc_name}' level {level}: text[{i}] must be string")

                    # ---- Validate name ----
                    if (
                        "name" in dialog_data
                        and dialog_data["name"] is not None
                        and not isinstance(dialog_data["name"], str)
                    ):
                        errors.append(f"Dialog '{npc_name}' level {level}: 'name' must be string or null")

                    # ---- Parse conditions ----
                    parsed_conditions: list[Condition] = []
                    conditions_raw: list[dict[str, Any]] = dialog_data.get("conditions") or []

                    if conditions_raw and not isinstance(conditions_raw, list):
                        errors.append(f"Dialog '{npc_name}' level {level}: 'conditions' must be a list")
                    else:
                        for i, condition_def in enumerate(conditions_raw):
                            try:
                                condition_obj = ConditionRegistry.create(condition_def)
                                parsed_conditions.append(condition_obj)
                            except ConditionParseError as e:
                                errors.append(f"Dialog '{npc_name}' level {level}: condition {i}: {e}")

                    total_conditions += len(parsed_conditions)

                    # ---- Parse on_condition_fail ----
                    parsed_actions: list[Action] = []
                    fail_raw: list[dict[str, Any]] = dialog_data.get("on_condition_fail") or []

                    if fail_raw and not isinstance(fail_raw, list):
                        errors.append(f"Dialog '{npc_name}' level {level}: 'on_condition_fail' must be a list")
                    else:
                        for i, action_def in enumerate(fail_raw):
                            try:
                                action_obj = ActionRegistry.create(action_def)
                                parsed_actions.append(action_obj)
                            except ActionParseError as e:
                                errors.append(f"Dialog '{npc_name}' level {level}: on_condition_fail action {i}: {e}")

                    total_actions += len(parsed_actions)

                    # ---- Collect references ----
                    refs: set[EntityReference] = set()

                    refs.add(EntityReference(type="map", name=scene_name))
                    refs.add(EntityReference(type="npc", name=npc_name))

                    for condition in parsed_conditions:
                        refs.update(condition.get_references())

                    for action in parsed_actions:
                        refs.update(action.get_references())

                    self.context.dialog_references[(scene_name, npc_name, str(level))] = refs

        return ValidationResult(
            errors=errors,
            item_count=total_dialogs,
            metadata={
                "Total Conditions": total_conditions,
                "Total Actions": total_actions,
            },
        )

    def validate_cross_references(self) -> ValidationResult:
        """Validate that dialog NPCs exist in corresponding maps.

        Returns:
            ValidationResult with cross-reference errors and metadata
        """
        errors: list[str] = []

        for scene_name, npc_name, level in self.context.dialog_references:
            map_npcs = self.context.get_map_npcs(scene_name)

            if npc_name not in map_npcs:
                errors.append(
                    f"Dialog '{scene_name}' NPC '{npc_name}' (level {level}) not found in map '{scene_name}.tmx'"
                )

        return ValidationResult(
            errors=errors,
            item_count=len(self.context.dialog_references),
            metadata={
                "Dialog entries validated": len(self.context.dialog_references),
            },
        )
