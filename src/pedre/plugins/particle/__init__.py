"""Particle effects plugin for visual polish.

This package provides:
- ParticleManager: Core particle effects plugin
- Particle: Individual particle data class

Actions (registered via INSTALLED_ACTIONS):
- EmitParticlesAction

The particle plugin creates visual feedback through hearts, sparkles,
trails, and burst effects that enhance player interactions and events.
"""

from pedre.plugins.particle.manager import Particle, ParticleManager

__all__ = [
    "Particle",
    "ParticleManager",
]
