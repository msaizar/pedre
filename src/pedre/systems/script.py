"""Script manager for loading and executing scripted sequences.

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
- GameContext: Provides access to all game managers for action execution
- NPC/Dialog/Inventory managers: Used for condition checking
- Map system: Scripts can be restricted to specific scenes/maps

Example usage:
    # Create script manager
    event_bus = EventBus()
    script_manager = ScriptManager(event_bus)

    # Load scripts from JSON
    script_manager.load_scripts("data/scripts.json", npc_dialogs)

    # Update each frame
    script_manager.update(delta_time, game_context)

    # Manually trigger a script
    script_manager.trigger_script("intro_cutscene", game_context)
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pedre.systems.actions import (
    AcquireItemAction,
    Action,
    ActionSequence,
    AdvanceDialogAction,
    DialogAction,
    EmitParticlesAction,
    MoveNPCAction,
    PlayMusicAction,
    PlaySFXAction,
    RemoveNPCFromWallsAction,
    RevealNPCsAction,
    SetCurrentNPCAction,
    SetDialogLevelAction,
    StartDisappearAnimationAction,
    WaitForDialogCloseAction,
    WaitForInventoryAccessAction,
    WaitForNPCMovementAction,
    WaitForNPCsAppearAction,
)
from pedre.systems.events import (
    DialogClosedEvent,
    Event,
    EventBus,
    GameStartEvent,
    InventoryClosedEvent,
    ItemAcquiredEvent,
    NPCDisappearCompleteEvent,
    NPCInteractedEvent,
    NPCMovementCompleteEvent,
    ObjectInteractedEvent,
    SceneStartEvent,
    ScriptCompleteEvent,
)

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


class Script:
    """Container for an action sequence with trigger conditions and execution rules.

    A Script represents a reusable sequence of game actions (dialog, movement, effects, etc.)
    that can be triggered by events or called manually. Scripts support conditional execution,
    scene restrictions, and run-once semantics.

    Scripts are typically loaded from JSON files and registered with the ScriptManager. When
    the script's trigger event occurs, the manager checks the script's conditions and scene
    restrictions before executing the action sequence.

    Attributes:
        name: Unique identifier for the script (used in logs and event triggers).
        actions: ActionSequence containing all actions to execute in order.
        conditions: List of condition dictionaries that must be met for execution.
        scene: Optional scene/map name - script only runs in this scene.
        defer_conditions: If True, delay condition checking until after current update cycle.
        run_once: If True, script executes only once and is marked as complete.
        has_run: Tracks whether a run_once script has already executed.

    Example JSON definition:
        {
            "intro_cutscene": {
                "trigger": {"event": "npc_interacted", "npc": "martin"},
                "conditions": [{"check": "npc_dialog_level", "npc": "martin", "equals": 0}],
                "scene": "village",
                "run_once": true,
                "actions": [
                    {"type": "dialog", "speaker": "martin", "text": ["Welcome!"]},
                    {"type": "wait_for_dialog_close"},
                    {"type": "advance_dialog", "npc": "martin"}
                ]
            }
        }
    """

    def __init__(
        self,
        name: str,
        actions: ActionSequence,
        conditions: list[dict[str, Any]] | None = None,
        scene: str | None = None,
        *,
        defer_conditions: bool = False,
        run_once: bool = False,
    ) -> None:
        """Initialize script.

        Args:
            name: Unique script identifier for debugging and event triggers.
            actions: ActionSequence to execute when script runs.
            conditions: Optional list of conditions that must be met to run.
                       Each condition is a dict with "check" key and comparison values.
            scene: Optional scene/map name. Script only runs when this scene is active.
            defer_conditions: If True, defer condition checking until after current update
                            cycle. This prevents race conditions where conditions check
                            before other systems have updated.
            run_once: If True, script will only execute once per game session and then
                     be marked as complete (has_run = True).
        """
        self.name = name
        self.actions = actions
        self.conditions = conditions or []
        self.scene = scene
        self.defer_conditions = defer_conditions
        self.run_once = run_once
        self.has_run = False


class ScriptManager:
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
        event_bus = EventBus()
        script_manager = ScriptManager(event_bus)

        # Load scripts from file
        script_manager.load_scripts("data/scripts.json", npc_dialog_data)

        # Game loop
        def update(delta_time):
            script_manager.update(delta_time, game_context)

        # Manual trigger
        script_manager.trigger_script("intro_cutscene", game_context)
    """

    def __init__(self, event_bus: EventBus) -> None:
        """Initialize script manager.

        Args:
            event_bus: EventBus instance for subscribing to game events and publishing
                      script completion events.
        """
        self.event_bus = event_bus
        self.scripts: dict[str, Script] = {}
        self.active_sequences: list[tuple[str, ActionSequence]] = []
        self._current_context: GameContext | None = None
        self.interacted_objects: set[str] = set()  # Track which objects have been interacted with
        self._pending_script_checks: list[str] = []  # Scripts to check conditions for after current update

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
            script_data: Dictionary of script definitions (already parsed from JSON).
            npc_dialogs: Dictionary of NPC dialog data for resolving text_from references.
                        Format: {npc_name: {dialog_level: {"text": [...]}}}
        """
        loaded_count = 0
        for script_name, script_definition in script_data.items():
            script = self._parse_script(script_name, script_definition, npc_dialogs)
            if script:
                self.scripts[script_name] = script

                # Register event trigger if present
                trigger = script_definition.get("trigger")
                if trigger:
                    self._register_trigger(script_name, trigger)

                loaded_count += 1

        logger.info("Loaded %d scripts from cached data", loaded_count)

    def parse_actions(self, actions_data: list[dict[str, Any]], npc_dialogs: dict[str, Any]) -> list[Action]:
        """Parse a list of action dictionaries into Action objects.

        Converts raw JSON action data into concrete Action instances. Each action dictionary
        must have a "type" field that determines which Action class to instantiate. Additional
        fields depend on the action type.

        Unknown action types are logged as warnings and filtered out (return None). This allows
        scripts to gracefully handle missing or unimplemented action types.

        Args:
            actions_data: List of action dictionaries from JSON, each with a "type" field.
            npc_dialogs: NPC dialog data for resolving text_from references in dialog actions.

        Returns:
            List of instantiated Action objects with None values filtered out.

        Example:
            actions_data = [
                {"type": "dialog", "speaker": "martin", "text": ["Hello!"]},
                {"type": "wait_for_dialog_close"},
                {"type": "move_npc", "npcs": ["martin"], "waypoint": "town_square"}
            ]
            actions = script_manager.parse_actions(actions_data, npc_dialogs)
        """
        actions = [self._parse_action(action_data, npc_dialogs) for action_data in actions_data]
        return [a for a in actions if a is not None]

    def _load_script_file(self, script_file: str, npc_dialogs: dict[str, Any]) -> None:
        """Load and parse scripts from a JSON file (internal implementation).

        Reads the JSON file, parses each script definition into a Script object, registers
        event triggers with the EventBus, and adds scripts to the registry. Handles JSON
        parsing errors and invalid script definitions gracefully with logging.

        This is an internal method called by load_scripts(). It iterates through all script
        definitions in the file, parses each one, and registers any event triggers.

        Args:
            script_file: Path to the JSON file containing script definitions.
            npc_dialogs: NPC dialog data dictionary for resolving text_from references.

        Side effects:
            - Adds parsed scripts to self.scripts
            - Registers event trigger handlers with self.event_bus
            - Logs info on successful load, errors on failures
        """
        try:
            with Path(script_file).open() as f:
                data = json.load(f)

            loaded_count = 0
            for script_name, script_data in data.items():
                script = self._parse_script(script_name, script_data, npc_dialogs)
                if script:
                    self.scripts[script_name] = script

                    # Register event trigger if present
                    trigger = script_data.get("trigger")
                    if trigger:
                        self._register_trigger(script_name, trigger)

                    loaded_count += 1

            logger.info("Loaded %d scripts from %s", loaded_count, script_file)

        except json.JSONDecodeError:
            logger.exception("Failed to parse script file: %s", script_file)
        except Exception:
            logger.exception("Error loading scripts from %s", script_file)

    def _parse_script(
        self,
        script_name: str,
        script_data: dict[str, Any],
        npc_dialogs: dict[str, Any],
    ) -> Script | None:
        """Parse raw script data into a Script object (internal implementation).

        Converts a script definition dictionary from JSON into a Script instance. Parses
        the actions list, extracts conditions and metadata, and constructs an ActionSequence.

        If action parsing fails for any action, that action is filtered out but the script
        is still created with the remaining valid actions. If the entire script fails to
        parse, returns None and logs an exception.

        Args:
            script_name: Unique identifier for the script.
            script_data: Dictionary containing script definition from JSON.
                        Expected keys: "actions" (required), "conditions", "scene",
                        "defer_conditions", "run_once".
            npc_dialogs: NPC dialog data for resolving text_from references in actions.

        Returns:
            Script object if parsing succeeds, None if an exception occurs.

        Example script_data:
            {
                "actions": [...],
                "conditions": [{"check": "npc_dialog_level", "npc": "martin", "equals": 1}],
                "scene": "village",
                "defer_conditions": false,
                "run_once": true
            }
        """
        try:
            actions_data = script_data.get("actions", [])
            actions = [self._parse_action(action_data, npc_dialogs) for action_data in actions_data]
            actions = [a for a in actions if a is not None]  # Filter out None

            conditions = script_data.get("conditions")
            scene = script_data.get("scene")  # Optional scene restriction
            defer_conditions = script_data.get("defer_conditions", False)
            run_once = script_data.get("run_once", False)

            return Script(
                script_name,
                ActionSequence(actions),
                conditions,
                scene,
                defer_conditions=defer_conditions,
                run_once=run_once,
            )

        except Exception:
            logger.exception("Failed to parse script: %s", script_name)
            return None

    def _parse_action(self, action_data: dict[str, Any], npc_dialogs: dict[str, Any]) -> Action | None:
        """Parse a single action dictionary into an Action object (internal implementation).

        Examines the "type" field to determine which Action class to instantiate, then
        extracts type-specific parameters and constructs the appropriate Action object.

        Supported action types:
        - dialog: Show dialog with text
        - move_npc: Move NPCs to waypoint
        - reveal_npcs: Make hidden NPCs visible
        - play_sfx: Play sound effect
        - play_music: Play background music
        - emit_particles: Create particle effects
        - advance_dialog: Increment NPC dialog level
        - set_dialog_level: Set NPC dialog level to specific value
        - set_current_npc: Set current NPC for dialog attribution
        - wait_for_dialog_close: Wait for dialog to be dismissed
        - wait_for_movement: Wait for NPC movement completion
        - wait_for_inventory_access: Wait for inventory to be opened
        - wait_for_npcs_appear: Wait for NPC appear animations
        - start_disappear_animation: Trigger NPC disappear animation
        - remove_npc_from_walls: Remove NPCs from collision walls

        Args:
            action_data: Dictionary with "type" key and type-specific parameters.
            npc_dialogs: NPC dialog data for resolving text_from references.

        Returns:
            Instantiated Action object, or None if type is unknown or parameters are invalid.

        Example action_data:
            {"type": "dialog", "speaker": "martin", "text": ["Hello!"]}
            {"type": "move_npc", "npcs": ["martin"], "waypoint": "town_square"}
            {"type": "wait_for_dialog_close"}
        """
        action_type = action_data.get("type")

        if action_type == "dialog":
            speaker = action_data["speaker"]
            text = action_data.get("text")
            instant = action_data.get("instant", False)

            # If text is not provided, try to resolve from reference
            if not text:
                text_ref = action_data.get("text_from", "")
                text = self._resolve_dialog_text(text_ref, npc_dialogs)

            return DialogAction(speaker, text or [""], instant=instant)

        if action_type == "move_npc":
            npc_names = action_data.get("npcs")
            if not npc_names:
                logger.warning("move_npc action missing 'npcs' parameter")
                return None

            waypoint = action_data.get("waypoint")
            if not waypoint:
                logger.warning("move_npc action missing 'waypoint' parameter")
                return None

            return MoveNPCAction(npc_names, waypoint)

        if action_type == "reveal_npcs":
            npcs = action_data["npcs"]
            return RevealNPCsAction(npcs)

        if action_type == "play_sfx":
            sfx_file = action_data["file"]
            return PlaySFXAction(sfx_file)

        if action_type == "play_music":
            music_file = action_data["file"]
            loop = action_data.get("loop", True)
            volume = action_data.get("volume")
            return PlayMusicAction(music_file, loop=loop, volume=volume)

        if action_type == "emit_particles":
            particle_type = action_data["particle_type"]
            x = action_data.get("x")
            y = action_data.get("y")
            npc_name = action_data.get("npc")
            return EmitParticlesAction(particle_type, x, y, npc_name)

        if action_type == "advance_dialog":
            npc_name = action_data["npc"]
            return AdvanceDialogAction(npc_name)

        if action_type == "acquire_item":
            item_id = action_data.get("item_id")
            if not item_id:
                logger.warning("acquire_item action missing 'item_id' parameter")
                return None
            return AcquireItemAction(item_id)

        if action_type == "set_dialog_level":
            npc_name = action_data["npc"]
            level = action_data["dialog_level"]
            return SetDialogLevelAction(npc_name, level)

        if action_type == "set_current_npc":
            npc_name = action_data["npc"]
            return SetCurrentNPCAction(npc_name)

        if action_type == "wait_for_dialog_close":
            return WaitForDialogCloseAction()

        if action_type == "wait_for_movement":
            npc_name = action_data.get("npc", "")
            return WaitForNPCMovementAction(npc_name)

        if action_type == "wait_for_inventory_access":
            return WaitForInventoryAccessAction()

        if action_type == "wait_for_npcs_appear":
            npc_names = action_data.get("npcs", [])
            return WaitForNPCsAppearAction(npc_names)

        if action_type == "start_disappear_animation":
            npc_names = action_data.get("npcs")
            if not npc_names:
                logger.warning("start_disappear_animation action missing 'npcs' parameter")
                return None
            return StartDisappearAnimationAction(npc_names)

        if action_type == "remove_npc_from_walls":
            npc_names = action_data.get("npcs")
            if not npc_names:
                logger.warning("remove_npc_from_walls action missing 'npcs' parameter")
                return None
            return RemoveNPCFromWallsAction(npc_names)

        if action_type == "wait_for_condition":
            # Generic condition - would need custom implementation
            logger.warning("Generic wait_for_condition not yet implemented")
            return None

        logger.warning("Unknown action type: %s", action_type)
        return None

    def _resolve_dialog_text(self, text_ref: str, npc_dialogs: dict[str, Any]) -> list[str] | None:
        """Resolve dialog text from a reference string (internal implementation).

        Allows dialog actions to reference text from the NPC dialog data instead of
        duplicating text in script definitions. This is useful when the same dialog
        appears in both regular NPC interactions and scripted sequences.

        Reference format: "dialogs.{npc_name}.{dialog_level}"

        Args:
            text_ref: Reference string in format "dialogs.npc_name.level".
                     Example: "dialogs.martin.2"
            npc_dialogs: NPC dialog data dictionary structured as:
                        {npc_name: {level: {"text": ["line1", "line2", ...]}}}

        Returns:
            List of dialog text strings if reference is valid, None if reference is
            malformed or NPC/level not found.

        Example:
            # With npc_dialogs = {"martin": {"2": {"text": ["Hello!", "How are you?"]}}}
            text = _resolve_dialog_text("dialogs.martin.2", npc_dialogs)
            # Returns: ["Hello!", "How are you?"]
        """
        parts = text_ref.split(".")
        if len(parts) != 3 or parts[0] != "dialogs":
            return None

        npc_name = parts[1]
        level = parts[2]

        if npc_name not in npc_dialogs:
            return None

        level_data = npc_dialogs[npc_name].get(level)
        if not level_data:
            return None

        return level_data.get("text")

    def _register_trigger(self, script_name: str, trigger: dict[str, Any]) -> None:
        """Register an event trigger handler for a script (internal implementation).

        Creates and subscribes an event handler to the EventBus that will trigger the
        specified script when matching events occur. The handler checks optional filters
        (like NPC name or dialog level) before triggering.

        Supported trigger event types:
        - dialog_closed: Triggered when dialog is dismissed (filters: npc, dialog_level)
        - inventory_closed: Triggered when inventory is closed
        - npc_interacted: Triggered when player interacts with NPC (filter: npc)
        - object_interacted: Triggered when player interacts with object (filter: object_name)
        - npc_movement_complete: Triggered when NPC reaches destination (filter: npc)
        - npc_disappear_complete: Triggered when NPC disappear animation finishes (filter: npc)
        - script_complete: Triggered when another script finishes (filter: script)

        Args:
            script_name: Name of the script to trigger when event occurs.
            trigger: Dictionary with "event" key and optional filter keys.
                    Example: {"event": "dialog_closed", "npc": "martin", "dialog_level": 1}

        Side effects:
            Subscribes a handler function to self.event_bus for the specified event type.
            The handler captures script_name and trigger filters in its closure.
        """
        event_type = trigger.get("event")

        if event_type == "dialog_closed":
            npc_filter = trigger.get("npc")
            level_filter = trigger.get("dialog_level")

            def handler(event: Event) -> None:
                if not isinstance(event, DialogClosedEvent):
                    return
                # Check filters
                if npc_filter and event.npc_name != npc_filter:
                    return
                if level_filter is not None and event.dialog_level != level_filter:
                    return
                # Get context and script's defer setting
                script = self.scripts.get(script_name)
                defer = script.defer_conditions if script else False
                self.trigger_script(script_name, self._current_context, defer_conditions=defer)

            self.event_bus.subscribe(DialogClosedEvent, handler)

        elif event_type == "inventory_closed":

            def handler(event: Event) -> None:
                if isinstance(event, InventoryClosedEvent):
                    self.trigger_script(script_name, self._current_context)

            self.event_bus.subscribe(InventoryClosedEvent, handler)

        elif event_type == "item_acquired":
            item_filter = trigger.get("item_id")

            def handler(event: Event) -> None:
                if not isinstance(event, ItemAcquiredEvent):
                    return
                if item_filter and event.item_id != item_filter:
                    return
                self.trigger_script(script_name, self._current_context)

            self.event_bus.subscribe(ItemAcquiredEvent, handler)

        elif event_type == "npc_interacted":
            npc_filter = trigger.get("npc")

            def handler(event: Event) -> None:
                if not isinstance(event, NPCInteractedEvent):
                    return
                if npc_filter and event.npc_name != npc_filter:
                    return
                self.trigger_script(script_name, self._current_context)

            self.event_bus.subscribe(NPCInteractedEvent, handler)

        elif event_type == "object_interacted":
            object_filter = trigger.get("object_name")

            def handler(event: Event) -> None:
                if not isinstance(event, ObjectInteractedEvent):
                    return
                if object_filter and event.object_name != object_filter:
                    return
                # Track that this object was interacted with
                self.interacted_objects.add(event.object_name)
                self.trigger_script(script_name, self._current_context)

            self.event_bus.subscribe(ObjectInteractedEvent, handler)

        elif event_type == "npc_movement_complete":
            npc_filter = trigger.get("npc")

            def handler(event: Event) -> None:
                if not isinstance(event, NPCMovementCompleteEvent):
                    return
                if npc_filter and event.npc_name != npc_filter:
                    return
                self.trigger_script(script_name, self._current_context)

            self.event_bus.subscribe(NPCMovementCompleteEvent, handler)

        elif event_type == "npc_disappear_complete":
            npc_filter = trigger.get("npc")

            def handler(event: Event) -> None:
                if not isinstance(event, NPCDisappearCompleteEvent):
                    return
                if npc_filter and event.npc_name != npc_filter:
                    return
                self.trigger_script(script_name, self._current_context)

            self.event_bus.subscribe(NPCDisappearCompleteEvent, handler)

        elif event_type == "game_start":

            def handler(event: Event) -> None:
                if isinstance(event, GameStartEvent):
                    self.trigger_script(script_name, self._current_context)

            self.event_bus.subscribe(GameStartEvent, handler)

        elif event_type == "scene_start":
            scene_filter = trigger.get("scene")

            def handler(event: Event) -> None:
                if not isinstance(event, SceneStartEvent):
                    return
                if scene_filter and event.scene_name != scene_filter:
                    return
                self.trigger_script(script_name, self._current_context)

            self.event_bus.subscribe(SceneStartEvent, handler)

        elif event_type == "script_complete":
            script_filter = trigger.get("script")

            def handler(event: Event) -> None:
                if not isinstance(event, ScriptCompleteEvent):
                    return
                if script_filter and event.script_name != script_filter:
                    return
                self.trigger_script(script_name, self._current_context)

            self.event_bus.subscribe(ScriptCompleteEvent, handler)

        else:
            logger.warning("Unknown event type in trigger: %s", event_type)

    def trigger_script(
        self, script_name: str, context: GameContext | None = None, *, defer_conditions: bool = False
    ) -> None:
        """Manually trigger a script by name.

        Attempts to execute a script, checking run_once status, scene restrictions, and
        conditions before adding it to the active sequences. Can be called manually or
        by event trigger handlers.

        The script will be skipped if:
        - Script name not found in registry
        - run_once enabled and script has already run
        - Scene restriction exists and doesn't match current scene
        - Conditions exist and are not met (unless deferred)
        - Script is already in active sequences

        If defer_conditions is True and the script has conditions, the script is added
        to pending_script_checks for evaluation after the current update cycle completes.
        This prevents race conditions where conditions are checked before other systems
        have finished updating.

        Args:
            script_name: Name of the script to trigger (must exist in self.scripts).
            context: GameContext for accessing current scene and evaluating conditions.
                    If None, scene and condition checks are skipped.
            defer_conditions: If True, delay condition checking until after current update.
                            This is used by dialog_closed triggers to avoid race conditions.

        Side effects:
            - May add (script_name, ActionSequence) to self.active_sequences
            - May add script_name to self._pending_script_checks
            - Sets script.has_run = True if run_once is enabled
            - Resets the action sequence before starting
        """
        if script_name not in self.scripts:
            logger.warning("Script not found: %s", script_name)
            return

        script = self.scripts[script_name]

        # Check if script has run_once enabled and has already run
        if script.run_once and script.has_run:
            logger.debug("Script %s skipped - run_once enabled and already executed", script_name)
            return

        # Check if script is restricted to a specific scene
        if script.scene and context and script.scene != context.current_scene:
            logger.debug(
                "Script %s skipped - requires scene '%s', current is '%s'",
                script_name,
                script.scene,
                context.current_scene,
            )
            return

        # If script has conditions and defer_conditions is True, add to pending checks
        if defer_conditions and script.conditions:
            if script_name not in self._pending_script_checks:
                self._pending_script_checks.append(script_name)
                logger.debug("Script %s deferred for condition check", script_name)
            return

        # Check conditions before triggering
        if script.conditions and context and not self._check_conditions(script.conditions, context):
            logger.debug("Script %s skipped - conditions not met", script_name)
            return

        # Check if script is already running
        if any(name == script_name for name, _ in self.active_sequences):
            logger.debug("Script %s already running, skipping duplicate trigger", script_name)
            return

        logger.info("Triggering script: %s", script_name)

        # Mark as run if run_once is enabled
        if script.run_once:
            script.has_run = True

        # Reset the action sequence before starting
        script.actions.reset()

        # Add to active sequences
        self.active_sequences.append((script_name, script.actions))

    def check_and_trigger(self, script_name: str, context: GameContext) -> None:
        """Check script conditions and trigger if all conditions are met.

        Convenience method that evaluates a script's conditions and triggers it if they're
        satisfied. This is useful for manually checking scripts based on game state changes.

        Unlike trigger_script(), this method always checks conditions immediately (no
        defer_conditions support) and only triggers if conditions pass.

        Args:
            script_name: Name of the script to check and potentially trigger.
            context: GameContext for evaluating script conditions.

        Side effects:
            Calls trigger_script() if conditions are met, which may add the script
            to active_sequences.
        """
        if script_name not in self.scripts:
            logger.warning("Script not found: %s", script_name)
            return

        script = self.scripts[script_name]

        # Check conditions
        if script.conditions and not self._check_conditions(script.conditions, context):
            logger.debug("Script %s conditions not met", script_name)
            return

        self.trigger_script(script_name)

    def _check_conditions(self, conditions: list[dict[str, Any]], context: GameContext) -> bool:
        """Evaluate all script conditions (internal implementation).

        Checks each condition in the list and returns True only if ALL conditions pass.
        Conditions are evaluated using game state from the GameContext.

        Supported condition types:
        - npc_dialog_level: Check NPC's dialog level with comparison operators
          (equals, gte, gt, lte, lt)
        - inventory_accessed: Check if inventory has been opened (equals boolean)
        - object_interacted: Check if an object has been interacted with (equals boolean)

        If any condition fails, returns False immediately (short-circuit evaluation).
        Unknown condition types log a warning and return False.

        Args:
            conditions: List of condition dictionaries, each with a "check" key and
                       comparison parameters. Example:
                       [{"check": "npc_dialog_level", "npc": "martin", "gte": 2}]
            context: GameContext providing access to managers for state queries.

        Returns:
            True if all conditions pass, False if any fail or are invalid.

        Example conditions:
            # NPC dialog level equals 1
            {"check": "npc_dialog_level", "npc": "martin", "equals": 1}

            # NPC dialog level >= 3
            {"check": "npc_dialog_level", "npc": "yema", "gte": 3}

            # Inventory has been accessed
            {"check": "inventory_accessed", "equals": true}

            # Treasure chest has been interacted with
            {"check": "object_interacted", "object": "treasure_chest", "equals": true}
        """
        for condition in conditions:
            check_type = condition.get("check")

            if check_type == "npc_dialog_level":
                npc_name = condition.get("npc", "")
                npc_state = context.npc_manager.npcs.get(npc_name)
                actual_level = npc_state.dialog_level if npc_state else None

                if not npc_state:
                    logger.debug(
                        "Condition failed: npc_dialog_level - npc=%s not found",
                        npc_name,
                    )
                    return False

                # Check for different comparison operators
                if "equals" in condition:
                    expected_level = condition["equals"]
                    if npc_state.dialog_level != expected_level:
                        logger.debug(
                            "Condition failed: npc_dialog_level - npc=%s, equals=%s, actual=%s",
                            npc_name,
                            expected_level,
                            actual_level,
                        )
                        return False
                elif "gte" in condition:
                    expected_level = condition["gte"]
                    if npc_state.dialog_level < expected_level:
                        logger.debug(
                            "Condition failed: npc_dialog_level - npc=%s, gte=%s, actual=%s",
                            npc_name,
                            expected_level,
                            actual_level,
                        )
                        return False
                elif "gt" in condition:
                    expected_level = condition["gt"]
                    if npc_state.dialog_level <= expected_level:
                        logger.debug(
                            "Condition failed: npc_dialog_level - npc=%s, gt=%s, actual=%s",
                            npc_name,
                            expected_level,
                            actual_level,
                        )
                        return False
                elif "lte" in condition:
                    expected_level = condition["lte"]
                    if npc_state.dialog_level > expected_level:
                        logger.debug(
                            "Condition failed: npc_dialog_level - npc=%s, lte=%s, actual=%s",
                            npc_name,
                            expected_level,
                            actual_level,
                        )
                        return False
                elif "lt" in condition:
                    expected_level = condition["lt"]
                    if npc_state.dialog_level >= expected_level:
                        logger.debug(
                            "Condition failed: npc_dialog_level - npc=%s, lt=%s, actual=%s",
                            npc_name,
                            expected_level,
                            actual_level,
                        )
                        return False
                else:
                    logger.warning("npc_dialog_level condition missing comparison operator (equals/gte/gt/lte/lt)")
                    return False

            elif check_type == "inventory_accessed":
                expected = condition.get("equals", True)
                actual = context.inventory_manager.has_been_accessed
                if actual != expected:
                    logger.debug(
                        "Condition failed: inventory_accessed - expected=%s, actual=%s",
                        expected,
                        actual,
                    )
                    return False

            elif check_type == "object_interacted":
                object_name = condition.get("object", "")
                expected = condition.get("equals", True)
                was_interacted = object_name in self.interacted_objects
                if was_interacted != expected:
                    logger.debug(
                        "Condition failed: object_interacted - object=%s, expected=%s, actual=%s",
                        object_name,
                        expected,
                        was_interacted,
                    )
                    return False

            else:
                logger.warning("Unknown condition type: %s", check_type)
                return False

        return True

    def update(self, _delta_time: float, context: GameContext) -> None:
        """Update and execute all active script sequences.

        Called each frame to advance all currently running scripts. Executes one step
        of each active script's ActionSequence, removes completed sequences, and processes
        any deferred script condition checks.

        The update process:
        1. Store context for event handlers to access
        2. Execute each active sequence (may complete in one frame or continue)
        3. Remove completed sequences and publish ScriptCompleteEvent
        4. Process pending deferred condition checks

        Deferred condition checking occurs after all active scripts have executed to
        prevent race conditions where a script checks conditions before other scripts
        have finished updating game state.

        Args:
            _delta_time: Time elapsed since last frame in seconds (currently unused
                        but kept for API consistency).
            context: GameContext providing access to all managers for action execution
                    and condition evaluation.

        Side effects:
            - Executes actions in active sequences, potentially modifying game state
            - Removes completed sequences from self.active_sequences
            - Publishes ScriptCompleteEvent for each completed script
            - Processes and clears self._pending_script_checks
            - Updates self._current_context for event handler access
        """
        # Store context for event handlers
        self._current_context = context

        # Execute active sequences
        for script_name, sequence in self.active_sequences[:]:
            if sequence.execute(context):
                # Sequence completed
                self.active_sequences.remove((script_name, sequence))
                logger.info("Script completed: %s", script_name)

                # Publish script complete event
                self.event_bus.publish(ScriptCompleteEvent(script_name=script_name))

        # Process pending script checks (after all scripts have executed)
        if self._pending_script_checks:
            pending = self._pending_script_checks[:]
            self._pending_script_checks.clear()
            for script_name in pending:
                # Trigger without deferring this time
                self.trigger_script(script_name, context, defer_conditions=False)

    def clear(self) -> None:
        """Clear all active script sequences.

        Immediately stops all currently executing scripts by clearing the active
        sequences list. This does not unload scripts from the registry or unsubscribe
        event handlers - those remain active.

        This is typically called when transitioning between major game states (like
        returning to menu or loading a saved game) where all in-progress scripts
        should be abandoned.

        Side effects:
            Clears self.active_sequences, stopping all running scripts mid-execution.
        """
        self.active_sequences.clear()

    def get_completed_scripts(self) -> list[str]:
        """Get list of run_once scripts that have completed.

        Returns the names of all scripts marked as run_once that have their has_run
        flag set to True. This is used for save data to prevent completed one-time
        scripts from re-triggering when the game is loaded.

        Returns:
            List of script names that have completed and should not run again.
            Empty list if no run_once scripts have completed.

        Example:
            # Save completed scripts
            completed = script_manager.get_completed_scripts()
            save_data["completed_scripts"] = completed
            # ["intro_cutscene", "first_boss_defeated", "ending_unlocked"]
        """
        completed = []
        for script_name, script in self.scripts.items():
            if script.run_once and script.has_run:
                completed.append(script_name)
        return completed

    def restore_completed_scripts(self, completed_scripts: list[str]) -> None:
        """Restore completed state for run_once scripts from save data.

        Marks scripts as completed (has_run = True) based on saved data. This prevents
        one-time scripts from triggering again when loading a save file.

        Scripts not present in completed_scripts will have has_run = False, allowing
        them to trigger normally. Scripts in completed_scripts that don't exist in
        the current script registry are logged as warnings but otherwise ignored.

        Args:
            completed_scripts: List of script names that were completed in the saved game.
                Example: ["intro_cutscene", "tutorial_complete"]

        Example:
            # After loading save data
            save_data = save_manager.load_game(slot=1)
            if save_data and save_data.completed_scripts:
                script_manager.restore_completed_scripts(save_data.completed_scripts)
                # One-time scripts won't re-trigger
        """
        for script_name in completed_scripts:
            script = self.scripts.get(script_name)
            if script and script.run_once:
                script.has_run = True
                logger.debug("Restored completed script: %s", script_name)
            elif script:
                logger.warning("Script %s in completed list but not marked run_once", script_name)
            else:
                logger.warning("Cannot restore unknown script: %s", script_name)
