"""Registry for pluggable cache providers.

Similar to SystemRegistry but for cache providers. Caches register
themselves using the @CacheRegistry.register decorator.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pedre.caches.base import BaseCacheProvider

logger = logging.getLogger(__name__)


class CacheRegistry:
    """Central registry for all cache providers.

    Cache providers register themselves using the @CacheRegistry.register
    decorator, enabling the CacheLoader to discover and use them based
    on GameSettings.installed_caches configuration.

    Class Attributes:
        _caches: Dictionary mapping cache names to their classes.
    """

    _caches: ClassVar[dict[str, type[BaseCacheProvider]]] = {}

    @classmethod
    def register(cls, cache_class: type[BaseCacheProvider]) -> type[BaseCacheProvider]:
        """Register a cache provider class.

        Used as a decorator on cache provider classes.

        Args:
            cache_class: The cache provider class to register.

        Returns:
            The same class, allowing use as a decorator.

        Raises:
            ValueError: If the class doesn't define a 'name' attribute.
        """
        if not hasattr(cache_class, "name") or not cache_class.name:
            msg = f"Cache {cache_class.__name__} must define a 'name' class attribute"
            raise ValueError(msg)

        if cache_class.name in cls._caches:
            logger.warning(
                "Cache '%s' is being re-registered (was %s, now %s)",
                cache_class.name,
                cls._caches[cache_class.name].__name__,
                cache_class.__name__,
            )

        cls._caches[cache_class.name] = cache_class
        logger.debug("Registered cache provider: %s", cache_class.name)
        return cache_class

    @classmethod
    def get(cls, name: str) -> type[BaseCacheProvider] | None:
        """Get a registered cache provider class by name."""
        return cls._caches.get(name)

    @classmethod
    def get_all(cls) -> dict[str, type[BaseCacheProvider]]:
        """Get all registered cache providers."""
        return cls._caches.copy()

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a cache provider is registered."""
        return name in cls._caches

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (for testing)."""
        cls._caches.clear()
        logger.debug("Cache registry cleared")
