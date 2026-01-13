"""Action system for reusable, chainable game actions."""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pedre.sprites import AnimatedNPC

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


class DialogAction(Action):
    """Show a dialog to the player.

    This action displays a dialog box with text from a speaker. The dialog
    is handled by the dialog manager and can consist of multiple pages that
    the player advances through.

    The action completes immediately after queuing the dialog - it doesn't
    wait for the player to finish reading. Use WaitForDialogCloseAction if
    you need to wait for the player to dismiss the dialog before proceeding.

    Example usage:
        {
            "type": "dialog",
            "speaker": "martin",
            "text": ["Hello there!", "Welcome to the game."]
        }

        # With instant display (no letter-by-letter reveal)
        {
            "type": "dialog",
            "speaker": "Narrator",
            "text": ["The world fades to black..."],
            "instant": true
        }
    """

    def __init__(self, speaker: str, text: list[str], *, instant: bool = False) -> None:
        """Initialize dialog action.

        Args:
            speaker: Name of the character speaking.
            text: List of dialog pages to show.
            instant: If True, text appears immediately without letter-by-letter reveal.
        """
        self.speaker = speaker
        self.text = text
        self.instant = instant
        self.started = False

    def execute(self, context: GameContext) -> bool:
        """Show dialog if not already showing."""
        if not self.started:
            context.dialog_manager.show_dialog(self.speaker, self.text, instant=self.instant)
            self.started = True
            logger.debug("DialogAction: Showing dialog from %s", self.speaker)

        # Action completes immediately, dialog system handles display
        return True

    def reset(self) -> None:
        """Reset the action."""
        self.started = False


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
            # Resolve waypoint to tile coordinates
            if self.waypoint in context.waypoints:
                tile_x, tile_y = context.waypoints[self.waypoint]
                logger.debug(
                    "MoveNPCAction: Resolved waypoint '%s' to tile (%d, %d)",
                    self.waypoint,
                    tile_x,
                    tile_y,
                )
            else:
                logger.warning("MoveNPCAction: Waypoint '%s' not found", self.waypoint)
                return True  # Complete immediately on error

            # Move all NPCs to the target
            for npc_name in self.npc_names:
                context.npc_manager.move_npc_to_tile(npc_name, tile_x, tile_y)
                logger.debug("MoveNPCAction: Moving %s to (%d, %d)", npc_name, tile_x, tile_y)

            self.started = True

        # Movement is asynchronous, completes immediately
        return True

    def reset(self) -> None:
        """Reset the action."""
        self.started = False


class RevealNPCsAction(Action):
    """Reveal hidden NPCs with visual effects.

    This action makes NPCs visible that have their sprite.visible property set to False.
    Hidden NPCs are not rendered and cannot be interacted with by the player. When revealed,
    the NPCs become visible, are added to the collision wall list, and a golden burst
    particle effect is emitted at each NPC's location for dramatic effect.

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
            context.npc_manager.show_npcs(self.npc_names, context.wall_list)

            # Emit burst particles at each NPC location
            for npc_name in self.npc_names:
                npc_state = context.npc_manager.npcs.get(npc_name)
                if npc_state:
                    context.particle_manager.emit_burst(
                        npc_state.sprite.center_x,
                        npc_state.sprite.center_y,
                        color=(255, 215, 0),  # Gold color for reveal
                    )

            self.executed = True
            logger.debug("RevealNPCsAction: Revealed NPCs %s", self.npc_names)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False


class PlaySFXAction(Action):
    """Play a sound effect.

    This action plays a one-time sound effect through the audio manager. Sound effects
    are short audio clips that don't loop, such as footsteps, item pickups, or interaction
    sounds.

    The sfx_file should be the filename without the path - the audio manager handles
    locating the file in the appropriate sound effects directory.

    Example usage:
        {
            "type": "play_sfx",
            "sfx": "door_open.wav"
        }
    """

    def __init__(self, sfx_file: str) -> None:
        """Initialize SFX action.

        Args:
            sfx_file: Name of the sound effect file to play.
        """
        self.sfx_file = sfx_file
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Play the sound effect."""
        if not self.executed:
            context.audio_manager.play_sfx(self.sfx_file)
            self.executed = True
            logger.debug("PlaySFXAction: Playing %s", self.sfx_file)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False


class PlayMusicAction(Action):
    """Play background music.

    This action plays or changes the background music track. Unlike sound effects,
    music tracks typically loop continuously to create atmosphere. The action can
    optionally override the default volume level.

    If music is already playing, it will be stopped and the new track will start.
    The music_file should be the filename without the path - the audio manager handles
    locating the file in the appropriate music directory.

    Example usage:
        # Standard looping music
        {
            "type": "play_music",
            "music": "town_theme.ogg"
        }

        # One-time music at custom volume
        {
            "type": "play_music",
            "music": "victory_fanfare.ogg",
            "loop": false,
            "volume": 0.8
        }
    """

    def __init__(self, music_file: str, *, loop: bool = True, volume: float | None = None) -> None:
        """Initialize music action.

        Args:
            music_file: Name of the music file to play.
            loop: Whether to loop the music (default True).
            volume: Optional volume override (0.0 to 1.0).
        """
        self.music_file = music_file
        self.loop = loop
        self.volume = volume
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Play the background music."""
        if not self.executed:
            context.audio_manager.play_music(self.music_file, loop=self.loop, volume=self.volume)
            self.executed = True
            logger.debug("PlayMusicAction: Playing %s (loop=%s)", self.music_file, self.loop)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False


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
            context.npc_manager.advance_dialog(self.npc_name)
            self.executed = True
            logger.debug("AdvanceDialogAction: Advanced %s dialog", self.npc_name)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False


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
            npc_state = context.npc_manager.npcs.get(self.npc_name)
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
            if context.game_view is not None:
                npc_state = context.npc_manager.npcs.get(self.npc_name)
                if npc_state:
                    context.game_view.current_npc_name = self.npc_name
                    context.game_view.current_npc_dialog_level = npc_state.dialog_level
                    logger.debug(
                        "SetCurrentNPCAction: Set current NPC to %s at level %d",
                        self.npc_name,
                        npc_state.dialog_level,
                    )

            self.executed = True

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False


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


class WaitForDialogCloseAction(WaitForConditionAction):
    """Wait for dialog to be closed.

    This action pauses script execution until the player dismisses the currently
    showing dialog. It's essential for creating proper dialog sequences where each
    message should be read before continuing.

    Commonly used after DialogAction to ensure the player has seen the message
    before the script proceeds to the next action.

    Example usage in a sequence:
        [
            {"type": "dialog", "speaker": "martin", "text": ["Hello!"]},
            {"type": "wait_dialog_close"},
            {"type": "dialog", "speaker": "yema", "text": ["Hi there!"]}
        ]
    """

    def __init__(self) -> None:
        """Initialize dialog wait action."""
        super().__init__(lambda ctx: not ctx.dialog_manager.showing, "Dialog closed")


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
            {"type": "wait_npc_movement", "npc": "martin"},
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
            npc_state = ctx.npc_manager.npcs.get(npc_name)
            if not npc_state:
                return True
            # NPC is not moving if path is empty and is_moving is False
            return len(npc_state.path) == 0 and not npc_state.is_moving

        super().__init__(check_movement, f"NPC {npc_name} movement complete")


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
            for npc_name in npc_names:
                npc_state = ctx.npc_manager.npcs.get(npc_name)
                if not npc_state:
                    continue
                # Check if it's an AnimatedNPC and if appear animation is complete
                if isinstance(npc_state.sprite, AnimatedNPC) and not npc_state.sprite.appear_complete:
                    return False
            # All NPCs have completed their appear animations
            return True

        super().__init__(check_all_appeared, f"NPCs {', '.join(npc_names)} appear complete")


class StartDisappearAnimationAction(Action):
    """Start the disappear animation for one or more NPCs.

    This action triggers the disappear animation for AnimatedNPCs, which plays
    a visual effect as the NPC fades away. The action also resets the disappear
    event flag so the NPCDisappearEvent can be emitted when the animation completes.

    Only AnimatedNPC sprites have disappear animations. Regular sprites will be
    silently skipped with a warning in the logs.

    This action completes immediately after starting the animation - it doesn't wait
    for the animation to finish. The NPC manager will automatically hide the sprite
    and emit the disappear event when the animation completes.

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
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Start the disappear animation."""
        if not self.executed:
            for npc_name in self.npc_names:
                npc_state = context.npc_manager.npcs.get(npc_name)
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

            self.executed = True

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False


class RemoveNPCFromWallsAction(Action):
    """Remove one or more NPCs from the collision wall list.

    This action removes NPC sprites from the wall collision list, making them
    non-solid so the player can walk through them. This is commonly used during
    disappear sequences or when an NPC should no longer block movement.

    NPCs are typically added to the wall list when they're created or revealed,
    which makes them block the player's movement. This action reverses that,
    allowing the player to pass through the NPC's space.

    Often used in combination with StartDisappearAnimationAction to make NPCs
    passable before or during their disappear animation.

    Example usage:
        # Single NPC
        {
            "type": "remove_npc_from_walls",
            "npcs": ["martin"]
        }

        # Multiple NPCs
        {
            "type": "remove_npc_from_walls",
            "npcs": ["martin", "yema"]
        }
    """

    def __init__(self, npc_names: list[str]) -> None:
        """Initialize remove NPC from walls action.

        Args:
            npc_names: List of NPC names to remove from walls.
        """
        self.npc_names = npc_names
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Remove the NPC(s) from the wall list."""
        if not self.executed:
            for npc_name in self.npc_names:
                npc_state = context.npc_manager.npcs.get(npc_name)
                if npc_state and context.wall_list and npc_state.sprite in context.wall_list:
                    context.wall_list.remove(npc_state.sprite)
                    logger.debug("RemoveNPCFromWallsAction: Removed %s from wall list", npc_name)
                else:
                    logger.debug(
                        "RemoveNPCFromWallsAction: NPC %s not in wall list or not found",
                        npc_name,
                    )

            self.executed = True

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False


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
