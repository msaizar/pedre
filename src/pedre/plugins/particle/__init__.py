"""Particle effects plugin for visual polish.

This package provides:
- ParticlePlugin: Core particle effects plugin
- Particle: Individual particle data class

Actions (registered via INSTALLED_ACTIONS):
- EmitParticlesAction

The particle plugin creates visual feedback through hearts, sparkles,
trails, and burst effects that enhance player interactions and events.
"""

from pedre.plugins.particle.base import Particle, ParticleBasePlugin
from pedre.plugins.particle.plugin import ParticlePlugin

__all__ = ["Particle", "ParticleBasePlugin", "ParticlePlugin"]
