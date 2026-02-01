"""Action loader for dynamically loading and registering actions.

This module provides the ActionLoader class which handles the discovery
and registration of actions based on configuration.

Example:
    Loading action modules::

        from pedre.actions.loader import ActionLoader
        from pedre.conf import settings

        # Configure settings in your settings.py:
        # INSTALLED_ACTIONS = [
        #     "pedre.plugins.dialog.actions",
        #     "myapp.custom_actions",  # Custom actions
        # ]

        loader = ActionLoader()
        loader.load_modules()
"""

from __future__ import annotations

import importlib
import logging

from pedre.conf import settings

logger = logging.getLogger(__name__)


class ActionLoader:
    """Loads action modules to trigger registration.

    The ActionLoader is responsible for importing action modules, which
    causes their @ActionRegistry.register decorators to execute and
    register the actions with the global ActionRegistry.

    This enables a Django-like plugin architecture where users can configure
    which action modules to load via settings.INSTALLED_ACTIONS.

    Example:
        Basic usage::

            loader = ActionLoader()
            loader.load_modules()

            # Now ActionRegistry.parse() can parse registered actions
            action = ActionRegistry.parse({"type": "dialog", "speaker": "npc", "text": ["Hi"]})
    """

    def load_modules(self) -> None:
        """Import all configured action modules to trigger registration.

        This imports each module path from settings.INSTALLED_ACTIONS,
        which causes any @ActionRegistry.register decorators to execute
        and register the actions.

        Raises:
            ImportError: If a module cannot be imported.
        """
        installed_actions = settings.INSTALLED_ACTIONS
        for module_path in installed_actions:
            try:
                importlib.import_module(module_path)
                logger.debug("Loaded action module: %s", module_path)
            except ImportError:
                logger.exception("Could not load action module '%s'", module_path)
                raise
