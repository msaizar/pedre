"""Script system for managing game scripts and event-driven sequences.

This module provides a powerful scripting system that allows game events, cutscenes, and
interactive sequences to be defined in JSON and executed dynamically. Scripts can be
triggered by game events, NPC interactions, or manual calls, and can chain together
complex sequences of actions.

The scripting system consists of:
- Script: Container for action sequences with trigger conditions and metadata
- ScriptManager: Loads scripts from JSON, registers event triggers, and executes sequences
- Integration with Actions: Scripts execute Action objects (dialog, movement, effects, etc.)
- Integration with Events: Scripts can be triggered by game events via EventBus

Key features:
- JSON-based script definitions for non-programmer content creation
- Event-driven triggers (dialog closed, NPC interacted, object touched, etc.)
- Conditional execution based on game state (NPC dialog levels, inventory, etc.)
- Action sequencing with automatic continuation when async actions complete
- Run-once scripts for one-time events
- Scene-restricted scripts that only run in specific maps
- Deferred condition checking to avoid race conditions
- Dialog text references to avoid duplication
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
1. Scripts are loaded from JSON files during game initialization
2. Event triggers are registered with the EventBus
3. When events occur, handlers check filters and trigger matching scripts
4. Scripts check conditions, validate scene restrictions, and run_once status
5. Action sequences execute frame-by-frame via update() calls
6. Completed scripts publish ScriptCompleteEvent for chaining

Integration with other systems:
- EventBus: Subscribes to game events for automatic script triggering
- ActionSequence: Executes actions from the actions module
- GameContext: Provides access to all managers for condition evaluation
"""

from __future__ import annotations

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
from pedre.systems.registry import SystemRegistry
from pedre.systems.script.base import Script, ScriptBaseManager, ScriptEvent
from pedre.systems.script.events import ScriptCompleteEvent

if TYPE_CHECKING:
    from pedre.events import Event
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@SystemRegistry.register
class ScriptManager(ScriptBaseManager):
    """Manages loading, triggering, and execution of scripted event sequences.

    The ScriptManager is the central system for the game's scripting engine. It loads
    scripts from JSON files, registers event triggers with the EventBus, evaluates
    conditions, and executes action sequences frame-by-frame.

    Key responsibilities:
    - Load and parse scripts from JSON files
    - Parse action data into Action objects
    - Register event triggers (dialog_closed, npc_interacted, etc.)
    - Evaluate script conditions (NPC dialog levels, inventory state, etc.)
    - Execute active scripts each frame via update()
    - Track run_once scripts
    - Handle deferred condition checking to avoid race conditions

    The manager maintains a registry of all loaded scripts and a list of currently
    active sequences. Scripts are triggered by events or manual calls, and their
    action sequences execute incrementally across multiple frames.

    Integration points:
    - EventBus: Subscribes to game events for automatic triggering
    - GameContext: Provides access to all managers for action execution and conditions
    - Action classes: Instantiates and executes actions from JSON data
    - NPC/Dialog/Inventory managers: Used for condition evaluation

    Attributes:
        event_bus: The EventBus for subscribing to and publishing events.
        scripts: Registry of all loaded scripts, keyed by script name.
        active_sequences: List of currently executing (script_name, ActionSequence) tuples.
        _pending_script_checks: Scripts queued for deferred condition checking.

    Example usage:
        # Initialize
        script_manager = ScriptManager()
        script_manager.setup(context, settings)

        # Load scripts from file
        script_manager.load_scripts("data/scripts.json", npc_dialog_data)

        # Game loop
        def update(delta_time):
            script_manager.update(delta_time)

        # Manual trigger
        script_manager.trigger_script("intro_cutscene")
    """

    name: ClassVar[str] = "script"
    dependencies: ClassVar[list[str]] = []

    # Class-level cache for per-scene script JSON data (lazy loaded).
    # Maps scene name to raw JSON data loaded from script files.
    _script_cache: ClassVar[dict[str, dict[str, Any]]] = {}

    def __init__(self) -> None:
        """Initialize script manager."""
        super().__init__()
        self.scripts: dict[str, Script] = {}
        self.active_sequences: list[tuple[str, ActionSequence]] = []
        self._pending_script_checks: list[str] = []  # Scripts to check conditions for after current update
        self._subscribed_events: set[str] = set()  # Track subscribed event types to avoid duplicates

    def setup(self, context: GameContext) -> None:
        """Set up the script system.

        Args:
            context: Game context containing all systems.
        """
        super().setup(context)
        self.context = context
        self._register_event_handlers()

    def cleanup(self) -> None:
        """Clean up script system resources."""
        self.context.event_bus.unregister_all(self)
        self.context.event_bus = None
        self.scripts.clear()
        self.active_sequences.clear()
        self._subscribed_events.clear()
        super().cleanup()

    def reset(self) -> None:
        """Reset script system for new game.

        Clears all scripts and active sequences while preserving system wiring.
        """
        self.context.event_bus.unregister_all(self)

        self.scripts.clear()
        self.active_sequences.clear()
        self._subscribed_events.clear()

    def get_scripts(self) -> dict[str, Script]:
        """Get scripts."""
        return self.scripts

    def get_save_state(self) -> dict[str, Any]:
        """Return serializable state for saving to disk.

        Saves lists of completed scripts and run-once scripts that have executed.
        Note: Active running scripts are NOT saved and will restart on load.
        """
        return {
            "completed_scripts": [name for name, script in self.scripts.items() if script.completed],
            "run_once_scripts": [name for name, script in self.scripts.items() if script.has_run],
        }

    def cache_scene_state(self, scene_name: str) -> dict[str, Any]:
        """Return state to cache during scene transitions."""
        return self.get_save_state()

    def restore_scene_state(self, scene_name: str, state: dict[str, Any]) -> None:
        """Restore cached state when returning to a scene."""
        self.restore_save_state(state)

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Restore script system state from save file.

        Restores completion flags and run-once history.
        """
        # Restore completed scripts
        if "completed_scripts" in state:
            for name in state["completed_scripts"]:
                if name in self.scripts:
                    self.scripts[name].completed = True
                else:
                    # We might load a save that has completion data for a script
                    # that isn't loaded yet (e.g. from another scene).
                    # Ideally we'd store this separately, but for now we warn/ignore
                    # or better: we can't easily set it on a script object that doesn't exist.
                    # However, since scripts are usually loaded per-scene or globally,
                    # we only care about scripts currently in memory.
                    pass

        # Restore run-once history (critical for not re-running one-time events)
        if "run_once_scripts" in state:
            for name in state["run_once_scripts"]:
                if name in self.scripts:
                    self.scripts[name].has_run = True

    def load_scripts(self, script_path: str, npc_dialogs: dict[str, Any]) -> None:
        """Load scripts from JSON file and register event triggers.

        Reads a JSON file containing script definitions, parses them into Script objects,
        and registers any event triggers with the EventBus. This is typically called once
        during game initialization.

        The JSON file should contain a dictionary where keys are script names and values
        are script definitions with optional trigger, conditions, scene, run_once, and
        actions fields.

        Args:
            script_path: Absolute or relative path to the script JSON file.
            npc_dialogs: Dictionary of NPC dialog data for resolving text_from references.
                        Format: {npc_name: {dialog_level: {"text": [...]}}}

        Example JSON structure:
            {
                "script_name": {
                    "trigger": {"event": "dialog_closed", "npc": "martin"},
                    "conditions": [{"check": "inventory_accessed", "equals": true}],
                    "scene": "village",
                    "run_once": true,
                    "actions": [...]
                }
            }
        """
        self._load_script_file(script_path, npc_dialogs)

    def load_scene_scripts(self, scene_name: str, npc_dialogs_data: dict[str, Any]) -> dict[str, Any]:
        """Load and cache scripts for a specific scene.

        Args:
            scene_name: Name of the scene (map file without extension).
            npc_dialogs_data: NPC dialog data for resolving text references.

        Returns:
            The loaded script data for the scene.
        """
        if scene_name in self._script_cache:
            self.load_scripts_from_data(self._script_cache[scene_name], npc_dialogs_data)
        else:
            try:
                scene_script_file = asset_path(f"scripts/{scene_name}_scripts.json", settings.ASSETS_HANDLE)
                self.load_scripts(scene_script_file, npc_dialogs_data)
                # Cache raw data
                with Path(scene_script_file).open() as f:
                    self._script_cache[scene_name] = json.load(f)
            except Exception:  # noqa: BLE001
                logger.debug("No scripts found for scene %s", scene_name)

        return self._script_cache.get(scene_name, {})

    def load_scripts_from_data(self, script_data: dict[str, Any], npc_dialogs: dict[str, Any]) -> None:
        """Load scripts from pre-loaded JSON data and register event triggers.

        Similar to load_scripts() but takes already-parsed JSON data instead of a file path.
        This is useful for loading from cached script data to avoid repeated file I/O.

        Args:
            script_data: Dictionary containing script definitions.
            npc_dialogs: Dictionary of NPC dialog data.
        """
        self._parse_scripts(script_data, npc_dialogs)
        self._register_event_handlers()

    def update(self, delta_time: float) -> None:
        """Update all active action sequences.

        Called each frame to update all currently executing script action sequences.
        Sequences that complete are removed from the active list.

        Args:
            delta_time: Time elapsed since the last frame, in seconds.
            context: Game context providing access to other systems.
        """
        if not self.context:
            return

        # Update active sequences
        completed_sequences = []
        for i, (script_name, sequence) in enumerate(self.active_sequences):
            if sequence.execute(self.context):
                completed_sequences.append(i)
                logger.debug("ScriptManager: Script '%s' completed", script_name)
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

    def trigger_script(self, script_name: str, *, manual_trigger: bool = False) -> bool:
        """Manually trigger a script by name.

        Args:
            script_name: Name of the script to trigger.
            manual_trigger: If True, bypasses scene and run_once restrictions.

        Returns:
            True if script was triggered, False if not found or conditions failed.
        """
        if not self.context:
            return False

        if script_name not in self.scripts:
            logger.warning("ScriptManager: Script '%s' not found", script_name)
            return False

        script = self.scripts[script_name]

        # Check scene restriction
        if not manual_trigger and script.scene and script.scene != self.context.scene_manager.get_current_scene():
            logger.debug(
                "ScriptManager: Script '%s' scene mismatch (need: %s, current: %s)",
                script_name,
                script.scene,
                self.context.scene_manager.get_current_scene(),
            )
            return False

        # Check run_once restriction
        if not manual_trigger and script.run_once and script.has_run:
            logger.debug("ScriptManager: Script '%s' already ran (run_once=True)", script_name)
            return False

        # Check conditions
        if not self._check_conditions(script.conditions):
            logger.debug("ScriptManager: Script '%s' conditions not met", script_name)
            return False

        # Execute script
        self._execute_script(script_name, script)

        # Mark as run if run_once
        if script.run_once:
            script.has_run = True

        return True

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
                logger.warning("ScriptManager: Event '%s' in script trigger is not registered", event_name)
                continue

            # Cast to proper type after None check - EventRegistry returns type | None
            event_type = cast("type[Event]", event_class)
            self.context.event_bus.subscribe(event_type, self._on_generic_event)
            self._subscribed_events.add(event_name)
            logger.debug("ScriptManager: Subscribed to '%s' for script triggers", event_name)

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

        logger.debug("ScriptManager: Handling event '%s' with data: %s", event_name, event_data)

        # Trigger scripts matching this event and data
        self._handle_event_trigger(event_name, event_data)

    def _load_script_file(self, script_path: str, npc_dialogs: dict[str, Any]) -> None:
        """Load scripts from JSON file.

        Args:
            script_path: Path to the script JSON file.
            npc_dialogs: Dictionary of NPC dialog data.
        """
        try:
            full_path = Path(script_path)
            if not full_path.exists():
                logger.error("ScriptManager: Script file not found: %s", script_path)
                return
            with Path(script_path).open() as f:
                script_data = json.load(f)

            self._parse_scripts(script_data, npc_dialogs)
            self._register_event_handlers()
            logger.info("ScriptManager: Loaded %d scripts from %s", len(self.scripts), script_path)

        except Exception:
            logger.exception("ScriptManager: Failed to load script file %s", script_path)

    def _parse_scripts(self, script_data: dict[str, Any], npc_dialogs: dict[str, Any]) -> None:
        """Parse script data into Script objects and register triggers.

        Args:
            script_data: Dictionary containing script definitions.
            npc_dialogs: Dictionary of NPC dialog data.
        """
        for script_name, script_def in script_data.items():
            script = Script(
                trigger=script_def.get("trigger"),
                conditions=script_def.get("conditions", []),
                scene=script_def.get("scene"),
                run_once=script_def.get("run_once", False),
                actions=script_def.get("actions", []),
                on_condition_fail=script_def.get("on_condition_fail", []),
            )

            # Process actions to resolve text_from references
            self._process_script_actions(script, npc_dialogs)

            self.scripts[script_name] = script

        logger.debug("ScriptManager: Parsed %d scripts", len(self.scripts))

    def _process_script_actions(self, script: Script, npc_dialogs: dict[str, Any]) -> None:
        """Process script actions to resolve text_from references.

        Args:
            script: Script object whose actions to process.
            npc_dialogs: Dictionary of NPC dialog data.
        """
        for action in script.actions:
            if action.get("type") == "dialog" and "text_from" in action:
                text_from = action["text_from"]
                if text_from in npc_dialogs:
                    # Use first dialog level's text
                    dialog_levels = npc_dialogs[text_from]
                    if dialog_levels:
                        first_level = next(iter(dialog_levels.values()))
                        if "text" in first_level:
                            action["text"] = first_level["text"]
                            del action["text_from"]
                        else:
                            logger.warning("ScriptManager: No text found for dialog reference: %s", text_from)
                    else:
                        logger.warning("ScriptManager: No dialog levels found for: %s", text_from)
                else:
                    logger.warning("ScriptManager: Dialog reference not found: %s", text_from)

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
            logger.warning("ScriptManager: Condition missing 'check' field")
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
                logger.warning("ScriptManager: Failed to parse action: %s", action_data)

        if actions:
            sequence = ActionSequence(actions)
            self.active_sequences.append((sequence_name, sequence))
            logger.info("ScriptManager: Executing '%s' with %d actions", sequence_name, len(actions))
        else:
            logger.warning("ScriptManager: '%s' has no valid actions", sequence_name)

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
                if script.scene and self.context and script.scene != self.context.scene_manager.get_current_scene():
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
                        "ScriptManager: Script '%s' conditions failed, executing on_condition_fail",
                        script_name,
                    )
                    self._execute_actions(f"{script_name}_fail", script.on_condition_fail)
                else:
                    logger.debug(
                        "ScriptManager: Script '%s' conditions failed, no on_condition_fail defined",
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

    def get_completed_scripts(self) -> list[str]:
        """Get names of all scripts that have fully completed.

        Returns:
            List of script names that have completed all actions.
        """
        return [name for name, script in self.scripts.items() if script.completed]

    def restore_completed_scripts(self, completed_scripts: list[str]) -> None:
        """Restore completed state for scripts.

        Args:
            completed_scripts: List of script names to mark as completed.
        """
        for name in completed_scripts:
            if name in self.scripts:
                self.scripts[name].completed = True
                self.scripts[name].has_run = True  # Also mark as run for run_once
            else:
                logger.warning("ScriptManager: Cannot restore unknown script: %s", name)
