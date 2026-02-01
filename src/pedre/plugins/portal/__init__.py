"""Portal plugin for map transitions.

This module provides the portal management plugin for the game, handling portal
registration, proximity detection, and event publishing when players enter portals.

The portal plugin consists of:
- PortalManager: Main plugin for managing portals and publishing events
- Portal: Data class representing a single portal

Events (registered via INSTALLED_EVENTS):
- PortalEnteredEvent: Event fired when player enters a portal zone
"""

from pedre.plugins.portal.manager import Portal, PortalManager

__all__ = [
    "Portal",
    "PortalManager",
]
