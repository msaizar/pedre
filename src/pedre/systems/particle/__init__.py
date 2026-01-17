"""Particle effects system for visual polish.

This package provides:
- ParticleManager: Core particle effects system
- Particle: Individual particle data class
- Actions: Script actions for emitting particles

The particle system creates visual feedback through hearts, sparkles,
trails, and burst effects that enhance player interactions and events.
"""

from pedre.systems.particle.actions import EmitParticlesAction
from pedre.systems.particle.manager import Particle, ParticleManager

__all__ = [
    "EmitParticlesAction",
    "Particle",
    "ParticleManager",
]
