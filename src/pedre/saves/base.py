"""Base class for save providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext


class BaseSaveProvider(ABC):
    """Abstract base class for save providers.

    Save providers handle persisting game state to save files. Each provider
    is responsible for a specific aspect of game state (audio settings,
    inventory, NPC state, etc.).

    Unlike cache providers (which handle scene transitions), save providers
    handle persistence to disk. They use a similar interface but are registered
    and managed separately.

    Class Attributes:
        name: Unique identifier for this save provider.
        priority: Processing order (lower values run first). Default is 100.

    Example:
        @SaveRegistry.register
        class AudioSaveProvider(BaseSaveProvider):
            name: ClassVar[str] = "audio"
            priority: ClassVar[int] = 100

            def gather(self, context: GameContext) -> None:
                audio_manager = context.get_system("audio")
                self._state = audio_manager.to_dict()

            def restore(self, context: GameContext) -> bool:
                if not self._state:
                    return False
                audio_manager = context.get_system("audio")
                audio_manager.from_dict(self._state)
                return True
    """

    name: ClassVar[str]
    priority: ClassVar[int] = 100

    @abstractmethod
    def gather(self, context: GameContext) -> None:
        """Gather state from the game context for saving.

        Called when saving the game to collect current state.

        Args:
            context: Game context providing access to managers.
        """

    @abstractmethod
    def restore(self, context: GameContext) -> bool:
        """Restore state to the game context after loading.

        Called after loading a save file to apply saved state.

        Args:
            context: Game context providing access to managers.

        Returns:
            True if state was restored, False if no state to restore.
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize state for save files.

        Returns:
            Dictionary with serialized state (must be JSON-serializable).
        """

    @abstractmethod
    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore state from save file data.

        Args:
            data: Dictionary with serialized state from save file.
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear any cached state.

        Override if the provider maintains internal state that should be
        cleared when starting a new game.
        """
