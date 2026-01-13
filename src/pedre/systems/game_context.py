"""Game context for passing state to actions and scripts.

This module provides the GameContext class, which serves as a central container
for all game systems and state. The context is passed to all actions and scripts,
giving them access to the managers and resources they need to interact with the
game world.

The GameContext pattern enables:
- Actions to be reusable and testable by providing dependencies explicitly
- Scripts to interact with any game system without tight coupling
- Easy mocking and testing by swapping out individual managers
- Centralized access to shared resources like sprite lists and waypoints

Key components stored in the context:
- Managers: Dialog, NPC, Inventory, Particle, Audio, Event Bus
- Game state: Player sprite, wall list, current scene
- Map data: Waypoints, interacted objects
- View references: Game view for accessing view-specific functionality

Example usage:
    # Create context with all managers
    context = GameContext(
        dialog_manager=dialog_mgr,
        npc_manager=npc_mgr,
        inventory_manager=inv_mgr,
        particle_manager=particle_mgr,
        audio_manager=audio_mgr,
        event_bus=event_bus,
        wall_list=walls,
        player_sprite=player,
        current_scene="town"
    )

    # Actions use the context to interact with systems
    action = DialogAction("martin", ["Hello!"])
    action.execute(context)

    # Update context when game state changes
    context.update_scene("forest")
    context.update_player(new_player_sprite)
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import arcade

    from pedre.systems import (
        AudioManager,
        DialogManager,
        InventoryManager,
        NPCManager,
        ParticleManager,
    )
    from pedre.systems.events import EventBus
    from pedre.views.game_view import GameView


class GameContext:
    """Central context object providing access to all game systems.

    The GameContext acts as a dependency injection container that holds references
    to all game managers and essential state. It's passed to every action's execute()
    method, giving actions the ability to interact with any game system they need.

    This design pattern provides several benefits:
    - **Testability**: Actions can be tested in isolation by providing mock managers
    - **Flexibility**: Actions are decoupled from how managers are created/configured
    - **Maintainability**: Adding new systems just requires adding them to the context
    - **Clarity**: Actions explicitly declare their dependencies through context usage

    The context is typically created once by the main game view and then updated as
    the game state changes (e.g., when loading new maps or updating references).

    Attributes:
        dialog_manager: Manages dialog display and state.
        npc_manager: Manages all NPCs, their movement, and interactions.
        inventory_manager: Handles player inventory and items.
        particle_manager: Creates and updates particle effects.
        audio_manager: Plays music and sound effects.
        event_bus: Publish/subscribe event system for decoupled communication.
        wall_list: SpriteList of collidable objects for physics.
        player_sprite: Reference to the player's sprite (or None if not spawned).
        game_view: Reference to the main game view (for accessing view-specific features).
        current_scene: Name of the currently loaded map/scene.
        waypoints: Dictionary mapping waypoint names to (tile_x, tile_y) coordinates.
        interacted_objects: Set of object names that the player has interacted with.
    """

    def __init__(
        self,
        dialog_manager: DialogManager,
        npc_manager: NPCManager,
        inventory_manager: InventoryManager,
        particle_manager: ParticleManager,
        audio_manager: AudioManager,
        event_bus: EventBus,
        wall_list: arcade.SpriteList,
        player_sprite: arcade.Sprite | None = None,
        game_view: GameView | None = None,
        current_scene: str = "",
        waypoints: dict[str, tuple[int, int]] | None = None,
        interacted_objects: set[str] | None = None,
    ) -> None:
        """Initialize game context with all required managers and state.

        Creates a new GameContext instance that bundles together all the game systems
        and state that actions need to execute. This is typically called once during
        game initialization and then updated as the game state changes.

        The context stores both required components (managers, wall_list) and optional
        state (player_sprite, waypoints) that may not be available at initialization time.

        Args:
            dialog_manager: Manages dialog boxes, text display, and conversation flow.
                          Actions use this to show dialog to the player.
            npc_manager: Manages all NPCs including movement, pathfinding, animations,
                        and dialog levels. Actions use this to control NPC behavior.
            inventory_manager: Manages the player's inventory, items, and equipment.
                              Actions use this to add/remove items and check inventory state.
            particle_manager: Manages visual particle effects like sparkles, hearts, and bursts.
                            Actions use this to emit particles at specific locations.
            audio_manager: Manages music and sound effect playback with volume control.
                         Actions use this to play audio in response to game events.
            event_bus: Central event system for publishing and subscribing to game events.
                      Actions can publish events to trigger scripts or notify other systems.
            wall_list: Arcade SpriteList containing all collidable objects (walls, NPCs, etc).
                      Used for collision detection and pathfinding calculations.
            player_sprite: Reference to the player's sprite. May be None if player hasn't
                         spawned yet. Updated via update_player() when player is created.
            game_view: Reference to the main GameView instance. Some actions need this to
                      access view-specific features like current_npc_name tracking or the
                      view manager for scene transitions.
            current_scene: Name of the currently loaded map/scene (e.g., "town", "forest").
                         Used to track which map is active for conditional logic.
            waypoints: Dictionary mapping waypoint names to (tile_x, tile_y) coordinates.
                      NPCs use these to navigate to named locations. Updated when loading
                      new maps via update_waypoints().
            interacted_objects: Set of object names that the player has interacted with.
                              Used by scripts and conditions to track which objects have
                              been activated. Persists across the game session.
        """
        self.dialog_manager = dialog_manager
        self.npc_manager = npc_manager
        self.inventory_manager = inventory_manager
        self.particle_manager = particle_manager
        self.audio_manager = audio_manager
        self.event_bus = event_bus
        self.wall_list = wall_list
        self.player_sprite = player_sprite
        self.game_view = game_view
        self.current_scene = current_scene
        self.waypoints = waypoints or {}
        self.interacted_objects = interacted_objects or set()

    def update_player(self, player_sprite: arcade.Sprite | None) -> None:
        """Update the player sprite reference in the context.

        This method is called when the player sprite is created or changes, such as when
        spawning into a new map or respawning after a game over. Actions that need to
        access the player sprite (for positioning, collision checks, etc.) will use the
        updated reference.

        Setting player_sprite to None is valid and indicates that no player is currently
        spawned in the game world.

        Args:
            player_sprite: The new player sprite reference, or None if no player exists.
        """
        self.player_sprite = player_sprite

    def update_wall_list(self, wall_list: arcade.SpriteList) -> None:
        """Update the collision wall list reference in the context.

        This method is called when loading a new map or when the collision geometry changes.
        The wall list contains all sprites that block movement (walls, obstacles, NPCs, etc.)
        and is used by the physics engine for collision detection and by the NPC pathfinding
        system to calculate valid paths.

        Note: This updates the reference to the entire list, not the contents of the existing
        list. Any actions or systems holding a reference to the old list will need to be
        updated separately.

        Args:
            wall_list: The new SpriteList containing all collidable sprites for the current map.
        """
        self.wall_list = wall_list

    def update_scene(self, scene_name: str) -> None:
        """Update the current scene/map name in the context.

        This method is called when transitioning between different maps or areas in the game
        world. The scene name is used by scripts and conditions to execute map-specific logic,
        such as triggering events that should only occur in certain locations.

        Scene names typically match the map filename without extension (e.g., "town", "forest",
        "dungeon_level_1"). The name should be consistent with what's used in script triggers
        and conditions.

        Args:
            scene_name: The name identifier of the new scene/map being entered.
        """
        self.current_scene = scene_name

    def update_waypoints(self, waypoints: dict[str, tuple[int, int]]) -> None:
        """Update the waypoints dictionary for the current map.

        This method is called when loading a new map that contains waypoint objects.
        Waypoints are named locations in the map (defined as point objects in Tiled) that
        NPCs can navigate to using MoveNPCAction. They provide human-readable names for
        specific coordinates, making scripts more maintainable.

        The dictionary maps waypoint names to tile coordinates (not pixel coordinates).
        For example, {"town_square": (15, 20)} means the waypoint is at tile column 15,
        row 20. The NPC pathfinding system will convert these to pixel coordinates when
        calculating paths.

        Waypoints are specific to each map and should be updated whenever transitioning
        to a new scene.

        Args:
            waypoints: Dictionary mapping waypoint names (strings) to (tile_x, tile_y)
                      coordinate tuples. Example: {"entrance": (5, 10), "exit": (25, 10)}.
        """
        self.waypoints = waypoints
