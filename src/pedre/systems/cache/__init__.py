"""Cache system for scene state transitions.

This system manages scene state cache, allowing systems to preserve their state
when the player leaves a scene and restore it when they return.
"""

from pedre.systems.cache.base import CacheBaseManager
from pedre.systems.cache.manager import CacheManager

__all__ = ["CacheBaseManager", "CacheManager"]
