"""Script plugin for managing game scripts and event-driven sequences.

This module provides a powerful scripting plugin that allows game events, cutscenes, and
interactive sequences to be defined in JSON and executed dynamically. Scripts can be
triggered by game events, NPC interactions, or manual calls, and can chain together
complex sequences of actions.

The scripting plugin consists of:
- Script: Container for action sequences with trigger conditions and metadata
- ScriptPlugin: Loads scripts from JSON, registers event triggers, and executes sequences
- Integration with Actions: Scripts execute Action objects (dialog, movement, effects, etc.)
- Integration with Events: Scripts can be triggered by game events via EventBus

Key features:
- JSON-based script definitions for non-programmer content creation
- Event-driven triggers (dialog closed, NPC interacted, object touched, etc.)
- Conditional execution based on game state (NPC dialog levels, inventory, etc.)
- Action sequencing with automatic continuation when async actions complete
- Run-once scripts for one-time events
- Scene-restricted scripts that only run in specific maps
- Global script loading for cross-scene condition checking
- Deferred condition checking to avoid race conditions
- Script chaining via script_complete events

Script anatomy:
{
  "script_name": {
    "trigger": {"event": "dialog_closed", "npc": "martin", "dialog_level": 1},
    "conditions": [{"check": "inventory_accessed", "equals": true}],
    "scene": "village",
    "run_once": true,
    "actions": [
      {"type": "dialog", "speaker": "martin", "text": ["Hello!"]},
      {"type": "wait_for_dialog_close"},
      {"type": "move_npc", "npcs": ["martin"], "waypoint": "town_square"}
    ]
  }
}

Workflow:
1. All scripts are loaded globally from the scripts directory during plugin setup
2. Event triggers are registered with the EventBus
3. When events occur, handlers check filters and trigger matching scripts
4. Scripts check conditions, validate scene restrictions, and run_once status
5. Action sequences execute frame-by-frame via update() calls
6. Completed scripts publish ScriptCompleteEvent for chaining

Integration with other plugins:
- EventBus: Subscribes to game events for automatic script triggering
- ActionSequence: Executes actions from the actions module
- GameContext: Provides access to all plugins for condition evaluation
"""

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.actions import ActionSequence
from pedre.actions.registry import ActionRegistry
from pedre.conditions.registry import ConditionRegistry
from pedre.conf import settings
from pedre.constants import asset_path
from pedre.events.registry import EventRegistry
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.script.base import Script, ScriptBasePlugin, ScriptEvent, ScriptValidationError
from pedre.plugins.script.events import ScriptCompleteEvent

if TYPE_CHECKING:
    from pedre.events import Event
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


@PluginRegistry.register
class ScriptPlugin(ScriptBasePlugin):
    """Manages loading, triggering, and execution of scripted event sequences.

    The ScriptPlugin is the central plugin for the game's scripting engine. It loads
    all scripts globally during setup, registers event triggers with the EventBus,
    evaluates conditions, and executes action sequences frame-by-frame.

    Key responsibilities:
    - Load all scripts globally from the scripts directory during setup
    - Parse action data into Action objects
    - Register event triggers (dialog_closed, npc_interacted, etc.)
    - Evaluate script conditions (NPC dialog levels, inventory state, etc.)
    - Execute active scripts each frame via update()
    - Track run_once scripts
    - Handle deferred condition checking to avoid race conditions

    The plugin maintains a registry of all loaded scripts (from all scenes) and a list
    of currently active sequences. Scripts are triggered by events or manual calls, and
    their action sequences execute incrementally across multiple frames. The scene field
    in each script definition controls when it can execute.

    Integration points:
    - EventBus: Subscribes to game events for automatic triggering
    - GameContext: Provides access to all plugins for action execution and conditions
    - Action classes: Instantiates and executes actions from JSON data
    - Condition plugin: Used for condition evaluation across all plugins

    Attributes:
        scripts: Registry of all loaded scripts (from all scenes), keyed by script name.
        active_sequences: List of currently executing (script_name, ActionSequence) tuples.
        _pending_script_checks: Scripts queued for deferred condition checking.
        _subscribed_events: Set of event types subscribed to (prevents duplicate handlers).

    Example usage:
        # Initialize (loads all scripts globally)
        script_plugin = ScriptPlugin()
        script_plugin.setup(context)

        # Game loop
        def update(delta_time):
            script_plugin.update(delta_time)

    """

    name: ClassVar[str] = "script"
    dependencies: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """Initialize script plugin."""
        super().__init__()
        self.scripts: dict[str, Script] = {}
        self.active_sequences: list[tuple[str, ActionSequence]] = []
        self._pending_script_checks: list[str] = []  # Scripts to check conditions for after current update
        self._subscribed_events: set[str] = set()  # Track subscribed event types to avoid duplicates
        self._validation_errors: list[str] = []  # Collects validation errors during script parsing

    def setup(self, context: GameContext) -> None:
        """Set up the script plugin.

        Loads all scripts globally from the scripts directory so they're available
        for conditions across all scenes.

        Args:
            context: Game context containing all plugins.
        """
        super().setup(context)

        # Load all scripts globally at initialization
        self._load_all_scripts()

        self._register_event_handlers()

    def cleanup(self) -> None:
        """Clean up script plugin resources."""
        self.context.event_bus.unregister_all(self)
        self.context.event_bus = None
        self.scripts.clear()
        self.active_sequences.clear()
        self._subscribed_events.clear()
        super().cleanup()

    def reset(self) -> None:
        """Reset script plugin for new game.

        Clears all runtime state (active sequences, completion flags) and reloads
        all scripts from disk so the plugin is ready for a new or loaded game.
        """
        self.context.event_bus.unregister_all(self)

        self.scripts.clear()
        self.active_sequences.clear()
        self._subscribed_events.clear()
        self._validation_errors.clear()

        # Reload all scripts and re-register event handlers so the plugin
        # is functional after reset (needed for both new games and loaded games).
        self._load_all_scripts()
        self._register_event_handlers()

    def get_scripts(self) -> dict[str, Script]:
        """Get scripts."""
        return self.scripts

    def get_save_state(self) -> dict[str, Any]:
        """Return serializable state for saving to disk.

        Saves lists of completed scripts, run-once scripts that have executed,
        and currently active script sequences with their progress.
        """
        active = []
        for script_name, sequence in self.active_sequences:
            is_fail = script_name.endswith("_fail")
            base_name = script_name[:-5] if is_fail else script_name
            active.append(
                {
                    "script_name": base_name,
                    "current_index": sequence.current_index,
                    "is_fail_sequence": is_fail,
                }
            )

        return {
            "completed_scripts": [name for name, script in self.scripts.items() if script.completed],
            "run_once_scripts": [name for name, script in self.scripts.items() if script.has_run],
            "active_scripts": active,
        }

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Restore script plugin state from save file.

        Restores completion flags, run-once history, and active script sequences.
        """
        # Clear any existing active sequences (important for quick-load where reset() isn't called)
        self.active_sequences.clear()

        # Restore completed scripts
        if "completed_scripts" in state:
            for name in state["completed_scripts"]:
                if name in self.scripts:
                    self.scripts[name].completed = True

        # Restore run-once history (critical for not re-running one-time events)
        if "run_once_scripts" in state:
            for name in state["run_once_scripts"]:
                if name in self.scripts:
                    self.scripts[name].has_run = True

        # Restore active scripts
        self._restore_active_scripts(state.get("active_scripts", []))

    def _restore_active_scripts(self, active_scripts_data: list[dict[str, Any]]) -> None:
        """Restore active script sequences from save data.

        Re-parses actions from the script's JSON data and resumes execution
        at the appropriate action index, backing up past wait actions so that
        initiating actions (like move_npc) re-execute and async operations
        restart from the saved entity state.

        Args:
            active_scripts_data: List of dicts with script_name, current_index,
                and is_fail_sequence keys.
        """
        for entry in active_scripts_data:
            script_name = entry["script_name"]
            saved_index = entry["current_index"]
            is_fail = entry.get("is_fail_sequence", False)

            script = self.scripts.get(script_name)
            if not script:
                logger.warning("Cannot restore active script '%s': not found", script_name)
                continue

            action_data_list = script.on_condition_fail if is_fail else script.actions
            if not action_data_list:
                continue

            # Parse actions from JSON
            actions = []
            for action_data in action_data_list:
                action = ActionRegistry.parse(action_data)
                if action:
                    actions.append(action)

            if not actions:
                continue

            # Calculate resume index (back up past wait actions)
            resume_index = self._calculate_resume_index(action_data_list, saved_index)
            resume_index = min(resume_index, len(actions))

            sequence = ActionSequence(actions)
            sequence.current_index = resume_index

            sequence_name = f"{script_name}_fail" if is_fail else script_name
            self.active_sequences.append((sequence_name, sequence))
            logger.info(
                "Restored active script '%s' at action %d (saved: %d)",
                sequence_name,
                resume_index,
                saved_index,
            )

    def _calculate_resume_index(self, actions: list[dict[str, Any]], saved_index: int) -> int:
        """Find the best action index to resume from after loading.

        If the saved action is a wait action, backs up to the preceding
        non-wait action so initiating actions (like move_npc) re-execute
        and async operations restart properly.

        Args:
            actions: List of action data dicts from the script definition.
            saved_index: The action index that was executing when the game was saved.

        Returns:
            The adjusted index to resume execution from.
        """
        resume_index = saved_index
        while resume_index > 0:
            action_type = actions[resume_index].get("type", "")
            if not action_type.startswith("wait_"):
                break
            resume_index -= 1
        return resume_index

    def _load_all_scripts(self) -> None:
        """Load all scripts from the scripts directory.

        Scans the scripts directory for all *_scripts.json files and loads them globally.
        This makes all scripts available for conditions regardless of the current scene.
        The scene field in each script definition controls when it can actually execute.

        Raises:
            ScriptValidationError: If any validation errors are found after loading scripts.
        """
        try:
            scripts_dir = Path(asset_path(settings.SCRIPTS_DIRECTORY, settings.ASSETS_HANDLE))
            if not scripts_dir.exists():
                logger.warning("Scripts directory not found: %s", scripts_dir)
                return

            # Find all script files
            script_files = list(scripts_dir.glob("*_scripts.json"))
            if not script_files:
                logger.info("No script files found in %s", scripts_dir)
                return

            # Clear validation errors from any previous load
            self._validation_errors.clear()

            # Load each script file
            for script_file in script_files:
                try:
                    with script_file.open() as f:
                        script_data = json.load(f)

                    # Parse scripts and merge into global registry
                    self._parse_scripts(script_data)

                    logger.info("Loaded %d scripts from %s", len(script_data), script_file.name)

                except json.JSONDecodeError:
                    logger.exception("Failed to parse script JSON from %s", script_file)
                except Exception:
                    logger.exception("Failed to load script file %s", script_file)

            logger.info("Total scripts loaded globally: %d", len(self.scripts))

            # Validate all loaded scripts
            self.validate_scripts()

        except ScriptValidationError:
            # Re-raise validation errors
            raise
        except Exception:
            logger.exception("Failed to load scripts from directory")

    def update(self, delta_time: float) -> None:
        """Update all active action sequences.

        Called each frame to update all currently executing script action sequences.
        Sequences that complete are removed from the active list.

        Args:
            delta_time: Time elapsed since the last frame, in seconds.
            context: Game context providing access to other plugins.
        """
        if not self.context:
            return

        # Update active sequences
        completed_sequences = []
        for i, (script_name, sequence) in enumerate(self.active_sequences):
            if sequence.execute(self.context):
                completed_sequences.append(i)
                logger.debug("ScriptPlugin: Script '%s' completed", script_name)
                # Mark script as completed
                if script_name in self.scripts:
                    self.scripts[script_name].completed = True
                # Publish completion event for chaining
                self.context.event_bus.publish(ScriptCompleteEvent(script_name))

        # Remove completed sequences (in reverse order to maintain indices)
        for i in reversed(completed_sequences):
            script_name, _ = self.active_sequences.pop(i)

        # Process any pending script condition checks
        if self._pending_script_checks:
            self._process_pending_checks()

    def _register_event_handlers(self) -> None:
        """Register event handlers for all events triggered by loaded scripts."""
        # Identify all unique events required by loaded scripts
        required_events = set()
        for script in self.scripts.values():
            if script.trigger and "event" in script.trigger:
                required_events.add(script.trigger["event"])

        # Subscribe to all required events using the generic handler
        # Skip events we've already subscribed to avoid duplicate handlers
        for event_name in required_events:
            if event_name in self._subscribed_events:
                continue

            event_class = EventRegistry.get(event_name)
            if not event_class:
                logger.warning("ScriptPlugin: Event '%s' in script trigger is not registered", event_name)
                continue

            # Cast to proper type after None check - EventRegistry returns type | None
            event_type = cast("type[Event]", event_class)
            self.context.event_bus.subscribe(event_type, self._on_generic_event)
            self._subscribed_events.add(event_name)
            logger.debug("ScriptPlugin: Subscribed to '%s' for script triggers", event_name)

    def _on_generic_event(self, event: Event) -> None:
        """Generic event handler for any registered event.

        Extracts event logic by calling event.get_script_data() if available,
        otherwise falls back to dataclass conversion.

        Args:
            event: The event instance that occurred.
        """
        event_name = EventRegistry.get_name(type(event))
        if not event_name:
            return

        # Extract data using the protocol if available
        # cast to ScriptEvent to satisfy type checker for get_script_data call
        script_event = cast("ScriptEvent", event)
        event_data = script_event.get_script_data() if hasattr(event, "get_script_data") else asdict(event)

        logger.debug("ScriptPlugin: Handling event '%s' with data: %s", event_name, event_data)

        # Trigger scripts matching this event and data
        self._handle_event_trigger(event_name, event_data)

    def _parse_scripts(self, script_data: dict[str, Any]) -> None:
        """Parse script data into Script objects and register triggers.

        Args:
            script_data: Dictionary containing script definitions.
        """
        # Valid top-level keys for script definitions
        valid_keys = {"trigger", "conditions", "scene", "run_once", "actions", "on_condition_fail"}

        for script_name, script_def in script_data.items():
            # Check for unknown keys
            unknown_keys = set(script_def.keys()) - valid_keys
            if unknown_keys:
                self._validation_errors.append(
                    f"Script '{script_name}': unknown keys {sorted(unknown_keys)} (valid keys: {sorted(valid_keys)})"
                )

            script = Script(
                trigger=script_def.get("trigger"),
                conditions=script_def.get("conditions", []),
                scene=script_def.get("scene"),
                run_once=script_def.get("run_once", False),
                actions=script_def.get("actions", []),
                on_condition_fail=script_def.get("on_condition_fail", []),
            )

            self.scripts[script_name] = script

        logger.debug("ScriptPlugin: Parsed %d scripts", len(self.scripts))

    def _check_conditions(self, conditions: list[dict[str, Any]]) -> bool:
        """Check if all conditions are satisfied.

        Args:
            conditions: List of condition dictionaries.

        Returns:
            True if all conditions are satisfied, False otherwise.
        """
        if not self.context:
            return False

        return all(self._check_single_condition(condition) for condition in conditions)

    def _check_single_condition(self, condition: dict[str, Any]) -> bool:
        """Check a single condition.

        Args:
            condition: Dictionary defining the condition.

        Returns:
            True if condition is satisfied, False otherwise.
        """
        if not self.context:
            return False

        check_type = condition.get("check")
        if not check_type:
            logger.warning("ScriptPlugin: Condition missing 'check' field")
            return False

        # Delegate to ConditionRegistry
        return ConditionRegistry.check(check_type, condition, self.context)

    def _execute_script(self, script_name: str, script: Script) -> None:
        """Execute a script's action sequence.

        Args:
            script_name: Name of the script being executed.
            script: Script object to execute.
        """
        self._execute_actions(script_name, script.actions)

    def _execute_actions(self, sequence_name: str, action_data_list: list[dict[str, Any]]) -> None:
        """Execute a list of actions as a sequence.

        Args:
            sequence_name: Name for the sequence (for logging).
            action_data_list: List of action dictionaries to execute.
        """
        if not self.context:
            return

        # Parse actions into Action objects
        actions = []
        for action_data in action_data_list:
            action = ActionRegistry.parse(action_data)
            if action:
                actions.append(action)
            else:
                logger.warning("ScriptPlugin: Failed to parse action: %s", action_data)

        if actions:
            sequence = ActionSequence(actions)
            self.active_sequences.append((sequence_name, sequence))
            logger.info("ScriptPlugin: Executing '%s' with %d actions", sequence_name, len(actions))
        else:
            logger.warning("ScriptPlugin: '%s' has no valid actions", sequence_name)

    def _process_pending_checks(self) -> None:
        """Process scripts that were queued for deferred condition checking."""
        if not self.context or not self._pending_script_checks:
            return

        pending_checks = list(self._pending_script_checks)
        self._pending_script_checks.clear()

        for script_name in pending_checks:
            if script_name in self.scripts:
                script = self.scripts[script_name]
                if self._check_conditions(script.conditions):
                    self._execute_script(script_name, script)
                    if script.run_once:
                        script.has_run = True

    def _handle_event_trigger(self, event_type: str, event_data: dict[str, Any]) -> None:
        """Handle an event trigger by checking all scripts for matching triggers.

        Args:
            event_type: Type of the event that occurred.
            event_data: Dictionary containing event-specific data.
        """
        for script_name, script in self.scripts.items():
            if not script.trigger:
                continue

            # Check if trigger matches this event
            if self._trigger_matches_event(script.trigger, event_type, event_data):
                # Check scene restriction
                if script.scene and self.context and script.scene != self.context.scene_plugin.get_current_scene():
                    continue

                # Check run_once restriction
                if script.run_once and script.has_run:
                    continue

                # Check conditions
                if self._check_conditions(script.conditions):
                    self._execute_script(script_name, script)
                    if script.run_once:
                        script.has_run = True
                elif script.on_condition_fail:
                    # Conditions failed - execute on_condition_fail actions
                    logger.debug(
                        "ScriptPlugin: Script '%s' conditions failed, executing on_condition_fail",
                        script_name,
                    )
                    self._execute_actions(f"{script_name}_fail", script.on_condition_fail)
                else:
                    logger.debug(
                        "ScriptPlugin: Script '%s' conditions failed, no on_condition_fail defined",
                        script_name,
                    )

    def _trigger_matches_event(self, trigger: dict[str, Any], event_type: str, event_data: dict[str, Any]) -> bool:
        """Check if a script trigger matches an event.

        Args:
            trigger: Script trigger definition.
            event_type: Type of the event.
            event_data: Event-specific data.

        Returns:
            True if trigger matches the event, False otherwise.
        """
        if trigger.get("event") != event_type:
            return False

        # Check additional filters
        for key, value in trigger.items():
            if key == "event":
                continue
            if event_data.get(key) != value:
                return False

        return True

    def validate_scripts(self) -> None:
        """Validate all loaded scripts against registered events, conditions, and actions.

        Checks that:
        - All trigger events are registered in EventRegistry
        - All conditions have valid "check" types registered in ConditionRegistry
        - All actions have valid "type" values registered in ActionRegistry
        - Each script has at least one action in its actions list

        Raises:
            ScriptValidationError: If any validation errors are found. The exception
                contains a list of all error messages.
        """
        errors = list(self._validation_errors)  # Include any errors from parsing

        for script_name, script in self.scripts.items():
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

        if errors:
            raise ScriptValidationError(errors)
