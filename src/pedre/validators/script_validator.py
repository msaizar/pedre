"""Script validator for game scripts."""

import json
from typing import TYPE_CHECKING

from pedre.actions.registry import ActionParseError, ActionRegistry
from pedre.conditions.registry import ConditionParseError, ConditionRegistry
from pedre.events.registry import EventRegistry
from pedre.plugins.script.base import Script, ScriptTrigger
from pedre.types import EntityReference
from pedre.validators.base import ValidationResult, Validator

if TYPE_CHECKING:
    from pedre.conditions.base import Condition


class ScriptValidator(Validator):
    """Validates game script files."""

    @property
    def name(self) -> str:
        """Return validator name."""
        return "Scripts"

    def validate(self) -> ValidationResult:
        """Validate all script files in the configured directory.

        Returns:
            ValidationResult with errors and metadata
        """
        if not self.path.exists():
            return ValidationResult(
                errors=[f"Scripts directory not found: {self.path}"],
                item_count=0,
                metadata={},
            )

        script_files = list(self.path.glob("*_scripts.json"))

        if not script_files:
            return ValidationResult(errors=[], item_count=0, metadata={})

        scripts: dict[str, Script] = {}
        errors: list[str] = []

        for script_file in script_files:
            try:
                with script_file.open() as f:
                    script_data = json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"Failed to parse {script_file.name}: {e}")
                continue
            except OSError as e:
                errors.append(f"Failed to load {script_file.name}: {e}")
                continue

            for script_name, script_def in script_data.items():
                # ---- Parse trigger ----
                trigger_obj = None
                trigger_def = script_def.get("trigger")

                if trigger_def:
                    event_name = trigger_def.get("event")

                    if not event_name:
                        errors.append(f"Script '{script_name}': trigger missing required 'event' key")
                    elif not EventRegistry.is_registered(event_name):
                        errors.append(
                            f"Script '{script_name}': unknown event '{event_name}' "
                            f"(registered events: {', '.join(EventRegistry.get_all_names())})"
                        )
                    else:
                        event = EventRegistry.get(event_name)
                        trigger_keys = event.trigger_keys if event else None
                        filters = {k: v for k, v in trigger_def.items() if k != "event"}

                        if trigger_keys is not None:
                            unknown = set(filters) - trigger_keys
                            if unknown:
                                errors.append(
                                    f"Script '{script_name}': trigger has unknown filter keys "
                                    f"{sorted(unknown)} for event '{event_name}' "
                                    f"(valid keys: {sorted(trigger_keys)})"
                                )

                        trigger_obj = ScriptTrigger(
                            event_name=event_name,
                            filters=filters,
                        )

                parsed_conditions: list[Condition] = []

                for i, condition_def in enumerate(script_def.get("conditions", [])):
                    try:
                        condition_obj = ConditionRegistry.create(condition_def)
                        parsed_conditions.append(condition_obj)

                    except ConditionParseError as e:
                        errors.append(f"Script '{script_name}': condition {i}: {e}")

                parsed_actions = []
                for i, action_def in enumerate(script_def.get("actions", [])):
                    try:
                        action_obj = ActionRegistry.create(action_def)
                        parsed_actions.append(action_obj)
                    except ActionParseError as e:
                        errors.append(f"Script '{script_name}': action {i}: {e}")

                if not parsed_actions:
                    errors.append(f"Script '{script_name}': 'actions' list is empty")

                parsed_fail_actions = []
                for i, action_def in enumerate(script_def.get("on_condition_fail", [])):
                    try:
                        action_obj = ActionRegistry.create(action_def)
                        parsed_fail_actions.append(action_obj)
                    except ActionParseError as e:
                        errors.append(f"Script '{script_name}': on_condition_fail action {i}: {e}")

                script = Script(
                    trigger=trigger_obj,
                    conditions=parsed_conditions,
                    scene=script_def.get("scene"),
                    run_once=script_def.get("run_once", False),
                    actions=parsed_actions,
                    on_condition_fail=parsed_fail_actions,
                )

                scripts[script_name] = script

        for script_name, script in scripts.items():
            refs: set[EntityReference] = set()

            if script.scene:
                refs.add(EntityReference(type="map", name=script.scene))

            if script.trigger:
                refs.update(script.trigger.get_references())

            for condition in script.conditions:
                refs.update(condition.get_references())

            for action in script.actions:
                refs.update(action.get_references())

            for action in script.on_condition_fail:
                refs.update(action.get_references())

            self.context.script_references[script_name] = refs

        total_actions = sum(len(s.actions) for s in scripts.values())
        total_conditions = sum(len(s.conditions) for s in scripts.values())
        total_triggers = sum(1 for s in scripts.values() if s.trigger)

        return ValidationResult(
            errors=errors,
            item_count=len(scripts),
            metadata={
                "Total Actions": total_actions,
                "Total Conditions": total_conditions,
                "Scripts with Triggers": total_triggers,
            },
        )

    def validate_cross_references(self) -> ValidationResult:
        """Validate that script references to NPCs, waypoints, portals, interactive objects, and maps exist.

        Returns:
            ValidationResult containing cross-reference errors and metadata.
        """
        errors: list[str] = []

        all_npcs = self.context.get_all_npcs()
        all_waypoints = self.context.get_all_waypoints()
        all_portals = self.context.get_all_portals()
        all_maps = self.context.get_all_maps()
        all_interactive = self.context.get_all_interactive_objects()
        all_inventory_items = self.context.get_inventory_items()

        total_npc_refs = 0
        total_waypoint_refs = 0
        total_portal_refs = 0
        total_inventory_item_refs = 0

        for script_name, refs in self.context.script_references.items():
            npc_refs = {r.name for r in refs if r.type == "npc"}
            waypoint_refs = {r.name for r in refs if r.type == "waypoint"}
            portal_refs = {r.name for r in refs if r.type == "portal"}
            interactive_refs = {r.name for r in refs if r.type == "interactive_object"}
            map_refs = {r.name for r in refs if r.type == "map"}
            inventory_item_refs = {r.name for r in refs if r.type == "inventory_item"}

            total_npc_refs += len(npc_refs)
            total_waypoint_refs += len(waypoint_refs)
            total_portal_refs += len(portal_refs)
            total_inventory_item_refs += len(inventory_item_refs)

            # Map-scoped NPC validation
            if map_refs:
                scene_name = next(iter(map_refs))
                valid_npcs = self.context.get_map_npcs(scene_name)
                npc_scope_msg = f"map '{scene_name}'"
            else:
                valid_npcs = all_npcs
                npc_scope_msg = "any map"

            errors.extend(
                f"Script '{script_name}': NPC '{npc_name}' not found in {npc_scope_msg}"
                for npc_name in npc_refs
                if npc_name not in valid_npcs
            )

            errors.extend(
                f"Script '{script_name}': waypoint '{waypoint_name}' not found"
                for waypoint_name in waypoint_refs
                if waypoint_name not in all_waypoints
            )

            errors.extend(
                f"Script '{script_name}': portal '{portal_name}' not found"
                for portal_name in portal_refs
                if portal_name not in all_portals
            )

            errors.extend(
                f"Script '{script_name}': interactive object '{obj_name}' not found"
                for obj_name in interactive_refs
                if obj_name not in all_interactive
            )

            errors.extend(
                f"Script '{script_name}': target map '{map_name}' not found"
                for map_name in map_refs
                if map_name not in all_maps
            )

            errors.extend(
                f"Script '{script_name}': inventory item '{item_id}' not found in inventory_items.json"
                for item_id in inventory_item_refs
                if item_id not in all_inventory_items
            )

        return ValidationResult(
            errors=errors,
            item_count=len(self.context.script_references),
            metadata={
                "NPC references validated": total_npc_refs,
                "Waypoint references validated": total_waypoint_refs,
                "Portal references validated": total_portal_refs,
                "Inventory item references validated": total_inventory_item_refs,
            },
        )
