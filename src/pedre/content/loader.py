"""Content loader for dynamically loading and registering content types.

Example:
    Loading content type modules::

        from pedre.content.loader import ContentLoader
        from pedre.conf import settings

        # Configure settings in your settings.py:
        # INSTALLED_CONTENT = [
        #     "pedre.content.types",
        #     "myapp.content.enemies",  # Custom content types
        # ]

        loader = ContentLoader()
        loader.load_modules()
"""

import importlib
import logging

from pedre.conf import settings

logger = logging.getLogger(__name__)


class ContentLoader:
    """Loads content type modules to trigger registration.

    The ContentLoader is responsible for importing content type modules, which
    causes their @ContentTypeRegistry.register decorators to execute and
    register the content types with the global ContentTypeRegistry.

    This enables a Django-like plugin architecture where users can configure
    which content type modules to load via settings.INSTALLED_CONTENT.

    Example:
        Basic usage::

            loader = ContentLoader()
            loader.load_modules()

            # Now ContentRegistry() will include all registered content types
            registry = ContentRegistry()
    """

    def load_modules(self) -> None:
        """Import all configured content type modules to trigger registration.

        This imports each module path from settings.INSTALLED_CONTENT,
        which causes any @ContentTypeRegistry.register decorators to execute
        and register the content types.

        Raises:
            ImportError: If a module cannot be imported.
        """
        installed_content = settings.INSTALLED_CONTENT
        for module_path in installed_content:
            try:
                importlib.import_module(module_path)
                logger.debug("Loaded content module: %s", module_path)
            except ImportError:
                logger.exception("Could not load content module '%s'", module_path)
                raise
