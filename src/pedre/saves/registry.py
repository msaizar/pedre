"""Registry for save providers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pedre.saves.base import BaseSaveProvider

logger = logging.getLogger(__name__)


class SaveRegistry:
    """Central registry for save provider classes.

    Similar to CacheRegistry but specifically for save providers.
    Save providers register themselves using the @SaveRegistry.register decorator.
    """

    _providers: ClassVar[dict[str, type[BaseSaveProvider]]] = {}

    @classmethod
    def register(cls, provider_class: type[BaseSaveProvider]) -> type[BaseSaveProvider]:
        """Register a save provider class.

        Use as a decorator:
            @SaveRegistry.register
            class MySaveProvider(BaseSaveProvider):
                name = "my_provider"
                ...

        Args:
            provider_class: The save provider class to register.

        Returns:
            The same class (allows use as decorator).
        """
        name = getattr(provider_class, "name", None)
        if not name:
            msg = f"Save provider {provider_class.__name__} must have a 'name' class attribute"
            raise ValueError(msg)

        if name in cls._providers:
            logger.warning("Re-registering save provider: %s", name)

        cls._providers[name] = provider_class
        logger.debug("Registered save provider: %s", name)
        return provider_class

    @classmethod
    def get(cls, name: str) -> type[BaseSaveProvider] | None:
        """Get a registered save provider class by name."""
        return cls._providers.get(name)

    @classmethod
    def get_all(cls) -> dict[str, type[BaseSaveProvider]]:
        """Get all registered save provider classes."""
        return cls._providers.copy()

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a save provider is registered."""
        return name in cls._providers

    @classmethod
    def clear(cls) -> None:
        """Clear all registered providers (for testing)."""
        cls._providers.clear()
