"""Script validator for game scripts."""

import json

from pedre.actions.registry import ActionRegistry
from pedre.conditions.registry import ConditionRegistry
from pedre.events.registry import EventRegistry
from pedre.plugins.script.base import Script
from pedre.validators.base import ValidationResult, Validator


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

        # Find all script files
        script_files = list(self.path.glob("*_scripts.json"))

        if not script_files:
            return ValidationResult(
                errors=[],
                item_count=0,
                metadata={},
            )

        # Load and parse all scripts
        scripts: dict[str, Script] = {}
        validation_errors: list[str] = []

        for script_file in script_files:
            try:
                with script_file.open() as f:
                    script_data = json.load(f)

                # Parse scripts
                valid_keys = {"trigger", "conditions", "scene", "run_once", "actions", "on_condition_fail"}

                for script_name, script_def in script_data.items():
                    # Check for unknown keys
                    unknown_keys = set(script_def.keys()) - valid_keys
                    if unknown_keys:
                        validation_errors.append(
                            f"Script '{script_name}': unknown keys {sorted(unknown_keys)} "
                            f"(valid keys: {sorted(valid_keys)})"
                        )

                    script = Script(
                        trigger=script_def.get("trigger"),
                        conditions=script_def.get("conditions", []),
                        scene=script_def.get("scene"),
                        run_once=script_def.get("run_once", False),
                        actions=script_def.get("actions", []),
                        on_condition_fail=script_def.get("on_condition_fail", []),
                    )

                    scripts[script_name] = script

            except json.JSONDecodeError as e:
                validation_errors.append(f"Failed to parse {script_file.name}: {e}")
            except OSError as e:
                validation_errors.append(f"Failed to load {script_file.name}: {e}")

        # Validate all scripts
        errors = list(validation_errors)

        for script_name, script in scripts.items():
            # Validate trigger event
            if script.trigger:
                event_name = script.trigger.get("event")
                if not event_name:
                    errors.append(f"Script '{script_name}': trigger missing required 'event' key")
                elif not EventRegistry.is_registered(event_name):
                    errors.append(
                        f"Script '{script_name}': unknown event '{event_name}' "
                        f"(registered events: {', '.join(EventRegistry.get_all_types())})"
                    )
                else:
                    # Validate trigger filter keys
                    trigger_keys_set = EventRegistry.get_trigger_keys(event_name)
                    if trigger_keys_set is not None:
                        filter_keys = {k for k in script.trigger if k != "event"}
                        unknown_filter_keys = filter_keys - trigger_keys_set
                        if unknown_filter_keys:
                            errors.append(
                                f"Script '{script_name}': trigger has unknown filter keys "
                                f"{sorted(unknown_filter_keys)} for event '{event_name}' "
                                f"(valid keys: {sorted(trigger_keys_set)})"
                            )

            # Validate conditions
            for i, condition in enumerate(script.conditions):
                check_type = condition.get("check")
                if not check_type:
                    errors.append(f"Script '{script_name}': condition {i} missing required 'check' key")
                elif not ConditionRegistry.is_registered(check_type):
                    errors.append(
                        f"Script '{script_name}': unknown condition '{check_type}' "
                        f"(registered conditions: {', '.join(ConditionRegistry.get_all_types())})"
                    )
                else:
                    # Validate condition parameters
                    param_errors = ConditionRegistry.validate(check_type, condition)
                    errors.extend(
                        f"Script '{script_name}': condition {i} ({check_type}): {err}" for err in param_errors
                    )

            # Validate actions list is not empty
            if not script.actions:
                errors.append(f"Script '{script_name}': 'actions' list is empty")

            # Validate actions
            for i, action in enumerate(script.actions):
                action_type = action.get("type")
                if not action_type:
                    errors.append(f"Script '{script_name}': action {i} missing required 'type' key")
                elif not ActionRegistry.is_registered(action_type):
                    errors.append(
                        f"Script '{script_name}': unknown action type '{action_type}' "
                        f"(registered actions: {', '.join(ActionRegistry.get_all_types())})"
                    )
                else:
                    # Validate action parameters
                    param_errors = ActionRegistry.validate(action_type, action)
                    errors.extend(f"Script '{script_name}': action {i} ({action_type}): {err}" for err in param_errors)

            # Validate on_condition_fail actions
            for i, action in enumerate(script.on_condition_fail):
                action_type = action.get("type")
                if not action_type:
                    errors.append(f"Script '{script_name}': on_condition_fail action {i} missing required 'type' key")
                elif not ActionRegistry.is_registered(action_type):
                    errors.append(
                        f"Script '{script_name}': on_condition_fail action {i} has unknown type '{action_type}' "
                        f"(registered actions: {', '.join(ActionRegistry.get_all_types())})"
                    )
                else:
                    # Validate action parameters
                    param_errors = ActionRegistry.validate(action_type, action)
                    errors.extend(
                        f"Script '{script_name}': on_condition_fail action {i} ({action_type}): {err}"
                        for err in param_errors
                    )

        # Populate context with entity references from scripts
        for script_name, script in scripts.items():
            refs = {"npcs": set(), "waypoints": set(), "portals": set()}

            # Scan trigger for portal references
            if script.trigger and script.trigger.get("event") == "portal_entered":
                if "portal_name" in script.trigger:
                    refs["portals"].add(script.trigger["portal_name"])
                elif "portal" in script.trigger:  # Handle possible legacy/alternative key
                    refs["portals"].add(script.trigger["portal"])

            # Scan conditions for NPC references
            for condition in script.conditions:
                if "npc" in condition:
                    refs["npcs"].add(condition["npc"])

            # Scan actions for entity references
            for action in script.actions + script.on_condition_fail:
                action_type = action.get("type")

                # Move NPC action
                if action_type == "move_npc":
                    if "npcs" in action:
                        refs["npcs"].update(action["npcs"])
                    if "waypoint" in action:
                        refs["waypoints"].add(action["waypoint"])

                # Change scene action (spawn waypoint)
                elif action_type == "change_scene":
                    if "spawn_waypoint" in action:
                        refs["waypoints"].add(action["spawn_waypoint"])

                # Other NPC-related actions
                elif action_type in ["start_appear_animation", "start_disappear_animation"]:
                    if "npcs" in action:
                        refs["npcs"].update(action["npcs"])
                elif action_type in ["advance_dialog", "set_dialog_level", "set_current_npc"]:
                    if "npc" in action:
                        refs["npcs"].add(action["npc"])

            self.context.script_references[script_name] = refs

        # Calculate metadata
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
        """Validate that script references to NPCs, waypoints, and portals exist in maps.

        Returns:
            ValidationResult with cross-reference errors and metadata
        """
        errors = []
        all_npcs = self.context.get_all_npcs()
        all_waypoints = self.context.get_all_waypoints()
        all_portals = self.context.get_all_portals()

        for script_name, refs in self.context.script_references.items():
            # Validate NPC references
            errors.extend(
                f"Script '{script_name}': NPC '{npc_name}' not found in any map"
                for npc_name in refs.get("npcs", set())
                if npc_name and npc_name not in all_npcs
            )

            # Validate waypoint references
            errors.extend(
                f"Script '{script_name}': waypoint '{waypoint_name}' not found in any map"
                for waypoint_name in refs.get("waypoints", set())
                if waypoint_name and waypoint_name not in all_waypoints
            )

            # Validate portal references
            errors.extend(
                f"Script '{script_name}': portal '{portal_name}' not found in any map"
                for portal_name in refs.get("portals", set())
                if portal_name and portal_name not in all_portals
            )

        total_npc_refs = sum(len(refs.get("npcs", set())) for refs in self.context.script_references.values())
        total_waypoint_refs = sum(len(refs.get("waypoints", set())) for refs in self.context.script_references.values())
        total_portal_refs = sum(len(refs.get("portals", set())) for refs in self.context.script_references.values())

        return ValidationResult(
            errors=errors,
            item_count=len(self.context.script_references),
            metadata={
                "NPC references validated": total_npc_refs,
                "Waypoint references validated": total_waypoint_refs,
                "Portal references validated": total_portal_refs,
            },
        )
