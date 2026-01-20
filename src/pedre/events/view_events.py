"""View transition events for decoupled view management.

This module defines events that trigger transitions between different game views
(screens). Systems can publish these events to request view changes without
directly depending on the ViewManager, maintaining separation of concerns.

The ViewManager subscribes to these events and handles the actual view transitions,
allowing game systems to remain decoupled from view management.

Example usage:
    # From a game system (e.g., InputManager)
    context.event_bus.publish(ShowMenuEvent(from_game_pause=True))

    # ViewManager handles the event
    def _on_show_menu_event(self, event: ShowMenuEvent) -> None:
        self.show_menu(from_game_pause=event.from_game_pause)
"""

from dataclasses import dataclass

from pedre.events.base import Event


@dataclass
class ShowMenuEvent(Event):
    """Request to show the menu view.

    Published when a system wants to transition to the main menu, such as when
    the player presses ESC to pause the game or when a script requests a menu
    transition.

    Attributes:
        from_game_pause: If True, preserve game view for quick resume (pause menu).
                        If False, cleanup game view and auto-save (quit to menu).
    """

    from_game_pause: bool = False


@dataclass
class ShowInventoryEvent(Event):
    """Request to show the inventory view.

    Published when a system wants to open the player's inventory, typically when
    the player presses the I key or when a script triggers inventory display.
    """


@dataclass
class ShowSaveGameEvent(Event):
    """Request to show the save game view.

    Published when a system wants to open the manual save game menu, allowing
    the player to save their progress to a specific save slot (1-3).
    """


@dataclass
class ShowLoadGameEvent(Event):
    """Request to show the load game view.

    Published when a system wants to open the load game menu, allowing the
    player to load a previously saved game from available save slots.
    """
