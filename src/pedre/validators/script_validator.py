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
            refs: dict[str, set[str]] = {
                "npcs": set(),
                "waypoints": set(),
                "portals": set(),
                "interactive_objects": set(),
                "target_maps": set(),
            }
            # Store scene-scoped spawn waypoints: list of (target_map, waypoint) pairs
            spawn_waypoints: list[tuple[str, str]] = []

            # Store script scene for scoped validation
            if script.scene:
                refs["scene"] = {script.scene}

            # Scan trigger for entity references
            if script.trigger:
                event_name = script.trigger.get("event", "")

                # Portal triggers
                if event_name == "portal_entered":
                    if "portal_name" in script.trigger:
                        refs["portals"].add(script.trigger["portal_name"])
                    elif "portal" in script.trigger:
                        refs["portals"].add(script.trigger["portal"])

                # NPC-related event triggers
                if "npc" in script.trigger:
                    refs["npcs"].add(script.trigger["npc"])

                # Object interaction triggers
                if "object_name" in script.trigger:
                    refs["interactive_objects"].add(script.trigger["object_name"])

            # Scan conditions for entity references
            for condition in script.conditions:
                if "npc" in condition:
                    refs["npcs"].add(condition["npc"])
                if "object" in condition:
                    refs["interactive_objects"].add(condition["object"])
                if condition.get("check") == "npc_interacted" and "scene" in condition:
                    refs["target_maps"].add(condition["scene"])

            # Scan actions for entity references
            for action in script.actions + script.on_condition_fail:
                action_type = action.get("type")

                # NPC list actions
                if action_type in [
                    "move_npc",
                    "start_appear_animation",
                    "start_disappear_animation",
                    "wait_npcs_appear",
                    "wait_for_npcs_disappear",
                ]:
                    if "npcs" in action:
                        refs["npcs"].update(action["npcs"])
                    if "waypoint" in action:
                        refs["waypoints"].add(action["waypoint"])

                # Single NPC actions
                elif action_type in [
                    "advance_dialog",
                    "set_dialog_level",
                    "set_current_npc",
                    "follow_npc",
                    "wait_for_movement",
                ]:
                    if "npc" in action:
                        refs["npcs"].add(action["npc"])

                # Change scene action
                elif action_type == "change_scene":
                    target_map = action.get("target_map")
                    if target_map:
                        # Strip .tmx extension for consistency with map_entities keys
                        map_name = target_map.removesuffix(".tmx")
                        refs["target_maps"].add(map_name)
                        if "spawn_waypoint" in action:
                            spawn_waypoints.append((map_name, action["spawn_waypoint"]))

                # Emit particles action
                elif action_type == "emit_particles":
                    if "npc" in action:
                        refs["npcs"].add(action["npc"])
                    if "interactive_object" in action:
                        refs["interactive_objects"].add(action["interactive_object"])

            self.context.script_references[script_name] = refs
            # Store spawn waypoint pairs separately for target-map-scoped validation
            if spawn_waypoints:
                self.context.script_references[script_name]["_spawn_waypoints"] = set()
                self.context.script_references[script_name]["_spawn_waypoint_pairs"] = spawn_waypoints  # type: ignore[assignment]

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
        """Validate that script references to NPCs, waypoints, portals, etc. exist in maps.

        Returns:
            ValidationResult with cross-reference errors and metadata
        """
        errors: list[str] = []
        all_npcs = self.context.get_all_npcs()
        all_waypoints = self.context.get_all_waypoints()
        all_portals = self.context.get_all_portals()
        all_maps = self.context.get_all_maps()
        all_interactive = self.context.get_all_interactive_objects()

        for script_name, refs in self.context.script_references.items():
            # Determine NPC validation scope
            scene_set = refs.get("scene", set())
            if scene_set:
                scene_name = next(iter(scene_set))
                valid_npcs = self.context.get_map_npcs(scene_name)
                npc_scope_msg = f"map '{scene_name}'"
            else:
                valid_npcs = all_npcs
                npc_scope_msg = "any map"

            # Validate NPC references
            errors.extend(
                f"Script '{script_name}': NPC '{npc_name}' not found in {npc_scope_msg}"
                for npc_name in refs.get("npcs", set())
                if npc_name and npc_name not in valid_npcs
            )

            # Validate waypoint references (non-spawn waypoints, global check)
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

            # Validate interactive object references
            errors.extend(
                f"Script '{script_name}': interactive object '{obj_name}' not found in any map"
                for obj_name in refs.get("interactive_objects", set())
                if obj_name and obj_name not in all_interactive
            )

            # Validate target map references
            errors.extend(
                f"Script '{script_name}': target map '{map_name}' not found"
                for map_name in refs.get("target_maps", set())
                if map_name and map_name not in all_maps
            )

            # Validate spawn waypoints exist in their target maps
            spawn_pairs = refs.get("_spawn_waypoint_pairs", [])
            for target_map, waypoint in spawn_pairs:
                if target_map in all_maps:
                    target_waypoints = self.context.get_map_waypoints(target_map)
                    if waypoint not in target_waypoints:
                        errors.append(
                            f"Script '{script_name}': spawn_waypoint '{waypoint}' "
                            f"not found in target map '{target_map}'"
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
