"""Event loader for dynamically loading and registering events.

This module provides the EventLoader class which handles the discovery
and registration of events based on configuration.

Example:
    Loading event modules::

        from pedre.events.loader import EventLoader
        from pedre.conf import settings

        # Configure settings in your settings.py:
        # INSTALLED_EVENTS = [
        #     "pedre.systems.dialog.events",
        #     "myapp.custom_events",  # Custom events
        # ]

        loader = EventLoader()
        loader.load_modules()
"""

from __future__ import annotations

import importlib
import logging

from pedre.conf import settings

logger = logging.getLogger(__name__)


class EventLoader:
    """Loads event modules to trigger registration.

    The EventLoader is responsible for importing event modules, which
    causes their @EventRegistry.register decorators to execute and
    register the events with the global EventRegistry.

    This enables a Django-like plugin architecture where users can configure
    which event modules to load via settings.INSTALLED_EVENTS.

    Example:
        Basic usage::

            loader = EventLoader()
            loader.load_modules()

            # Now EventRegistry.get() can retrieve registered events
            event_class = EventRegistry.get("dialog_closed")
    """

    def load_modules(self) -> None:
        """Import all configured event modules to trigger registration.

        This imports each module path from settings.INSTALLED_EVENTS,
        which causes any @EventRegistry.register decorators to execute
        and register the events.

        Raises:
            ImportError: If a module cannot be imported.
        """
        installed_events = settings.INSTALLED_EVENTS
        for module_path in installed_events:
            try:
                importlib.import_module(module_path)
                logger.debug("Loaded event module: %s", module_path)
            except ImportError:
                logger.exception("Could not load event module '%s'", module_path)
                raise
