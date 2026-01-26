"""Actions for NPC system."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

from pedre.actions import Action, WaitForConditionAction
from pedre.actions.registry import ActionRegistry
from pedre.sprites import AnimatedNPC

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@ActionRegistry.register("move_npc")
class MoveNPCAction(Action):
    """Move one or more NPCs to a waypoint.

    This action initiates NPC movement to a named waypoint location. The waypoint
    is resolved to tile coordinates from the game's waypoint registry, and the NPC
    pathfinding system handles the actual movement.

    The action completes immediately after initiating the movement - it doesn't
    wait for the NPC to arrive. Use WaitForNPCMovementAction if you need to wait
    for the NPC to reach the destination before proceeding.

    Multiple NPCs can be moved simultaneously by providing a list of names. This is
    useful for coordinated group movements.

    Example usage:
        # Single NPC
        {
            "type": "move_npc",
            "npcs": ["martin"],
            "waypoint": "town_square"
        }

        # Multiple NPCs
        {
            "type": "move_npc",
            "npcs": ["martin", "yema"],
            "waypoint": "forest_entrance"
        }
    """

    def __init__(
        self,
        npc_names: list[str],
        waypoint: str,
    ) -> None:
        """Initialize NPC movement action.

        Args:
            npc_names: List of NPC names to move.
            waypoint: Name of waypoint to move to.
        """
        self.npc_names = npc_names
        self.waypoint = waypoint
        self.started = False

    def execute(self, context: GameContext) -> bool:
        """Start NPC movement."""
        if not self.started:
            # Resolve waypoint to pixel coordinates
            waypoints = context.waypoint_manager.get_waypoints()
            if self.waypoint in context.waypoint_manager.get_waypoints():
                target_x, target_y = waypoints[self.waypoint]
                logger.debug(
                    "MoveNPCAction: Resolved waypoint '%s' to position (%.1f, %.1f)",
                    self.waypoint,
                    target_x,
                    target_y,
                )
            else:
                logger.warning("MoveNPCAction: Waypoint '%s' not found", self.waypoint)
                return True  # Complete immediately on error

            # Move all NPCs to the target
            npc_manager = context.npc_manager
            if npc_manager:
                for npc_name in self.npc_names:
                    npc_manager.move_npc_to_position(npc_name, target_x, target_y)
                    logger.debug("MoveNPCAction: Moving %s to (%.1f, %.1f)", npc_name, target_x, target_y)

            self.started = True

        # Movement is asynchronous, completes immediately
        return True

    def reset(self) -> None:
        """Reset the action."""
        self.started = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create MoveNPCAction from a dictionary."""
        npcs = data.get("npcs", [])
        waypoint = data.get("waypoint", "")
        return cls(npc_names=npcs, waypoint=waypoint)


@ActionRegistry.register("reveal_npcs")
class RevealNPCsAction(Action):
    """Reveal hidden NPCs with visual effects.

    This action makes NPCs visible that have their sprite.visible property set to False.
    Hidden NPCs are not rendered and cannot be interacted with by the player. When revealed,
    the NPCs become visible, are added to the collision wall list.

    NPCs can be hidden by setting sprite.visible = False during initialization in the map
    data or programmatically. AnimatedNPCs will also play their appear animation when revealed.

    Example usage:
        {
            "type": "reveal_npcs",
            "npcs": ["martin", "yema", "romi"]
        }
    """

    def __init__(self, npc_names: list[str]) -> None:
        """Initialize NPC reveal action.

        Args:
            npc_names: List of NPC names to reveal.
        """
        self.npc_names = npc_names
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Reveal NPCs and show particle effects."""
        if not self.executed:
            npc_manager = context.npc_manager
            if npc_manager:
                npc_manager.show_npcs(self.npc_names)

            self.executed = True
            logger.debug("RevealNPCsAction: Revealed NPCs %s", self.npc_names)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create RevealNPCsAction from a dictionary."""
        return cls(npc_names=data.get("npcs", []))


@ActionRegistry.register("advance_dialog")
class AdvanceDialogAction(Action):
    """Advance an NPC's dialog level.

    This action increments an NPC's dialog level by 1, which is used to track progression
    through conversation stages. NPCs can have different dialog text and behaviors at
    different levels, allowing for branching conversations and story progression.

    The dialog level is stored persistently in the NPC's state and is commonly used
    in combination with dialog conditions to show different content based on player progress.

    Example usage:
        {
            "type": "advance_dialog",
            "npc": "martin"
        }
    """

    def __init__(self, npc_name: str) -> None:
        """Initialize dialog advance action.

        Args:
            npc_name: Name of the NPC whose dialog to advance.
        """
        self.npc_name = npc_name
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Advance the dialog."""
        if not self.executed:
            npc_manager = context.npc_manager
            if npc_manager:
                npc_manager.advance_dialog(self.npc_name)
            self.executed = True
            logger.debug("AdvanceDialogAction: Advanced %s dialog", self.npc_name)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create AdvanceDialogAction from a dictionary."""
        return cls(npc_name=data.get("npc", ""))


@ActionRegistry.register("set_dialog_level")
class SetDialogLevelAction(Action):
    """Set an NPC's dialog level to a specific value.

    This action sets an NPC's dialog level to an exact value, unlike AdvanceDialogAction
    which increments by 1. This is useful for jumping to specific conversation states,
    resetting progress, or handling non-linear dialog flows.

    Use this when you need precise control over dialog state, such as when triggering
    special events or skipping conversation stages based on other game conditions.

    Example usage:
        # Jump to a specific dialog stage
        {
            "type": "set_dialog_level",
            "npc": "martin",
            "dialog_level": 5
        }

        # Reset dialog to beginning
        {
            "type": "set_dialog_level",
            "npc": "yema",
            "dialog_level": 0
        }
    """

    def __init__(self, npc_name: str, level: int) -> None:
        """Initialize set dialog level action.

        Args:
            npc_name: Name of the NPC whose dialog level to set.
            level: The dialog level to set.
        """
        self.npc_name = npc_name
        self.level = level
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Set the dialog level."""
        if not self.executed:
            npc_manager = context.npc_manager
            if npc_manager:
                npc_state = npc_manager.get_npcs().get(self.npc_name)
                if npc_state:
                    old_level = npc_state.dialog_level
                    npc_state.dialog_level = self.level
                    logger.debug(
                        "SetDialogLevelAction: Set %s dialog level from %d to %d",
                        self.npc_name,
                        old_level,
                        self.level,
                    )
                else:
                    logger.warning("SetDialogLevelAction: NPC %s not found", self.npc_name)
            self.executed = True

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create SetDialogLevelAction from a dictionary."""
        return cls(
            npc_name=data.get("npc", ""),
            level=data.get("dialog_level", 0),
        )


@ActionRegistry.register("set_current_npc")
class SetCurrentNPCAction(Action):
    """Set the current NPC tracking for dialog event attribution.

    This action is necessary when showing dialogs through scripts rather than
    direct player interaction with an NPC. It ensures that when the dialog closes,
    the correct DialogClosedEvent is published with the proper NPC attribution.

    Why this is needed:
    - When a player directly interacts with an NPC, current_npc_name is set automatically
    - When the dialog closes, a DialogClosedEvent is published with that NPC's name and level
    - Scripts can trigger on dialog_closed events to chain actions

    However, when a script shows a dialog (not from direct NPC interaction):
    - current_npc_name would be empty
    - The dialog closed event wouldn't know which NPC it belonged to
    - Subsequent scripts waiting for dialog_closed events for that NPC wouldn't trigger

    Example usage:
        {
            "type": "set_current_npc",
            "npc": "martin"
        }

    This should be used before any scripted dialog action to ensure proper event tracking.
    """

    def __init__(self, npc_name: str) -> None:
        """Initialize set current NPC action.

        Args:
            npc_name: Name of the NPC to set as current for dialog attribution.
        """
        self.npc_name = npc_name
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Set the current NPC for dialog event tracking.

        Returns:
            True when the action completes (always completes immediately).
        """
        if not self.executed:
            # Access game view through context to set current NPC
            npc_manager = context.npc_manager
            dialog_manager = context.dialog_manager
            if npc_manager and dialog_manager:
                npc_state = npc_manager.get_npcs().get(self.npc_name)
                if npc_state:
                    dialog_manager.set_current_npc_name(self.npc_name)
                    dialog_manager.set_current_dialog_level(npc_state.dialog_level)
                logger.debug(
                    "SetCurrentNPCAction: Set current NPC to %s at level %d",
                    self.npc_name,
                    npc_state.dialog_level if npc_state else 0,
                )

            self.executed = True

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create SetCurrentNPCAction from a dictionary."""
        return cls(npc_name=data.get("npc", ""))


@ActionRegistry.register("wait_for_movement")
class WaitForNPCMovementAction(WaitForConditionAction):
    """Wait for NPC to complete movement.

    This action pauses script execution until the specified NPC finishes moving
    to their destination. NPCs move asynchronously along paths, so this action
    is necessary when you need to ensure an NPC has arrived before proceeding.

    The action checks that both the NPC's path is empty and the is_moving flag
    is False, ensuring the movement is fully complete.

    Commonly used after MoveNPCAction to coordinate actions that should happen
    when the NPC reaches their destination.

    Example usage in a sequence:
        [
            {"type": "move_npc", "npc": "martin", "waypoint": "town_square"},
            {"type": "wait_for_movement", "npc": "martin"},
            {"type": "dialog", "speaker": "martin", "text": ["I made it!"]}
        ]
    """

    def __init__(self, npc_name: str) -> None:
        """Initialize NPC movement wait action.

        Args:
            npc_name: Name of the NPC to wait for.
        """
        self.npc_name = npc_name

        def check_movement(ctx: GameContext) -> bool:
            npc_manager = ctx.npc_manager
            if not npc_manager:
                return True
            npc_state = npc_manager.get_npcs().get(npc_name)
            if not npc_state:
                return True
            # NPC is not moving if path is empty and is_moving is False
            return len(npc_state.path) == 0 and not npc_state.is_moving

        super().__init__(check_movement, f"NPC {npc_name} movement complete")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create WaitForNPCMovementAction from a dictionary."""
        return cls(npc_name=data.get("npc", ""))


@ActionRegistry.register("wait_npcs_appear")
class WaitForNPCsAppearAction(WaitForConditionAction):
    """Wait for multiple NPCs to complete their appear animations.

    This action pauses script execution until all specified AnimatedNPCs finish
    their appear animation. AnimatedNPCs play a special appear animation when
    they're revealed (see RevealNPCsAction), and this action ensures that animation
    completes before proceeding.

    Only AnimatedNPC sprites have appear animations. Regular NPC sprites will be
    considered complete immediately. The action waits for all NPCs in the list
    to finish appearing.

    Commonly used after RevealNPCsAction to ensure NPCs have fully materialized
    before starting dialog or other interactions.

    Example usage in a reveal sequence:
        [
            {"type": "reveal_npcs", "npcs": ["martin", "yema"]},
            {"type": "wait_npcs_appear", "npcs": ["martin", "yema"]},
            {"type": "dialog", "speaker": "martin", "text": ["We're here!"]}
        ]
    """

    def __init__(self, npc_names: list[str]) -> None:
        """Initialize NPC appear wait action.

        Args:
            npc_names: List of NPC names to wait for.
        """
        self.npc_names = npc_names

        def check_all_appeared(ctx: GameContext) -> bool:
            npc_manager = ctx.npc_manager
            if not npc_manager:
                return True
            for npc_name in npc_names:
                npc_state = npc_manager.get_npcs().get(npc_name)
                if not npc_state:
                    continue
                # Check if it's an AnimatedNPC and if appear animation is complete
                if isinstance(npc_state.sprite, AnimatedNPC) and not npc_state.sprite.appear_complete:
                    return False
            # All NPCs have completed their appear animations
            return True

        super().__init__(check_all_appeared, f"NPCs {', '.join(npc_names)} appear complete")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create WaitForNPCsAppearAction from a dictionary."""
        return cls(npc_names=data.get("npcs", []))


@ActionRegistry.register("wait_for_npcs_disappear")
class WaitForNPCsDisappearAction(WaitForConditionAction):
    """Wait for multiple NPCs to complete their disappear animations.

    This action pauses script execution until all specified AnimatedNPCs finish
    their disappear animation. AnimatedNPCs play a special disappear animation when
    StartDisappearAnimationAction is triggered, and this action ensures that animation
    completes before proceeding.

    Only AnimatedNPC sprites have disappear animations. Regular NPC sprites will be
    considered complete immediately. The action waits for all NPCs in the list
    to finish disappearing.

    Commonly used after StartDisappearAnimationAction to ensure NPCs have fully
    faded away before continuing the script or transitioning scenes.

    Example usage in a disappear sequence:
        [
            {"type": "start_disappear_animation", "npcs": ["martin", "yema"]},
            {"type": "wait_for_npcs_disappear", "npcs": ["martin", "yema"]},
            {"type": "change_scene", "target_map": "Forest.tmx"}
        ]
    """

    def __init__(self, npc_names: list[str]) -> None:
        """Initialize NPC disappear wait action.

        Args:
            npc_names: List of NPC names to wait for.
        """
        self.npc_names = npc_names

        def check_all_disappeared(ctx: GameContext) -> bool:
            npc_manager = ctx.npc_manager
            if not npc_manager:
                return True
            for npc_name in npc_names:
                npc_state = npc_manager.get_npcs().get(npc_name)
                if not npc_state:
                    continue
                # Check if it's an AnimatedNPC and if disappear animation is complete
                if isinstance(npc_state.sprite, AnimatedNPC) and not npc_state.sprite.disappear_complete:
                    return False
            # All NPCs have completed their disappear animations
            return True

        super().__init__(check_all_disappeared, f"NPCs {', '.join(npc_names)} disappear complete")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create WaitForNPCsDisappearAction from a dictionary."""
        return cls(npc_names=data.get("npcs", []))


@ActionRegistry.register("start_disappear_animation")
class StartDisappearAnimationAction(Action):
    """Start the disappear animation for one or more NPCs.

    This action triggers the disappear animation for AnimatedNPCs, which plays
    a visual effect as the NPC fades away. The action also resets the disappear
    event flag so the NPCDisappearEvent can be emitted when the animation completes.

    Only AnimatedNPC sprites have disappear animations. Regular sprites will be
    silently skipped with a warning in the logs.

    This action waits for all NPCs to complete their disappear animations before
    completing. Once the animation finishes, the NPCs are automatically removed
    from the wall collision list so the player can walk through their space.

    Example usage:
        # Single NPC
        {
            "type": "start_disappear_animation",
            "npcs": ["martin"]
        }

        # Multiple NPCs
        {
            "type": "start_disappear_animation",
            "npcs": ["martin", "yema"]
        }
    """

    def __init__(self, npc_names: list[str]) -> None:
        """Initialize disappear animation action.

        Args:
            npc_names: List of NPC names to make disappear.
        """
        self.npc_names = npc_names
        self.animation_started = False

    def execute(self, context: GameContext) -> bool:
        """Start the disappear animation and wait for completion."""
        # Start animations for all NPCs on first call
        if not self.animation_started:
            npc_manager = context.npc_manager
            if npc_manager:
                for npc_name in self.npc_names:
                    npc_state = npc_manager.get_npcs().get(npc_name)
                    if npc_state and isinstance(npc_state.sprite, AnimatedNPC):
                        npc_state.sprite.start_disappear_animation()
                        # Reset the disappear event flag so event can be emitted
                        npc_state.disappear_event_emitted = False
                        logger.debug("StartDisappearAnimationAction: Started disappear animation for %s", npc_name)
                    else:
                        logger.warning(
                            "StartDisappearAnimationAction: NPC %s not found or not AnimatedNPC",
                            npc_name,
                        )
            self.animation_started = True

        # Check if all animations have completed
        npc_manager = context.npc_manager
        if npc_manager:
            for npc_name in self.npc_names:
                npc_state = npc_manager.get_npcs().get(npc_name)
                if not npc_state:
                    continue
                # Check if it's an AnimatedNPC and if disappear animation is still running
                if isinstance(npc_state.sprite, AnimatedNPC) and not npc_state.sprite.disappear_complete:
                    return False
        else:
            return True
        scene_manager = context.scene_manager
        # All animations complete - remove NPCs from walls
        if npc_manager and scene_manager:
            for npc_name in self.npc_names:
                npc_state = npc_manager.get_npcs().get(npc_name)
                if npc_state and npc_state.sprite:
                    scene_manager.remove_from_wall_list(npc_state.sprite)
                    logger.debug("StartDisappearAnimationAction: Removed %s from wall list", npc_name)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.animation_started = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create StartDisappearAnimationAction from a dictionary."""
        return cls(npc_names=data.get("npcs", []))
