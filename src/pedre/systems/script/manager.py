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
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from pedre.systems.action_registry import ActionRegistry
from pedre.systems.actions import (
    ActionSequence,
)
from pedre.systems.base import BaseSystem
from pedre.systems.dialog import DialogClosedEvent
from pedre.systems.events import (
    EventBus,
    GameStartEvent,
    MapTransitionEvent,
    SceneStartEvent,
)
from pedre.systems.interaction import ObjectInteractedEvent
from pedre.systems.inventory import InventoryClosedEvent, ItemAcquiredEvent
from pedre.systems.npc import (
    NPCInteractedEvent,
    NPCMovementCompleteEvent,
)
from pedre.systems.portal import PortalEnteredEvent
from pedre.systems.registry import SystemRegistry
from pedre.systems.script.events import ScriptCompleteEvent

if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@dataclass
class Script:
    """Represents a game script with triggers, conditions, and actions.

    A script encapsulates a sequence of actions that can be triggered by events
    or manual calls. Scripts support conditional execution, scene restrictions,
    and one-time execution for story progression control.

    Attributes:
        trigger: Event specification that triggers this script.
        conditions: List of condition dictionaries that must all be true.
        scene: Optional scene name where this script can run.
        run_once: If True, script only executes once per game session.
        actions: List of action dictionaries to execute in sequence.
        has_run: Tracks if this script has already executed (for run_once).
    """

    trigger: dict[str, Any] | None = None
    conditions: list[dict[str, Any]] = field(default_factory=list)
    scene: str | None = None
    run_once: bool = False
    actions: list[dict[str, Any]] = field(default_factory=list)
    has_run: bool = False


@SystemRegistry.register
class ScriptManager(BaseSystem):
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
    - Track run_once scripts and object interactions
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
        interacted_objects: Set of object names that have been interacted with.
        _current_context: Cached GameContext for event handlers to access.
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

    def __init__(self) -> None:
        """Initialize script manager."""
        super().__init__()
        self.event_bus: EventBus | None = None
        self.scripts: dict[str, Script] = {}
        self.active_sequences: list[tuple[str, ActionSequence]] = []
        self._current_context: GameContext | None = None
        self.interacted_objects: set[str] = set()  # Track which objects have been interacted with
        self._pending_script_checks: list[str] = []  # Scripts to check conditions for after current update

    def setup(self, context: GameContext, settings: GameSettings) -> None:
        """Set up the script system.

        Args:
            context: Game context containing all systems.
            settings: Game configuration.
        """
        super().setup(context, settings)
        self.event_bus = context.event_bus
        self._register_event_handlers()

    def cleanup(self) -> None:
        """Clean up script system resources."""
        if self.event_bus:
            # Unregister all event handlers
            self.event_bus.unregister_all(self)
        self.event_bus = None
        self.scripts.clear()
        self.active_sequences.clear()
        self._current_context = None
        super().cleanup()

    def get_state(self) -> dict[str, Any]:
        """Get script system state for saving.

        Returns:
            Dictionary containing current script system state.
        """
        return {
            "interacted_objects": list(self.interacted_objects),
            "active_scripts": [name for name, _ in self.active_sequences],
        }

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restore script system state from saved data.

        Args:
            state: Dictionary containing saved script system state.
        """
        self.interacted_objects = set(state.get("interacted_objects", []))
        # Note: active_scripts are not restored as they should restart on load

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

    def load_scripts_from_data(self, script_data: dict[str, Any], npc_dialogs: dict[str, Any]) -> None:
        """Load scripts from pre-loaded JSON data and register event triggers.

        Similar to load_scripts() but takes already-parsed JSON data instead of a file path.
        This is useful for loading from cached script data to avoid repeated file I/O.

        Args:
            script_data: Dictionary containing script definitions.
            npc_dialogs: Dictionary of NPC dialog data for resolving text_from references.
        """
        self._parse_scripts(script_data, npc_dialogs)

    def update(self, delta_time: float) -> None:
        """Update all active action sequences.

        Called each frame to update all currently executing script action sequences.
        Sequences that complete are removed from the active list.

        Args:
            delta_time: Time elapsed since last update (unused but kept for consistency).
        """
        if not self.context:
            return

        # Update active sequences
        completed_sequences = []
        for i, (script_name, sequence) in enumerate(self.active_sequences):
            if sequence.execute(self.context):
                completed_sequences.append(i)
                logger.debug("ScriptManager: Script '%s' completed", script_name)
                # Publish completion event for chaining
                if self.event_bus:
                    self.event_bus.publish(ScriptCompleteEvent(script_name))

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
        if not manual_trigger and script.scene and script.scene != self.context.scene_name:
            logger.debug(
                "ScriptManager: Script '%s' scene mismatch (need: %s, current: %s)",
                script_name,
                script.scene,
                self.context.scene_name,
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

    def object_interacted(self, object_name: str) -> None:
        """Mark an object as interacted with.

        This method should be called whenever the player interacts with an object.
        It tracks interactions for script conditions that check if an object
        has been interacted with.

        Args:
            object_name: Name of the object that was interacted with.
        """
        self.interacted_objects.add(object_name)
        logger.debug("ScriptManager: Object '%s' marked as interacted", object_name)

    def has_interacted_with(self, object_name: str) -> bool:
        """Check if an object has been interacted with.

        Args:
            object_name: Name of the object to check.

        Returns:
            True if the object has been interacted with, False otherwise.
        """
        return object_name in self.interacted_objects

    def _register_event_handlers(self) -> None:
        """Register event handlers with the EventBus."""
        if not self.event_bus:
            return

        # Register handlers for all relevant events

        handlers = {
            GameStartEvent: self._on_game_start,
            SceneStartEvent: self._on_scene_start,
            DialogClosedEvent: self._on_dialog_closed,
            NPCInteractedEvent: self._on_npc_interacted,
            NPCMovementCompleteEvent: self._on_npc_movement_complete,
            ObjectInteractedEvent: self._on_object_interacted,
            PortalEnteredEvent: self._on_portal_entered,
            ItemAcquiredEvent: self._on_item_acquired,
            InventoryClosedEvent: self._on_inventory_closed,
            MapTransitionEvent: self._on_map_transition,
            ScriptCompleteEvent: self._on_script_complete,
        }

        for event_type, handler in handlers.items():
            self.event_bus.subscribe(event_type, handler)

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
        check_type = condition.get("check")
        expected = condition.get("equals")

        if check_type == "inventory_accessed":
            if not self.context.inventory_manager:
                return False
            result = self.context.inventory_manager.has_been_accessed
        elif check_type == "npc_interacted":
            npc_name = condition.get("npc")
            if not npc_name or not self.context.npc_manager:
                return False
            result = self.context.npc_manager.has_npc_been_interacted_with(npc_name)
        elif check_type == "object_interacted":
            object_name = condition.get("object")
            if not object_name:
                return False
            result = self.has_interacted_with(object_name)
        else:
            logger.warning("ScriptManager: Unknown condition type: %s", check_type)
            return False

        return result == expected

    def _execute_script(self, script_name: str, script: Script) -> None:
        """Execute a script's action sequence.

        Args:
            script_name: Name of the script being executed.
            script: Script object to execute.
        """
        if not self.context:
            return

        # Parse actions into Action objects
        actions = []
        for action_data in script.actions:
            action = ActionRegistry.parse_action(action_data)
            if action:
                actions.append(action)
            else:
                logger.warning("ScriptManager: Failed to parse action: %s", action_data)

        if actions:
            sequence = ActionSequence(actions)
            self.active_sequences.append((script_name, sequence))
            logger.info("ScriptManager: Executing script '%s' with %d actions", script_name, len(actions))
        else:
            logger.warning("ScriptManager: Script '%s' has no valid actions", script_name)

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

    # Event handlers

    def _on_game_start(self, event: GameStartEvent) -> None:
        """Handle game start event."""
        self._current_context = self.context
        # Trigger any scripts with game_start trigger
        self._handle_event_trigger("game_start", {})

    def _on_scene_start(self, event: SceneStartEvent) -> None:
        """Handle scene start event."""
        self._current_context = self.context
        # Trigger any scripts with scene_start trigger for this scene
        self._handle_event_trigger("scene_start", {"scene": event.scene_name})

    def _on_dialog_closed(self, event: DialogClosedEvent) -> None:
        """Handle dialog closed event."""
        self._current_context = self.context
        self._handle_event_trigger("dialog_closed", {"npc": event.npc_name, "dialog_level": event.dialog_level})

    def _on_npc_interacted(self, event: NPCInteractedEvent) -> None:
        """Handle NPC interacted event."""
        self._current_context = self.context
        self._handle_event_trigger("npc_interacted", {"npc": event.npc_name, "dialog_level": event.dialog_level})

    def _on_npc_movement_complete(self, event: NPCMovementCompleteEvent) -> None:
        """Handle NPC movement complete event."""
        self._current_context = self.context
        self._handle_event_trigger("npc_movement_complete", {"npc": event.npc_name})

    def _on_object_interacted(self, event: ObjectInteractedEvent) -> None:
        """Handle object interacted event."""
        self._current_context = self.context
        self.object_interacted(event.object_name)
        self._handle_event_trigger("object_interacted", {"object": event.object_name})

    def _on_portal_entered(self, event: PortalEnteredEvent) -> None:
        """Handle portal entered event."""
        self._current_context = self.context
        self._handle_event_trigger("portal_entered", {"portal": event.portal_name})

    def _on_item_acquired(self, event: ItemAcquiredEvent) -> None:
        """Handle item acquired event."""
        self._current_context = self.context
        self._handle_event_trigger("item_acquired", {"item": event.item_name})

    def _on_inventory_closed(self, event: InventoryClosedEvent) -> None:
        """Handle inventory closed event."""
        self._current_context = self.context
        self._handle_event_trigger("inventory_closed", {})

    def _on_map_transition(self, event: MapTransitionEvent) -> None:
        """Handle map transition event."""
        self._current_context = self.context
        self._handle_event_trigger("map_transition", {"target_map": event.target_map})

    def _on_script_complete(self, event: ScriptCompleteEvent) -> None:
        """Handle script complete event for chaining."""
        self._current_context = self.context
        self._handle_event_trigger("script_complete", {"script": event.script_name})

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
                if script.scene and script.scene != self.context.scene_name:
                    continue

                # Check run_once restriction
                if script.run_once and script.has_run:
                    continue

                # Check conditions - defer to next frame if some systems might not be ready
                if self._check_conditions(script.conditions):
                    self._execute_script(script_name, script)
                    if script.run_once:
                        script.has_run = True
                # Queue for deferred checking to avoid race conditions
                elif script_name not in self._pending_script_checks:
                    self._pending_script_checks.append(script_name)

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
