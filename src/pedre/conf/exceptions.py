"""Configuration-related exceptions for the Pedre game engine.

This module defines custom exceptions for configuration and validation errors
that occur during game initialization, asset loading, and system setup.
"""


class ConfigurationError(Exception):
    """Raised when there is an error in game configuration.

    This exception is used for invalid settings, malformed data in Tiled maps,
    incorrect asset properties, or any other configuration-related issues that
    prevent the game from initializing correctly.

    Examples:
        - Animation properties with wrong types in Tiled objects
        - Missing required properties in map objects
        - Invalid sprite sheet configurations
        - Malformed dialog or script files
    """
