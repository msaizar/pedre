"""Particle effects system for visual polish.

This package provides:
- ParticleManager: Core particle effects system
- Particle: Individual particle data class

Actions (registered via INSTALLED_ACTIONS):
- EmitParticlesAction

The particle system creates visual feedback through hearts, sparkles,
trails, and burst effects that enhance player interactions and events.
"""

from pedre.systems.particle.manager import Particle, ParticleManager

__all__ = [
    "Particle",
    "ParticleManager",
]
