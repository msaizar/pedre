"""Action system for reusable, chainable game actions."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self

from pedre.systems.action_registry import ActionRegistry

if TYPE_CHECKING:
    from collections.abc import Callable

    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


class Action(ABC):
    """Base class for all actions."""

    @abstractmethod
    def execute(self, context: GameContext) -> bool:
        """Execute the action.

        Args:
            context: Game context containing all managers and state.

        Returns:
            True if action is complete, False if still executing.
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset action state for reuse."""


class WaitForConditionAction(Action):
    """Wait until a condition is met.

    This is a base class for creating actions that pause execution until a specific
    condition becomes true. Unlike actions that complete immediately, this action
    will continue to return False from execute() until the condition function returns True.

    This enables complex sequencing where later actions wait for asynchronous events
    like NPC movements, animations, or player interactions to complete.

    The condition function receives the GameContext and should return True when the
    wait is over. The description is used for debug logging to help track what the
    system is waiting for.

    This class is typically subclassed for specific wait conditions rather than used
    directly. See WaitForDialogCloseAction, WaitForNPCMovementAction, etc.

    Example subclass:
        class WaitForCustomAction(WaitForConditionAction):
            def __init__(self):
                super().__init__(
                    lambda ctx: ctx.custom_manager.is_ready,
                    "Custom event ready"
                )
    """

    def __init__(self, condition: Callable[[GameContext], bool], description: str = "") -> None:
        """Initialize wait action.

        Args:
            condition: Function that returns True when condition is met.
            description: Description of what we're waiting for (for debugging).
        """
        self.condition = condition
        self.description = description

    def execute(self, context: GameContext) -> bool:
        """Check if condition is met."""
        result = self.condition(context)
        if result:
            logger.debug("WaitForConditionAction: Condition met - %s", self.description)
        return result

    def reset(self) -> None:
        """Reset does nothing for wait actions."""


class ActionSequence(Action):
    """Execute multiple actions in sequence.

    This action container executes a list of actions one after another, waiting
    for each action to complete before proceeding to the next. This enables
    complex scripted sequences where actions must happen in a specific order.

    The sequence tracks which action is currently executing via current_index.
    Each frame, it executes the current action and advances to the next when
    that action returns True (indicating completion).

    Actions within the sequence can be immediate (complete in one frame) or
    waiting actions (complete when a condition is met), allowing for flexible
    timing and synchronization.

    Example usage:
        ActionSequence([
            DialogAction("martin", ["Hello!"]),
            WaitForDialogCloseAction(),
            MoveNPCAction("martin", "waypoint_1"),
            WaitForNPCMovementAction("martin"),
            DialogAction("martin", ["I'm here!"])
        ])

    This is typically constructed programmatically rather than from JSON,
    though scripts can define action sequences in data files.
    """

    def __init__(self, actions: list[Action]) -> None:
        """Initialize action sequence.

        Args:
            actions: List of actions to execute in order.
        """
        self.actions = actions
        self.current_index = 0

    def execute(self, context: GameContext) -> bool:
        """Execute current action and advance if complete."""
        if self.current_index >= len(self.actions):
            return True

        current_action = self.actions[self.current_index]
        if current_action.execute(context):
            self.current_index += 1

        return self.current_index >= len(self.actions)

    def reset(self) -> None:
        """Reset the sequence and all actions."""
        self.current_index = 0
        for action in self.actions:
            action.reset()


@ActionRegistry.register("emit_particles")
class EmitParticlesAction(Action):
    """Emit particle effects.

    This action creates visual particle effects at a specified location. Particles can
    be emitted at fixed coordinates or follow an NPC's position. Available particle types
    include hearts, sparkles, and colored bursts.

    When using npc_name, the particles will be emitted at the NPC's current center position,
    which is useful for effects that should appear on or around a character.

    Example usage:
        # Fixed position burst
        {
            "type": "emit_particles",
            "particle_type": "burst",
            "x": 512,
            "y": 384
        }

        # Hearts around an NPC
        {
            "type": "emit_particles",
            "particle_type": "hearts",
            "npc": "yema"
        }
    """

    def __init__(
        self,
        particle_type: str,
        x: float | None = None,
        y: float | None = None,
        npc_name: str | None = None,
    ) -> None:
        """Initialize particle emission action.

        Args:
            particle_type: Type of particles (hearts, sparkles, burst).
            x: X coordinate (if not using NPC position).
            y: Y coordinate (if not using NPC position).
            npc_name: NPC name to emit particles at (overrides x, y).
        """
        self.particle_type = particle_type
        self.x = x
        self.y = y
        self.npc_name = npc_name
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Emit the particles."""
        if not self.executed:
            # Determine position
            emit_x = self.x
            emit_y = self.y

            if self.npc_name:
                npc_state = context.npc_manager.npcs.get(self.npc_name)
                if npc_state:
                    emit_x = npc_state.sprite.center_x
                    emit_y = npc_state.sprite.center_y

            if emit_x is None or emit_y is None:
                logger.warning("EmitParticlesAction: No valid position to emit particles")
                return True

            # Emit particles
            if self.particle_type == "hearts":
                context.particle_manager.emit_hearts(emit_x, emit_y)
            elif self.particle_type == "sparkles":
                context.particle_manager.emit_sparkles(emit_x, emit_y)
            elif self.particle_type == "burst":
                context.particle_manager.emit_burst(emit_x, emit_y, color=(255, 215, 0))

            self.executed = True
            logger.debug("EmitParticlesAction: Emitted %s at (%s, %s)", self.particle_type, emit_x, emit_y)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create EmitParticlesAction from a dictionary."""
        return cls(
            particle_type=data.get("particle_type", "burst"),
            x=data.get("x"),
            y=data.get("y"),
            npc_name=data.get("npc"),
        )


@ActionRegistry.register("wait_inventory_access")
class WaitForInventoryAccessAction(WaitForConditionAction):
    """Wait for inventory to be accessed.

    This action pauses script execution until the player opens their inventory
    for the first time. It's useful for tutorial sequences or quests that require
    the player to check their items.

    The inventory manager tracks whether it has been accessed via the has_been_accessed
    flag, which this action monitors.

    Example usage in a tutorial sequence:
        [
            {"type": "dialog", "speaker": "martin", "text": ["Check your inventory!"]},
            {"type": "wait_dialog_close"},
            {"type": "wait_inventory_access"},
            {"type": "dialog", "speaker": "martin", "text": ["Great job!"]}
        ]
    """

    def __init__(self) -> None:
        """Initialize inventory access wait action."""
        super().__init__(lambda ctx: ctx.inventory_manager.has_been_accessed, "Inventory accessed")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:  # noqa: ARG003
        """Create WaitForInventoryAccessAction from a dictionary."""
        return cls()


@ActionRegistry.register("acquire_item")
class AcquireItemAction(Action):
    """Give an item to the player's inventory.

    This action adds a specified item to the player's inventory by calling the
    inventory manager's acquire_item() method. The item must already be defined
    in the inventory manager - this action only marks it as acquired.

    When the item is successfully acquired, an ItemAcquiredEvent is published
    (if the inventory manager has an event bus), which can trigger follow-up
    scripts or reactions.

    The action completes immediately after attempting to acquire the item. It
    returns True regardless of whether the item was newly acquired or already
    owned, so it can be used safely in scripts without worrying about double
    acquisition.

    Example usage:
        {
            "type": "acquire_item",
            "item_id": "rusty_key"
        }

        # In a script after finding a treasure chest
        {
            "actions": [
                {"type": "dialog", "speaker": "Narrator", "text": ["You found a key!"]},
                {"type": "acquire_item", "item_id": "tower_key"},
                {"type": "wait_for_dialog_close"}
            ]
        }
    """

    def __init__(self, item_id: str) -> None:
        """Initialize acquire item action.

        Args:
            item_id: Unique identifier of the item to acquire. Must match an item
                    ID in the inventory manager's registry.
        """
        self.item_id = item_id
        self.started = False

    def execute(self, context: GameContext) -> bool:
        """Acquire the item if not already started."""
        if not self.started:
            context.inventory_manager.acquire_item(self.item_id)
            self.started = True
            logger.debug("AcquireItemAction: Acquired item %s", self.item_id)

        # Action completes immediately
        return True

    def reset(self) -> None:
        """Reset the action."""
        self.started = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create AcquireItemAction from a dictionary."""
        return cls(item_id=data.get("item_id", ""))


@ActionRegistry.register("change_scene")
class ChangeSceneAction(Action):
    """Transition to a different map/scene.

    This action triggers a map transition through the game view's scene transition
    system, complete with fade effects. It allows scripts to control when and where
    map transitions occur, enabling conditional portals, cutscenes before transitions,
    and complex multi-step sequences.

    The target_map should be the filename of the map to load (e.g., "Forest.tmx").
    The optional spawn_waypoint specifies where the player should appear in the new
    map. If not provided, the default spawn point from the map data is used.

    This action is typically used in response to PortalEnteredEvent, allowing scripts
    to handle portal transitions with full control over conditions and sequences.

    Example usage:
        # Simple transition
        {
            "type": "change_scene",
            "target_map": "Forest.tmx"
        }

        # Transition with specific spawn point
        {
            "type": "change_scene",
            "target_map": "Tower.tmx",
            "spawn_waypoint": "tower_entrance"
        }

        # In a portal script with dialog first
        {
            "trigger": {"event": "portal_entered", "portal": "forest_gate"},
            "actions": [
                {"type": "dialog", "speaker": "Narrator", "text": ["The gate opens..."]},
                {"type": "wait_for_dialog_close"},
                {"type": "change_scene", "target_map": "Forest.tmx", "spawn_waypoint": "entrance"}
            ]
        }
    """

    def __init__(self, target_map: str, spawn_waypoint: str | None = None) -> None:
        """Initialize scene change action.

        Args:
            target_map: Filename of the map to transition to (e.g., "Forest.tmx").
            spawn_waypoint: Optional waypoint name for player spawn position in target map.
                           If None, uses the target map's default spawn point.
        """
        self.target_map = target_map
        self.spawn_waypoint = spawn_waypoint
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Trigger the scene transition."""
        if not self.executed:
            if context.game_view is not None:
                context.game_view.start_scene_transition(
                    self.target_map,
                    self.spawn_waypoint,
                )
                logger.debug(
                    "ChangeSceneAction: Transitioning to %s (spawn: %s)",
                    self.target_map,
                    self.spawn_waypoint or "default",
                )
            else:
                logger.warning("ChangeSceneAction: No game_view in context, cannot transition")
            self.executed = True

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create ChangeSceneAction from a dictionary."""
        return cls(target_map=data.get("target_map", ""), spawn_waypoint=data.get("spawn_waypoint", ""))
