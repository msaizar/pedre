"""Condition loader for dynamically loading and registering conditions.

This module provides the ConditionLoader class which handles the discovery
and registration of script conditions based on configuration.

Example:
    Loading condition modules::

        from pedre.conditions.loader import ConditionLoader
        from pedre.conf import settings

        # Configure settings in your settings.py:
        # INSTALLED_CONDITIONS = [
        #     "pedre.systems.inventory.conditions",
        #     "myapp.custom_conditions",  # Custom conditions
        # ]

        loader = ConditionLoader()
        loader.load_modules()
"""

from __future__ import annotations

import importlib
import logging

from pedre.conf import settings

logger = logging.getLogger(__name__)


class ConditionLoader:
    """Loads condition modules to trigger registration.

    The ConditionLoader is responsible for importing condition modules, which
    causes their @ConditionRegistry.register decorators to execute and
    register the conditions with the global ConditionRegistry.

    This enables a Django-like plugin architecture where users can configure
    which condition modules to load via settings.INSTALLED_CONDITIONS.

    Example:
        Basic usage::

            loader = ConditionLoader()
            loader.load_modules()

            # Now ConditionRegistry.check() can evaluate registered conditions
            result = ConditionRegistry.check("item_acquired", {"item_id": "key"}, context)
    """

    def load_modules(self) -> None:
        """Import all configured condition modules to trigger registration.

        This imports each module path from settings.INSTALLED_CONDITIONS,
        which causes any @ConditionRegistry.register decorators to execute
        and register the conditions.

        Raises:
            ImportError: If a module cannot be imported.
        """
        installed_conditions = settings.INSTALLED_CONDITIONS
        for module_path in installed_conditions:
            try:
                importlib.import_module(module_path)
                logger.debug("Loaded condition module: %s", module_path)
            except ImportError:
                logger.exception("Could not load condition module '%s'", module_path)
                raise
