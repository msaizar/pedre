"""Loader for save providers."""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING, Any

from pedre.saves.registry import SaveRegistry

if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.saves.base import BaseSaveProvider
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


class SaveLoader:
    """Loads and manages save provider instances.

    The SaveLoader handles:
    1. Importing save provider modules to trigger registration
    2. Instantiating save providers
    3. Gathering state from all providers for saving
    4. Restoring state to all providers when loading

    Save providers use BaseSaveProvider interface and are registered via
    SaveRegistry, separate from the CacheRegistry used for scene caching.
    """

    def __init__(self, settings: GameSettings) -> None:
        """Initialize the save loader.

        Args:
            settings: Game configuration containing installed_saves list.
        """
        self.settings = settings
        self._instances: dict[str, BaseSaveProvider] = {}
        self._load_order: list[str] = []

    def load_modules(self) -> None:
        """Import all configured save provider modules to trigger registration."""
        installed_saves = self.settings.installed_saves or []
        for module_path in installed_saves:
            try:
                importlib.import_module(module_path)
                logger.debug("Loaded save provider module: %s", module_path)
            except ImportError:
                logger.exception("Could not load save provider module '%s'", module_path)
                raise

    def instantiate_all(self) -> dict[str, BaseSaveProvider]:
        """Create instances of all registered save providers.

        Returns:
            Dictionary mapping provider names to their instances.
        """
        self.load_modules()

        all_providers = SaveRegistry.get_all()
        if not all_providers:
            logger.warning("No save providers registered")
            return {}

        # Sort by priority (lower = earlier)
        sorted_providers = sorted(all_providers.items(), key=lambda x: x[1].priority)

        self._load_order = [name for name, _ in sorted_providers]

        for name in self._load_order:
            provider_class = all_providers[name]
            self._instances[name] = provider_class()
            logger.debug("Instantiated save provider: %s", name)

        logger.info("Instantiated %d save providers", len(self._instances))
        return self._instances

    def gather_state(self, context: GameContext) -> None:
        """Gather state from all providers.

        Args:
            context: Game context.
        """
        for name in self._load_order:
            provider = self._instances.get(name)
            if provider:
                provider.gather(context)
                logger.debug("Gathered state from save provider: %s", name)

    def restore_state(self, context: GameContext) -> bool:
        """Restore state to all providers.

        Args:
            context: Game context.

        Returns:
            True if any provider had state to restore.
        """
        any_restored = False
        for name in self._load_order:
            provider = self._instances.get(name)
            if provider and provider.restore(context):
                any_restored = True
                logger.debug("Restored state from provider: %s", name)
        return any_restored

    def clear_all(self) -> None:
        """Clear all save providers."""
        for provider in self._instances.values():
            provider.clear()
        logger.debug("Cleared all save providers")

    def to_dict(self) -> dict[str, Any]:
        """Serialize all providers for save files.

        Returns:
            Dictionary mapping provider names to their serialized state.
        """
        result: dict[str, Any] = {}
        for name, provider in self._instances.items():
            result[name] = provider.to_dict()
        return result

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore all providers from save file data.

        Args:
            data: Dictionary mapping provider names to their serialized state.
        """
        for name, provider_data in data.items():
            provider = self._instances.get(name)
            if provider:
                provider.from_dict(provider_data)
                logger.debug("Restored save provider %s from save data", name)
            else:
                logger.warning("Unknown save provider in save data: %s", name)

    def get_provider(self, name: str) -> BaseSaveProvider | None:
        """Get a save provider instance by name."""
        return self._instances.get(name)
