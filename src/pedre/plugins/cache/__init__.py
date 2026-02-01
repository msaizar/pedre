"""Cache plugin for scene state transitions.

This plugin manages scene state cache, allowing plugins to preserve their state
when the player leaves a scene and restore it when they return.
"""

from pedre.plugins.cache.base import CacheBasePlugin
from pedre.plugins.cache.plugin import CachePlugin

__all__ = ["CacheBasePlugin", "CachePlugin"]
