"""Django-like settings system for Pedre.

Usage:
    # In your game project's settings.py
    from pedre.conf import global_settings

    # Override defaults
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080
    WINDOW_TITLE = "My RPG"

    # Add custom settings
    WEATHER_UPDATE_INTERVAL = 5.0

    # In your game code
    from pedre.conf import settings

    print(settings.SCREEN_WIDTH)  # 1920
    print(settings.WEATHER_UPDATE_INTERVAL)  # 5.0
"""

import importlib
import os
from typing import Any

from pedre.conf import global_settings


class LazySettings:
    """Lazy settings proxy that loads user settings on first access.

    Similar to Django's LazySettings, this defers loading until the first
    attribute access. Settings are loaded from:
    1. global_settings (framework defaults)
    2. User's settings module (overrides)

    The settings module location is determined by:
    - PEDRE_SETTINGS_MODULE environment variable, or
    - Convention: "settings" module in current directory
    """

    def __init__(self) -> None:
        """Initialize the lazy settings proxy."""
        self._wrapped: Settings | None = None

    def _setup(self) -> None:
        """Load settings from global_settings and user's settings module."""
        settings_module = os.environ.get("PEDRE_SETTINGS_MODULE", "settings")

        # Start with global settings
        self._wrapped = Settings()

        # Try to import user settings
        try:
            mod = importlib.import_module(settings_module)
            for setting in dir(mod):
                if setting.isupper():
                    setattr(self._wrapped, setting, getattr(mod, setting))
        except ImportError:
            # No user settings module found, use defaults only
            pass

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        """Get a setting value, loading settings if not yet loaded."""
        if self._wrapped is None:
            self._setup()
        if self._wrapped is None:
            msg = "Settings could not be loaded"
            raise RuntimeError(msg)
        return getattr(self._wrapped, name)

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: ANN401
        """Set a setting value."""
        if name == "_wrapped":
            self.__dict__["_wrapped"] = value
        else:
            if self._wrapped is None:
                self._setup()
            if self._wrapped is None:
                msg = "Settings could not be loaded"
                raise RuntimeError(msg)
            setattr(self._wrapped, name, value)

    def configure(self, **options: Any) -> None:  # noqa: ANN401
        """Manually configure settings (useful for testing).

        Example:
            settings.configure(
                SCREEN_WIDTH=800,
                SCREEN_HEIGHT=600
            )
        """
        if self._wrapped is None:
            self._wrapped = Settings()
        for name, value in options.items():
            setattr(self._wrapped, name, value)

    def is_configured(self) -> bool:
        """Check if settings have been loaded."""
        return self._wrapped is not None


class Settings:
    """Container for all settings with attribute access."""

    def __init__(self) -> None:
        """Initialize settings with defaults from global_settings."""
        # Load all uppercase attributes from global_settings
        for setting in dir(global_settings):
            if setting.isupper():
                setattr(self, setting, getattr(global_settings, setting))


# Global singleton instance
settings = LazySettings()

__all__ = ["LazySettings", "Settings", "global_settings", "settings"]
