"""Pause menu plugin for in-game menu overlay.

This plugin provides an in-game pause menu overlay that appears when ESC is pressed,
replacing the traditional menu view transition with a seamless overlay experience.
"""

from pedre.plugins.pause_menu.base import PauseMenuBasePlugin
from pedre.plugins.pause_menu.plugin import PauseMenuPlugin

__all__ = ["PauseMenuBasePlugin", "PauseMenuPlugin"]
