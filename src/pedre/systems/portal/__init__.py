"""Portal system for map transitions.

This module provides the portal management system for the game, handling portal
registration, proximity detection, and event publishing when players enter portals.

The portal system consists of:
- PortalManager: Main system for managing portals and publishing events
- Portal: Data class representing a single portal
- PortalEnteredEvent: Event fired when player enters a portal zone
"""

from pedre.systems.portal.events import PortalEnteredEvent
from pedre.systems.portal.manager import Portal, PortalManager

__all__ = [
    "Portal",
    "PortalEnteredEvent",
    "PortalManager",
]
