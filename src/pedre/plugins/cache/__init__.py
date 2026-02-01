"""Cache plugin for scene state transitions.

This plugin manages scene state cache, allowing plugins to preserve their state
when the player leaves a scene and restore it when they return.
"""

from pedre.plugins.cache.base import CacheBaseManager
from pedre.plugins.cache.manager import CacheManager

__all__ = ["CacheBaseManager", "CacheManager"]
