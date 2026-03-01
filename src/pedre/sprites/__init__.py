"""Sprite classes for the game.

This module provides base sprite classes.
"""

from pedre.sprites.animated_sprite import AnimatedSprite
from pedre.sprites.factory import create_sprite_from_definition
from pedre.sprites.types import AnimationStateConfig

__all__ = ["AnimatedSprite", "AnimationStateConfig", "create_sprite_from_definition"]
